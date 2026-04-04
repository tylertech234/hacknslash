"""Name entry screen — shown once on first launch to capture a display name.

The player types their name (3–16 alphanumeric/underscore characters).
A default is pre-filled so they can just press Enter.
Returns the accepted name string via .result after .active becomes False.
"""

import pygame
import random
import string

from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT


_ALLOWED = set(string.ascii_letters + string.digits + "_")
_MIN_LEN = 3
_MAX_LEN = 16


def _default_name() -> str:
    suffix = "".join(random.choices(string.digits, k=4))
    return f"Survivor{suffix}"


class NameEntryScreen:
    """Blocking first-run display name prompt."""

    def __init__(self):
        self.active = False
        self.result: str = ""
        self._text = ""
        self._font_title = pygame.font.SysFont("consolas", 36, bold=True)
        self._font_sub = pygame.font.SysFont("consolas", 20)
        self._font_input = pygame.font.SysFont("consolas", 28, bold=True)
        self._font_hint = pygame.font.SysFont("consolas", 15)
        self._cursor_visible = True
        self._cursor_timer = 0
        self._error = ""

    def activate(self, suggested: str = "") -> None:
        self.active = True
        self.result = ""
        self._text = suggested if suggested else _default_name()
        self._error = ""

    @property
    def _valid(self) -> bool:
        return (
            len(self._text) >= _MIN_LEN
            and all(c in _ALLOWED for c in self._text)
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.active:
            return
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_RETURN:
            if self._valid:
                self.result = self._text
                self.active = False
            else:
                self._error = (
                    f"Name must be {_MIN_LEN}–{_MAX_LEN} characters "
                    "(letters, digits, underscore only)."
                )
        elif event.key == pygame.K_BACKSPACE:
            self._text = self._text[:-1]
            self._error = ""
        else:
            ch = event.unicode
            if ch and ch in _ALLOWED and len(self._text) < _MAX_LEN:
                self._text += ch
                self._error = ""

    def update(self, dt: int) -> None:
        self._cursor_timer += dt
        if self._cursor_timer >= 530:
            self._cursor_visible = not self._cursor_visible
            self._cursor_timer = 0

    def draw(self, screen: pygame.Surface) -> None:
        if not self.active:
            return

        # Background
        screen.fill((6, 8, 14))

        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        # Subtle grid lines
        for gx in range(0, SCREEN_WIDTH, 60):
            pygame.draw.line(screen, (14, 18, 28), (gx, 0), (gx, SCREEN_HEIGHT))
        for gy in range(0, SCREEN_HEIGHT, 60):
            pygame.draw.line(screen, (14, 18, 28), (0, gy), (SCREEN_WIDTH, gy))

        # Title
        title = self._font_title.render("WELCOME TO CYBER SURVIVOR", True, (100, 220, 255))
        screen.blit(title, title.get_rect(center=(cx, cy - 140)))

        # Subtitle
        sub = self._font_sub.render("Enter your display name for the leaderboard", True, (140, 160, 180))
        screen.blit(sub, sub.get_rect(center=(cx, cy - 90)))

        # Input box
        box_w, box_h = 400, 48
        box_rect = pygame.Rect(cx - box_w // 2, cy - box_h // 2, box_w, box_h)
        pygame.draw.rect(screen, (20, 30, 50), box_rect, border_radius=6)
        border_col = (100, 220, 255) if self._valid else (80, 80, 100)
        pygame.draw.rect(screen, border_col, box_rect, 2, border_radius=6)

        # Text inside box
        display = self._text + ("|" if self._cursor_visible else " ")
        text_surf = self._font_input.render(display, True, (220, 240, 255))
        text_rect = text_surf.get_rect(midleft=(box_rect.left + 12, box_rect.centery))
        screen.blit(text_surf, text_rect)

        # Char counter
        counter_col = (180, 60, 60) if len(self._text) < _MIN_LEN else (100, 200, 100)
        counter = self._font_hint.render(
            f"{len(self._text)}/{_MAX_LEN}", True, counter_col
        )
        screen.blit(counter, counter.get_rect(midright=(box_rect.right - 8, box_rect.centery)))

        # Error or hint
        if self._error:
            err_surf = self._font_hint.render(self._error, True, (220, 80, 80))
            screen.blit(err_surf, err_surf.get_rect(center=(cx, cy + 44)))
        else:
            hint = self._font_hint.render(
                "Letters, digits and _ only  •  Enter to confirm  •  Pre-fill is just a suggestion",
                True, (80, 100, 120)
            )
            screen.blit(hint, hint.get_rect(center=(cx, cy + 44)))

        # Confirm button indicator
        btn_col = (40, 180, 100) if self._valid else (50, 55, 65)
        btn_rect = pygame.Rect(cx - 80, cy + 70, 160, 36)
        pygame.draw.rect(screen, btn_col, btn_rect, border_radius=6)
        btn_text = self._font_sub.render("CONFIRM  [Enter]", True, (220, 255, 220) if self._valid else (90, 95, 105))
        screen.blit(btn_text, btn_text.get_rect(center=btn_rect.center))
