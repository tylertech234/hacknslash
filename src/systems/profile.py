"""Player profile — identity, per-player save namespacing, and storage backends.

Desktop layout:
  profile.json                           ← root pointer (player_id only)
  profiles/{player_id}/profile.json      ← display name, consent, etc.
  profiles/{player_id}/legacy_save.json
  profiles/{player_id}/compendium_save.json

Web (pyodide/pygbag localStorage) layout:
  localStorage["cyber_survivor:profile.json"]
  localStorage["cyber_survivor:{player_id}:legacy_save.json"]
  localStorage["cyber_survivor:{player_id}:compendium_save.json"]

On first launch, any existing root-level legacy/compendium saves are migrated
into the new per-player directory automatically.
"""

import json
import os
import sys
import uuid
import logging

log = logging.getLogger("profile")

_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_ROOT_POINTER = os.path.join(_PROJECT_ROOT, "profile.json")


# ── Storage backends ───────────────────────────────────────────────────────────

class StorageBackend:
    """Abstract: read/write named JSON blobs for one player."""

    def read(self, filename: str) -> dict | None:
        raise NotImplementedError

    def write(self, filename: str, data: dict) -> None:
        raise NotImplementedError

    def exists(self, filename: str) -> bool:
        raise NotImplementedError


class FileStorage(StorageBackend):
    """Saves JSON files under a local directory."""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def read(self, filename: str) -> dict | None:
        path = os.path.join(self.base_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def write(self, filename: str, data: dict) -> None:
        os.makedirs(self.base_dir, exist_ok=True)
        path = os.path.join(self.base_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def exists(self, filename: str) -> bool:
        return os.path.exists(os.path.join(self.base_dir, filename))


class WebStorage(StorageBackend):
    """Persists JSON to browser localStorage via pygbag's JS interop.

    Key format: "cyber_survivor:{namespace}:{filename}"
    Pass namespace="" for the root profile pointer.
    """

    _BASE = "cyber_survivor"

    def __init__(self, namespace: str = ""):
        self._ns = namespace  # e.g. player UUID

    def _key(self, filename: str) -> str:
        if self._ns:
            return f"{self._BASE}:{self._ns}:{filename}"
        return f"{self._BASE}:{filename}"

    def _get_ls(self):
        from js import localStorage  # type: ignore  # injected by pygbag
        return localStorage

    def read(self, filename: str) -> dict | None:
        try:
            raw = self._get_ls().getItem(self._key(filename))
            if raw:
                return json.loads(str(raw))
        except Exception as e:
            log.debug("WebStorage.read(%s) failed: %s", filename, e)
        return None

    def write(self, filename: str, data: dict) -> None:
        try:
            self._get_ls().setItem(self._key(filename), json.dumps(data))
        except Exception as e:
            log.debug("WebStorage.write(%s) failed: %s", filename, e)

    def exists(self, filename: str) -> bool:
        try:
            return self._get_ls().getItem(self._key(filename)) is not None
        except Exception:
            return False


# ── Player profile ─────────────────────────────────────────────────────────────

class PlayerProfile:
    """Runtime identity carrier.  Also passed to LegacyData and Compendium so
    they save into the right per-player directory / localStorage namespace."""

    def __init__(
        self,
        player_id: str,
        display_name: str,
        platform: str,
        analytics_consent: bool | None,
        storage: StorageBackend,
    ):
        self.player_id = player_id
        self.display_name = display_name
        self.platform = platform
        self.analytics_consent = analytics_consent  # None = not yet decided
        self.storage = storage

    # ── Persistence ────────────────────────────────────────────────────────────

    def save(self) -> None:
        """Persist profile metadata (name, consent) to per-player storage."""
        self.storage.write("profile.json", {
            "player_id": self.player_id,
            "display_name": self.display_name,
            "platform": self.platform,
            "analytics_consent": self.analytics_consent,
        })
        # Update the root pointer so future launches can find the player quickly
        _write_root_pointer(self.player_id, self.display_name, self.analytics_consent)

    def needs_name(self) -> bool:
        return not self.display_name

    def needs_consent(self) -> bool:
        return self.analytics_consent is None


# ── Factory ────────────────────────────────────────────────────────────────────

def create_profile() -> PlayerProfile:
    """Load the existing profile or create a brand-new one.  Never raises."""
    return _load_desktop_profile()


# ── Desktop implementation ─────────────────────────────────────────────────────

def _load_desktop_profile() -> PlayerProfile:
    # 1. Read root pointer to get player_id
    pid: str | None = None
    try:
        with open(_ROOT_POINTER, "r", encoding="utf-8") as f:
            root = json.load(f)
        if isinstance(root, dict) and root.get("player_id"):
            pid = root["player_id"]
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    if not pid:
        pid = str(uuid.uuid4())
        _migrate_root_saves(pid)

    # 2. Per-player storage inside profiles/{pid}/
    profile_dir = os.path.join(_PROJECT_ROOT, "profiles", pid)
    storage = FileStorage(profile_dir)

    # 3. Load profile metadata from per-player directory
    data = storage.read("profile.json") or {}
    name = data.get("display_name", "")
    consent = data.get("analytics_consent", None)

    profile = PlayerProfile(pid, name, "desktop", consent, storage)
    profile.save()  # ensures root pointer is written
    return profile


def _write_root_pointer(player_id: str, display_name: str, consent) -> None:
    try:
        with open(_ROOT_POINTER, "w", encoding="utf-8") as f:
            json.dump({
                "player_id": player_id,
                "display_name": display_name,
                "analytics_consent": consent,
            }, f, indent=2)
    except OSError as e:
        log.warning("Could not write root profile pointer: %s", e)


def _migrate_root_saves(new_pid: str) -> None:
    """Move any existing root-level saves into the new per-player directory."""
    dest_dir = os.path.join(_PROJECT_ROOT, "profiles", new_pid)
    for fname in ("legacy_save.json", "compendium_save.json"):
        src = os.path.join(_PROJECT_ROOT, fname)
        if os.path.exists(src):
            try:
                os.makedirs(dest_dir, exist_ok=True)
                dst = os.path.join(dest_dir, fname)
                if not os.path.exists(dst):  # never overwrite a newer file
                    import shutil
                    shutil.move(src, dst)
                    log.info("Migrated %s → profiles/%s/%s", fname, new_pid, fname)
            except OSError as e:
                log.warning("Migration of %s failed: %s", fname, e)
