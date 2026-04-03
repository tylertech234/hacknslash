"""Atmospheric effects — zone-specific ambient particles and visual overlays."""

import pygame
import math
import random
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT


class AtmosphericSystem:
    """Renders zone-specific ambient particles and atmosphere overlays."""

    def __init__(self):
        self.particles: list[dict] = []
        self.zone = "wasteland"
        self.wave = 1
        self.particle_color = (160, 140, 100)
        self.particle_dir = (1.0, 0.3)
        self.ambient_color = (10, 15, 20)
        self._dust_storm_active = False
        self._dust_storm_timer = 0
        self._dust_storm_duration = 15000   # 15s
        self._dust_storm_cooldown = 45000   # 45s between storms
        self._last_storm_end = 0
        self._lightning_flash = 0
        self._lightning_next = 0
        # Screen glitch (abyss)
        self._glitch_timer = 0
        self._glitch_lines: list[tuple] = []

    def set_zone(self, zone_name: str, zone_data: dict):
        self.zone = zone_name
        self.particle_color = zone_data.get("particle_color", (160, 140, 100))
        self.particle_dir = zone_data.get("particle_dir", (1.0, 0.3))
        self.ambient_color = zone_data.get("ambient_color", (10, 15, 20))
        self.particles.clear()
        self._dust_storm_active = False

    def set_wave(self, wave: int):
        self.wave = wave

    def update(self, dt: float, now: int, camera_x: int, camera_y: int):
        """Update atmospheric particles."""
        # Spawn atmospheric particles based on wave intensity
        density = min(3, 1 + self.wave // 3)
        if len(self.particles) < density * 30:
            for _ in range(density):
                self._spawn_particle(camera_x, camera_y)

        # Update particles
        wind_x, wind_y = self.particle_dir
        speed_mult = 0.5 + self.wave * 0.05
        for p in self.particles:
            p["x"] += wind_x * speed_mult + p["vx"]
            p["y"] += wind_y * speed_mult + p["vy"]
            p["life"] -= dt
            # Add slight wobble
            p["x"] += math.sin(now * 0.002 + p["seed"]) * 0.3

        self.particles = [p for p in self.particles if p["life"] > 0]

        # Dust storm (wasteland, wave 5+)
        if self.zone == "wasteland" and self.wave >= 5:
            if not self._dust_storm_active:
                if now - self._last_storm_end >= self._dust_storm_cooldown:
                    self._dust_storm_active = True
                    self._dust_storm_timer = now
            elif now - self._dust_storm_timer >= self._dust_storm_duration:
                self._dust_storm_active = False
                self._last_storm_end = now

        # Distant lightning (wasteland, wave 6+)
        if self.zone == "wasteland" and self.wave >= 6:
            if now >= self._lightning_next:
                self._lightning_flash = now
                self._lightning_next = now + random.randint(8000, 20000)

        # Screen glitch (abyss)
        if self.zone == "abyss" and self.wave >= 2:
            if now >= self._glitch_timer:
                self._glitch_timer = now + random.randint(3000, 8000)
                # Generate random glitch lines
                self._glitch_lines = []
                for _ in range(random.randint(2, 5)):
                    y = random.randint(0, SCREEN_HEIGHT)
                    h = random.randint(1, 4)
                    offset = random.randint(-20, 20)
                    self._glitch_lines.append((y, h, offset))

    def _spawn_particle(self, cam_x: int, cam_y: int):
        dx, dy = self.particle_dir
        # Spawn from edge based on direction
        if abs(dx) > abs(dy):
            x = -10 if dx > 0 else SCREEN_WIDTH + 10
            y = random.randint(-20, SCREEN_HEIGHT + 20)
        else:
            x = random.randint(-20, SCREEN_WIDTH + 20)
            y = -10 if dy > 0 else SCREEN_HEIGHT + 10

        self.particles.append({
            "x": x, "y": y,
            "vx": random.uniform(-0.3, 0.3),
            "vy": random.uniform(-0.3, 0.3),
            "size": random.randint(1, 3),
            "life": random.randint(3000, 8000),
            "seed": random.random() * 100,
            "alpha": random.randint(40, 120),
        })

    def draw(self, surface: pygame.Surface, now: int):
        """Draw atmospheric effects on top of the game world."""
        # Ambient particles
        for p in self.particles:
            fade = min(1.0, p["life"] / 1000)
            alpha = int(p["alpha"] * fade)
            if alpha <= 0:
                continue
            ps = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*self.particle_color, alpha),
                             (p["size"], p["size"]), p["size"])
            surface.blit(ps, (int(p["x"]) - p["size"], int(p["y"]) - p["size"]))

        # Dust storm overlay (wasteland)
        if self._dust_storm_active:
            intensity = 0.3 + self.wave * 0.03
            alpha = int(min(120, 60 * intensity))
            storm = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            storm.fill((140, 120, 80, alpha))
            surface.blit(storm, (0, 0))
            # Extra dense particles during storm
            for _ in range(10):
                sx = random.randint(0, SCREEN_WIDTH)
                sy = random.randint(0, SCREEN_HEIGHT)
                sw = random.randint(10, 40)
                ps = pygame.Surface((sw, 2), pygame.SRCALPHA)
                ps.fill((180, 160, 120, 60))
                surface.blit(ps, (sx, sy))

        # Lightning flash (wasteland)
        if self._lightning_flash and now - self._lightning_flash < 150:
            elapsed = now - self._lightning_flash
            if elapsed < 50:
                flash_alpha = 30
            elif elapsed < 80:
                flash_alpha = 0
            else:
                flash_alpha = max(0, 20 - (elapsed - 80))
            if flash_alpha > 0:
                flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                flash.fill((200, 200, 255, flash_alpha))
                surface.blit(flash, (0, 0))

        # Fog layer (city)
        if self.zone == "city":
            fog_alpha = min(50, 15 + self.wave * 3)
            fog = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT // 3), pygame.SRCALPHA)
            fog.fill((40, 50, 40, fog_alpha))
            surface.blit(fog, (0, SCREEN_HEIGHT * 2 // 3))

        # Flickering neon (city, wave 2+)
        if self.zone == "city" and self.wave >= 2:
            if random.random() < 0.02:
                colors = [(255, 0, 100), (0, 255, 200), (255, 200, 0), (100, 0, 255)]
                c = random.choice(colors)
                x = random.choice([10, SCREEN_WIDTH - 30])
                y = random.randint(50, 300)
                ns = pygame.Surface((20, 8), pygame.SRCALPHA)
                ns.fill((*c, 40))
                surface.blit(ns, (x, y))

        # Screen glitch (abyss)
        if self.zone == "abyss" and self._glitch_lines:
            elapsed = now - (self._glitch_timer - random.randint(3000, 8000))
            if elapsed < 200:  # Glitch visible for 200ms
                for gy, gh, goffset in self._glitch_lines:
                    if 0 <= gy < SCREEN_HEIGHT:
                        # Horizontal line shift
                        strip = surface.subsurface((0, max(0, gy), SCREEN_WIDTH, min(gh, SCREEN_HEIGHT - gy))).copy()
                        surface.blit(strip, (goffset, gy))

        # Edge darkening (abyss) — progressively shrinks visible area
        if self.zone == "abyss":
            edge_size = min(80, 20 + self.wave * 5)
            edge = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for i in range(edge_size):
                alpha = int(120 * (1 - i / edge_size))
                # Top
                pygame.draw.line(edge, (10, 5, 20, alpha), (0, i), (SCREEN_WIDTH, i))
                # Bottom
                pygame.draw.line(edge, (10, 5, 20, alpha), (0, SCREEN_HEIGHT - 1 - i), (SCREEN_WIDTH, SCREEN_HEIGHT - 1 - i))
                # Left
                pygame.draw.line(edge, (10, 5, 20, alpha), (i, 0), (i, SCREEN_HEIGHT))
                # Right
                pygame.draw.line(edge, (10, 5, 20, alpha), (SCREEN_WIDTH - 1 - i, 0), (SCREEN_WIDTH - 1 - i, SCREEN_HEIGHT))
            surface.blit(edge, (0, 0))

        # Cosmic starfield background (abyss)
        if self.zone == "abyss":
            random.seed(42)  # deterministic stars
            for _ in range(60):
                star_x = random.randint(0, SCREEN_WIDTH)
                star_y = random.randint(0, SCREEN_HEIGHT)
                twinkle = 0.3 + 0.7 * abs(math.sin(now * 0.002 + star_x * 0.1 + star_y * 0.07))
                star_a = int(40 * twinkle)
                star_r = 1 if random.random() < 0.7 else 2
                ss = pygame.Surface((star_r * 2, star_r * 2), pygame.SRCALPHA)
                star_c = random.choice([(180, 140, 255), (140, 100, 220), (200, 180, 255)])
                pygame.draw.circle(ss, (*star_c, star_a), (star_r, star_r), star_r)
                surface.blit(ss, (star_x - star_r, star_y - star_r))
            random.seed()

        # Floating eldritch eyes (abyss, wave 3+)
        if self.zone == "abyss" and self.wave >= 3:
            random.seed(int(now // 5000))
            n_eyes = min(4, 1 + self.wave // 3)
            for _ in range(n_eyes):
                ex = random.randint(40, SCREEN_WIDTH - 40)
                ey = random.randint(40, SCREEN_HEIGHT - 40)
                # Slow fade in/out
                phase = (now % 5000) / 5000
                eye_a = int(35 * math.sin(phase * math.pi))
                if eye_a > 5:
                    es = pygame.Surface((20, 12), pygame.SRCALPHA)
                    # Outer eye
                    pygame.draw.ellipse(es, (120, 60, 180, eye_a), (0, 0, 20, 12))
                    # Pupil
                    px = 10 + int(math.sin(now * 0.001) * 3)
                    pygame.draw.circle(es, (200, 100, 255, min(255, eye_a + 20)), (px, 6), 3)
                    pygame.draw.circle(es, (0, 0, 0, min(255, eye_a + 10)), (px, 6), 1)
                    surface.blit(es, (ex - 10, ey - 6))
            random.seed()

        # Reality distortion waves (abyss, wave 5+)
        if self.zone == "abyss" and self.wave >= 5:
            wave_a = int(20 + 10 * math.sin(now * 0.001))
            for ring_i in range(2):
                ring_t = (now * 0.0005 + ring_i * 0.5) % 1.0
                ring_r = int(ring_t * 400)
                if ring_r > 10:
                    ring_a = int(wave_a * (1.0 - ring_t))
                    rs = pygame.Surface((ring_r * 2, ring_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(rs, (100, 40, 160, ring_a),
                                       (ring_r, ring_r), ring_r, 2)
                    surface.blit(rs, (SCREEN_WIDTH // 2 - ring_r,
                                      SCREEN_HEIGHT // 2 - ring_r))

        # Void upward particles (abyss) — glow particles floating up
        if self.zone == "abyss":
            for p in self.particles:
                if p["size"] >= 2:
                    glow_r = p["size"] + 2
                    fade = min(1.0, p["life"] / 1000)
                    alpha = int(30 * fade)
                    gs = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(gs, (140, 80, 220, alpha), (glow_r, glow_r), glow_r)
                    surface.blit(gs, (int(p["x"]) - glow_r, int(p["y"]) - glow_r))

    def get_dust_storm_active(self) -> bool:
        return self._dust_storm_active

    def get_visibility_modifier(self) -> float:
        """Returns a multiplier for player light radius (1.0 = normal, <1.0 = reduced)."""
        if self._dust_storm_active:
            return 0.6
        return 1.0
