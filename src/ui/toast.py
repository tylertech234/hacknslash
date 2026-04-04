"""Toast notification system — sliding achievement-style popups."""
import pygame
import math
from src.font_cache import get_font

# Toast dimensions
_TOAST_W = 280
_TOAST_H = 60
_SLIDE_DURATION = 300   # ms to slide in/out
_HOLD_DURATION = 2800   # ms to remain visible


class _Toast:
    def __init__(self, title: str, subtitle: str, icon_color: tuple, now: int):
        self.title = title
        self.subtitle = subtitle
        self.icon_color = icon_color
        self.start = now
        self.total = _SLIDE_DURATION + _HOLD_DURATION + _SLIDE_DURATION

    @property
    def alive(self):
        return pygame.time.get_ticks() - self.start < self.total


class ToastManager:
    """Manages a queue of toast notifications rendered on-screen."""

    MAX_VISIBLE = 3

    def __init__(self):
        self._queue: list[_Toast] = []

    def show(self, title: str, subtitle: str = "", icon_color: tuple = (200, 200, 200)):
        """Queue a new toast notification."""
        now = pygame.time.get_ticks()
        self._queue.append(_Toast(title, subtitle, icon_color, now))

    def update(self) -> None:
        """Remove expired toasts."""
        now = pygame.time.get_ticks()
        self._queue = [t for t in self._queue if now - t.start < t.total]

    def draw(self, surface: pygame.Surface) -> None:
        """Draw all active toasts stacked in the top-right corner."""
        self.update()
        sw, sh = surface.get_size()
        now = pygame.time.get_ticks()
        font_title = get_font("consolas", 13, True)
        font_sub   = get_font("consolas", 11, False)

        visible = self._queue[-self.MAX_VISIBLE:]
        for idx, toast in enumerate(visible):
            elapsed = now - toast.start
            # Slide-in  phase
            if elapsed < _SLIDE_DURATION:
                t = elapsed / _SLIDE_DURATION
                slide = math.pow(1 - t, 2)        # ease-out quad
            # Hold phase
            elif elapsed < _SLIDE_DURATION + _HOLD_DURATION:
                slide = 0.0
            # Slide-out phase
            else:
                t = (elapsed - _SLIDE_DURATION - _HOLD_DURATION) / _SLIDE_DURATION
                slide = math.pow(t, 2)              # ease-in quad

            offset_x = int((_TOAST_W + 16) * slide)
            base_x = sw - _TOAST_W - 14 + offset_x
            base_y = 14 + idx * (_TOAST_H + 8)

            # Background panel
            bg = pygame.Surface((_TOAST_W, _TOAST_H), pygame.SRCALPHA)
            bg.fill((10, 10, 20, 210))
            pygame.draw.rect(bg, (60, 60, 80), (0, 0, _TOAST_W, _TOAST_H), 1)
            # Accent bar on left
            pygame.draw.rect(bg, toast.icon_color, (0, 0, 4, _TOAST_H))

            surface.blit(bg, (base_x, base_y))

            # Icon circle
            icon_r = 14
            icon_cx = base_x + 18
            icon_cy = base_y + _TOAST_H // 2
            pygame.draw.circle(surface, toast.icon_color, (icon_cx, icon_cy), icon_r)
            pygame.draw.circle(surface, (255, 255, 255), (icon_cx, icon_cy), icon_r, 2)
            # Exclamation mark
            pygame.draw.line(surface, (255, 255, 255),
                             (icon_cx, icon_cy - 6), (icon_cx, icon_cy + 2), 2)
            pygame.draw.circle(surface, (255, 255, 255), (icon_cx, icon_cy + 6), 2)

            # Text
            tx = base_x + 40
            title_surf = font_title.render(toast.title, True, (230, 230, 240))
            surface.blit(title_surf, (tx, base_y + 10))
            if toast.subtitle:
                sub_surf = font_sub.render(toast.subtitle, True, (160, 160, 180))
                surface.blit(sub_surf, (tx, base_y + 30))
