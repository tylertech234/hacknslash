"""Zone maps — procedurally generated per-zone with unique tile art."""

import pygame
import math
import random
from src.settings import (
    TILE_SIZE, MAP_WIDTH, MAP_HEIGHT, FLOOR_COLOR, WALL_COLOR,
)


class GameMap:
    """Generates and renders a per-zone map with unique visual themes."""

    def __init__(self):
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.tile_size = TILE_SIZE
        # 0 = walkable floor, 1 = impassable border/obstacle
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

    # ─── public interface ────────────────────────────────────────────────────

    @property
    def pixel_width(self) -> int:
        return self.width * self.tile_size

    @property
    def pixel_height(self) -> int:
        return self.height * self.tile_size

    def set_colors(self, tile_colors: dict):
        self.floor_color = tile_colors.get("floor", self.floor_color)
        self.floor_alt   = tile_colors.get("floor_alt", self.floor_alt)
        self.wall_color  = tile_colors.get("wall", self.wall_color)
        self._map_surface = None

    def set_zone(self, zone: str):
        self.zone = zone
        # Re-generate tile layout for the new zone
        self.tiles = [[0] * self.width for _ in range(self.height)]
        self._rng = random.Random(42)
        if zone == "wasteland":
            self._build_forest()
        elif zone == "city":
            self._build_city()
        elif zone == "abyss":
            self._build_abyss()
        else:
            self._build_forest()
        self._bake_grass_variation()
        self._map_surface = None

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int,
             screen_w: int, screen_h: int):
        if self._map_surface is None:
            self._bake_map_surface()
        src_rect = (int(camera_x), int(camera_y), screen_w, screen_h)
        surface.blit(self._map_surface, (0, 0), src_rect)

    def is_wall(self, tx: int, ty: int) -> bool:
        if tx < 0 or ty < 0 or tx >= self.width or ty >= self.height:
            return True
        return self.tiles[ty][tx] == 1

    # ─── layout builders ─────────────────────────────────────────────────────

    def _build_forest(self):
        """Organic forest clearing: large irregular circle of open ground."""
        cx, cy = self.width / 2, self.height / 2
        # Clearing fills ~65% of the map width for a big open area
        base_r = min(self.width, self.height) * 0.44
        for y in range(self.height):
            for x in range(self.width):
                dx, dy = x - cx, y - cy
                dist = math.hypot(dx, dy)
                angle = math.atan2(dy, dx)
                # Multi-frequency edge wobble for organic shape
                wobble = (self._rng.random() - 0.5) * 3.5
                edge = (2.5 * math.sin(angle * 3.7) +
                        1.8 * math.cos(angle * 5.3) +
                        1.2 * math.sin(angle * 8.1))
                threshold = base_r + edge + wobble
                if x <= 1 or x >= self.width - 2 or y <= 1 or y >= self.height - 2:
                    self.tiles[y][x] = 1
                elif dist > threshold:
                    self.tiles[y][x] = 1
                elif dist > threshold - 4:
                    if self._rng.random() < 0.40:
                        self.tiles[y][x] = 1

    def _build_city(self):
        """Ruined city grid: large open area with rubble walls at edges and
        scattered interior rubble obstacles along what were city blocks."""
        cw, ch = self.width, self.height
        border = 6  # thick rubble border

        # Fill border with impassable rubble
        for y in range(ch):
            for x in range(cw):
                if x < border or x >= cw - border or y < border or y >= ch - border:
                    self.tiles[y][x] = 1

        # Scattered interior rubble chunks — suggest collapsed buildings
        # Use a grid-of-blocks layout with random chunk density near edges
        rng = self._rng
        for y in range(border, ch - border):
            for x in range(border, cw - border):
                # Distance from nearest edge (normalised 0=edge, 1=centre)
                edge_d = min(x - border, cw - border - 1 - x,
                             y - border, ch - border - 1 - y)
                # Rubble probability decreases sharply toward centre
                if edge_d < 6:
                    p = 0.55 - edge_d * 0.07
                    if rng.random() < p:
                        self.tiles[y][x] = 1
                elif edge_d < 10:
                    # Occasional isolated rubble chunks suggest ruined walls
                    block_x = (x // 14) * 14
                    block_y = (y // 14) * 14
                    seed = (block_x * 7 + block_y * 13) % 100
                    if seed < 18 and rng.random() < 0.35:
                        self.tiles[y][x] = 1

    def _build_abyss(self):
        """Floating asteroid: an irregular island of solid ground surrounded
        by void.  The island is large and has craggy, broken edges."""
        cx, cy = self.width / 2, self.height / 2
        # Large island, ~62% of map width
        base_r = min(self.width, self.height) * 0.42
        rng = self._rng
        for y in range(self.height):
            for x in range(self.width):
                dx, dy = x - cx, y - cy
                dist = math.hypot(dx, dy)
                angle = math.atan2(dy, dx)
                # Craggy multi-frequency edge — more jagged than forest
                wobble = (rng.random() - 0.5) * 5.0
                edge = (3.5 * math.sin(angle * 4.2) +
                        2.0 * math.cos(angle * 7.1) +
                        1.5 * math.sin(angle * 11.3) +
                        1.0 * math.cos(angle * 2.8))
                threshold = base_r + edge + wobble
                if x <= 1 or x >= self.width - 2 or y <= 1 or y >= self.height - 2:
                    self.tiles[y][x] = 1
                elif dist > threshold:
                    self.tiles[y][x] = 1  # void outside island
                elif dist > threshold - 5:
                    # Very broken cliff edge — many impassable crags
                    if rng.random() < 0.55:
                        self.tiles[y][x] = 1

    def _bake_grass_variation(self):
        self._grass_offsets = []
        for y in range(self.height):
            row = [self._rng.randint(-10, 10) for _ in range(self.width)]
            self._grass_offsets.append(row)

    # ─── map surface bake ────────────────────────────────────────────────────

    def _bake_map_surface(self):
        ts = self.tile_size
        self._map_surface = pygame.Surface((self.pixel_width, self.pixel_height))
        for row in range(self.height):
            for col in range(self.width):
                rx, ry = col * ts, row * ts
                if self.tiles[row][col] == 1:
                    self._draw_wall_tile(self._map_surface, rx, ry, col, row)
                else:
                    self._draw_floor_tile(self._map_surface, rx, ry, col, row)

    def _draw_floor_tile(self, surface, rx, ry, col, row):
        ts = self.tile_size
        off = self._grass_offsets[row][col]
        fc = self.floor_color
        r = max(0, min(255, fc[0] + off))
        g = max(0, min(255, fc[1] + off))
        b = max(0, min(255, fc[2] + off // 2))
        pygame.draw.rect(surface, (r, g, b), (rx, ry, ts, ts))

        if self.zone == "wasteland":
            self._detail_forest_floor(surface, rx, ry, col, row, r, g, b)
        elif self.zone == "city":
            self._detail_city_floor(surface, rx, ry, col, row)
        elif self.zone == "abyss":
            self._detail_abyss_floor(surface, rx, ry, col, row)

    # ─── WASTELAND floor details ──────────────────────────────────────────────

    def _detail_forest_floor(self, surface, rx, ry, col, row, r, g, b):
        ts = self.tile_size
        seed = (col * 17 + row * 11) % 100
        # Grass blades
        if seed % 4 < 3:
            for i in range(2 + seed % 3):
                bx = rx + (col * 23 + row * 7 + i * 13) % (ts - 6) + 3
                by = ry + (col * 9 + row * 19 + i * 11) % (ts - 8) + 4
                h = 4 + seed % 6
                gc = (max(0, r - 20), min(255, g + 18), max(0, b - 8))
                pygame.draw.line(surface, gc, (bx, by), (bx - 1, by - h), 1)
                pygame.draw.line(surface, gc, (bx + 2, by), (bx + 2, by - h + 2), 1)
        # Moss patches
        if seed % 7 == 0:
            mx = rx + seed % (ts - 8)
            my = ry + (seed * 3) % (ts - 8)
            mc = (max(0, r - 10), min(255, g + 22), max(0, b - 5))
            pygame.draw.ellipse(surface, mc, (mx, my, 8, 5))
        # Occasional small flowers
        if seed % 13 == 0:
            fx = rx + (seed * 7) % (ts - 6) + 3
            fy = ry + (seed * 5) % (ts - 6) + 3
            pygame.draw.circle(surface, (220, 220, 60), (fx, fy), 2)
            pygame.draw.circle(surface, (255, 255, 255), (fx, fy), 1)

    # ─── CITY floor details ───────────────────────────────────────────────────

    def _detail_city_floor(self, surface, rx, ry, col, row):
        ts = self.tile_size
        # Cracked asphalt base is already drawn (floor_color)
        seed = (col * 31 + row * 17) % 100
        rng = random.Random(seed)

        # Road markings every ~8 tiles (faded white lines)
        if col % 8 == 0:
            lx = rx + ts // 2
            pygame.draw.line(surface, (60, 60, 60), (lx, ry), (lx, ry + ts), 2)
        if row % 8 == 0:
            ly = ry + ts // 2
            pygame.draw.line(surface, (60, 60, 60), (rx, ly), (rx + ts, ly), 2)

        # Cracks in asphalt
        for _ in range(1 + seed % 3):
            x1 = rx + rng.randint(4, ts - 4)
            y1 = ry + rng.randint(4, ts - 4)
            x2 = x1 + rng.randint(-10, 10)
            y2 = y1 + rng.randint(-10, 10)
            pygame.draw.line(surface, (22, 20, 24), (x1, y1), (x2, y2), 1)

        # Rubble dust / debris scatter
        if seed % 5 == 0:
            px = rx + rng.randint(4, ts - 8)
            py = ry + rng.randint(4, ts - 8)
            pw, ph = rng.randint(3, 7), rng.randint(2, 4)
            shade = rng.randint(50, 80)
            pygame.draw.rect(surface, (shade, shade - 5, shade - 10), (px, py, pw, ph))

        # Wet puddle reflections (dark teal sheen)
        if seed % 17 == 0:
            pr = rx + (seed * 11) % (ts - 12) + 6
            pc = ry + (seed * 7) % (ts - 8) + 4
            pygame.draw.ellipse(surface, (25, 35, 40), (pr, pc, 10, 5))
            pygame.draw.ellipse(surface, (35, 55, 65), (pr + 1, pc + 1, 6, 2))

    # ─── ABYSS floor details ──────────────────────────────────────────────────

    def _detail_abyss_floor(self, surface, rx, ry, col, row):
        ts = self.tile_size
        seed = (col * 29 + row * 19) % 100
        rng = random.Random(seed)

        # Dark cracked rock veins
        for _ in range(1 + seed % 3):
            x1 = rx + rng.randint(2, ts - 2)
            y1 = ry + rng.randint(2, ts - 2)
            x2 = x1 + rng.randint(-12, 12)
            y2 = y1 + rng.randint(-12, 12)
            col_v = (20 + rng.randint(0, 15), 0, 35 + rng.randint(0, 20))
            pygame.draw.line(surface, col_v, (x1, y1), (x2, y2), 1)

        # Small glowing void crystals embedded in floor
        if seed % 6 == 0:
            cx = rx + (seed * 9) % (ts - 6) + 3
            cy = ry + (seed * 7) % (ts - 6) + 3
            h = 4 + seed % 5
            crystal_pts = [(cx, cy - h), (cx + 2, cy), (cx, cy + 2), (cx - 2, cy)]
            pygame.draw.polygon(surface, (50, 15, 90), crystal_pts)
            pygame.draw.line(surface, (120, 60, 200), (cx, cy - h), (cx + 2, cy), 1)

        # Faint void glow rings
        if seed % 11 == 0:
            gx = rx + ts // 2
            gy = ry + ts // 2
            pygame.draw.circle(surface, (12, 5, 22), (gx, gy), 6, 1)

    # ─── WALL TILES ───────────────────────────────────────────────────────────

    def _draw_wall_tile(self, surface, rx, ry, col, row):
        if self.zone == "city":
            self._draw_rubble_tile(surface, rx, ry, col, row)
        elif self.zone == "abyss":
            self._draw_void_tile(surface, rx, ry, col, row)
        else:
            self._draw_tree_tile(surface, rx, ry, col, row)

    def _draw_tree_tile(self, surface, rx, ry, col, row):
        ts = self.tile_size
        dark_floor = (max(0, self.floor_color[0] - 10),
                      max(0, self.floor_color[1] - 16),
                      max(0, self.floor_color[2] - 8))
        pygame.draw.rect(surface, dark_floor, (rx, ry, ts, ts))
        seed = (col * 31 + row * 17) % 100
        rng = random.Random(seed)

        # Thick undergrowth — fern/bush cluster before the trunk
        for fi in range(2 + seed % 3):
            fgx = rx + rng.randint(4, ts - 6)
            fgy = ry + ts - rng.randint(8, 18)
            fr = 4 + fi + seed % 3
            fc = (20 + seed % 20, 60 + seed % 50, 15 + seed % 20)
            pygame.draw.ellipse(surface, fc, (fgx - fr, fgy - fr // 2, fr * 2, fr))

        # Tree trunk
        trunk_w = 8 + seed % 6
        trunk_h = int(ts * 0.65) + seed % 10
        trunk_x = rx + ts // 2 - trunk_w // 2
        trunk_y = ry + ts - trunk_h
        bark_r = 55 + seed % 25
        bark_g = 32 + seed % 18
        bark_b = 12 + seed % 12
        pygame.draw.rect(surface, (bark_r, bark_g, bark_b),
                         (trunk_x, trunk_y, trunk_w, trunk_h))
        # Bark texture lines
        for bi in range(3):
            bly = trunk_y + 6 + bi * (trunk_h // 4)
            pygame.draw.line(surface, (bark_r - 15, bark_g - 10, bark_b - 5),
                             (trunk_x + 2, bly), (trunk_x + trunk_w - 2, bly), 1)
        # Moss on trunk base
        mc = (25, 68, 22)
        pygame.draw.rect(surface, mc, (trunk_x, trunk_y + trunk_h - 5, trunk_w, 5))

        # Canopy — 3 overlapping circles for fuller look
        cx2 = rx + ts // 2
        cy2 = trunk_y - 4
        cr = int(ts * 0.38) + seed % 8
        leaf_g = 55 + seed % 45
        leaf_b = 18 + seed % 20
        pygame.draw.circle(surface, (10, leaf_g - 20, 8), (cx2 + 3, cy2 + 4), cr)      # shadow
        pygame.draw.circle(surface, (22, leaf_g, leaf_b), (cx2, cy2), cr)               # main
        pygame.draw.circle(surface, (35, min(255, leaf_g + 25), leaf_b + 8),
                           (cx2 - 3, cy2 - 4), cr - 6)                                  # highlight
        # A few lighter leaf clusters
        for li in range(3):
            la = seed * 0.18 + li * 2.1
            lx = cx2 + int(math.cos(la) * (cr * 0.5))
            ly = cy2 + int(math.sin(la) * (cr * 0.4))
            pygame.draw.circle(surface, (30, min(255, leaf_g + 15), leaf_b + 5), (lx, ly), cr // 3)

    def _draw_rubble_tile(self, surface, rx, ry, col, row):
        """City zone border: crumbled concrete rubble with fire at dense spots."""
        ts = self.tile_size
        seed = (col * 31 + row * 17) % 100
        rng = random.Random(seed + col * 7 + row * 3)

        # Decide border density: edges are darker and more ruined
        edge_d = min(col, row, self.width - 1 - col, self.height - 1 - row)
        is_deep = edge_d <= 2

        # Base: dark cracked concrete
        base_shade = 20 if is_deep else 32
        pygame.draw.rect(surface, (base_shade, base_shade - 3, base_shade + 2),
                         (rx, ry, ts, ts))

        # Large rubble chunks
        for _ in range(4 + seed % 4):
            cw2 = 5 + rng.randint(0, 14)
            ch2 = 3 + rng.randint(0, 10)
            cx3 = rx + rng.randint(1, ts - cw2 - 1)
            cy3 = ry + rng.randint(1, ts - ch2 - 1)
            shade = rng.randint(50, 100)
            r_tint = min(255, shade + rng.randint(5, 25))
            pygame.draw.rect(surface, (r_tint, shade, shade - 12), (cx3, cy3, cw2, ch2))
            # Highlight edge on top-left
            pygame.draw.line(surface, (min(255, r_tint + 20), min(255, shade + 15), shade),
                             (cx3, cy3), (cx3 + cw2, cy3), 1)

        # Cracks
        for _ in range(3):
            x1 = rx + rng.randint(3, ts - 3)
            y1 = ry + rng.randint(3, ts - 3)
            x2 = x1 + rng.randint(-12, 12)
            y2 = y1 + rng.randint(-12, 12)
            pygame.draw.line(surface, (12, 10, 14), (x1, y1), (x2, y2), 1)

        # Rebar / exposed metal
        if seed % 6 == 0:
            rby = ry + rng.randint(ts // 4, ts - 8)
            pygame.draw.line(surface, (60, 45, 30),
                             (rx + 4, rby), (rx + ts - 4, rby + rng.randint(-3, 3)), 2)

        # FIRE — at edge tiles (every 3rd, for rhythm not chaos)
        if seed % 3 == 0 and edge_d <= 5:
            fx = rx + ts // 2 + (seed % 9) - 4
            fy = ry + ts - 7
            # Hot glow base
            pygame.draw.circle(surface, (100, 45, 0), (fx, fy), 7)
            pygame.draw.circle(surface, (60, 25, 0), (fx, fy), 9, 2)
            # Flame shape — large triplet
            for fi, (fo, fh, fc_) in enumerate([
                (-3, 11, (220, 70, 5)),
                (0,  15, (255, 140, 10)),
                (3,  10, (240, 90, 0)),
            ]):
                flame = [(fx + fo - 3, fy), (fx + fo + 3, fy),
                         (fx + fo + 2, fy - fh // 2),
                         (fx + fo,     fy - fh),
                         (fx + fo - 2, fy - fh // 2)]
                pygame.draw.polygon(surface, fc_, flame)
            # White-hot core
            pygame.draw.polygon(surface, (255, 220, 120),
                                [(fx - 1, fy - 2), (fx + 1, fy - 2), (fx, fy - 8)])

        # Scattered char/ash dust for very deep tiles
        if is_deep:
            for _ in range(4):
                ax = rx + rng.randint(0, ts)
                ay = ry + rng.randint(0, ts)
                pygame.draw.circle(surface, (18, 16, 18), (ax, ay), 2)

    def _draw_void_tile(self, surface, rx, ry, col, row):
        """Abyss zone border: open void — deep space with stars and crumbling cliff edge."""
        ts = self.tile_size
        seed = (col * 31 + row * 17) % 100
        rng = random.Random(seed + col * 11 + row * 5)

        edge_d = min(col, row, self.width - 1 - col, self.height - 1 - row)

        # Deep space void background — very dark purple-black
        void_r = max(2, 6 - edge_d)
        void_b = max(4, 12 - edge_d * 2)
        pygame.draw.rect(surface, (void_r, 0, void_b), (rx, ry, ts, ts))

        # Stars — deterministic per tile
        rng2 = random.Random(seed * 3 + col + row * 7)
        n_stars = 1 + seed % 4
        for _ in range(n_stars):
            sx = rx + rng2.randint(0, ts - 1)
            sy = ry + rng2.randint(0, ts - 1)
            star_r = rng2.choice([(180, 150, 255), (200, 180, 255), (140, 110, 200)])
            pygame.draw.circle(surface, (star_r[0] // 4, star_r[1] // 4, star_r[2] // 4),
                               (sx, sy), 1)

        # Void nebula swirls (occasional large glow blobs)
        if seed % 7 == 0:
            nx = rx + rng.randint(4, ts - 6)
            ny = ry + rng.randint(4, ts - 6)
            na = 25 + seed % 20
            pygame.draw.ellipse(surface, (30 * na // 255, 10 * na // 255, 80 * na // 255),
                                (nx - 8, ny - 5, 16, 10))

        # Cliff edge — where void meets island.  Show crumbled rock.
        # Only draw rock detail on tiles adjacent to walkable floor (edge_d <= 3)
        if edge_d <= 3:
            # Rock/dirt cliff face at the island's edge
            cliff_c = (30 + seed % 20, 20 + seed % 15, 35 + seed % 20)
            # A ragged horizontal band of rock on the "inner" side of each edge tile
            band_h = 6 + seed % 10
            if row < self.height // 2:
                # Top half: rock band at bottom of tile (island below)
                pygame.draw.rect(surface, cliff_c, (rx, ry + ts - band_h, ts, band_h))
            else:
                # Bottom half: rock band at top
                pygame.draw.rect(surface, cliff_c, (rx, ry, ts, band_h))
            # Jagged edge decoration
            for ji in range(0, ts, 6):
                jh = rng.randint(2, 8)
                pygame.draw.rect(surface, (cliff_c[0] + 10, cliff_c[1] + 8, cliff_c[2] + 12),
                                 (rx + ji, ry + ts // 2 - jh // 2, 4, jh))
            # Purple glow seeping from cracks
            if seed % 4 == 0:
                gx = rx + rng.randint(4, ts - 4)
                gy = ry + ts // 2
                pygame.draw.circle(surface, (40, 10, 90), (gx, gy), 5)
                pygame.draw.circle(surface, (80, 30, 160), (gx, gy), 3)

        # Purple crack veins on deep void tiles
        if edge_d > 3:
            for _ in range(2 + seed % 3):
                x1 = rx + rng.randint(0, ts)
                y1 = ry + rng.randint(0, ts)
                x2 = x1 + rng.randint(-ts // 2, ts // 2)
                y2 = y1 + rng.randint(-ts // 2, ts // 2)
                col_c = (35 + rng.randint(0, 30), 0, 70 + rng.randint(0, 50))
                pygame.draw.line(surface, col_c, (x1, y1), (x2, y2), 1)
