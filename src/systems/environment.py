import pygame
import math
import random
from src.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT


# Zone-specific prop distributions
ZONE_PROPS = {
    "wasteland": {
        "kinds": ["dead_tree", "dead_tree", "dead_tree", "toxic_barrel",
                  "rock", "rock", "stump"],
        "healing_kind": "fruit_tree",
        "healing_chance": 0.12,
        "count": 130,
    },
    "city": {
        "kinds": ["building", "building", "car", "rubble", "rubble",
                  "fire_hydrant"],
        "healing_kind": "first_aid_box",
        "healing_chance": 0.18,
        "count": 70,
    },
    "abyss": {
        "kinds": ["eldritch_pillar", "eldritch_pillar", "void_crystal",
                  "tentacle", "tentacle", "floating_rock"],
        "healing_kind": "void_bloom",
        "healing_chance": 0.12,
        "count": 100,
    },
}


class Prop:
    """A decorative/collidable environment object."""

    COLLISION_RADIUS = {
        "tree": 10, "rock": 14, "bush": 0, "stump": 0, "fruit_tree": 10,
        "dead_tree": 10, "toxic_barrel": 12,
        "building": 40, "car": 25, "first_aid_box": 8, "rubble": 0,
        "fire_hydrant": 6,
        "eldritch_pillar": 14, "void_crystal": 10, "tentacle": 0,
        "void_bloom": 10, "floating_rock": 0,
    }

    HEALING_KINDS = frozenset(("fruit_tree", "first_aid_box", "void_bloom"))

    def __init__(self, x: float, y: float, kind: str):
        self.x = x
        self.y = y
        self.kind = kind
        self.anim_offset = random.uniform(0, math.tau)
        self.collision_r = self.COLLISION_RADIUS.get(kind, 0)
        self.has_healing = kind in self.HEALING_KINDS
        self.healing_respawn_time = 0

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        now = pygame.time.get_ticks()
        drawer = getattr(self, f"_draw_{self.kind}", None)
        if drawer:
            drawer(surface, sx, sy, now)

    # ---- Wasteland props ----

    def _draw_dead_tree(self, surface, sx, sy, now):
        sway = math.sin(now * 0.0008 + self.anim_offset) * 1
        swi = int(sway)
        pygame.draw.rect(surface, (55, 38, 18), (sx - 3, sy - 8, 6, 22))
        branches = [(-0.9, 16), (-0.3, 20), (0.5, 18), (1.0, 13)]
        for angle, length in branches:
            bx = sx + int(math.cos(angle) * length) + swi
            by = sy - 8 - int(abs(math.sin(angle + 1.0)) * length)
            pygame.draw.line(surface, (45, 32, 15), (sx + swi, sy - 8), (bx, by), 2)
            sbx = bx + int(math.cos(angle + 0.3) * 6)
            sby = by - int(abs(math.sin(angle + 0.5)) * 5)
            pygame.draw.line(surface, (40, 28, 12), (bx, by), (sbx, sby), 1)

    def _draw_toxic_barrel(self, surface, sx, sy, now):
        glow = 0.5 + 0.5 * math.sin(now * 0.003 + self.anim_offset)
        pygame.draw.rect(surface, (70, 70, 72), (sx - 8, sy - 12, 16, 22))
        pygame.draw.rect(surface, (55, 55, 58), (sx - 8, sy - 12, 16, 22), 2)
        pygame.draw.line(surface, (90, 90, 95), (sx - 8, sy - 6), (sx + 8, sy - 6), 2)
        pygame.draw.line(surface, (90, 90, 95), (sx - 8, sy + 4), (sx + 8, sy + 4), 2)
        gc = int(160 + 80 * glow)
        pygame.draw.circle(surface, (30, gc, 20), (sx, sy - 2), 5)
        pygame.draw.circle(surface, (20, gc, 10), (sx, sy - 2), 3)
        drip_y = sy + 10 + int(glow * 4)
        pygame.draw.line(surface, (30, 200, 20), (sx + 3, sy + 10), (sx + 3, drip_y), 1)
        if glow > 0.7:
            gs = pygame.Surface((20, 8), pygame.SRCALPHA)
            pygame.draw.ellipse(gs, (30, 180, 20, int(40 * glow)), (0, 0, 20, 8))
            surface.blit(gs, (sx - 10, sy + 10))

    def _draw_fruit_tree(self, surface, sx, sy, now):
        sway = math.sin(now * 0.001 + self.anim_offset) * 2
        pygame.draw.rect(surface, (100, 65, 35), (sx - 4, sy - 10, 8, 24))
        pygame.draw.circle(surface, (25, 100, 25), (int(sx + sway), sy - 22), 18)
        pygame.draw.circle(surface, (40, 120, 35), (int(sx + sway - 4), sy - 18), 13)
        pygame.draw.circle(surface, (35, 110, 30), (int(sx + sway + 5), sy - 26), 11)
        pygame.draw.circle(surface, (55, 140, 45), (int(sx + sway - 2), sy - 26), 6)
        if self.has_healing:
            swi = int(sx + sway)
            pygame.draw.circle(surface, (220, 40, 30), (swi - 8, sy - 14), 4)
            pygame.draw.circle(surface, (220, 40, 30), (swi + 6, sy - 18), 4)
            pygame.draw.circle(surface, (220, 40, 30), (swi - 2, sy - 28), 3)
            pygame.draw.line(surface, (80, 50, 20), (swi - 8, sy - 18), (swi - 8, sy - 14), 1)
            pygame.draw.line(surface, (80, 50, 20), (swi + 6, sy - 22), (swi + 6, sy - 18), 1)

    def _draw_rock(self, surface, sx, sy, now):
        pts = [
            (sx - 14, sy + 4), (sx - 10, sy - 8), (sx - 2, sy - 12),
            (sx + 8, sy - 9), (sx + 13, sy - 2), (sx + 11, sy + 6),
            (sx + 2, sy + 8), (sx - 8, sy + 7),
        ]
        pygame.draw.polygon(surface, (100, 95, 88), pts)
        pygame.draw.polygon(surface, (120, 115, 108), pts, 2)
        pygame.draw.circle(surface, (130, 125, 118), (sx - 2, sy - 4), 4)

    def _draw_stump(self, surface, sx, sy, now):
        pygame.draw.ellipse(surface, (80, 55, 30), (sx - 10, sy - 4, 20, 12))
        pygame.draw.ellipse(surface, (100, 70, 40), (sx - 8, sy - 6, 16, 8))
        pygame.draw.ellipse(surface, (70, 48, 25), (sx - 5, sy - 4, 10, 5), 1)

    # ---- City props ----

    def _draw_building(self, surface, sx, sy, now):
        w, h = 50, 70
        shadow = pygame.Surface((w + 6, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 40), (0, 0, w + 6, 10))
        surface.blit(shadow, (sx - w // 2 - 3, sy + 8))
        wall_color = (50, 48, 55)
        pygame.draw.rect(surface, wall_color, (sx - w // 2, sy - h + 20, w, h))
        broken_top = [
            (sx - w // 2, sy - h + 20),
            (sx - w // 2 + 8, sy - h + 14),
            (sx - w // 2 + 16, sy - h + 22),
            (sx - w // 2 + 22, sy - h + 10),
            (sx - 2, sy - h + 18),
            (sx + 6, sy - h + 8),
            (sx + 14, sy - h + 20),
            (sx + w // 2, sy - h + 16),
            (sx + w // 2, sy - h + 20),
        ]
        bg_pts = broken_top + [(sx + w // 2, sy - h), (sx - w // 2, sy - h)]
        pygame.draw.polygon(surface, (40, 38, 45), bg_pts)
        pygame.draw.lines(surface, (65, 60, 70), False, broken_top, 2)
        for wy in range(sy - h + 30, sy + 10, 14):
            for wx_off in [-14, -2, 10]:
                wx = sx + wx_off
                is_broken = (int(self.anim_offset * 100 + wx + wy) % 5) < 2
                if is_broken:
                    pygame.draw.rect(surface, (20, 18, 25), (wx, wy, 8, 10))
                    pygame.draw.line(surface, (60, 55, 65), (wx, wy), (wx + 8, wy + 10), 1)
                else:
                    flicker = 0.3 + 0.7 * math.sin(now * 0.001 + wx * 0.1 + self.anim_offset)
                    wc = int(40 + 25 * flicker)
                    pygame.draw.rect(surface, (wc, wc - 10, 15), (wx, wy, 8, 10))
        pygame.draw.rect(surface, (65, 60, 70), (sx - w // 2, sy - h + 20, w, h), 2)

    def _draw_car(self, surface, sx, sy, now):
        body_color = (60 + int(self.anim_offset * 10) % 30,
                      40 + int(self.anim_offset * 7) % 20,
                      40 + int(self.anim_offset * 13) % 20)
        pygame.draw.rect(surface, body_color, (sx - 20, sy - 8, 40, 14))
        pygame.draw.polygon(surface, body_color, [
            (sx - 16, sy - 8), (sx - 10, sy - 16), (sx + 8, sy - 16),
            (sx + 16, sy - 8),
        ])
        pygame.draw.polygon(surface, (40, 50, 60), [
            (sx - 8, sy - 15), (sx - 4, sy - 8), (sx + 6, sy - 8),
            (sx + 8, sy - 15),
        ])
        pygame.draw.line(surface, (80, 90, 100), (sx - 2, sy - 14), (sx + 3, sy - 10), 1)
        pygame.draw.line(surface, (80, 90, 100), (sx + 3, sy - 10), (sx, sy - 9), 1)
        pygame.draw.circle(surface, (30, 30, 35), (sx - 12, sy + 6), 5)
        pygame.draw.circle(surface, (30, 30, 35), (sx + 12, sy + 6), 5)
        pygame.draw.circle(surface, (50, 50, 55), (sx - 12, sy + 6), 3)
        pygame.draw.circle(surface, (50, 50, 55), (sx + 12, sy + 6), 3)
        pygame.draw.circle(surface, (100, 50, 30), (sx - 6, sy - 4), 2)
        pygame.draw.circle(surface, (90, 45, 25), (sx + 10, sy - 2), 3)
        pygame.draw.rect(surface, (75, 70, 65), (sx - 20, sy - 8, 40, 14), 1)

    def _draw_first_aid_box(self, surface, sx, sy, now):
        bob = math.sin(now * 0.002 + self.anim_offset) * 1
        pygame.draw.rect(surface, (120, 120, 125), (sx - 2, sy - 4, 4, 20))
        bx, by = sx, int(sy - 12 + bob)
        if self.has_healing:
            pygame.draw.rect(surface, (230, 230, 235), (bx - 8, by - 8, 16, 14))
            pygame.draw.rect(surface, (200, 40, 40), (bx - 8, by - 8, 16, 14), 2)
            pygame.draw.rect(surface, (220, 30, 30), (bx - 2, by - 6, 4, 10))
            pygame.draw.rect(surface, (220, 30, 30), (bx - 5, by - 3, 10, 4))
            gs = pygame.Surface((24, 22), pygame.SRCALPHA)
            pygame.draw.ellipse(gs, (255, 100, 100, 30), (0, 0, 24, 22))
            surface.blit(gs, (bx - 12, by - 11))
        else:
            pygame.draw.rect(surface, (80, 80, 85), (bx - 6, by - 6, 12, 10))
            pygame.draw.line(surface, (100, 100, 105), (bx - 6, by - 6), (bx + 6, by + 4), 1)

    def _draw_rubble(self, surface, sx, sy, now):
        pygame.draw.polygon(surface, (65, 60, 68), [
            (sx - 10, sy + 4), (sx - 6, sy - 4), (sx + 2, sy - 6),
            (sx + 10, sy - 2), (sx + 8, sy + 5), (sx - 4, sy + 6),
        ])
        pygame.draw.polygon(surface, (80, 75, 78), [
            (sx - 10, sy + 4), (sx - 6, sy - 4), (sx + 2, sy - 6),
            (sx + 10, sy - 2), (sx + 8, sy + 5), (sx - 4, sy + 6),
        ], 1)
        pygame.draw.line(surface, (90, 70, 50), (sx - 3, sy - 4), (sx - 5, sy - 12), 1)
        pygame.draw.line(surface, (90, 70, 50), (sx + 4, sy - 3), (sx + 6, sy - 10), 1)

    def _draw_fire_hydrant(self, surface, sx, sy, now):
        pygame.draw.rect(surface, (180, 40, 30), (sx - 4, sy - 8, 8, 14))
        pygame.draw.rect(surface, (200, 50, 40), (sx - 6, sy - 4, 12, 4))
        pygame.draw.ellipse(surface, (160, 35, 25), (sx - 5, sy - 10, 10, 5))
        pygame.draw.circle(surface, (120, 60, 30), (sx + 2, sy), 2)

    # ---- Abyss props ----

    def _draw_eldritch_pillar(self, surface, sx, sy, now):
        pulse = 0.5 + 0.5 * math.sin(now * 0.002 + self.anim_offset)
        pygame.draw.rect(surface, (35, 20, 55), (sx - 6, sy - 30, 12, 44))
        for ry in range(sy - 26, sy + 8, 8):
            rune_a = int(80 + 120 * math.sin(now * 0.003 + ry * 0.1 + self.anim_offset))
            rs = pygame.Surface((8, 4), pygame.SRCALPHA)
            pygame.draw.rect(rs, (140, 60, 220, rune_a), (0, 0, 8, 4))
            surface.blit(rs, (sx - 4, ry))
        crystal_pts = [(sx, sy - 38), (sx - 6, sy - 28), (sx + 6, sy - 28)]
        pc = int(120 + 80 * pulse)
        pygame.draw.polygon(surface, (pc, 50, 200), crystal_pts)
        gr = int(10 + 4 * pulse)
        gs = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
        pygame.draw.circle(gs, (160, 80, 255, int(50 * pulse)), (gr, gr), gr)
        surface.blit(gs, (sx - gr, sy - 36 - gr + 3))

    def _draw_void_crystal(self, surface, sx, sy, now):
        pulse = 0.5 + 0.5 * math.sin(now * 0.004 + self.anim_offset)
        hover = math.sin(now * 0.003 + self.anim_offset) * 4
        cy = int(sy + hover)
        pts = [
            (sx, cy - 16), (sx - 8, cy - 4), (sx - 5, cy + 8),
            (sx + 5, cy + 8), (sx + 8, cy - 4),
        ]
        pc = int(100 + 60 * pulse)
        pygame.draw.polygon(surface, (pc, 40, 180), pts)
        pygame.draw.polygon(surface, (180, 100, 255), pts, 2)
        gs = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(gs, (200, 120, 255, int(80 * pulse)), (8, 8), 6)
        surface.blit(gs, (sx - 8, cy - 8))
        shadow = pygame.Surface((16, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 40), (0, 0, 16, 6))
        surface.blit(shadow, (sx - 8, sy + 10))

    def _draw_tentacle(self, surface, sx, sy, now):
        prev = (sx, sy + 4)
        segments = 8
        for i in range(segments):
            t = i / segments
            wobble = math.sin(now * 0.005 + i * 0.8 + self.anim_offset) * (6 * t)
            nx = sx + int(wobble)
            ny = sy + 4 - int(t * 30)
            thick = max(1, int(4 * (1 - t)))
            cv = int(60 + 40 * t)
            pygame.draw.line(surface, (cv, 20, cv + 40), prev, (nx, ny), thick)
            prev = (nx, ny)
        wave = math.sin(now * 0.003 + self.anim_offset)
        gs = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(gs, (180, 60, 220, int(100 + 80 * wave)), (4, 4), 4)
        surface.blit(gs, (prev[0] - 4, prev[1] - 4))
        pygame.draw.ellipse(surface, (20, 10, 30), (sx - 6, sy + 2, 12, 6))

    def _draw_void_bloom(self, surface, sx, sy, now):
        pulse = 0.5 + 0.5 * math.sin(now * 0.003 + self.anim_offset)
        pygame.draw.rect(surface, (50, 25, 70), (sx - 2, sy - 6, 4, 20))
        bloom_y = sy - 12
        for i in range(5):
            a = now * 0.001 + i * math.tau / 5 + self.anim_offset
            px = sx + int(math.cos(a) * 8)
            py = bloom_y + int(math.sin(a) * 5)
            pc = int(120 + 60 * pulse)
            pygame.draw.circle(surface, (pc, 40, 180), (px, py), 4)
        if self.has_healing:
            oc = int(180 + 60 * pulse)
            pygame.draw.circle(surface, (oc, 120, 255), (sx, bloom_y), 5)
            gs = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(gs, (200, 140, 255, int(60 * pulse)), (8, 8), 8)
            surface.blit(gs, (sx - 8, bloom_y - 8))
        else:
            pygame.draw.circle(surface, (60, 30, 80), (sx, bloom_y), 4)

    def _draw_floating_rock(self, surface, sx, sy, now):
        hover = math.sin(now * 0.002 + self.anim_offset) * 5
        fy = int(sy + hover - 6)
        pts = [
            (sx - 8, fy + 4), (sx - 6, fy - 6), (sx + 2, fy - 8),
            (sx + 9, fy - 3), (sx + 7, fy + 5), (sx - 2, fy + 6),
        ]
        pygame.draw.polygon(surface, (60, 50, 75), pts)
        pygame.draw.polygon(surface, (80, 70, 100), pts, 1)
        pygame.draw.circle(surface, (90, 60, 110), (sx, fy - 2), 3)
        shadow = pygame.Surface((14, 5), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 30), (0, 0, 14, 5))
        surface.blit(shadow, (sx - 7, sy + 8))


class EnvironmentSystem:
    """Scatters zone-specific decorative props across the map."""

    def __init__(self, zone: str = "wasteland"):
        self.zone = zone
        self.props: list[Prop] = []
        self._generate()

    def _generate(self):
        world_w = MAP_WIDTH * TILE_SIZE
        world_h = MAP_HEIGHT * TILE_SIZE
        margin = TILE_SIZE * 2
        center_x = world_w // 2
        center_y = world_h // 2

        zone_cfg = ZONE_PROPS.get(self.zone, ZONE_PROPS["wasteland"])
        kinds = zone_cfg["kinds"]
        healing_kind = zone_cfg["healing_kind"]
        healing_chance = zone_cfg["healing_chance"]
        count = zone_cfg["count"]

        random.seed(42)
        for _ in range(count):
            x = random.randint(margin, world_w - margin)
            y = random.randint(margin, world_h - margin)
            if math.hypot(x - center_x, y - center_y) < 200:
                continue
            kind = random.choice(kinds)
            if random.random() < healing_chance:
                kind = healing_kind
            self.props.append(Prop(x, y, kind))
        random.seed()

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int,
             screen_w: int, screen_h: int):
        cull_margin = 80 if self.zone == "city" else 50
        for p in self.props:
            sx = p.x - camera_x
            sy = p.y - camera_y
            if (-cull_margin < sx < screen_w + cull_margin
                    and -cull_margin < sy < screen_h + cull_margin):
                p.draw(surface, camera_x, camera_y)

    def collide_entity(self, ex: float, ey: float,
                       entity_half: int) -> tuple[float, float]:
        """Push entity out of any solid props. Returns corrected (x, y)."""
        for p in self.props:
            if p.collision_r <= 0:
                continue
            dx = ex - p.x
            dy = ey - p.y
            dist = math.hypot(dx, dy)
            min_dist = p.collision_r + entity_half
            if dist < min_dist and dist > 0:
                overlap = min_dist - dist
                ex += (dx / dist) * overlap
                ey += (dy / dist) * overlap
        return ex, ey

    def check_healing_prop_hit(self, attack_rect: pygame.Rect,
                                now: int) -> list[tuple[float, float, str]]:
        """Check if an attack hits any healing props. Returns (x, y, kind) drops."""
        drops = []
        respawn_delay = 30000
        for p in self.props:
            if not p.has_healing:
                continue
            tree_rect = pygame.Rect(p.x - 18, p.y - 30, 36, 40)
            if attack_rect.colliderect(tree_rect):
                p.has_healing = False
                p.healing_respawn_time = now + respawn_delay
                drops.append((p.x, p.y + 10, p.kind))
        return drops

    def update_healing(self, now: int):
        """Regrow healing items whose timer has expired."""
        for p in self.props:
            if p.kind in Prop.HEALING_KINDS and not p.has_healing:
                if now >= p.healing_respawn_time:
                    p.has_healing = True
