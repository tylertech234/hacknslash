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
        # Cached surfaces — allocated once, reused every frame
        self._overlay_surf: pygame.Surface | None = None  # SCREEN_WIDTH x SCREEN_HEIGHT
        self._fog_surf: pygame.Surface | None = None      # horizontal fog strip
        self._edge_surf: pygame.Surface | None = None     # abyss edge vignette
        self._edge_size_cached: int = 0

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
        # Ambient particles — premultiplied direct draw (no per-particle surface allocation)
        for p in self.particles:
            fade = min(1.0, p["life"] / 1000)
            alpha = int(p["alpha"] * fade)
            if alpha <= 0:
                continue
            r = self.particle_color[0] * alpha // 255
            g = self.particle_color[1] * alpha // 255
            b = self.particle_color[2] * alpha // 255
            if r or g or b:
                pygame.draw.circle(surface, (r, g, b), (int(p["x"]), int(p["y"])), p["size"])

        # Dust storm overlay (wasteland)
        if self._dust_storm_active:
            intensity = 0.3 + self.wave * 0.03
            alpha = int(min(120, 60 * intensity))
            if self._overlay_surf is None:
                self._overlay_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            self._overlay_surf.fill((140, 120, 80, alpha))
            surface.blit(self._overlay_surf, (0, 0))
            # Extra dense particles during storm — premultiplied lines (no per-line surface)
            for _ in range(10):
                sx_p = random.randint(0, SCREEN_WIDTH)
                sy_p = random.randint(0, SCREEN_HEIGHT)
                sw = random.randint(10, 40)
                pygame.draw.line(surface, (42, 37, 28), (sx_p, sy_p), (sx_p + sw, sy_p), 2)

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
                if self._overlay_surf is None:
                    self._overlay_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                self._overlay_surf.fill((200, 200, 255, flash_alpha))
                surface.blit(self._overlay_surf, (0, 0))

        # Fog layer (city) — cached surface, only refilled when alpha changes
        if self.zone == "city":
            fog_alpha = min(50, 15 + self.wave * 3)
            if self._fog_surf is None:
                self._fog_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT // 3), pygame.SRCALPHA)
            self._fog_surf.fill((40, 50, 40, fog_alpha))
            surface.blit(self._fog_surf, (0, SCREEN_HEIGHT * 2 // 3))

        # Flickering neon (city, wave 2+) — premultiplied rect (no SRCALPHA surface)
        if self.zone == "city" and self.wave >= 2:
            if random.random() < 0.02:
                colors = [(255, 0, 100), (0, 255, 200), (255, 200, 0), (100, 0, 255)]
                c = random.choice(colors)
                x = random.choice([10, SCREEN_WIDTH - 30])
                y = random.randint(50, 300)
                pm_c = (c[0] * 40 // 255, c[1] * 40 // 255, c[2] * 40 // 255)
                pygame.draw.rect(surface, pm_c, (x, y, 20, 8))

        # Screen glitch (abyss)
        if self.zone == "abyss" and self._glitch_lines:
            elapsed = now - (self._glitch_timer - random.randint(3000, 8000))
            if elapsed < 200:  # Glitch visible for 200ms
                for gy, gh, goffset in self._glitch_lines:
                    if 0 <= gy < SCREEN_HEIGHT:
                        # Horizontal line shift
                        strip = surface.subsurface((0, max(0, gy), SCREEN_WIDTH, min(gh, SCREEN_HEIGHT - gy))).copy()
                        surface.blit(strip, (goffset, gy))

        # Edge darkening (abyss) — cached surface, rebuilt only when edge_size changes
        if self.zone == "abyss":
            edge_size = min(80, 20 + self.wave * 5)
            if self._edge_surf is None or self._edge_size_cached != edge_size:
                self._edge_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                self._edge_surf.fill((0, 0, 0, 0))
                for i in range(edge_size):
                    alpha = int(120 * (1 - i / edge_size))
                    col = (10, 5, 20, alpha)
                    self._edge_surf.fill(col, (0, i, SCREEN_WIDTH, 1))
                    self._edge_surf.fill(col, (0, SCREEN_HEIGHT - 1 - i, SCREEN_WIDTH, 1))
                    self._edge_surf.fill(col, (i, 0, 1, SCREEN_HEIGHT))
                    self._edge_surf.fill(col, (SCREEN_WIDTH - 1 - i, 0, 1, SCREEN_HEIGHT))
                self._edge_size_cached = edge_size
            surface.blit(self._edge_surf, (0, 0))

        # Cosmic starfield background (abyss) — premultiplied circles (no per-star surface)
        if self.zone == "abyss":
            random.seed(42)  # deterministic stars
            for _ in range(60):
                star_x = random.randint(0, SCREEN_WIDTH)
                star_y = random.randint(0, SCREEN_HEIGHT)
                twinkle = 0.3 + 0.7 * abs(math.sin(now * 0.002 + star_x * 0.1 + star_y * 0.07))
                star_a = int(40 * twinkle)
                star_r = 1 if random.random() < 0.7 else 2
                star_c = random.choice([(180, 140, 255), (140, 100, 220), (200, 180, 255)])
                pm_c = (star_c[0] * star_a // 255, star_c[1] * star_a // 255, star_c[2] * star_a // 255)
                pygame.draw.circle(surface, pm_c, (star_x, star_y), star_r)
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
                    # Outer oval — premultiplied
                    pm_outer = (120 * eye_a // 255, 60 * eye_a // 255, 180 * eye_a // 255)
                    pygame.draw.ellipse(surface, pm_outer, (ex - 10, ey - 6, 20, 12))
                    # Pupil
                    px_p = ex + int(math.sin(now * 0.001) * 3)
                    p_a = min(255, eye_a + 20)
                    pm_pupil = (200 * p_a // 255, 100 * p_a // 255, 255 * p_a // 255)
                    pygame.draw.circle(surface, pm_pupil, (px_p, ey), 3)
                    pygame.draw.circle(surface, (0, 0, 0), (px_p, ey), 1)
            random.seed()

        # Reality distortion waves (abyss, wave 5+) — premultiplied circles
        if self.zone == "abyss" and self.wave >= 5:
            wave_a = int(20 + 10 * math.sin(now * 0.001))
            for ring_i in range(2):
                ring_t = (now * 0.0005 + ring_i * 0.5) % 1.0
                ring_r = int(ring_t * 400)
                if ring_r > 10:
                    ring_a = int(wave_a * (1.0 - ring_t))
                    pm_c = (100 * ring_a // 255, 40 * ring_a // 255, 160 * ring_a // 255)
                    pygame.draw.circle(surface, pm_c,
                                       (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), ring_r, 2)

        # Void upward particles (abyss) — premultiplied glow circles
        if self.zone == "abyss":
            for p in self.particles:
                if p["size"] >= 2:
                    glow_r = p["size"] + 2
                    fade = min(1.0, p["life"] / 1000)
                    alpha = int(30 * fade)
                    pm_c = (140 * alpha // 255, 80 * alpha // 255, 220 * alpha // 255)
                    pygame.draw.circle(surface, pm_c, (int(p["x"]), int(p["y"])), glow_r)

    def get_dust_storm_active(self) -> bool:
        return self._dust_storm_active

    def get_visibility_modifier(self) -> float:
        """Returns a multiplier for player light radius (1.0 = normal, <1.0 = reduced)."""
        if self._dust_storm_active:
            return 0.6
        return 1.0
