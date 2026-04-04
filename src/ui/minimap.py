import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT

# World dimensions in pixels
_WORLD_W = MAP_WIDTH * TILE_SIZE
_WORLD_H = MAP_HEIGHT * TILE_SIZE


class Minimap:
    """Lightweight full-map minimap showing player and enemy positions as dots."""

    def __init__(self, size: int = 140):
        self.size = size
        self.margin = 12
        # Position: bottom-right corner
        self.x = SCREEN_WIDTH - size - self.margin
        self.y = SCREEN_HEIGHT - size - self.margin
        # Pre-render the static background once
        self._bg = pygame.Surface((size, size))
        self._bg.fill((8, 12, 8))
        pygame.draw.rect(self._bg, (0, 80, 0), (0, 0, size, size), 1)
        # Grid lines
        for i in range(1, 4):
            pos = size * i // 4
            pygame.draw.line(self._bg, (0, 35, 0), (pos, 0), (pos, size))
            pygame.draw.line(self._bg, (0, 35, 0), (0, pos), (size, pos))

    def draw(self, surface: pygame.Surface, player_x: float, player_y: float,
             enemies: list):
        """Draw the minimap with player and enemy blips."""
        s = self.size
        # Blit cached background
        surface.blit(self._bg, (self.x, self.y))

        # Scale factors: world coords → minimap coords
        sx = s / _WORLD_W
        sy = s / _WORLD_H

        # Enemy blips (red dots)
        for enemy in enemies:
            if not enemy.alive:
                continue
            ex = self.x + int(enemy.x * sx)
            ey = self.y + int(enemy.y * sy)
            if enemy.is_boss:
                pygame.draw.circle(surface, (255, 60, 60), (ex, ey), 3)
            else:
                pygame.draw.rect(surface, (220, 50, 50), (ex - 1, ey - 1, 2, 2))

        # Player blip (bright green dot)
        px = self.x + int(player_x * sx)
        py = self.y + int(player_y * sy)
        pygame.draw.circle(surface, (0, 255, 0), (px, py), 3)

        # Border (drawn last so dots don't overlap it)
        pygame.draw.rect(surface, (0, 120, 0), (self.x, self.y, s, s), 1)

        # Label
        from src.font_cache import get_font
        label = get_font("consolas", 11).render("MAP", True, (0, 140, 0))
        surface.blit(label, (self.x + s // 2 - label.get_width() // 2, self.y - 14))
