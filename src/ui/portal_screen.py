"""Portal zone-transition menu — shown when the player steps into the portal."""

import pygame
import math
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, YELLOW, WHITE


_ZONE_DISPLAY = {
    "wasteland": "The Forest",
    "city":      "Ruined Metropolis",
    "abyss":     "The Abyss",
}


class PortalMenuScreen:
    """Full-screen overlay shown when player enters a portal.

    Returns one of: "continue", "summary", "compendium" via handle_event().
    None means still active.
    """

    def __init__(self):
        self.active = False
        self.next_zone: str = ""
        self.current_zone: str = ""
        self.selected = 1          # default highlight on "Continue"
        self._options = []
        self._spin = 0.0
        self._font_big   = pygame.font.SysFont("consolas", 36, bold=True)
        self._font_med   = pygame.font.SysFont("consolas", 22, bold=True)
        self._font_small = pygame.font.SysFont("consolas", 16)

    def activate(self, current_zone: str, next_zone: str):
        self.active = True
        self.current_zone = current_zone
        self.next_zone = next_zone
        self.selected = 1
        # Build option list
        self._options = [
            ("summary",    "VIEW RUN PROGRESS",  (100, 200, 255)),
            ("continue",   "ENTER NEXT ZONE",    (100, 255, 130)),
            ("compendium", "OPEN COMPENDIUM",    (200, 150, 255)),
        ]

    def handle_event(self, event: pygame.event.Event):
        """Returns action string or None."""
        if not self.active:
            return None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_w, pygame.K_UP):
                self.selected = (self.selected - 1) % len(self._options)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.selected = (self.selected + 1) % len(self._options)
            elif event.key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE):
                action = self._options[self.selected][0]
                if action == "continue":
                    self.active = False
                return action
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for i, (action, _, _) in enumerate(self._options):
                r = self._option_rect(i)
                if r.collidepoint(mx, my):
                    if action == "continue":
                        self.active = False
                    return action
        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            for i in range(len(self._options)):
                if self._option_rect(i).collidepoint(mx, my):
                    self.selected = i
        return None

    def _option_rect(self, idx: int) -> pygame.Rect:
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2 + 20
        w, h = 360, 52
        spacing = 68
        y = cy + (idx - 1) * spacing
        return pygame.Rect(cx - w // 2, y - h // 2, w, h)

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return
        now = pygame.time.get_ticks()
        self._spin = now * 0.001

        # Dark translucent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH // 2

        # Spinning portal glyph behind header
        self._draw_portal_glyph(surface, cx, SCREEN_HEIGHT // 2 - 130, now)

        # "ZONE CLEARED!" header
        zone_name = _ZONE_DISPLAY.get(self.current_zone, self.current_zone.replace("_", " ").title())
        cleared_surf = self._font_big.render(f"{zone_name.upper()} CLEARED!", True, (80, 255, 120))
        surface.blit(cleared_surf, (cx - cleared_surf.get_width() // 2, 40))

        # Arrow showing next zone
        next_name = _ZONE_DISPLAY.get(self.next_zone, self.next_zone.replace("_", " ").title())
        arrow_surf = self._font_small.render(f"↳  Next: {next_name}", True, (160, 200, 255))
        surface.blit(arrow_surf, (cx - arrow_surf.get_width() // 2, 88))

        # Separator
        pygame.draw.line(surface, (60, 60, 100), (cx - 230, 118), (cx + 230, 118), 1)

        # Options
        for i, (action, label, color) in enumerate(self._options):
            rect = self._option_rect(i)
            is_sel = (i == self.selected)

            # Box
            box_color = (30, 40, 55) if not is_sel else (20, 50, 70)
            border_color = color if is_sel else (50, 60, 80)
            border_w = 2 if is_sel else 1
            pygame.draw.rect(surface, box_color, rect, border_radius=8)
            pygame.draw.rect(surface, border_color, rect, border_w, border_radius=8)

            # Glow for selected
            if is_sel:
                pulse = 0.6 + 0.4 * math.sin(now * 0.006)
                glow = pygame.Surface((rect.width + 12, rect.height + 12), pygame.SRCALPHA)
                gc = (*color, int(40 * pulse))
                pygame.draw.rect(glow, gc, (0, 0, rect.width + 12, rect.height + 12), border_radius=10)
                surface.blit(glow, (rect.x - 6, rect.y - 6))

            # Label
            label_c = color if is_sel else (140, 150, 165)
            txt = self._font_med.render(label, True, label_c)
            surface.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

        # Hint
        hint = self._font_small.render("[W/S] Navigate   [E / Enter] Select", True, (70, 70, 90))
        surface.blit(hint, (cx - hint.get_width() // 2, SCREEN_HEIGHT - 35))

    def _draw_portal_glyph(self, surface: pygame.Surface, cx: int, cy: int, now: int):
        spin = now * 0.0015
        for ring in range(3):
            r = 28 + ring * 14
            alpha = int(60 - ring * 15)
            ring_s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring_s, (120, 80, 220, alpha), (r + 2, r + 2), r, 2)
            surface.blit(ring_s, (cx - r - 2, cy - r - 2))
        for arm in range(4):
            angle = spin + arm * (math.pi / 2)
            ex = cx + int(math.cos(angle) * 42)
            ey = cy + int(math.sin(angle) * 42)
            pygame.draw.line(surface, (180, 120, 255), (cx, cy), (ex, ey), 1)
            pygame.draw.circle(surface, (200, 160, 255), (ex, ey), 3)
        inner = pygame.Surface((24, 24), pygame.SRCALPHA)
        pulse = int(100 + 60 * math.sin(now * 0.004))
        pygame.draw.circle(inner, (160, 100, 255, pulse), (12, 12), 10)
        surface.blit(inner, (cx - 12, cy - 12))
