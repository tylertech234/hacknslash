import pygame
from src.settings import (
    TILE_SIZE, MAP_WIDTH, MAP_HEIGHT, FLOOR_COLOR, WALL_COLOR,
)


class GameMap:
    """Simple tile-based map. For now: open arena with a border of walls."""

    def __init__(self):
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.tile_size = TILE_SIZE
        # 0 = floor, 1 = wall
        self.tiles: list[list[int]] = [
            [0] * self.width for _ in range(self.height)
        ]
        self._build_border()

    @property
    def pixel_width(self) -> int:
        return self.width * self.tile_size

    @property
    def pixel_height(self) -> int:
        return self.height * self.tile_size

    def _build_border(self):
        for x in range(self.width):
            self.tiles[0][x] = 1
            self.tiles[self.height - 1][x] = 1
        for y in range(self.height):
            self.tiles[y][0] = 1
            self.tiles[y][self.width - 1] = 1

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int, screen_w: int, screen_h: int):
        # Only draw tiles visible on screen
        start_col = max(0, int(camera_x) // self.tile_size)
        end_col = min(self.width, (int(camera_x) + screen_w) // self.tile_size + 1)
        start_row = max(0, int(camera_y) // self.tile_size)
        end_row = min(self.height, (int(camera_y) + screen_h) // self.tile_size + 1)

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                tile = self.tiles[row][col]
                color = WALL_COLOR if tile == 1 else FLOOR_COLOR
                rect = pygame.Rect(
                    col * self.tile_size - int(camera_x),
                    row * self.tile_size - int(camera_y),
                    self.tile_size,
                    self.tile_size,
                )
                pygame.draw.rect(surface, color, rect)
                if tile == 1:
                    pygame.draw.rect(surface, (60, 55, 50), rect, 1)
