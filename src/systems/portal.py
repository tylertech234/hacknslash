"""Portal entity — spawns after zone boss is defeated to transition to next zone."""

import pygame
import math
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Portal:
    """A glowing portal that takes the player to the next zone."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.alive = True
        self.spawn_time = pygame.time.get_ticks()
        self.radius = 40
        self.entered = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)

    def check_collision(self, player_rect: pygame.Rect) -> bool:
        """Check if the player has entered the portal."""
        if not self.alive or self.entered:
            return False
        if player_rect.colliderect(self.rect):
            self.entered = True
            return True
        return False

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        if not self.alive:
            return

        now = pygame.time.get_ticks()
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)

        # Skip if off screen
        if sx < -100 or sx > SCREEN_WIDTH + 100 or sy < -100 or sy > SCREEN_HEIGHT + 100:
            return

        age = now - self.spawn_time
        # Grow-in animation
        scale = min(1.0, age / 1000)
        r = int(self.radius * scale)
        if r < 2:
            return

        # Outer glow
        glow_r = r + int(10 + 8 * math.sin(now * 0.003))
        glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (100, 50, 200, 30), (glow_r, glow_r), glow_r)
        surface.blit(glow_s, (sx - glow_r, sy - glow_r))

        # Portal ring
        pygame.draw.circle(surface, (140, 80, 220), (sx, sy), r, 3)
        pygame.draw.circle(surface, (200, 150, 255), (sx, sy), r - 3, 1)

        # Inner swirl
        spin = now * 0.002
        inner_r = r - 6
        if inner_r > 1:
            inner_s = pygame.Surface((inner_r * 2, inner_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(inner_s, (60, 20, 100, 120), (inner_r, inner_r), inner_r)
            # Spiral dots
            for arm in range(3):
                for j in range(8):
                    t = j / 8
                    angle = spin + arm * (math.tau / 3) + t * 4
                    px = inner_r + int(math.cos(angle) * inner_r * t * 0.8)
                    py = inner_r + int(math.sin(angle) * inner_r * t * 0.8)
                    alpha = int(180 * (1 - t))
                    pygame.draw.circle(inner_s, (180, 120, 255, alpha), (px, py), max(1, int(3 * (1 - t))))
            surface.blit(inner_s, (sx - inner_r, sy - inner_r))

        # Center bright spot
        center_r = max(1, r // 4)
        pulse = 0.7 + 0.3 * math.sin(now * 0.005)
        cs = pygame.Surface((center_r * 2, center_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(cs, (220, 200, 255, int(150 * pulse)), (center_r, center_r), center_r)
        surface.blit(cs, (sx - center_r, sy - center_r))

        # "ENTER" text floating above
        if scale >= 1.0:
            bob = int(math.sin(now * 0.003) * 4)
            from src.font_cache import get_font
            text = get_font("consolas", 14, True).render("ENTER PORTAL", True, (180, 150, 255))
            surface.blit(text, (sx - text.get_width() // 2, sy - r - 24 + bob))
