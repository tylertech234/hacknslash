"""Global leaderboard — two-tier ranking from run_analytics.

Tier 1  "Champions"  — completed all 3 zones, ranked by fastest runtime.
Tier 2  "Contenders" — everyone else, ranked by highest damage dealt.

Fetches rows from Supabase once on activate().  Shows a loading state
while the request is in-flight (background thread on desktop, blocking
but brief on web).  Falls back to an "unavailable" notice on any error.
"""

import json
import threading
import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from src.systems.telemetry import TelemetryClient

_CLASS_COLORS = {
    "knight":  (100, 160, 255),
    "archer":  (100, 220, 140),
    "jester":  (255, 140, 220),
}
_CLASS_LABELS = {
    "knight": "Knight",
    "archer": "Ranger",
    "jester": "Jester",
}
_RANK_COLORS = {1: (255, 215, 0), 2: (192, 192, 192), 3: (205, 127, 50)}
_ALL_ZONES = {"wasteland", "city", "abyss"}


def _fmt_time(seconds: float | None) -> str:
    """Format seconds as M:SS or H:MM:SS."""
    if seconds is None or seconds <= 0:
        return "--:--"
    s = int(seconds)
    if s >= 3600:
        return f"{s // 3600}:{(s % 3600) // 60:02d}:{s % 60:02d}"
    return f"{s // 60}:{s % 60:02d}"


def _fmt_damage(dmg: int) -> str:
    """Format large damage numbers compactly: 12345 → 12.3K."""
    if dmg >= 1_000_000:
        return f"{dmg / 1_000_000:.1f}M"
    if dmg >= 10_000:
        return f"{dmg / 1_000:.1f}K"
    return f"{dmg:,}"


def _completed_all_zones(row: dict) -> bool:
    """Check if a run completed all 3 zones."""
    zc = row.get("zones_completed")
    if not zc:
        return False
    if isinstance(zc, str):
        try:
            zc = json.loads(zc)
        except (json.JSONDecodeError, TypeError):
            return False
    if isinstance(zc, list):
        return _ALL_ZONES.issubset(set(zc))
    return False


def _build_tiers(rows: list[dict], max_per_tier: int = 10) -> tuple[list[dict], list[dict]]:
    """Deduplicate per player and split into champion / contender tiers.

    Champions: best (fastest) completing run per player.
    Contenders: best (highest damage) non-completing run per player.
    """
    champ_best: dict[str, dict] = {}   # player_id → best completing run
    cont_best: dict[str, dict] = {}    # player_id → best non-completing run

    for row in rows:
        pid = row.get("player_id", "")
        if not pid:
            continue
        rt = row.get("run_time_s")
        dmg = row.get("damage_dealt") or 0

        if _completed_all_zones(row):
            if rt is None or rt <= 0:
                continue  # skip champions with missing/invalid runtime
            prev = champ_best.get(pid)
            if prev is None or rt < (prev.get("run_time_s") or float("inf")):
                champ_best[pid] = row
        else:
            prev = cont_best.get(pid)
            if prev is None or dmg > (prev.get("damage_dealt") or 0):
                cont_best[pid] = row

    # Remove contender entries for players who are already champions
    for pid in champ_best:
        cont_best.pop(pid, None)

    champions = sorted(champ_best.values(), key=lambda r: r.get("run_time_s") or float("inf"))
    contenders = sorted(cont_best.values(), key=lambda r: r.get("damage_dealt") or 0, reverse=True)
    return champions[:max_per_tier], contenders[:max_per_tier]


class LeaderboardScreen:
    """Full-screen leaderboard overlay."""

    def __init__(self, telemetry: TelemetryClient):
        self._telemetry = telemetry
        self.active = False
        self._champions: list[dict] = []
        self._contenders: list[dict] = []
        self._loading = False
        self._error = ""
        self._local_player_id: str = ""

        self._font_title = pygame.font.SysFont("consolas", 34, bold=True)
        self._font_section = pygame.font.SysFont("consolas", 18, bold=True)
        self._font_head = pygame.font.SysFont("consolas", 15, bold=True)
        self._font_row = pygame.font.SysFont("consolas", 15)
        self._font_hint = pygame.font.SysFont("consolas", 14)

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def activate(self, local_player_id: str = "") -> None:
        self.active = True
        self._local_player_id = local_player_id
        self._champions = []
        self._contenders = []
        self._loading = True
        self._error = ""
        self._fetch_async()

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Returns 'close' when the player exits."""
        if not self.active:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_TAB):
                self.active = False
                return "close"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self._panel_rect().collidepoint(event.pos):
                self.active = False
                return "close"
        return None

    # ── Data fetch ─────────────────────────────────────────────────────────────

    def _fetch_async(self) -> None:
        t = threading.Thread(target=self._do_fetch, daemon=True)
        t.start()

    def _do_fetch(self) -> None:
        champ_rows = self._telemetry.fetch_champions(limit=50)
        cont_rows = self._telemetry.fetch_contenders(limit=50)
        if champ_rows is None:
            champ_rows = []
        if cont_rows is None:
            cont_rows = []
        combined = champ_rows + cont_rows
        if combined:
            self._champions, self._contenders = _build_tiers(combined)
        self._loading = False
        if not combined and self._telemetry._enabled:
            self._error = "No scores yet — be the first!"
        elif not self._telemetry._enabled:
            self._error = "Leaderboard not configured."

    # ── Drawing ────────────────────────────────────────────────────────────────

    def _panel_rect(self) -> pygame.Rect:
        pw = min(860, SCREEN_WIDTH - 40)
        ph = min(620, SCREEN_HEIGHT - 40)
        return pygame.Rect(
            SCREEN_WIDTH // 2 - pw // 2,
            SCREEN_HEIGHT // 2 - ph // 2,
            pw, ph,
        )

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        screen.blit(overlay, (0, 0))

        panel = self._panel_rect()
        pygame.draw.rect(screen, (8, 12, 22), panel, border_radius=10)
        pygame.draw.rect(screen, (60, 90, 160), panel, 2, border_radius=10)

        cx = panel.centerx

        title = self._font_title.render("LEADERBOARD", True, (100, 200, 255))
        screen.blit(title, title.get_rect(center=(cx, panel.top + 32)))

        if self._loading:
            loading = self._font_head.render("Loading...", True, (140, 160, 190))
            screen.blit(loading, loading.get_rect(center=(cx, panel.centery)))
        elif self._error:
            err = self._font_head.render(self._error, True, (160, 160, 180))
            screen.blit(err, err.get_rect(center=(cx, panel.centery)))
        else:
            self._draw_tiers(screen, panel)

        hint = self._font_hint.render("Esc / Backspace to close", True, (60, 70, 90))
        screen.blit(hint, hint.get_rect(center=(cx, panel.bottom - 16)))

    def _draw_tiers(self, screen: pygame.Surface, panel: pygame.Rect) -> None:
        y = panel.top + 58

        if self._champions:
            y = self._draw_section(screen, panel, y,
                                   "CHAMPIONS  —  All Zones Cleared  —  Fastest Time",
                                   (255, 215, 80), self._champions, sort_key="time")
            y += 8

        if self._contenders:
            y = self._draw_section(screen, panel, y,
                                   "CONTENDERS  —  Highest Damage Dealt",
                                   (180, 140, 255), self._contenders, sort_key="damage")

        if not self._champions and not self._contenders:
            msg = self._font_head.render("No scores yet — be the first!", True, (160, 160, 180))
            screen.blit(msg, msg.get_rect(center=(panel.centerx, panel.centery)))

    def _draw_section(self, screen: pygame.Surface, panel: pygame.Rect,
                      y: int, label: str, label_color: tuple,
                      rows: list[dict], sort_key: str) -> int:
        # Section header
        lbl = self._font_section.render(label, True, label_color)
        screen.blit(lbl, lbl.get_rect(center=(panel.centerx, y)))
        y += 24

        # Column headers
        col_x = self._col_positions(panel)
        headers = ["#", "Name", "Class", "Wave", "Kills", "Damage", "Time", "Date"]

        for x, h in zip(col_x, headers):
            surf = self._font_head.render(h, True, (120, 150, 200))
            screen.blit(surf, (x, y))
        y += 18
        pygame.draw.line(screen, (40, 60, 100),
                         (panel.left + 20, y), (panel.right - 20, y))
        y += 6

        row_h = 26
        for i, row in enumerate(rows):
            if y + row_h > panel.bottom - 34:
                break
            rank = i + 1
            pid = row.get("player_id", "")
            is_local = pid == self._local_player_id if self._local_player_id else False

            if is_local:
                hi = pygame.Rect(panel.left + 18, y - 2, panel.width - 36, row_h - 2)
                pygame.draw.rect(screen, (20, 40, 70), hi, border_radius=3)
                pygame.draw.rect(screen, (80, 140, 220), hi, 1, border_radius=3)

            rank_col = _RANK_COLORS.get(rank, (160, 170, 180))
            name_col = (240, 245, 255) if is_local else (180, 195, 210)
            char = row.get("char_class", "knight")
            class_col = _CLASS_COLORS.get(char, (180, 180, 180))
            val_col = (220, 200, 120) if is_local else (180, 180, 180)

            rt = row.get("run_time_s")
            dmg = row.get("damage_dealt") or 0
            created = str(row.get("created_at", ""))[:10]

            cells = [
                (f"{rank}", rank_col),
                (str(row.get("display_name", "???"))[:16], name_col),
                (_CLASS_LABELS.get(char, char.capitalize()), class_col),
                (str(row.get("wave", 0)), val_col),
                (str(row.get("kills", 0)), val_col),
                (_fmt_damage(dmg), (255, 180, 80) if sort_key == "damage" else val_col),
                (_fmt_time(rt), (80, 255, 160) if sort_key == "time" else val_col),
                (created, (100, 120, 140)),
            ]
            for x, (text, col) in zip(col_x, cells):
                surf = self._font_row.render(text, True, col)
                screen.blit(surf, (x, y))
            y += row_h

        return y

    def _col_positions(self, panel: pygame.Rect) -> list[int]:
        l = panel.left
        return [l + 22, l + 58, l + 260, l + 370, l + 440, l + 520, l + 640, l + 740]
