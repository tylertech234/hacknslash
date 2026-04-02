import pygame
import math
import random
from src.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT


class Prop:
    """A decorative/collidable environment object."""

    # Collision radii per kind (0 = no collision)
    COLLISION_RADIUS = {"tree": 10, "rock": 14, "bush": 0, "stump": 0}

    def __init__(self, x: float, y: float, kind: str):
        self.x = x
        self.y = y
        self.kind = kind  # "tree", "rock", "bush", "stump"
        self.anim_offset = random.uniform(0, math.tau)
        self.collision_r = self.COLLISION_RADIUS.get(kind, 0)

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        now = pygame.time.get_ticks()

        if self.kind == "tree":
            self._draw_tree(surface, sx, sy, now)
        elif self.kind == "rock":
            self._draw_rock(surface, sx, sy)
        elif self.kind == "bush":
            self._draw_bush(surface, sx, sy, now)
        elif self.kind == "stump":
            self._draw_stump(surface, sx, sy)

    def _draw_tree(self, surface, sx, sy, now):
        sway = math.sin(now * 0.001 + self.anim_offset) * 2
        # Trunk
        pygame.draw.rect(surface, (90, 60, 30), (sx - 4, sy - 10, 8, 24))
        # Canopy layers
        pygame.draw.circle(surface, (20, 80, 20), (int(sx + sway), sy - 22), 18)
        pygame.draw.circle(surface, (30, 100, 30), (int(sx + sway - 4), sy - 18), 13)
        pygame.draw.circle(surface, (25, 90, 25), (int(sx + sway + 5), sy - 26), 11)
        # Highlight
        pygame.draw.circle(surface, (45, 120, 40), (int(sx + sway - 2), sy - 26), 6)

    def _draw_rock(self, surface, sx, sy):
        # Irregular rock shape using polygon
        pts = [
            (sx - 14, sy + 4),
            (sx - 10, sy - 8),
            (sx - 2, sy - 12),
            (sx + 8, sy - 9),
            (sx + 13, sy - 2),
            (sx + 11, sy + 6),
            (sx + 2, sy + 8),
            (sx - 8, sy + 7),
        ]
        pygame.draw.polygon(surface, (100, 95, 88), pts)
        pygame.draw.polygon(surface, (120, 115, 108), pts, 2)
        # Highlight
        pygame.draw.circle(surface, (130, 125, 118), (sx - 2, sy - 4), 4)

    def _draw_bush(self, surface, sx, sy, now):
        sway = math.sin(now * 0.0015 + self.anim_offset) * 1.5
        pygame.draw.circle(surface, (30, 70, 25), (int(sx + sway), sy), 12)
        pygame.draw.circle(surface, (35, 85, 30), (int(sx + sway - 5), sy + 2), 9)
        pygame.draw.circle(surface, (40, 95, 35), (int(sx + sway + 4), sy - 3), 8)
        # Berry detail
        if int(self.anim_offset * 10) % 3 == 0:
            pygame.draw.circle(surface, (180, 30, 30), (int(sx + sway + 2), sy - 1), 2)
            pygame.draw.circle(surface, (180, 30, 30), (int(sx + sway - 4), sy + 3), 2)

    def _draw_stump(self, surface, sx, sy):
        pygame.draw.ellipse(surface, (80, 55, 30), (sx - 10, sy - 4, 20, 12))
        pygame.draw.ellipse(surface, (100, 70, 40), (sx - 8, sy - 6, 16, 8))
        # Ring detail
        pygame.draw.ellipse(surface, (70, 48, 25), (sx - 5, sy - 4, 10, 5), 1)


class EnvironmentSystem:
    """Scatters decorative props across the map."""

    def __init__(self):
        self.props: list[Prop] = []
        self._generate()

    def _generate(self):
        world_w = MAP_WIDTH * TILE_SIZE
        world_h = MAP_HEIGHT * TILE_SIZE
        margin = TILE_SIZE * 2  # keep away from walls
        center_x = world_w // 2
        center_y = world_h // 2

        kinds = ["tree", "tree", "tree", "rock", "rock", "bush", "bush", "stump"]
        count = 120

        random.seed(42)  # deterministic placement
        for _ in range(count):
            x = random.randint(margin, world_w - margin)
            y = random.randint(margin, world_h - margin)
            # Keep a clear zone around center (spawn / campfire area)
            if math.hypot(x - center_x, y - center_y) < 200:
                continue
            kind = random.choice(kinds)
            self.props.append(Prop(x, y, kind))
        random.seed()  # re-randomize

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int, screen_w: int, screen_h: int):
        for p in self.props:
            # Simple culling
            sx = p.x - camera_x
            sy = p.y - camera_y
            if -40 < sx < screen_w + 40 and -40 < sy < screen_h + 40:
                p.draw(surface, camera_x, camera_y)

    def collide_entity(self, ex: float, ey: float, entity_half: int) -> tuple[float, float]:
        """Push entity out of any solid props. Returns corrected (x, y)."""
        for p in self.props:
            if p.collision_r <= 0:
                continue
            dx = ex - p.x
            dy = ey - p.y
            dist = math.hypot(dx, dy)
            min_dist = p.collision_r + entity_half
            if dist < min_dist and dist > 0:
                # Push out
                overlap = min_dist - dist
                ex += (dx / dist) * overlap
                ey += (dy / dist) * overlap
        return ex, ey
