"""Analytics and leaderboard client backed by Supabase REST API.

Design rules:
  - NEVER raises exceptions — all network calls are wrapped in try/except.
  - Desktop: I/O happens in a daemon thread (non-blocking).
  - Web (pyodide): urllib.request works synchronously; calls are light enough
    that a brief pause at run-end is imperceptible.
  - If SUPABASE_URL is empty (not configured), all methods are silent no-ops.

Tables expected in Supabase (see supabase/schema.sql):
  run_analytics  — one row per completed run
  leaderboard    — one row per player, best_wave; updated via GREATEST
"""

import json
import sys
import logging
import threading
import urllib.request
import urllib.error
from typing import Callable

log = logging.getLogger("telemetry")


class TelemetryClient:
    """Supabase REST client for run analytics and leaderboard."""

    def __init__(self, url: str, anon_key: str):
        self._url = url.rstrip("/") if url else ""
        self._key = anon_key
        self._enabled = bool(self._url and self._key)

    # ── Public API ─────────────────────────────────────────────────────────────

    def submit_run(self, player_id: str, display_name: str, platform: str,
                   run_entry: dict) -> None:
        """Append one run record to run_analytics.  run_entry is the same
        dict that RunStats.save_to_log() builds."""
        if not self._enabled:
            return
        payload = {
            "player_id": player_id,
            "display_name": display_name,
            "platform": platform,
            **run_entry,
            # Serialise nested dicts that Supabase stores as jsonb
            "upgrades": json.dumps(run_entry.get("upgrades", [])),
            "weapons": json.dumps(run_entry.get("weapons", {})),
            "passives": json.dumps(run_entry.get("passives", {})),
            "zones_completed": json.dumps(run_entry.get("zones_completed", [])),
        }
        self._post_async(f"{self._url}/rest/v1/run_analytics", payload)

    def submit_leaderboard(self, player_id: str, display_name: str,
                           platform: str, char_class: str,
                           best_wave: int, run_date: str) -> None:
        """Upsert the player's best wave onto the global leaderboard.
        The DB GREATEST() guard means stored best_wave only ever increases."""
        if not self._enabled:
            return
        payload = {
            "player_id": player_id,
            "display_name": display_name,
            "platform": platform,
            "char_class": char_class,
            "best_wave": best_wave,
            "best_run_date": run_date,
        }
        self._post_async(
            f"{self._url}/rest/v1/leaderboard",
            payload,
            extra_headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
        )

    def fetch_leaderboard(self, limit: int = 10) -> list[dict]:
        """Return top-N leaderboard rows synchronously (called from UI thread).
        Returns [] on any error."""
        if not self._enabled:
            return []
        url = (
            f"{self._url}/rest/v1/leaderboard"
            f"?select=display_name,char_class,best_wave,best_run_date,platform"
            f"&order=best_wave.desc&limit={limit}"
        )
        try:
            req = urllib.request.Request(url, headers=self._base_headers())
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            log.debug("fetch_leaderboard failed: %s", e)
            return []

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _base_headers(self) -> dict:
        return {
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        }

    def _post(self, url: str, payload: dict,
              extra_headers: dict | None = None) -> None:
        """Blocking POST — call from background thread on desktop."""
        try:
            headers = self._base_headers()
            if extra_headers:
                headers.update(extra_headers)
            data = json.dumps(payload).encode()
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=8) as resp:
                log.debug("POST %s → %d", url.split("/rest/v1/")[-1], resp.status)
        except Exception as e:
            log.debug("POST %s failed: %s", url, e)

    def _post_async(self, url: str, payload: dict,
                    extra_headers: dict | None = None) -> None:
        """Fire-and-forget POST.  Uses a daemon thread on desktop.
        Skipped on web — blocking urllib hangs in WASM (no blocking I/O)."""
        if sys.platform == "emscripten":
            # WASM has no blocking network I/O — skip silently
            return
        else:
            t = threading.Thread(
                target=self._post,
                args=(url, payload, extra_headers),
                daemon=True,
            )
            t.start()
