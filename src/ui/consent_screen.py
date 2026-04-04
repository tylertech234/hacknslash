"""Analytics consent modal — shown once before the player's first run.

Sets profile.analytics_consent (True/False) and saves the profile.
Never shown again once a decision is made.
"""

import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT


_BODY_LINES = [
    "Help improve Cyber Survivor by sharing anonymous play data.",
    "",
    "What we collect:",
    "  \u2022  Your display name (chosen by you)",
    "  \u2022  Wave reached, class played, run time",
    "  \u2022  Upgrades chosen, damage dealt / taken",
    "  \u2022  Which enemies killed you (crash analytics)",
    "",
    "What we do NOT collect:",
    "  \u2022  Any personally identifying information",
    "  \u2022  Your IP address or location",
    "  \u2022  Anything outside this game",
    "",
    "You can change this at any time in Settings.",
]


class ConsentScreen:
    """One-time analytics opt-in modal."""

    def __init__(self):
        self.active = False
        self.result: bool | None = None   # True = allowed, False = declined
        self._font_title = pygame.font.SysFont("consolas", 30, bold=True)
        self._font_body = pygame.font.SysFont("consolas", 16)
        self._font_btn = pygame.font.SysFont("consolas", 20, bold=True)
        self._selected = 0  # 0 = Allow, 1 = No Thanks

    def activate(self) -> None:
        self.active = True
        self.result = None
        self._selected = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.active:
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._selected = 0
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self._selected = 1
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self._confirm()
            elif event.key == pygame.K_ESCAPE:
                self._selected = 1
                self._confirm()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for i, rect in enumerate(self._btn_rects()):
                if rect.collidepoint(mx, my):
                    self._selected = i
                    self._confirm()

    def _confirm(self) -> None:
        self.result = (self._selected == 0)
        self.active = False

    def _btn_rects(self) -> list[pygame.Rect]:
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        btn_y = cy + 160
        return [
            pygame.Rect(cx - 200, btn_y, 180, 44),   # Allow
            pygame.Rect(cx + 20,  btn_y, 180, 44),   # No Thanks
        ]

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return

        # Dim overlay over whatever is behind
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        # Panel
        panel_rect = pygame.Rect(cx - 380, cy - 220, 760, 460)
        pygame.draw.rect(screen, (10, 14, 24), panel_rect, border_radius=10)
        pygame.draw.rect(screen, (60, 100, 160), panel_rect, 2, border_radius=10)

        # Title
        title = self._font_title.render("SHARE PLAY DATA?", True, (100, 200, 255))
        screen.blit(title, title.get_rect(center=(cx, cy - 195)))

        # Body text
        line_y = cy - 155
        for line in _BODY_LINES:
            if line:
                col = (140, 180, 140) if line.startswith("  •") else (180, 190, 200)
                if line.startswith("What we"):
                    col = (220, 220, 240)
                surf = self._font_body.render(line, True, col)
                screen.blit(surf, surf.get_rect(midleft=(cx - 340, line_y)))
            line_y += 20

        # Buttons
        labels = ["ALLOW", "NO THANKS"]
        colors_active = [(40, 160, 80), (130, 50, 50)]
        colors_inactive = [(25, 40, 50), (25, 40, 50)]
        btns = self._btn_rects()
        for i, (rect, label) in enumerate(zip(btns, labels)):
            col = colors_active[i] if self._selected == i else colors_inactive[i]
            pygame.draw.rect(screen, col, rect, border_radius=6)
            border = (100, 220, 100) if i == 0 else (200, 100, 100)
            pygame.draw.rect(screen, border if self._selected == i else (60, 70, 90),
                             rect, 2, border_radius=6)
            txt = self._font_btn.render(label, True, (230, 255, 230) if self._selected == i else (130, 140, 150))
            screen.blit(txt, txt.get_rect(center=rect.center))

        # Keyboard hint
        hint_font = pygame.font.SysFont("consolas", 13)
        hint = hint_font.render("← → to select  •  Enter to confirm  •  Esc = No Thanks", True, (70, 80, 100))
        screen.blit(hint, hint.get_rect(center=(cx, cy + 220)))
