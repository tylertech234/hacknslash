"""Global leaderboard screen — top players by best wave reached.

Fetches rows from Supabase once on activate().  Shows a loading state
while the request is in-flight (background thread on desktop, blocking
but brief on web).  Falls back to an "unavailable" notice on any error.
"""

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


class LeaderboardScreen:
    """Full-screen leaderboard overlay."""

    def __init__(self, telemetry: TelemetryClient):
        self._telemetry = telemetry
        self.active = False
        self._rows: list[dict] = []
        self._loading = False
        self._error = ""
        self._local_player_id: str = ""

        self._font_title = pygame.font.SysFont("consolas", 34, bold=True)
        self._font_head = pygame.font.SysFont("consolas", 17, bold=True)
        self._font_row = pygame.font.SysFont("consolas", 17)
        self._font_hint = pygame.font.SysFont("consolas", 14)

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def activate(self, local_player_id: str = "") -> None:
        self.active = True
        self._local_player_id = local_player_id
        self._rows = []
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
            # Click anywhere outside the panel closes it
            if not self._panel_rect().collidepoint(event.pos):
                self.active = False
                return "close"
        return None

    # ── Data fetch ─────────────────────────────────────────────────────────────

    def _fetch_async(self) -> None:
        t = threading.Thread(target=self._do_fetch, daemon=True)
        t.start()

    def _do_fetch(self) -> None:
        rows = self._telemetry.fetch_leaderboard(limit=15)
        if rows is None:
            rows = []
        self._rows = rows
        self._loading = False
        if not rows and self._telemetry._enabled:
            self._error = "No scores yet — be the first!"
        elif not self._telemetry._enabled:
            self._error = "Leaderboard not configured."

    # ── Drawing ────────────────────────────────────────────────────────────────

    def _panel_rect(self) -> pygame.Rect:
        pw, ph = 760, 560
        return pygame.Rect(
            SCREEN_WIDTH // 2 - pw // 2,
            SCREEN_HEIGHT // 2 - ph // 2,
            pw, ph,
        )

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return

        # Dim background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        screen.blit(overlay, (0, 0))

        panel = self._panel_rect()
        pygame.draw.rect(screen, (8, 12, 22), panel, border_radius=10)
        pygame.draw.rect(screen, (60, 90, 160), panel, 2, border_radius=10)

        cx = panel.centerx

        # Title
        title = self._font_title.render("LEADERBOARD", True, (100, 200, 255))
        screen.blit(title, title.get_rect(center=(cx, panel.top + 36)))

        # Subtitle
        sub = self._font_hint.render("Top players by highest wave reached", True, (80, 100, 130))
        screen.blit(sub, sub.get_rect(center=(cx, panel.top + 68)))

        if self._loading:
            loading = self._font_head.render("Loading...", True, (140, 160, 190))
            screen.blit(loading, loading.get_rect(center=(cx, panel.centery)))
        elif self._error:
            err = self._font_head.render(self._error, True, (160, 160, 180))
            screen.blit(err, err.get_rect(center=(cx, panel.centery)))
        else:
            self._draw_table(screen, panel)

        # Close hint
        hint = self._font_hint.render("Esc / Backspace to close", True, (60, 70, 90))
        screen.blit(hint, hint.get_rect(center=(cx, panel.bottom - 20)))

    def _draw_table(self, screen: pygame.Surface, panel: pygame.Rect) -> None:
        col_x = [panel.left + 28, panel.left + 80, panel.left + 330, panel.left + 490, panel.left + 620]
        headers = ["#", "Name", "Class", "Wave", "Date"]

        header_y = panel.top + 96
        for x, h in zip(col_x, headers):
            surf = self._font_head.render(h, True, (120, 150, 200))
            screen.blit(surf, (x, header_y))

        pygame.draw.line(screen, (40, 60, 100),
                         (panel.left + 20, header_y + 22),
                         (panel.right - 20, header_y + 22))

        row_h = 34
        row_y = header_y + 30
        for i, row in enumerate(self._rows):
            rank = i + 1
            pid = row.get("player_id", "")
            is_local = pid == self._local_player_id if self._local_player_id else False

            # Row highlight for local player
            if is_local:
                hi_rect = pygame.Rect(panel.left + 18, row_y - 4, panel.width - 36, row_h - 4)
                pygame.draw.rect(screen, (20, 40, 70), hi_rect, border_radius=4)
                pygame.draw.rect(screen, (80, 140, 220), hi_rect, 1, border_radius=4)

            rank_col = _RANK_COLORS.get(rank, (160, 170, 180))
            name_col = (240, 245, 255) if is_local else (180, 195, 210)
            char = row.get("char_class", "knight")
            class_col = _CLASS_COLORS.get(char, (180, 180, 180))
            wave_col = (255, 220, 80) if is_local else (220, 200, 120)

            cells = [
                (f"{rank}", rank_col),
                (row.get("display_name", "???")[:18], name_col),
                (_CLASS_LABELS.get(char, char.capitalize()), class_col),
                (str(row.get("best_wave", 0)), wave_col),
                (str(row.get("best_run_date", ""))[:10], (100, 120, 140)),
            ]
            for x, (text, col) in zip(col_x, cells):
                surf = self._font_row.render(text, True, col)
                screen.blit(surf, (x, row_y))

            row_y += row_h
            if row_y + row_h > panel.bottom - 40:
                break
