import pygame
import math
import random


class Particle:
    """A single visual particle."""

    __slots__ = ("x", "y", "dx", "dy", "life", "max_life",
                 "color", "size", "gravity", "shrink")

    def __init__(self, x, y, dx, dy, life, color, size, gravity=0.0, shrink=True):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.gravity = gravity
        self.shrink = shrink

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += self.gravity
        self.dx *= 0.96
        self.dy *= 0.96
        self.life -= 1

    @property
    def alive(self):
        return self.life > 0


class DeathAnimation:
    """A brief shrink-spin-fade animation at an enemy's death position."""

    __slots__ = ("x", "y", "enemy_type", "timer", "duration", "color")

    def __init__(self, x: float, y: float, enemy_type: str, color: tuple):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        self.timer = 0.0
        self.duration = 400.0  # ms
        self.color = color

    @property
    def alive(self):
        return self.timer < self.duration

    def update(self, dt: float):
        self.timer += dt

    def draw(self, surface: pygame.Surface, cx: int, cy: int):
        t = self.timer / self.duration  # 0..1
        if t >= 1.0:
            return
        sx = int(self.x - cx)
        sy = int(self.y - cy)

        # Shrink from full size to nothing
        scale = 1.0 - t
        alpha = int(255 * (1.0 - t))
        spin = t * 720  # degrees, two full rotations

        size = int(24 * scale)
        if size < 2:
            return

        # Create a small surface representing the dying enemy
        w = h = size * 2 + 4
        tmp = pygame.Surface((w, h), pygame.SRCALPHA)
        c = (*self.color[:3], alpha)
        # Body shrinking ellipse
        pygame.draw.ellipse(tmp, c, (2, h // 4, w - 4, h // 2))
        # "X" eyes
        eye_c = (255, 255, 255, alpha)
        mid_x, mid_y = w // 2, h // 3
        es = max(2, size // 4)
        pygame.draw.line(tmp, eye_c, (mid_x - es - 3, mid_y - es), (mid_x - 3 + es, mid_y + es), 2)
        pygame.draw.line(tmp, eye_c, (mid_x - es - 3, mid_y + es), (mid_x - 3 + es, mid_y - es), 2)
        pygame.draw.line(tmp, eye_c, (mid_x + 3 - es, mid_y - es), (mid_x + 3 + es, mid_y + es), 2)
        pygame.draw.line(tmp, eye_c, (mid_x + 3 - es, mid_y + es), (mid_x + 3 + es, mid_y - es), 2)

        # Rotate
        rotated = pygame.transform.rotate(tmp, spin)
        rect = rotated.get_rect(center=(sx, sy))
        surface.blit(rotated, rect)


class AnimationSystem:
    """Manages screen-space particles and effects."""

    def __init__(self):
        self.particles: list[Particle] = []
        self.death_anims: list[DeathAnimation] = []
        self.screen_shake = 0.0
        self._shake_dx = 0
        self._shake_dy = 0

    def spawn_death_burst(self, world_x: float, world_y: float, color: tuple, count: int = 12):
        """Explosion of particles when an enemy dies."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(1.5, 5.0)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            life = random.randint(15, 30)
            size = random.uniform(2, 5)
            # Slightly vary color
            r = min(255, max(0, color[0] + random.randint(-30, 30)))
            g = min(255, max(0, color[1] + random.randint(-30, 30)))
            b = min(255, max(0, color[2] + random.randint(-30, 30)))
            self.particles.append(
                Particle(world_x, world_y, dx, dy, life, (r, g, b), size, gravity=0.1))

    def spawn_hit_sparks(self, world_x: float, world_y: float, count: int = 6):
        """Small white/yellow sparks on hit."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(2, 4)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            life = random.randint(6, 14)
            c = random.choice([(255, 255, 200), (255, 220, 100), (255, 255, 255)])
            self.particles.append(
                Particle(world_x, world_y, dx, dy, life, c, random.uniform(1.5, 3)))

    def spawn_death_anim(self, world_x: float, world_y: float, enemy_type: str, color: tuple):
        """Start a death animation at the given world position."""
        self.death_anims.append(DeathAnimation(world_x, world_y, enemy_type, color))

    def spawn_confetti_explosion(self, world_x: float, world_y: float, count: int = 20):
        """Burst of colourful confetti particles for grenade explosions."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(2.0, 6.0)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            life = random.randint(20, 40)
            c = random.choice([
                (255, 50, 100), (50, 255, 100), (100, 50, 255),
                (255, 255, 50), (50, 200, 255), (255, 150, 50)])
            size = random.uniform(2, 5)
            self.particles.append(
                Particle(world_x, world_y, dx, dy, life, c, size, gravity=0.15))

    def add_screen_shake(self, amount: float):
        self.screen_shake = min(12, self.screen_shake + amount)

    def update(self, dt: float = 16.0):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

        for da in self.death_anims:
            da.update(dt)
        self.death_anims = [da for da in self.death_anims if da.alive]

        # Decay screen shake
        if self.screen_shake > 0.5:
            self._shake_dx = random.randint(int(-self.screen_shake), int(self.screen_shake))
            self._shake_dy = random.randint(int(-self.screen_shake), int(self.screen_shake))
            self.screen_shake *= 0.85
        else:
            self.screen_shake = 0
            self._shake_dx = 0
            self._shake_dy = 0

    @property
    def shake_offset(self) -> tuple[int, int]:
        return (self._shake_dx, self._shake_dy)

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        for da in self.death_anims:
            da.draw(surface, camera_x, camera_y)
        for p in self.particles:
            sx = int(p.x - camera_x)
            sy = int(p.y - camera_y)
            t = p.life / p.max_life
            alpha = int(255 * t)
            size = p.size * t if p.shrink else p.size
            size = max(1, int(size))
            if 0 < alpha <= 255:
                s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p.color, alpha), (size, size), size)
                surface.blit(s, (sx - size, sy - size))
