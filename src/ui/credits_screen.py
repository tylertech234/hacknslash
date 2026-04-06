"""Victory credits screen — fireworks + scrolling text after beating the final boss."""

import pygame
import math
import random
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, VERSION


# ── Credits text lines ──
_CREDITS = [
    ("title", "CYBER SURVIVOR"),
    ("spacer", ""),
    ("heading", "Lead Design"),
    ("body", "McMinn Central High School"),
    ("body", "Technology Class"),
    ("spacer", ""),
    ("heading", "Executive Producer"),
    ("body", "Tyler Morrison"),
    ("spacer", ""),
    ("heading", "Lead Artist"),
    ("body", "Python"),
    ("spacer", ""),
    ("heading", "Lead Programmer"),
    ("body", "Claude Opus 4.6"),
    ("spacer", ""),
    ("heading", "Special Thanks"),
    ("body", "Mr. K"),
    ("spacer", ""),
    ("spacer", ""),
    ("heading", "Thanks for playing!"),
    ("spacer", ""),
    ("body", "Go out and make a difference"),
    ("spacer", ""),
    ("spacer", ""),
    ("micro", f"v{VERSION}"),
]


class _Firework:
    """Single firework burst with expanding/fading sparks."""
    __slots__ = ("x", "y", "sparks", "born", "life", "color")

    def __init__(self, x: float, y: float, born: int):
        self.x = x
        self.y = y
        self.born = born
        self.life = random.randint(1200, 2200)
        hue = random.random() * 360
        # Bright saturated HSV → RGB
        c = 1.0
        x2 = c * (1 - abs((hue / 60) % 2 - 1))
        if hue < 60:
            r, g, b = c, x2, 0.0
        elif hue < 120:
            r, g, b = x2, c, 0.0
        elif hue < 180:
            r, g, b = 0.0, c, x2
        elif hue < 240:
            r, g, b = 0.0, x2, c
        elif hue < 300:
            r, g, b = x2, 0.0, c
        else:
            r, g, b = c, 0.0, x2
        self.color = (int(r * 255), int(g * 255), int(b * 255))
        # Each spark: (angle, speed, size)
        count = random.randint(20, 40)
        self.sparks = [
            (random.uniform(0, math.tau),
             random.uniform(40, 180),
             random.randint(2, 4))
            for _ in range(count)
        ]

    def alive(self, now: int) -> bool:
        return now - self.born < self.life

    def draw(self, surface: pygame.Surface, now: int):
        elapsed = now - self.born
        frac = elapsed / self.life
        alpha = max(0, int(255 * (1.0 - frac)))
        r, g, b = self.color
        for angle, speed, sz in self.sparks:
            t = elapsed / 1000.0
            # Gravity-affected arc
            px = self.x + math.cos(angle) * speed * t
            py = self.y + math.sin(angle) * speed * t + 60 * t * t
            s = max(1, int(sz * (1.0 - frac)))
            if 0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT:
                c = (r, g, b, alpha)
                spark_s = pygame.Surface((s * 2 + 2, s * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(spark_s, c, (s + 1, s + 1), s)
                surface.blit(spark_s, (int(px) - s - 1, int(py) - s - 1))


class CreditsScreen:
    """Full-screen victory credits with fireworks."""

    def __init__(self):
        self.active = False
        self._start_time = 0
        self._fireworks: list[_Firework] = []
        self._next_fw = 0
        self._done_callback = None  # called when credits dismissed
        self.font_title = pygame.font.SysFont("consolas", 48, bold=True)
        self.font_heading = pygame.font.SysFont("consolas", 28, bold=True)
        self.font_body = pygame.font.SysFont("consolas", 22)
        self.font_micro = pygame.font.SysFont("consolas", 14)

    def activate(self, done_callback=None):
        """Start credits rolling. done_callback() is called when player dismisses."""
        self.active = True
        self._start_time = pygame.time.get_ticks()
        self._fireworks.clear()
        self._next_fw = 0
        self._done_callback = done_callback

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True when credits are dismissed (click / Enter / Esc)."""
        if not self.active:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._dismiss()
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_e
        ):
            return self._dismiss()
        return False

    def _dismiss(self) -> bool:
        self.active = False
        if self._done_callback:
            self._done_callback()
        return True

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return

        now = pygame.time.get_ticks()
        elapsed = now - self._start_time

        # Background: near-black with subtle gradient
        surface.fill((5, 5, 15))

        # Spawn fireworks periodically
        if now >= self._next_fw:
            fx = random.randint(60, SCREEN_WIDTH - 60)
            fy = random.randint(40, SCREEN_HEIGHT // 2)
            self._fireworks.append(_Firework(fx, fy, now))
            self._next_fw = now + random.randint(300, 800)

        # Prune dead fireworks
        self._fireworks = [fw for fw in self._fireworks if fw.alive(now)]

        # Draw fireworks behind text
        for fw in self._fireworks:
            fw.draw(surface, now)

        # Scrolling credits — start below screen, scroll up
        scroll_speed = 40  # pixels per second
        scroll_offset = elapsed / 1000.0 * scroll_speed
        y = SCREEN_HEIGHT - scroll_offset + 80  # start from bottom

        cx = SCREEN_WIDTH // 2

        for kind, text in _CREDITS:
            if kind == "spacer":
                y += 30
                continue
            if kind == "title":
                font = self.font_title
                color = (80, 255, 255)
            elif kind == "heading":
                font = self.font_heading
                color = (255, 220, 80)
            elif kind == "micro":
                font = self.font_micro
                color = (100, 100, 120)
            else:
                font = self.font_body
                color = (220, 220, 240)

            rendered = font.render(text, True, color)
            tx = cx - rendered.get_width() // 2

            # Only draw if on screen
            if -60 < y < SCREEN_HEIGHT + 60:
                surface.blit(rendered, (tx, int(y)))

            y += rendered.get_height() + 8

        # "Click to continue" hint after credits have scrolled up a bit
        if elapsed > 3000:
            pulse = int(120 + 80 * math.sin(now * 0.003))
            hint = self.font_micro.render("Click or press Enter to continue", True,
                                          (pulse, pulse, pulse))
            surface.blit(hint, (cx - hint.get_width() // 2, SCREEN_HEIGHT - 36))
