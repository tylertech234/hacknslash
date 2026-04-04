import pygame
import math
import random
from src.settings import (
    TILE_SIZE, MAP_WIDTH, MAP_HEIGHT, FLOOR_COLOR, WALL_COLOR,
)


class GameMap:
    """Forest clearing map — green grass center with procedural tree border."""

    def __init__(self):
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.tile_size = TILE_SIZE
        # 0 = grass, 1 = tree (impassable border), 2 = grass decoration
        self.tiles: list[list[int]] = [
            [0] * self.width for _ in range(self.height)
        ]
        self.floor_color = FLOOR_COLOR
        self.floor_alt = tuple(max(0, c - 5) for c in FLOOR_COLOR)
        self.wall_color = WALL_COLOR
        self._rng = random.Random(42)
        self.zone = "wasteland"
        self._build_forest()
        self._bake_grass_variation()
        self._map_surface: pygame.Surface | None = None  # lazily baked

    @property
    def pixel_width(self) -> int:
        return self.width * self.tile_size

    @property
    def pixel_height(self) -> int:
        return self.height * self.tile_size

    def set_colors(self, tile_colors: dict):
        """Override tile colors for zone."""
        self.floor_color = tile_colors.get("floor", self.floor_color)
        self.floor_alt = tile_colors.get("floor_alt", self.floor_alt)
        self.wall_color = tile_colors.get("wall", self.wall_color)
        self._map_surface = None  # invalidate cache

    def set_zone(self, zone: str):
        """Switch zone, invalidates map cache so border tiles redraw."""
        self.zone = zone
        self._map_surface = None

    def _build_forest(self):
        """Create a clearing surrounded by trees."""
        cx, cy = self.width / 2, self.height / 2
        # Clearing radius with irregular edge
        base_r = min(self.width, self.height) * 0.38
        for y in range(self.height):
            for x in range(self.width):
                # Distance from center
                dx = x - cx
                dy = y - cy
                dist = math.hypot(dx, dy)
                # Irregular edge using seeded noise
                angle = math.atan2(dy, dx)
                wobble = (self._rng.random() - 0.5) * 3.0
                # Perlin-ish roughness from angle
                edge_noise = 2.0 * math.sin(angle * 3.7) + 1.5 * math.cos(angle * 5.3)
                threshold = base_r + edge_noise + wobble
                # Always wall at map edge
                if x <= 0 or x >= self.width - 1 or y <= 0 or y >= self.height - 1:
                    self.tiles[y][x] = 1
                elif dist > threshold:
                    self.tiles[y][x] = 1
                elif dist > threshold - 3:
                    # Scattered trees near edge
                    if self._rng.random() < 0.35:
                        self.tiles[y][x] = 1

    def _bake_grass_variation(self):
        """Pre-compute per-tile grass color offsets for natural look."""
        self._grass_offsets = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(self._rng.randint(-8, 8))
            self._grass_offsets.append(row)

    def _bake_map_surface(self):
        """Pre-render entire map once; reused every frame via blit."""
        ts = self.tile_size
        self._map_surface = pygame.Surface((self.pixel_width, self.pixel_height))
        for row in range(self.height):
            for col in range(self.width):
                tile = self.tiles[row][col]
                rx = col * ts
                ry = row * ts
                if tile == 1:
                    if self.zone == "city":
                        self._draw_rubble_tile(self._map_surface, rx, ry, col, row)
                    elif self.zone == "abyss":
                        self._draw_void_tile(self._map_surface, rx, ry, col, row)
                    else:
                        self._draw_tree_tile(self._map_surface, rx, ry, col, row)
                else:
                    off = self._grass_offsets[row][col]
                    r = max(0, min(255, self.floor_color[0] + off))
                    g = max(0, min(255, self.floor_color[1] + off))
                    b = max(0, min(255, self.floor_color[2] + off // 2))
                    pygame.draw.rect(self._map_surface, (r, g, b), (rx, ry, ts, ts))
                    if (col * 7 + row * 13) % 11 < 3:
                        tx = rx + (col * 17 + row * 3) % (ts - 8) + 4
                        ty = ry + (col * 11 + row * 7) % (ts - 8) + 4
                        h = 4 + (col + row) % 4
                        gc = (max(0, r - 15), min(255, g + 15), max(0, b - 10))
                        pygame.draw.line(self._map_surface, gc, (tx, ty), (tx - 1, ty - h), 1)
                        pygame.draw.line(self._map_surface, gc, (tx + 2, ty), (tx + 3, ty - h + 1), 1)

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int, screen_w: int, screen_h: int):
        if self._map_surface is None:
            self._bake_map_surface()
        src_rect = (int(camera_x), int(camera_y), screen_w, screen_h)
        surface.blit(self._map_surface, (0, 0), src_rect)

    def _draw_rubble_tile(self, surface, rx, ry, col, row):
        """City zone border: crumbled concrete rubble with flicker fire."""
        ts = self.tile_size
        seed = (col * 31 + row * 17) % 100
        # Dark cracked concrete ground
        pygame.draw.rect(surface, (30, 28, 32), (rx, ry, ts, ts))
        # Rubble chunks (grey/brown rectangles)
        rng = random.Random(seed + col * 7 + row * 3)
        for _ in range(3 + seed % 3):
            cw = 4 + rng.randint(0, 8)
            ch = 3 + rng.randint(0, 6)
            cx2 = rx + rng.randint(2, ts - cw - 2)
            cy2 = ry + rng.randint(2, ts - ch - 2)
            shade = rng.randint(55, 100)
            tint_r = shade + rng.randint(0, 20)
            pygame.draw.rect(surface, (tint_r, shade, shade - 10), (cx2, cy2, cw, ch))
        # Cracks (dark lines)
        for _ in range(2):
            x1 = rx + rng.randint(4, ts - 4)
            y1 = ry + rng.randint(4, ts - 4)
            x2 = x1 + rng.randint(-8, 8)
            y2 = y1 + rng.randint(-8, 8)
            pygame.draw.line(surface, (15, 14, 16), (x1, y1), (x2, y2), 1)
        # Fire (static bake — warm glow + flame shape every ~5th tile)
        if seed % 5 == 0:
            fx = rx + ts // 2 + (seed % 7) - 3
            fy = ry + ts - 6
            # Glow base
            pygame.draw.circle(surface, (80, 40, 0), (fx, fy), 5)
            # Flame core
            flame_pts = [
                (fx - 3, fy), (fx + 3, fy),
                (fx + 2, fy - 5), (fx - 2, fy - 5),
                (fx, fy - 10),
            ]
            pygame.draw.polygon(surface, (200, 80, 0), flame_pts)
            pygame.draw.polygon(surface, (255, 180, 20),
                                [(fx - 1, fy - 1), (fx + 1, fy - 1), (fx, fy - 7)])

    def _draw_void_tile(self, surface, rx, ry, col, row):
        """Abyss zone border: void cracks and dark crystals."""
        ts = self.tile_size
        seed = (col * 31 + row * 17) % 100
        rng = random.Random(seed + col * 11 + row * 5)
        # Very dark void ground
        r_base = 8 + seed % 8
        pygame.draw.rect(surface, (r_base, 0, r_base + 4), (rx, ry, ts, ts))
        # Void crack lines (purple/dark blue)
        for _ in range(2 + seed % 3):
            x1 = rx + rng.randint(0, ts)
            y1 = ry + rng.randint(0, ts)
            x2 = x1 + rng.randint(-ts // 2, ts // 2)
            y2 = y1 + rng.randint(-ts // 2, ts // 2)
            col_c = (40 + rng.randint(0, 40), 0, 80 + rng.randint(0, 60))
            pygame.draw.line(surface, col_c, (x1, y1), (x2, y2), 1)
        # Crystal shards (every ~4th tile)
        if seed % 4 < 2:
            cx2 = rx + ts // 2 + (seed % 9) - 4
            cy2 = ry + ts // 2 + (seed % 7) - 3
            h = 8 + seed % 10
            w = 3 + seed % 4
            # Dark crystal body
            pts = [
                (cx2, cy2 - h),
                (cx2 + w, cy2),
                (cx2, cy2 + w // 2),
                (cx2 - w, cy2),
            ]
            pygame.draw.polygon(surface, (60, 10, 100), pts)
            # Crystal highlight edge
            pygame.draw.line(surface, (140, 60, 200),
                             (cx2, cy2 - h), (cx2 + w, cy2), 1)

    def _draw_tree_tile(self, surface, rx, ry, col, row):
        ts = self.tile_size
        # Ground behind tree matches forest floor (slightly darker for depth)
        dark_floor = (max(0, self.floor_color[0] - 8),
                      max(0, self.floor_color[1] - 12),
                      max(0, self.floor_color[2] - 6))
        pygame.draw.rect(surface, dark_floor, (rx, ry, ts, ts))
        # Tree trunk (brown)
        seed = (col * 31 + row * 17) % 100
        trunk_w = 6 + seed % 4
        trunk_h = ts // 2 + seed % 8
        trunk_x = rx + ts // 2 - trunk_w // 2
        trunk_y = ry + ts - trunk_h
        bark_r = 60 + seed % 20
        bark_g = 35 + seed % 15
        bark_b = 15 + seed % 10
        pygame.draw.rect(surface, (bark_r, bark_g, bark_b),
                         (trunk_x, trunk_y, trunk_w, trunk_h))
        # Canopy (layered green circles)
        canopy_cx = rx + ts // 2
        canopy_cy = trunk_y - 2
        canopy_r = ts // 3 + seed % 6
        leaf_g = 50 + seed % 40
        leaf_b = 20 + seed % 15
        # Shadow layer
        pygame.draw.circle(surface, (15, leaf_g - 30, 5),
                           (canopy_cx + 2, canopy_cy + 2), canopy_r)
        # Main canopy
        pygame.draw.circle(surface, (25, leaf_g, leaf_b),
                           (canopy_cx, canopy_cy), canopy_r)
        # Highlight
        pygame.draw.circle(surface, (35, min(255, leaf_g + 20), leaf_b + 5),
                           (canopy_cx - 2, canopy_cy - 2), canopy_r - 4)
