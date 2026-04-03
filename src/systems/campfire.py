import pygame
import math
import random
from src.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT


class Campfire:
    """A campfire at map center where the player heals between waves."""

    def __init__(self):
        self.x = (MAP_WIDTH * TILE_SIZE) // 2
        self.y = (MAP_HEIGHT * TILE_SIZE) // 2
        self.radius = 80  # healing radius
        self.heal_rate = 2  # HP per tick when resting
        self.heal_interval = 200  # ms between heals
        self.last_heal = 0
        self.active = False  # only active between waves
        self.particles: list[dict] = []

    def set_active(self, active: bool):
        self.active = active

    def update(self, now: int, player):
        # Always update particles for visuals
        self._update_particles(now)

        if not self.active:
            return

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist < self.radius and player.hp < player.max_hp:
            if now - self.last_heal >= self.heal_interval:
                player.hp = min(player.max_hp, player.hp + self.heal_rate)
                self.last_heal = now

    def _update_particles(self, now: int):
        # Spawn new particles
        if now % 3 == 0:
            self.particles.append({
                "x": self.x + random.uniform(-8, 8),
                "y": self.y,
                "vx": random.uniform(-0.3, 0.3),
                "vy": random.uniform(-1.5, -0.5),
                "life": random.randint(400, 900),
                "born": now,
                "size": random.uniform(2, 5),
            })
        # Update existing
        alive = []
        for p in self.particles:
            age = now - p["born"]
            if age < p["life"]:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] -= 0.01  # rise faster
                alive.append(p)
        self.particles = alive[-60:]  # cap particles

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        now = pygame.time.get_ticks()

        # Healing radius indicator (only when active)
        if self.active:
            glow_surf = pygame.Surface((self.radius * 2 + 4, self.radius * 2 + 4), pygame.SRCALPHA)
            pulse = int(20 + 15 * math.sin(now * 0.003))
            pygame.draw.circle(glow_surf, (255, 180, 50, pulse),
                               (self.radius + 2, self.radius + 2), self.radius)
            surface.blit(glow_surf, (sx - self.radius - 2, sy - self.radius - 2))

        # Fire glow on ground
        glow_r = 30 + int(5 * math.sin(now * 0.008))
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 120, 20, 40), (glow_r, glow_r), glow_r)
        surface.blit(glow_surf, (sx - glow_r, sy - glow_r))

        # Log base
        pygame.draw.ellipse(surface, (70, 45, 20), (sx - 14, sy - 2, 28, 10))
        pygame.draw.rect(surface, (90, 55, 25), (sx - 12, sy - 4, 10, 6))
        pygame.draw.rect(surface, (85, 50, 22), (sx + 2, sy - 3, 10, 5))

        # Fire flames
        flicker = math.sin(now * 0.012) * 3
        # Outer flame
        flame_pts = [
            (sx - 6, sy - 2),
            (sx + 6, sy - 2),
            (sx + 3, sy - 16 + flicker),
            (sx, sy - 22 + flicker * 1.3),
            (sx - 3, sy - 14 + flicker),
        ]
        pygame.draw.polygon(surface, (255, 100, 20), flame_pts)
        # Inner flame
        inner_pts = [
            (sx - 3, sy - 4),
            (sx + 3, sy - 4),
            (sx + 1, sy - 12 + flicker),
            (sx - 1, sy - 10 + flicker),
        ]
        pygame.draw.polygon(surface, (255, 200, 50), inner_pts)
        # Core
        pygame.draw.circle(surface, (255, 240, 150), (sx, int(sy - 8 + flicker * 0.5)), 3)

        # Fire particles
        for p in self.particles:
            age = now - p["born"]
            ratio = age / p["life"]
            alpha = max(0, int(200 * (1.0 - ratio)))
            r = max(1, int(p["size"] * (1.0 - ratio * 0.5)))
            px = int(p["x"] - camera_x)
            py = int(p["y"] - camera_y)
            # Color shifts from yellow to red to dark
            cr = max(0, min(255, int(255 * (1.0 - ratio * 0.3))))
            cg = max(0, min(255, int(180 * (1.0 - ratio))))
            cb = 0
            ps = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (cr, cg, cb, alpha), (r + 1, r + 1), r)
            surface.blit(ps, (px - r - 1, py - r - 1))

        # "Rest here" text when active
        if self.active:
            from src.font_cache import get_font
            txt = get_font("consolas", 12).render("~ REST ~", True, (255, 200, 100))
            surface.blit(txt, (sx - txt.get_width() // 2, sy + 14))
