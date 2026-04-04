import pygame
import math
from src.settings import ENEMY_BULLET_SPEED, ENEMY_BULLET_SIZE, ENEMY_BULLET_COLOR


class Projectile:
    """A single bullet fired by an enemy."""

    def __init__(self, x: float, y: float, dx: float, dy: float, damage: int,
                 style: str = "circle"):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = ENEMY_BULLET_SPEED
        self.size = ENEMY_BULLET_SIZE
        self.damage = damage
        self.style = style
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
        if self.style == "beam":
            # Elongated beam line in travel direction
            length = 18
            width = 3
            ex = int(self.dx * length)
            ey = int(self.dy * length)
            # Draw outer glow line
            pygame.draw.line(surface, (0, 220, 180), (sx - ex, sy - ey), (sx + ex, sy + ey), width + 2)
            # Draw bright core
            pygame.draw.line(surface, (180, 255, 240), (sx - ex, sy - ey), (sx + ex, sy + ey), width - 1)
        else:
            # Glowing bullet
            pygame.draw.circle(surface, ENEMY_BULLET_COLOR, (sx, sy), self.size)
            pygame.draw.circle(surface, (200, 255, 240), (sx, sy), self.size // 2)


class ProjectileSystem:
    """Manages all active projectiles."""

    def __init__(self):
        self.bullets: list[Projectile] = []

    def spawn(self, x: float, y: float, target_x: float, target_y: float, damage: int,
               style: str = "circle"):
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        self.bullets.append(Projectile(x, y, dx / dist, dy / dist, damage, style))

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
    """A projectile thrown by the player. Visual style varies by weapon."""

    def __init__(self, x: float, y: float, dx: float, dy: float, damage: int,
                 visual: str = "dagger", piercing: bool = False):
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
        self.visual = visual
        self.piercing = piercing
        self._hit_enemies: set = set()

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
        if self.visual == "arrow":
            self._draw_arrow(surface, sx, sy)
        elif self.visual == "bolt":
            self._draw_bolt(surface, sx, sy)
        elif self.visual == "pellet":
            self._draw_pellet(surface, sx, sy)
        else:
            self._draw_dagger(surface, sx, sy)

    def _draw_dagger(self, surface, sx, sy):
        bx = int(math.cos(self.angle) * 10)
        by = int(math.sin(self.angle) * 10)
        pygame.draw.line(surface, (180, 220, 220), (sx - bx, sy - by), (sx + bx, sy + by), 3)
        pygame.draw.circle(surface, (200, 255, 220), (sx + bx, sy + by), 3)
        glow = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.circle(glow, (150, 255, 200, 80), (7, 7), 7)
        surface.blit(glow, (sx - 7, sy - 7))

    def _draw_arrow(self, surface, sx, sy):
        angle = math.atan2(self.dy, self.dx)
        length = 18
        back_x = sx - int(math.cos(angle) * length)
        back_y = sy - int(math.sin(angle) * length)
        # Trail particles
        for i in range(4):
            t = (i + 1) / 5
            tx = int(sx + (back_x - sx) * t * 1.6)
            ty = int(sy + (back_y - sy) * t * 1.6)
            alpha = int(80 * (1.0 - t))
            ts = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(ts, (0, 255, 180, alpha), (3, 3), 3)
            surface.blit(ts, (tx - 3, ty - 3))
        # Shaft
        pygame.draw.line(surface, (0, 255, 180), (back_x, back_y), (sx, sy), 3)
        pygame.draw.line(surface, (200, 255, 240), (back_x, back_y), (sx, sy), 1)
        # Bright tip
        pygame.draw.circle(surface, (200, 255, 230), (sx, sy), 4)
        glow = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(glow, (0, 255, 180, 60), (10, 10), 10)
        surface.blit(glow, (sx - 10, sy - 10))

    def _draw_bolt(self, surface, sx, sy):
        now = pygame.time.get_ticks()
        pulse = 3 + int(math.sin(now * 0.015) * 1.5)
        pygame.draw.circle(surface, (255, 150, 50), (sx, sy), pulse)
        pygame.draw.circle(surface, (255, 220, 150), (sx, sy), max(1, pulse - 2))
        glow = pygame.Surface((pulse * 4, pulse * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 100, 50, 60), (pulse * 2, pulse * 2), pulse * 2)
        surface.blit(glow, (sx - pulse * 2, sy - pulse * 2))

    def _draw_pellet(self, surface, sx, sy):
        pygame.draw.circle(surface, (255, 255, 100), (sx, sy), 3)
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), 1)
        glow = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 255, 100, 50), (4, 4), 4)
        surface.blit(glow, (sx - 4, sy - 4))


# ---- Orbiting projectile (banana / blade) ----

class OrbitingProjectile:
    """A projectile that flies out, returns, and orbits the player.
    
    Can be a banana or a spinning blade. Max 3 orbiters at once;
    when a 4th is thrown the oldest is dropped."""

    def __init__(self, x: float, y: float, dx: float, dy: float, damage: int,
                 proj_type: str = "banana", orbit_radius: float = 55,
                 orbit_speed: float = 0.06):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = 7.0
        self.damage = damage
        self.alive = True
        self.spawn_time = pygame.time.get_ticks()
        self.size = 7
        self.angle = math.atan2(dy, dx)
        self.proj_type = proj_type  # "banana" or "blade"

        # Orbit params
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.orbit_angle = math.atan2(dy, dx)
        self.phase = "launch"  # "launch" -> "return" -> "orbit"
        self.launch_dist = 0.0

        # Hit tracking — cooldown per enemy so orbiting hits repeatedly
        self._hit_cooldowns: dict[int, int] = {}
        self.hit_cooldown_ms = 500

    def update(self, now: int, player_x: float, player_y: float):
        if not self.alive:
            return
        if self.phase == "launch":
            self.x += self.dx * self.speed
            self.y += self.dy * self.speed
            self.launch_dist += self.speed
            self.speed *= 0.96
            if self.launch_dist > 140 or now - self.spawn_time > 350:
                self.phase = "return"
        elif self.phase == "return":
            target_x = player_x + math.cos(self.orbit_angle) * self.orbit_radius
            target_y = player_y + math.sin(self.orbit_angle) * self.orbit_radius
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)
            if dist < 8:
                self.phase = "orbit"
            else:
                spd = min(12, dist * 0.18)
                self.x += (dx / dist) * spd
                self.y += (dy / dist) * spd
        elif self.phase == "orbit":
            self.orbit_angle += self.orbit_speed
            self.x = player_x + math.cos(self.orbit_angle) * self.orbit_radius
            self.y = player_y + math.sin(self.orbit_angle) * self.orbit_radius
        self.angle += 0.3

    def can_hit(self, enemy_id: int, now: int) -> bool:
        last = self._hit_cooldowns.get(enemy_id, 0)
        return now - last >= self.hit_cooldown_ms

    def register_hit(self, enemy_id: int, now: int):
        self._hit_cooldowns[enemy_id] = now

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        if not self.alive:
            return
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        if self.proj_type == "banana":
            self._draw_banana(surface, sx, sy)
        else:
            self._draw_blade(surface, sx, sy)

    def _draw_banana(self, surface, sx, sy):
        r = 10
        rect = pygame.Rect(sx - r, sy - r, r * 2, r * 2)
        start_a = self.angle
        pygame.draw.arc(surface, (255, 230, 0), rect, start_a, start_a + 2.8, 5)
        tip1_x = sx + int(math.cos(start_a) * r)
        tip1_y = sy - int(math.sin(start_a) * r)
        tip2_x = sx + int(math.cos(start_a + 2.8) * r)
        tip2_y = sy - int(math.sin(start_a + 2.8) * r)
        pygame.draw.circle(surface, (139, 100, 20), (tip1_x, tip1_y), 2)
        pygame.draw.circle(surface, (139, 100, 20), (tip2_x, tip2_y), 2)
        pygame.draw.circle(surface, (255, 255, 150), (sx, sy), 2)

    def _draw_blade(self, surface, sx, sy):
        blade_len = 12
        for i in range(3):
            a = self.angle + (math.tau / 3) * i
            bx = sx + int(math.cos(a) * blade_len)
            by = sy + int(math.sin(a) * blade_len)
            pygame.draw.line(surface, (180, 220, 255), (sx, sy), (bx, by), 3)
            pygame.draw.circle(surface, (220, 240, 255), (bx, by), 2)
        # Center glow
        glow = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(glow, (150, 200, 255, 120), (4, 4), 4)
        surface.blit(glow, (sx - 4, sy - 4))


# ---- Confetti grenade ----

class ConfettiGrenade:
    """A thrown grenade that explodes into confetti on impact or timeout."""

    CONFETTI_COLORS = [
        (255, 100, 200), (100, 255, 100), (255, 255, 0),
        (100, 200, 255), (255, 150, 50), (200, 100, 255),
    ]

    def __init__(self, x: float, y: float, dx: float, dy: float, damage: int):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = 5.5
        self.damage = damage
        self.alive = True
        self.exploded = False
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 600
        self.size = 5
        self.splash_radius = 60  # explosion hits enemies in this radius
        self.angle = math.atan2(dy, dx)

    def update(self, now: int):
        if not self.alive:
            return
        elapsed = now - self.spawn_time
        # Arc upward then down
        t = elapsed / self.lifetime
        arc = -math.sin(t * math.pi) * 2  # slight vertical arc
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed + arc
        self.speed *= 0.985  # decelerate
        self.angle += 0.15
        if elapsed > self.lifetime:
            self.exploded = True
            self.alive = False

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        if not self.alive:
            return
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        # Round grenade body
        pygame.draw.circle(surface, (80, 80, 80), (sx, sy), 6)
        pygame.draw.circle(surface, (255, 100, 200), (sx, sy), 6, 2)
        # Confetti pattern
        for i in range(3):
            a = self.angle + i * 2.1
            cx = sx + int(math.cos(a) * 3)
            cy = sy + int(math.sin(a) * 3)
            pygame.draw.circle(surface, self.CONFETTI_COLORS[i], (cx, cy), 1)
        # Fuse spark
        spark_x = sx + int(math.cos(self.angle) * 8)
        spark_y = sy + int(math.sin(self.angle) * 8) - 3
        ss = pygame.Surface((4, 4), pygame.SRCALPHA)
        pygame.draw.circle(ss, (255, 255, 100, 200), (2, 2), 2)
        surface.blit(ss, (spark_x - 2, spark_y - 2))


import random as _rng


class PlayerProjectileSystem:
    """Manages player-thrown projectiles (daggers, orbiters, grenades)."""

    MAX_ORBITERS = 3

    def __init__(self):
        self.daggers: list[ThrownDagger] = []
        self.orbiters: list[OrbitingProjectile] = []
        self.grenades: list[ConfettiGrenade] = []

    def spawn_daggers(self, x: float, y: float, facing_x: float, facing_y: float,
                      damage: int, count: int = 1, speed: float = 7.0,
                      lifetime: int = 800, visual: str = "dagger",
                      piercing: bool = False):
        """Spawn projectiles at a spread. count/speed/lifetime from weapon."""
        base_angle = math.atan2(facing_y, facing_x)
        if count == 1:
            offsets = [0.0]
        elif count == 2:
            offsets = [-0.15, 0.15]
        else:
            spread = 0.4  # total spread in radians
            offsets = [spread * (i / (count - 1) - 0.5) for i in range(count)]
        for offset in offsets:
            a = base_angle + offset
            dx = math.cos(a)
            dy = math.sin(a)
            d = ThrownDagger(x, y, dx, dy, damage, visual=visual, piercing=piercing)
            d.speed = speed
            d.lifetime = lifetime
            self.daggers.append(d)

    def spawn_orbiter(self, x: float, y: float, facing_x: float, facing_y: float,
                      damage: int, proj_type: str = "banana"):
        """Spawn a single orbiting projectile. Drops oldest if at max."""
        if len(self.orbiters) >= self.MAX_ORBITERS:
            # Drop oldest
            self.orbiters.pop(0)
        # Evenly redistribute orbit angles for existing orbiters
        base_angle = math.atan2(facing_y, facing_x)
        dx = math.cos(base_angle)
        dy = math.sin(base_angle)
        orb = OrbitingProjectile(x, y, dx, dy, damage, proj_type=proj_type)
        self.orbiters.append(orb)
        # Redistribute orbit angles so they space evenly
        n = len(self.orbiters)
        for i, o in enumerate(self.orbiters):
            if o.phase == "orbit":
                o.orbit_angle = (math.tau / n) * i

    def spawn_grenades(self, x: float, y: float, facing_x: float, facing_y: float,
                       damage: int, count: int = 1, speed: float = 5.5,
                       lifetime: int = 600, splash_radius: int = 60):
        """Spawn confetti grenades."""
        base_angle = math.atan2(facing_y, facing_x)
        for i in range(count):
            offset = (i - (count - 1) / 2) * 0.2
            a = base_angle + offset
            dx = math.cos(a)
            dy = math.sin(a)
            g = ConfettiGrenade(x, y, dx, dy, damage)
            g.speed = speed
            g.lifetime = lifetime
            g.splash_radius = splash_radius
            self.grenades.append(g)

    def update(self, now: int, enemies: list, world_w: int, world_h: int,
               player_x: float = 0, player_y: float = 0):
        """Move projectiles, check hits. Returns (hits, grenade_explosions)."""
        hits = []
        grenade_explosions = []

        # Standard daggers
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
                eid = id(enemy)
                if d.piercing and eid in d._hit_enemies:
                    continue
                if d_rect.colliderect(enemy.rect):
                    kb_x = enemy.x - d.x
                    kb_y = enemy.y - d.y
                    enemy.take_damage(d.damage, kb_x, kb_y, now)
                    hits.append((enemy, d.damage))
                    if d.piercing:
                        d._hit_enemies.add(eid)
                    else:
                        d.alive = False
                        break
        self.daggers = [d for d in self.daggers if d.alive]

        # Orbiting projectiles — hit with cooldown per enemy
        for orb in self.orbiters:
            orb.update(now, player_x, player_y)
            orb_rect = pygame.Rect(orb.x - orb.size, orb.y - orb.size,
                                   orb.size * 2, orb.size * 2)
            for enemy in enemies:
                if not enemy.alive:
                    continue
                eid = id(enemy)
                if not orb.can_hit(eid, now):
                    continue
                if orb_rect.colliderect(enemy.rect):
                    kb_x = enemy.x - orb.x
                    kb_y = enemy.y - orb.y
                    enemy.take_damage(orb.damage, kb_x, kb_y, now)
                    hits.append((enemy, orb.damage))
                    orb.register_hit(eid, now)
        self.orbiters = [o for o in self.orbiters if o.alive]

        # Grenades — explode on enemy contact or timeout
        for g in self.grenades:
            g.update(now)
            if g.x < 0 or g.x > world_w or g.y < 0 or g.y > world_h:
                g.alive = False
                g.exploded = True
            if not g.alive:
                if g.exploded:
                    grenade_explosions.append((g.x, g.y, g.damage, g.splash_radius))
                continue
            g_rect = pygame.Rect(g.x - g.size, g.y - g.size, g.size * 2, g.size * 2)
            for enemy in enemies:
                if not enemy.alive:
                    continue
                if g_rect.colliderect(enemy.rect):
                    g.exploded = True
                    g.alive = False
                    grenade_explosions.append((g.x, g.y, g.damage, g.splash_radius))
                    break
        self.grenades = [g for g in self.grenades if g.alive]

        # Process grenade splash damage
        for gx, gy, gdmg, splash_r in grenade_explosions:
            for enemy in enemies:
                if not enemy.alive:
                    continue
                dist = math.hypot(enemy.x - gx, enemy.y - gy)
                if dist < splash_r:
                    falloff = max(0.3, 1.0 - dist / splash_r)
                    splash_dmg = int(gdmg * falloff)
                    kb_x = enemy.x - gx
                    kb_y = enemy.y - gy
                    enemy.take_damage(splash_dmg, kb_x, kb_y, now)
                    hits.append((enemy, splash_dmg))

        return hits, grenade_explosions

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        for d in self.daggers:
            d.draw(surface, camera_x, camera_y)
        for orb in self.orbiters:
            orb.draw(surface, camera_x, camera_y)
        for g in self.grenades:
            g.draw(surface, camera_x, camera_y)
