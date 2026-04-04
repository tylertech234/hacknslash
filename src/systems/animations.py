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
    """A death animation at an enemy's death position — shape varies by type."""

    # Duration (ms) and base size by type
    _TYPE_PARAMS = {
        # (duration_ms, base_size, style)
        "cyber_rat":      (220, 14,  "burst_ring"),
        "cyber_raccoon":  (300, 24,  "shatter"),
        "mega_cyber_deer":(800, 54,  "boss_explosion"),
        "d_lek":          (380, 28,  "burst_ring"),
        "specter":        (500, 32,  "dissolve"),
        "iron_sentinel": (700, 52,  "boss_explosion"),
        "warlord_kron":  (1100, 72, "big_boss_explosion"),
        "charger":       (300, 26,  "shatter"),
        "shielder":      (420, 36,  "shield_pop"),
        "spitter":       (350, 28,  "splat"),
        "cyber_zombie":  (360, 28,  "burst_ring"),
        "cyber_dog":     (300, 22,  "shatter"),
        "drone":         (280, 20,  "burst_ring"),
        "cultist":       (400, 30,  "dissolve"),
        "shambler":      (500, 40,  "splat"),
        "street_preacher": (750, 50,  "boss_explosion"),
        "eldritch_horror":(1200,78, "big_boss_explosion"),
        "void_wisp":     (250, 18,  "dissolve"),
        "rift_walker":   (350, 32,  "dissolve"),
        "mirror_shade":  (300, 26,  "shatter"),
        "gravity_warden":(420, 38,  "shield_pop"),
        "null_serpent":  (360, 34,  "splat"),
        "architect":     (800, 54,  "boss_explosion"),
        "nexus":         (1400, 88, "big_boss_explosion"),
    }

    def __init__(self, x: float, y: float, enemy_type: str, color: tuple):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        params = self._TYPE_PARAMS.get(enemy_type, (400, 28, "burst_ring"))
        self.duration = float(params[0])
        self.base_size = params[1]
        self.style = params[2]
        self.timer = 0.0
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
        alpha = int(255 * (1.0 - t) ** 1.2)
        c3 = self.color[:3]

        if self.style == "burst_ring":
            # Expanding ring + shrinking body
            ring_r = int(self.base_size * (0.5 + t * 1.5))
            if ring_r > 0 and alpha > 0:
                rs = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(rs, (*c3, alpha), (ring_r + 2, ring_r + 2), ring_r, 3)
                surface.blit(rs, (sx - ring_r - 2, sy - ring_r - 2))
            # Shrinking body
            body_r = max(1, int(self.base_size * (1.0 - t)))
            bs = pygame.Surface((body_r * 2 + 2, body_r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(bs, (*c3, alpha), (body_r + 1, body_r + 1), body_r)
            surface.blit(bs, (sx - body_r - 1, sy - body_r - 1))

        elif self.style == "dissolve":
            # Fade-expanding ghost cloud
            for i in range(5):
                angle = i * math.pi * 2 / 5 + t * 4
                r = int(self.base_size * (0.4 + t * 1.2))
                ox = int(math.cos(angle) * r * 0.5)
                oy = int(math.sin(angle) * r * 0.5)
                blob_r = max(1, int(self.base_size * 0.45 * (1.0 - t * 0.7)))
                a2 = max(0, int(alpha * (1.0 - i * 0.12)))
                bs = pygame.Surface((blob_r * 2 + 2, blob_r * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(bs, (*c3, a2), (blob_r + 1, blob_r + 1), blob_r)
                surface.blit(bs, (sx + ox - blob_r - 1, sy + oy - blob_r - 1))

        elif self.style == "shatter":
            # Debris shards flying outward, then fade
            for i in range(6):
                angle = i * math.pi * 2 / 6 + math.pi / 6
                dist = int(self.base_size * t * 2.2)
                ox = int(math.cos(angle) * dist)
                oy = int(math.sin(angle) * dist)
                shard_w = max(2, int(8 * (1.0 - t)))
                shard_h = max(2, int(4 * (1.0 - t)))
                ss = pygame.Surface((shard_w + 2, shard_h + 2), pygame.SRCALPHA)
                pygame.draw.ellipse(ss, (*c3, alpha), (1, 1, shard_w, shard_h))
                spin_surf = pygame.transform.rotate(ss, math.degrees(angle) + t * 360)
                surface.blit(spin_surf, (sx + ox - spin_surf.get_width() // 2,
                                         sy + oy - spin_surf.get_height() // 2))

        elif self.style == "shield_pop":
            # Two concentric rings expanding outward
            for mult in (1.0, 1.6):
                ring_r = int(self.base_size * mult * t * 1.8)
                if ring_r > 0 and alpha > 0:
                    rs = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
                    ring_alpha = max(0, int(alpha * (1.0 - t * 0.5)))
                    pygame.draw.circle(rs, (*c3, ring_alpha), (ring_r + 2, ring_r + 2), ring_r, 4)
                    surface.blit(rs, (sx - ring_r - 2, sy - ring_r - 2))

        elif self.style == "splat":
            # Acid splat — 8 blobs expanding along cardinal + diagonal dirs
            for i in range(8):
                angle = i * math.pi / 4
                dist = int(self.base_size * t * 2.5)
                ox = int(math.cos(angle) * dist)
                oy = int(math.sin(angle) * dist)
                blob_r = max(1, int(self.base_size * 0.3 * (1.0 - t)))
                bs = pygame.Surface((blob_r * 2 + 2, blob_r * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(bs, (*c3, alpha), (blob_r + 1, blob_r + 1), blob_r)
                surface.blit(bs, (sx + ox - blob_r - 1, sy + oy - blob_r - 1))

        elif self.style == "boss_explosion":
            # Three expanding shockwave rings + bright core flash
            for phase, ring_mult in enumerate((0.6, 1.0, 1.4)):
                t2 = min(1.0, t * (1.0 + phase * 0.25))
                ring_r = int(self.base_size * ring_mult * t2 * 2.5)
                ring_a = max(0, int(200 * (1.0 - t2) ** 1.5))
                if ring_r > 0 and ring_a > 0:
                    rs = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(rs, (*c3, ring_a), (ring_r + 2, ring_r + 2), ring_r, 5)
                    surface.blit(rs, (sx - ring_r - 2, sy - ring_r - 2))
            # Bright flash core
            core_r = max(1, int(self.base_size * 0.8 * (1.0 - t) ** 0.5))
            core_a = max(0, int(255 * (1.0 - t) ** 2))
            if core_r > 0 and core_a > 0:
                cs = pygame.Surface((core_r * 2 + 2, core_r * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(cs, (255, 255, 200, core_a), (core_r + 1, core_r + 1), core_r)
                surface.blit(cs, (sx - core_r - 1, sy - core_r - 1))

        elif self.style == "big_boss_explosion":
            # Massive layered explosion — 5 rings, giant flash, debris
            for phase in range(5):
                frac = 0.2 * phase
                t2 = max(0.0, min(1.0, (t - frac) / (1.0 - frac))) if t > frac else 0.0
                if t2 <= 0:
                    continue
                ring_r = int(self.base_size * (1.5 + phase * 0.6) * t2 * 2.0)
                ring_a = max(0, int(220 * (1.0 - t2) ** 1.3))
                if ring_r > 0 and ring_a > 0:
                    rs = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
                    ring_col = (*c3, ring_a)
                    # Alternating colors for drama
                    if phase % 2 == 1:
                        ring_col = (255, min(255, c3[0] + 100), 50, ring_a)
                    pygame.draw.circle(rs, ring_col, (ring_r + 2, ring_r + 2), ring_r, 6)
                    surface.blit(rs, (sx - ring_r - 2, sy - ring_r - 2))
            # Giant white flash core — fades quickly
            if t < 0.35:
                flash_r = int(self.base_size * 1.2 * (1.0 - t / 0.35) ** 0.6)
                flash_a = int(255 * (1.0 - t / 0.35) ** 1.5)
                if flash_r > 0 and flash_a > 0:
                    fs = pygame.Surface((flash_r * 2 + 2, flash_r * 2 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(fs, (255, 255, 255, flash_a), (flash_r + 1, flash_r + 1), flash_r)
                    surface.blit(fs, (sx - flash_r - 1, sy - flash_r - 1))
            # Debris chunks orbiting outward
            if t < 0.7:
                for i in range(12):
                    angle = i * math.pi * 2 / 12 + t * 3.0
                    dist = int(self.base_size * t * 3.5)
                    ox = int(math.cos(angle) * dist)
                    oy = int(math.sin(angle) * dist)
                    deb_r = max(2, int(6 * (1.0 - t / 0.7)))
                    da = max(0, int(alpha * (1.0 - t / 0.7)))
                    ds = pygame.Surface((deb_r * 2 + 2, deb_r * 2 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(ds, (*c3, da), (deb_r + 1, deb_r + 1), deb_r)
                    surface.blit(ds, (sx + ox - deb_r - 1, sy + oy - deb_r - 1))


class AnimationSystem:
    """Manages screen-space particles and effects."""

    def __init__(self):
        self.particles: list[Particle] = []
        self.death_anims: list[DeathAnimation] = []
        self.screen_shake = 0.0
        self._shake_dx = 0
        self._shake_dy = 0
        self._particle_surf_cache: dict[int, pygame.Surface] = {}

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
        _psc = self._particle_surf_cache
        for p in self.particles:
            sx = int(p.x - camera_x)
            sy = int(p.y - camera_y)
            t = p.life / p.max_life
            alpha = int(255 * t)
            size = p.size * t if p.shrink else p.size
            size = max(1, int(size))
            if 0 < alpha <= 255:
                if size not in _psc:
                    _psc[size] = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                s = _psc[size]
                s.fill((0, 0, 0, 0))
                pygame.draw.circle(s, (*p.color, alpha), (size, size), size)
                surface.blit(s, (sx - size, sy - size))
