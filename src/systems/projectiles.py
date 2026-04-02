import pygame
import math
from src.settings import ENEMY_BULLET_SPEED, ENEMY_BULLET_SIZE, ENEMY_BULLET_COLOR


class Projectile:
    """A single bullet fired by a Dalek."""

    def __init__(self, x: float, y: float, dx: float, dy: float, damage: int):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = ENEMY_BULLET_SPEED
        self.size = ENEMY_BULLET_SIZE
        self.damage = damage
        self.alive = True
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 4000  # ms

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.x - self.size // 2,
            self.y - self.size // 2,
            self.size,
            self.size,
        )

    def update(self, now: int):
        if not self.alive:
            return
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        if now - self.spawn_time > self.lifetime:
            self.alive = False

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        if not self.alive:
            return
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        # Glowing bullet
        pygame.draw.circle(surface, ENEMY_BULLET_COLOR, (sx, sy), self.size)
        pygame.draw.circle(surface, (200, 255, 240), (sx, sy), self.size // 2)


class ProjectileSystem:
    """Manages all active projectiles."""

    def __init__(self):
        self.bullets: list[Projectile] = []

    def spawn(self, x: float, y: float, target_x: float, target_y: float, damage: int):
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        self.bullets.append(Projectile(x, y, dx / dist, dy / dist, damage))

    def update(self, now: int, player, world_w: int, world_h: int):
        for b in self.bullets:
            b.update(now)
            # Out-of-bounds check
            if b.x < 0 or b.x > world_w or b.y < 0 or b.y > world_h:
                b.alive = False
            # Hit player
            if b.alive and b.rect.colliderect(player.rect):
                player.take_damage(b.damage, now)
                b.alive = False
        self.bullets = [b for b in self.bullets if b.alive]

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        for b in self.bullets:
            b.draw(surface, camera_x, camera_y)


# ---- Player-thrown daggers ----

class ThrownDagger:
    """A spinning dagger thrown by the player."""

    def __init__(self, x: float, y: float, dx: float, dy: float, damage: int):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = 7.0
        self.damage = damage
        self.alive = True
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 800  # ms
        self.size = 5
        self.angle = math.atan2(dy, dx)

    def update(self, now: int):
        if not self.alive:
            return
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.angle += 0.3  # spin
        if now - self.spawn_time > self.lifetime:
            self.alive = False

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        if not self.alive:
            return
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        # Spinning dagger blade
        bx = int(math.cos(self.angle) * 8)
        by = int(math.sin(self.angle) * 8)
        pygame.draw.line(surface, (180, 220, 220), (sx - bx, sy - by), (sx + bx, sy + by), 3)
        pygame.draw.circle(surface, (200, 255, 220), (sx + bx, sy + by), 2)


class PlayerProjectileSystem:
    """Manages player-thrown projectiles (daggers)."""

    def __init__(self):
        self.daggers: list[ThrownDagger] = []

    def spawn_daggers(self, x: float, y: float, facing_x: float, facing_y: float, damage: int):
        """Spawn twin daggers at a slight spread."""
        base_angle = math.atan2(facing_y, facing_x)
        for offset in (-0.15, 0.15):
            a = base_angle + offset
            dx = math.cos(a)
            dy = math.sin(a)
            self.daggers.append(ThrownDagger(x, y, dx, dy, damage))

    def update(self, now: int, enemies: list, world_w: int, world_h: int):
        """Move daggers, check hits. Returns list of (enemy, damage) tuples."""
        hits = []
        for d in self.daggers:
            d.update(now)
            if d.x < 0 or d.x > world_w or d.y < 0 or d.y > world_h:
                d.alive = False
            if not d.alive:
                continue
            d_rect = pygame.Rect(d.x - d.size, d.y - d.size, d.size * 2, d.size * 2)
            for enemy in enemies:
                if not enemy.alive:
                    continue
                if d_rect.colliderect(enemy.rect):
                    kb_x = enemy.x - d.x
                    kb_y = enemy.y - d.y
                    enemy.take_damage(d.damage, kb_x, kb_y, now)
                    hits.append((enemy, d.damage))
                    d.alive = False
                    break
        self.daggers = [d for d in self.daggers if d.alive]
        return hits

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        for d in self.daggers:
            d.draw(surface, camera_x, camera_y)
