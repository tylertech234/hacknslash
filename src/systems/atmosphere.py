"""Atmospheric effects — zone-specific ambient particles and visual overlays.

Each zone has a distinct edge treatment:
  wasteland — dense forest fog rolls in from the trees at the screen border
  city       — ashy haze, neon reflections, fire-glow at rubble edges
  abyss      — parallax void/stars drift behind the island's cliff edges
"""

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
        self._dust_storm_duration = 15000
        self._dust_storm_cooldown = 45000
        self._last_storm_end = 0
        self._lightning_flash = 0
        self._lightning_next = 0
        # Screen glitch (abyss)
        self._glitch_timer = 0
        self._glitch_lines: list[tuple] = []
        # Abyss void drift — parallax stars separate from regular particles
        self._void_stars: list[dict] = []
        self._void_drift_x = 0.0   # accumulated parallax offset (wraps)
        self._void_drift_y = 0.0
        # Cached surfaces
        self._overlay_surf: pygame.Surface | None = None
        self._fog_surf: pygame.Surface | None = None
        self._edge_fog_surf: pygame.Surface | None = None
        self._edge_fog_size_cached: int = 0
        self._edge_surf: pygame.Surface | None = None
        self._edge_size_cached: int = 0
        self._fire_glow_surf: pygame.Surface | None = None
        self._fire_glow_w: int = 0
        self._fire_glow_h: int = 0
        self._abyss_void_surf: pygame.Surface | None = None
        self._abyss_void_w: int = 0
        self._abyss_void_h: int = 0
        # World/camera state for proximity-based boundary effects
        self._cam_x: int = 0
        self._cam_y: int = 0
        self._world_w: int = 0
        self._world_h: int = 0

    def set_zone(self, zone_name: str, zone_data: dict):
        self.zone = zone_name
        self.particle_color = zone_data.get("particle_color", (160, 140, 100))
        self.particle_dir = zone_data.get("particle_dir", (1.0, 0.3))
        self.ambient_color = zone_data.get("ambient_color", (10, 15, 20))
        self.particles.clear()
        self._void_stars.clear()
        self._dust_storm_active = False
        # Invalidate all cached surfaces when zone changes
        self._overlay_surf = None
        self._fog_surf = None
        self._edge_fog_surf = None
        self._edge_surf = None
        self._fire_glow_surf = None
        self._abyss_void_surf = None
        if zone_name == "abyss":
            self._init_void_stars()

    def _init_void_stars(self):
        """Seed the parallax void star field for the abyss."""
        rng = random.Random(99)
        self._void_stars = []
        for _ in range(200):
            self._void_stars.append({
                "x": rng.uniform(0, 1),    # normalised 0..1
                "y": rng.uniform(0, 1),
                "size": rng.choice([1, 1, 1, 2]),
                "color": rng.choice([(180, 150, 255), (200, 180, 255),
                                     (140, 110, 200), (220, 200, 255)]),
                "speed": rng.uniform(0.00008, 0.00025),  # parallax speed
                "twinkle_off": rng.uniform(0, math.tau),
            })

    def set_wave(self, wave: int):
        self.wave = wave

    def _boundary_factors(self, sw: int, sh: int, fade: float = 500.0):
        """Return (left, right, top, bottom) 0..1 proximity to world edge.
        1.0 = at boundary, 0.0 = more than `fade` world-pixels away."""
        cx, cy = self._cam_x, self._cam_y
        ww = self._world_w if self._world_w else sw * 100
        wh = self._world_h if self._world_h else sh * 100
        lf = max(0.0, 1.0 - cx / fade)
        rf = max(0.0, 1.0 - (ww - cx - sw) / fade)
        tf = max(0.0, 1.0 - cy / fade)
        bf = max(0.0, 1.0 - (wh - cy - sh) / fade)
        return lf, rf, tf, bf

    def _draw_boundary_strip(self, surface, sw, sh,
                              lf, rf, tf, bf,
                              depth, color, max_alpha, falloff=2.2):
        """Draw edge-gradient strips only on sides near the world boundary."""
        if not (lf or rf or tf or bf):
            return
        if tf or bf:
            hs = pygame.Surface((sw, depth), pygame.SRCALPHA)
            hs.fill((0, 0, 0, 0))
            for i in range(depth):
                a = int(max_alpha * (1.0 - i / depth) ** falloff)
                if a > 0:
                    hs.fill((*color, a), (0, i, sw, 1))
            if tf:
                ts = hs.copy()
                ts.set_alpha(int(255 * tf))
                surface.blit(ts, (0, 0))
            if bf:
                bot = pygame.transform.flip(hs, False, True)
                bot.set_alpha(int(255 * bf))
                surface.blit(bot, (0, sh - depth))
        if lf or rf:
            vd = min(sw // 3, depth)
            vs = pygame.Surface((vd, sh), pygame.SRCALPHA)
            vs.fill((0, 0, 0, 0))
            for i in range(vd):
                a = int(max_alpha * (1.0 - i / vd) ** falloff)
                if a > 0:
                    vs.fill((*color, a), (i, 0, 1, sh))
            if lf:
                ls = vs.copy()
                ls.set_alpha(int(255 * lf))
                surface.blit(ls, (0, 0))
            if rf:
                rv = pygame.transform.flip(vs, True, False)
                rv.set_alpha(int(255 * rf))
                surface.blit(rv, (sw - vd, 0))

    def update(self, dt: float, now: int, camera_x: int, camera_y: int,
               world_w: int = 0, world_h: int = 0):
        self._cam_x = camera_x
        self._cam_y = camera_y
        if world_w:
            self._world_w = world_w
        if world_h:
            self._world_h = world_h
        density = min(3, 1 + self.wave // 3)
        if len(self.particles) < density * 30:
            for _ in range(density):
                self._spawn_particle(camera_x, camera_y)

        wind_x, wind_y = self.particle_dir
        speed_mult = 0.5 + self.wave * 0.05
        for p in self.particles:
            p["x"] += wind_x * speed_mult + p["vx"]
            p["y"] += wind_y * speed_mult + p["vy"]
            p["life"] -= dt
            p["x"] += math.sin(now * 0.002 + p["seed"]) * 0.3
        self.particles = [p for p in self.particles if p["life"] > 0]

        # Wasteland dust storm
        if self.zone == "wasteland" and self.wave >= 5:
            if not self._dust_storm_active:
                if now - self._last_storm_end >= self._dust_storm_cooldown:
                    self._dust_storm_active = True
                    self._dust_storm_timer = now
            elif now - self._dust_storm_timer >= self._dust_storm_duration:
                self._dust_storm_active = False
                self._last_storm_end = now

        # Wasteland distant lightning
        if self.zone == "wasteland" and self.wave >= 6:
            if now >= self._lightning_next:
                self._lightning_flash = now
                self._lightning_next = now + random.randint(8000, 20000)

        # Abyss glitch lines
        if self.zone == "abyss" and self.wave >= 2:
            if now >= self._glitch_timer:
                self._glitch_timer = now + random.randint(3000, 8000)
                self._glitch_lines = []
                for _ in range(random.randint(2, 5)):
                    y = random.randint(0, SCREEN_HEIGHT)
                    h = random.randint(1, 4)
                    offset = random.randint(-20, 20)
                    self._glitch_lines.append((y, h, offset))

        # Abyss parallax void drift — the island appears to move through space
        if self.zone == "abyss":
            self._void_drift_x = (self._void_drift_x + 0.00012) % 1.0
            self._void_drift_y = (self._void_drift_y + 0.00005) % 1.0

    def _spawn_particle(self, cam_x: int, cam_y: int,
                        vp_w: int = 0, vp_h: int = 0):
        sw = vp_w if vp_w > 0 else SCREEN_WIDTH
        sh = vp_h if vp_h > 0 else SCREEN_HEIGHT
        dx, dy = self.particle_dir
        if abs(dx) > abs(dy):
            x = -10 if dx > 0 else sw + 10
            y = random.randint(-20, sh + 20)
        else:
            x = random.randint(-20, sw + 20)
            y = -10 if dy > 0 else sh + 10

        self.particles.append({
            "x": x, "y": y,
            "vx": random.uniform(-0.3, 0.3),
            "vy": random.uniform(-0.3, 0.3),
            "size": random.randint(1, 3),
            "life": random.randint(3000, 8000),
            "seed": random.random() * 100,
            "alpha": random.randint(40, 120),
        })

    # ─── draw ────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, now: int,
             vp_w: int = 0, vp_h: int = 0):
        sw = vp_w if vp_w > 0 else surface.get_width()
        sh = vp_h if vp_h > 0 else surface.get_height()

        # ── Ambient particles ────────────────────────────────────────────────
        for p in self.particles:
            fade = min(1.0, p["life"] / 1000)
            alpha = int(p["alpha"] * fade)
            if alpha <= 0:
                continue
            r = self.particle_color[0] * alpha // 255
            g = self.particle_color[1] * alpha // 255
            b = self.particle_color[2] * alpha // 255
            if r or g or b:
                pygame.draw.circle(surface, (r, g, b),
                                   (int(p["x"]), int(p["y"])), p["size"])

        # ── Zone-specific effects ────────────────────────────────────────────
        if self.zone == "wasteland":
            self._draw_wasteland(surface, now, sw, sh)
        elif self.zone == "city":
            self._draw_city(surface, now, sw, sh)
        elif self.zone == "abyss":
            self._draw_abyss(surface, now, sw, sh)

    # ─── WASTELAND atmosphere ────────────────────────────────────────────────

    def _draw_wasteland(self, surface, now, sw, sh):
        # Dust storm overlay
        if self._dust_storm_active:
            intensity = 0.3 + self.wave * 0.03
            alpha = int(min(120, 60 * intensity))
            if self._overlay_surf is None or self._overlay_surf.get_size() != (sw, sh):
                self._overlay_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            self._overlay_surf.fill((140, 120, 80, alpha))
            surface.blit(self._overlay_surf, (0, 0))
            for _ in range(10):
                sx_p = random.randint(0, sw)
                sy_p = random.randint(0, sh)
                pygame.draw.line(surface, (42, 37, 28),
                                 (sx_p, sy_p), (sx_p + random.randint(10, 40), sy_p), 2)

        # Lightning flash
        if self._lightning_flash and now - self._lightning_flash < 150:
            elapsed = now - self._lightning_flash
            flash_alpha = 30 if elapsed < 50 else (0 if elapsed < 80 else max(0, 20 - (elapsed - 80)))
            if flash_alpha > 0:
                if self._overlay_surf is None or self._overlay_surf.get_size() != (sw, sh):
                    self._overlay_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
                self._overlay_surf.fill((200, 200, 255, flash_alpha))
                surface.blit(self._overlay_surf, (0, 0))

        # ── Forest edge fog — only at actual world boundary ────────────────
        lf, rf, tf, bf = self._boundary_factors(sw, sh)
        fog_depth = min(sh // 3, 80 + self.wave * 6)
        self._draw_boundary_strip(surface, sw, sh, lf, rf, tf, bf,
                                   fog_depth, (180, 195, 170), 160)

    # ─── CITY atmosphere ─────────────────────────────────────────────────────

    def _draw_city(self, surface, now, sw, sh):
        # ── Ashy haze — a thin grey overlay that thickens with wave ─────────
        haze_alpha = min(40, 8 + self.wave * 3)
        if self._overlay_surf is None or self._overlay_surf.get_size() != (sw, sh):
            self._overlay_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self._overlay_surf.fill((50, 48, 45, haze_alpha))
        surface.blit(self._overlay_surf, (0, 0))

        # Falling ash/ember particles (draw larger on-screen dots)
        t = now * 0.001
        for p in self.particles:
            if p["size"] >= 2:
                fade = min(1.0, p["life"] / 1000)
                em_a = int(80 * fade)
                em_c = (200 * em_a // 255, 90 * em_a // 255, 30 * em_a // 255)
                if any(em_c):
                    pygame.draw.circle(surface, em_c, (int(p["x"]), int(p["y"])), 2)

        # ── Fire glow at rubble edge — only at actual world boundary ────────
        lf, rf, tf, bf = self._boundary_factors(sw, sh)
        if lf or rf or tf or bf:
            flicker = 0.80 + 0.20 * math.sin(t * 4.7 + 1.2)
            fire_depth = min(sh // 4, 50 + self.wave * 5)
            self._draw_boundary_strip(surface, sw, sh,
                                       lf * flicker, rf * flicker,
                                       tf * flicker, bf * flicker,
                                       fire_depth, (220, 80, 10), 90, falloff=2.0)

        # Flickering neon signs (sparse, near edges)
        if self.wave >= 2 and random.random() < 0.025:
            colors = [(255, 0, 100), (0, 255, 200), (255, 200, 0), (100, 0, 255)]
            c = random.choice(colors)
            x = random.choice([8, sw - 32])
            y = random.randint(50, sh - 100)
            pm_a = 50
            pm_c = (c[0] * pm_a // 255, c[1] * pm_a // 255, c[2] * pm_a // 255)
            pygame.draw.rect(surface, pm_c, (x, y, 24, 10))

    # ─── ABYSS atmosphere ────────────────────────────────────────────────────

    def _draw_abyss(self, surface, now, sw, sh):
        t = now * 0.001

        # ── Parallax void at screen edges — stars drift as if island moves ──
        # Only visible in the outer 30% of the screen in each direction
        void_band = int(sw * 0.28)

        if (self._abyss_void_surf is None
                or self._abyss_void_surf.get_size() != (sw, sh)
                or self._abyss_void_w != void_band):
            self._build_abyss_void_bg(sw, sh, void_band)
            self._abyss_void_w = void_band

        # Scroll the cached void background with parallax drift
        # Use fractional offset so it tiles seamlessly
        dx_px = int(self._void_drift_x * sw) % sw
        dy_px = int(self._void_drift_y * sh) % sh
        surface.blit(self._abyss_void_surf, (-dx_px, -dy_px))
        # Wrap-around tiles
        if dx_px > 0:
            surface.blit(self._abyss_void_surf, (sw - dx_px, -dy_px))
        if dy_px > 0:
            surface.blit(self._abyss_void_surf, (-dx_px, sh - dy_px))
        if dx_px > 0 and dy_px > 0:
            surface.blit(self._abyss_void_surf, (sw - dx_px, sh - dy_px))

        # Twinkling individual stars (drawn on top of void bg)
        rng = random.Random(42)
        for star in self._void_stars:
            sx2 = int((star["x"] + self._void_drift_x * star["speed"] * 600) % 1.0 * sw)
            sy2 = int((star["y"] + self._void_drift_y * star["speed"] * 600) % 1.0 * sh)
            twinkle = 0.3 + 0.7 * abs(math.sin(t * 2.0 + star["twinkle_off"]))
            # Only draw stars in the void band (near edges)
            in_band = (sx2 < void_band or sx2 > sw - void_band or
                       sy2 < void_band or sy2 > sh - void_band)
            if not in_band:
                continue
            star_a = int(55 * twinkle)
            sc = star["color"]
            pm = (sc[0] * star_a // 255, sc[1] * star_a // 255, sc[2] * star_a // 255)
            pygame.draw.circle(surface, pm, (sx2, sy2), star["size"])

        # ── Dark void vignette at edges — only at actual world boundary ─────
        lf2, rf2, tf2, bf2 = self._boundary_factors(sw, sh)
        edge_size = min(sh // 3, 60 + self.wave * 5)
        self._draw_boundary_strip(surface, sw, sh, lf2, rf2, tf2, bf2,
                                   edge_size, (8, 3, 18), 140, falloff=1.8)

        # Distant nebula pulses (visible through the void edge)
        nebula_a = int(12 + 8 * math.sin(t * 0.7))
        for ni, (nx_f, ny_f, nr, nc) in enumerate([
            (0.08, 0.15, 55, (80, 20, 140)),
            (0.92, 0.80, 45, (100, 30, 60)),
            (0.85, 0.12, 40, (40, 15, 100)),
            (0.10, 0.88, 50, (60, 10, 120)),
        ]):
            nx2 = int(nx_f * sw)
            ny2 = int(ny_f * sh)
            # Only draw if in void band
            if (nx2 < void_band or nx2 > sw - void_band or
                    ny2 < void_band or ny2 > sh - void_band):
                pulse = 0.5 + 0.5 * math.sin(t * 0.6 + ni * 1.5)
                a = int(nebula_a * pulse)
                pm_c = (nc[0] * a // 255, nc[1] * a // 255, nc[2] * a // 255)
                pygame.draw.circle(surface, pm_c, (nx2, ny2), nr)

        # Screen glitch lines (abyss)
        if self._glitch_lines:
            glitch_age = now - (self._glitch_timer - 3000)
            if 0 < glitch_age < 200:
                for gy, gh, goffset in self._glitch_lines:
                    if 0 <= gy < sh:
                        strip = surface.subsurface(
                            (0, max(0, gy), sw, min(gh, sh - gy))).copy()
                        surface.blit(strip, (goffset, gy))

        # Eldritch eyes (wave 3+)
        if self.wave >= 3:
            random.seed(int(now // 5000))
            n_eyes = min(4, 1 + self.wave // 3)
            for _ in range(n_eyes):
                ex = random.randint(40, sw - 40)
                ey = random.randint(40, sh - 40)
                # Only in void band
                if (ex > void_band and ex < sw - void_band and
                        ey > void_band and ey < sh - void_band):
                    continue
                phase = (now % 5000) / 5000
                eye_a = int(40 * math.sin(phase * math.pi))
                if eye_a > 5:
                    pm_outer = (120 * eye_a // 255, 60 * eye_a // 255, 180 * eye_a // 255)
                    pygame.draw.ellipse(surface, pm_outer, (ex - 10, ey - 6, 20, 12))
                    px2 = ex + int(math.sin(now * 0.001) * 3)
                    p_a = min(255, eye_a + 20)
                    pm_pupil = (200 * p_a // 255, 100 * p_a // 255, 255 * p_a // 255)
                    pygame.draw.circle(surface, pm_pupil, (px2, ey), 3)
                    pygame.draw.circle(surface, (0, 0, 0), (px2, ey), 1)
            random.seed()

        # Reality distortion rings (wave 5+)
        if self.wave >= 5:
            wave_a = int(20 + 10 * math.sin(t))
            for ring_i in range(2):
                ring_t = (now * 0.0005 + ring_i * 0.5) % 1.0
                ring_r = int(ring_t * min(sw, sh) * 0.55)
                if ring_r > 10:
                    ring_a = int(wave_a * (1.0 - ring_t))
                    pm_c = (100 * ring_a // 255, 40 * ring_a // 255, 160 * ring_a // 255)
                    pygame.draw.circle(surface, pm_c, (sw // 2, sh // 2), ring_r, 2)

        # Void particle glows
        for p in self.particles:
            if p["size"] >= 2:
                glow_r = p["size"] + 2
                fade = min(1.0, p["life"] / 1000)
                alpha = int(30 * fade)
                pm_c = (140 * alpha // 255, 80 * alpha // 255, 220 * alpha // 255)
                pygame.draw.circle(surface, pm_c, (int(p["x"]), int(p["y"])), glow_r)

    def _build_abyss_void_bg(self, sw: int, sh: int, void_band: int):
        """Pre-bake the static void background (only redrawn on viewport resize)."""
        surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        rng = random.Random(7)
        # Dense star field only in the void band region
        for _ in range(600):
            # Bias star positions toward edges
            edge_choice = rng.randint(0, 3)
            if edge_choice == 0:    # left band
                sx, sy = rng.randint(0, void_band), rng.randint(0, sh)
            elif edge_choice == 1:  # right band
                sx, sy = rng.randint(sw - void_band, sw), rng.randint(0, sh)
            elif edge_choice == 2:  # top band
                sx, sy = rng.randint(0, sw), rng.randint(0, void_band)
            else:                   # bottom band
                sx, sy = rng.randint(0, sw), rng.randint(sh - void_band, sh)
            star_c = rng.choice([(140, 120, 200), (160, 140, 220), (120, 100, 180)])
            brightness = rng.randint(25, 60)
            pm = (star_c[0] * brightness // 255,
                  star_c[1] * brightness // 255,
                  star_c[2] * brightness // 255,
                  brightness)
            pygame.draw.circle(surf, pm, (sx, sy), rng.choice([1, 1, 1, 2]))
        # Nebula smears
        for _ in range(8):
            nx, ny = rng.randint(0, sw), rng.randint(0, sh)
            if (nx > void_band and nx < sw - void_band and
                    ny > void_band and ny < sh - void_band):
                continue
            nc = rng.choice([(40, 10, 90, 30), (80, 20, 50, 25), (20, 8, 70, 20)])
            pygame.draw.ellipse(surf, nc, (nx - 20, ny - 10, 40, 20))
        self._abyss_void_surf = surf

    def get_dust_storm_active(self) -> bool:
        return self._dust_storm_active

    def get_visibility_modifier(self) -> float:
        if self._dust_storm_active:
            return 0.6
        return 1.0
