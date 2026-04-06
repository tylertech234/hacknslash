"""Environmental hazards — zone-specific damage areas that escalate with waves."""

import pygame
import math
import random
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Hazard:
    """A single active hazard instance."""

    def __init__(self, hazard_type: str, x: float, y: float, duration: int, now: int):
        self.type = hazard_type
        self.x = x
        self.y = y
        self.duration = duration
        self.spawn_time = now
        self.alive = True
        self.warning = True  # Warning phase before damage
        self.warning_duration = 1500
        self.radius = 50
        self.damage_per_tick = 3
        self.tick_interval = 500  # ms between damage ticks
        self.last_tick = 0
        self.hits_enemies = False

        self._configure(hazard_type)

    def _configure(self, t: str):
        if t == "acid_puddle":
            self.radius = 40
            self.damage_per_tick = 3
            self.tick_interval = 500
            self.duration = 8000
            self.warning_duration = 800
            self.hits_enemies = True
        elif t == "solar_flare":
            self.radius = 60
            self.damage_per_tick = 20
            self.tick_interval = 0  # One-shot
            self.duration = 3000
            self.warning_duration = 2000
            self.hits_enemies = True
        elif t == "falling_debris":
            self.radius = 35
            self.damage_per_tick = 15
            self.tick_interval = 0
            self.duration = 2500
            self.warning_duration = 1500
            self.hits_enemies = True
        elif t == "toxic_gas":
            self.radius = 55
            self.damage_per_tick = 4
            self.tick_interval = 500
            self.duration = 6000
            self.warning_duration = 600
            self.hits_enemies = True
        elif t == "electrical_surge":
            self.radius = 30
            self.damage_per_tick = 25
            self.tick_interval = 0
            self.duration = 4000
            self.warning_duration = 1500
            self.hits_enemies = True
            # Surge has a second point (stored as extra attrs)
            self.x2 = self.x + random.randint(-200, 200)
            self.y2 = self.y + random.randint(-200, 200)
        elif t == "void_rift":
            self.radius = 70
            self.damage_per_tick = 5
            self.tick_interval = 500
            self.duration = 5000
            self.warning_duration = 1000
            self.hits_enemies = False
            self.pull_strength = 1.5
        elif t == "reality_fracture":
            self.radius = 80
            self.damage_per_tick = 8
            self.tick_interval = 400
            self.duration = 6000
            self.warning_duration = 1200
            self.hits_enemies = False
        elif t == "entropic_decay":
            # This is zone-wide, position doesn't matter
            self.radius = 9999
            self.damage_per_tick = 2
            self.tick_interval = 1000
            self.duration = 999999
            self.warning_duration = 0
            self.hits_enemies = False

    def get_age(self, now: int) -> int:
        return now - self.spawn_time

    def is_warning(self, now: int) -> bool:
        return self.get_age(now) < self.warning_duration

    def is_active(self, now: int) -> bool:
        age = self.get_age(now)
        return age >= self.warning_duration and age < self.duration

    def is_expired(self, now: int) -> bool:
        return self.get_age(now) >= self.duration


class HazardSystem:
    """Manages environmental hazards per zone."""

    def __init__(self):
        self.hazards: list[Hazard] = []
        self.zone = "wasteland"
        self.wave = 1
        self._hazard_config: dict = {}
        self._spawn_timers: dict[str, int] = {}
        self._entropic_decay_active = False
        # Cooldowns per hazard type (ms between spawns)
        self._cooldowns = {
            "acid_puddle": 6000,
            "solar_flare": 12000,
            "falling_debris": 5000,
            "toxic_gas": 8000,
            "electrical_surge": 10000,
            "void_rift": 8000,
            "reality_fracture": 10000,
            "entropic_decay": 999999,
        }

    def set_zone(self, zone_name: str, zone_data: dict):
        self.zone = zone_name
        self._hazard_config = zone_data.get("hazards", {})
        self.hazards.clear()
        self._spawn_timers.clear()
        self._entropic_decay_active = False

    def set_wave(self, wave: int):
        self.wave = wave

    def update(self, now: int, player_x: float, player_y: float,
               camera_x: int, camera_y: int,
               world_w: int, world_h: int) -> list[dict]:
        """Update hazards and return damage events: [{'target': 'player'|'enemy', 'x': f, 'y': f, 'damage': int, 'type': str, 'pull': (dx, dy)|None}]"""
        damage_events = []

        # Spawn new hazards based on wave thresholds
        for wave_threshold, hazard_type in self._hazard_config.items():
            if self.wave >= int(wave_threshold):
                cooldown = self._cooldowns.get(hazard_type, 10000)
                # Scale: more frequent at higher waves
                cooldown = max(3000, cooldown - (self.wave - int(wave_threshold)) * 500)
                last_spawn = self._spawn_timers.get(hazard_type, 0)

                if now - last_spawn >= cooldown:
                    self._spawn_hazard(hazard_type, now, player_x, player_y, world_w, world_h)
                    self._spawn_timers[hazard_type] = now

        # Update existing hazards
        for h in self.hazards:
            if h.is_expired(now):
                h.alive = False
                continue

            if h.is_active(now):
                # Check for damage tick
                if h.tick_interval == 0:
                    # One-shot damage at activation moment
                    if h.last_tick == 0:
                        h.last_tick = now
                        damage_events.append({
                            "x": h.x, "y": h.y,
                            "radius": h.radius,
                            "damage": h.damage_per_tick,
                            "type": h.type,
                            "hits_enemies": h.hits_enemies,
                            "pull": None,
                        })
                elif now - h.last_tick >= h.tick_interval:
                    h.last_tick = now
                    pull = None
                    if h.type == "void_rift":
                        # Calculate pull toward center
                        dx = h.x - player_x
                        dy = h.y - player_y
                        dist = math.hypot(dx, dy)
                        if dist < h.radius * 2 and dist > 1:
                            strength = getattr(h, "pull_strength", 1.5)
                            pull = (dx / dist * strength, dy / dist * strength)

                    damage_events.append({
                        "x": h.x, "y": h.y,
                        "radius": h.radius,
                        "damage": h.damage_per_tick,
                        "type": h.type,
                        "hits_enemies": h.hits_enemies,
                        "pull": pull,
                    })

        # Entropic decay (abyss wave 7+): zone-wide passive damage
        if (self.zone == "abyss" and self.wave >= 7
                and not self._entropic_decay_active):
            self._entropic_decay_active = True

        self.hazards = [h for h in self.hazards if h.alive]
        return damage_events

    def _spawn_hazard(self, hazard_type: str, now: int,
                      player_x: float, player_y: float,
                      world_w: int, world_h: int):
        """Spawn a hazard near the player (but not right on top)."""
        if hazard_type == "entropic_decay":
            if not self._entropic_decay_active:
                self._entropic_decay_active = True
            return

        # Spawn within 300px of player but at least 60px away
        for _ in range(10):
            angle = random.uniform(0, math.tau)
            dist = random.uniform(60, 300)
            x = player_x + math.cos(angle) * dist
            y = player_y + math.sin(angle) * dist
            x = max(50, min(world_w - 50, x))
            y = max(50, min(world_h - 50, y))
            break

        count = 1
        if hazard_type == "acid_puddle":
            count = min(3, 1 + (self.wave - 3) // 2)
        elif hazard_type == "solar_flare":
            count = min(3, 1 + (self.wave - 7) // 2)

        for i in range(count):
            hx = x + random.randint(-80, 80) * i
            hy = y + random.randint(-80, 80) * i
            self.hazards.append(Hazard(hazard_type, hx, hy, 0, now))

    def is_entropic_decay_active(self) -> bool:
        return self._entropic_decay_active

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int, now: int,
             vp_w: int = 0, vp_h: int = 0):
        """Draw hazard warnings and active effects."""
        sw = vp_w if vp_w > 0 else SCREEN_WIDTH
        sh = vp_h if vp_h > 0 else SCREEN_HEIGHT
        for h in self.hazards:
            sx = int(h.x - camera_x)
            sy = int(h.y - camera_y)

            # Skip off-screen
            if sx < -100 or sx > sw + 100 or sy < -100 or sy > sh + 100:
                continue

            if h.is_warning(now):
                self._draw_warning(surface, sx, sy, h, now)
            elif h.is_active(now):
                self._draw_active(surface, sx, sy, h, now)

    def _draw_warning(self, surface: pygame.Surface, sx: int, sy: int,
                      h: Hazard, now: int):
        """Draw hazard warning indicator."""
        age = h.get_age(now)
        progress = age / max(1, h.warning_duration)
        pulse = 0.5 + 0.5 * math.sin(now * 0.01)
        alpha = int(40 + 60 * progress * pulse)

        if h.type in ("acid_puddle", "toxic_gas"):
            color = (80, 200, 50, alpha)
        elif h.type == "solar_flare":
            color = (255, 200, 50, alpha)
        elif h.type in ("falling_debris",):
            color = (150, 150, 150, alpha)
        elif h.type == "electrical_surge":
            color = (100, 200, 255, alpha)
        elif h.type == "void_rift":
            color = (150, 50, 220, alpha)
        elif h.type == "reality_fracture":
            color = (180, 50, 180, alpha)
        else:
            color = (200, 200, 200, alpha)

        # Pulsing circle
        r = int(h.radius * (0.5 + 0.5 * progress))
        ws = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(ws, color, (r, r), r)
        pygame.draw.circle(ws, (*color[:3], min(255, alpha + 40)), (r, r), r, 2)
        surface.blit(ws, (sx - r, sy - r))

        # Exclamation mark
        if progress > 0.5:
            from src.font_cache import get_font
            warn = get_font("consolas", 16, True).render("!", True, color[:3])
            surface.blit(warn, (sx - warn.get_width() // 2, sy - warn.get_height() // 2))

    def _draw_active(self, surface: pygame.Surface, sx: int, sy: int,
                     h: Hazard, now: int):
        """Draw active hazard effect."""
        age = h.get_age(now)
        remaining = max(0, h.duration - age)
        fade = min(1.0, remaining / 1000)

        if h.type == "acid_puddle":
            # Green bubbling puddle
            r = h.radius
            ps = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(ps, (50, 180, 30, int(80 * fade)), (0, r // 2, r * 2, r))
            # Bubbles
            for i in range(4):
                bx = r + int(math.sin(now * 0.003 + i * 1.5) * r * 0.6)
                by = r - int(abs(math.sin(now * 0.005 + i)) * 8)
                pygame.draw.circle(ps, (80, 220, 50, int(100 * fade)), (bx, by), 3)
            surface.blit(ps, (sx - r, sy - r))

        elif h.type == "solar_flare":
            # Bright expanding ring
            progress = min(1.0, (age - h.warning_duration) / 500)
            r = int(h.radius * progress)
            if r > 0:
                fs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(fs, (255, 220, 80, int(120 * fade)), (r, r), r)
                pygame.draw.circle(fs, (255, 255, 200, int(180 * fade * (1 - progress))), (r, r), max(1, r // 2))
                surface.blit(fs, (sx - r, sy - r))

        elif h.type == "falling_debris":
            # Shadow on ground then impact
            progress = min(1.0, (age - h.warning_duration) / 300)
            if progress < 1.0:
                # Falling rock
                rock_y = sy - int(100 * (1 - progress))
                pygame.draw.rect(surface, (120, 110, 100),
                               (sx - 8, rock_y - 8, 16, 16))
            # Impact dust
            if progress >= 0.8:
                dust_r = int(h.radius * (progress - 0.8) / 0.2)
                ds = pygame.Surface((dust_r * 2, dust_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(ds, (160, 150, 130, int(60 * fade)), (dust_r, dust_r), dust_r)
                surface.blit(ds, (sx - dust_r, sy - dust_r))

        elif h.type == "toxic_gas":
            # Green cloud
            r = h.radius
            for i in range(3):
                offset_x = int(math.sin(now * 0.002 + i * 2) * 15)
                offset_y = int(math.cos(now * 0.003 + i) * 10)
                cr = r - i * 8
                if cr > 0:
                    gs = pygame.Surface((cr * 2, cr * 2), pygame.SRCALPHA)
                    pygame.draw.circle(gs, (60, 180, 40, int(40 * fade)),
                                     (cr, cr), cr)
                    surface.blit(gs, (sx + offset_x - cr, sy + offset_y - cr))

        elif h.type == "electrical_surge":
            # Lightning bolt between two points
            x2 = int(getattr(h, "x2", h.x + 100) - (h.x - sx + h.x))
            y2 = int(getattr(h, "y2", h.y + 100) - (h.y - sy + h.y))
            # Offset x2, y2 relative to camera same as sx, sy
            x2 = int(getattr(h, "x2", h.x) - (h.x - sx))
            y2 = int(getattr(h, "y2", h.y) - (h.y - sy))
            # Draw zigzag line
            points = [(sx, sy)]
            steps = 8
            for i in range(1, steps):
                t = i / steps
                mx = sx + int((x2 - sx) * t) + random.randint(-15, 15)
                my = sy + int((y2 - sy) * t) + random.randint(-15, 15)
                points.append((mx, my))
            points.append((x2, y2))
            if len(points) >= 2:
                pygame.draw.lines(surface, (100, 200, 255), False, points, 3)
                pygame.draw.lines(surface, (200, 230, 255), False, points, 1)

        elif h.type == "void_rift":
            # Swirling purple portal
            r = h.radius
            spin = now * 0.003
            vs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(vs, (80, 20, 140, int(60 * fade)), (r, r), r)
            # Spiral arms
            for arm in range(4):
                angle = spin + arm * math.pi / 2
                for j in range(10):
                    t = j / 10
                    ax = r + int(math.cos(angle + t * 3) * r * t)
                    ay = r + int(math.sin(angle + t * 3) * r * t)
                    pygame.draw.circle(vs, (140, 60, 220, int(80 * fade * (1 - t))),
                                     (ax, ay), 2)
            surface.blit(vs, (sx - r, sy - r))

        elif h.type == "reality_fracture":
            # Flickering rectangle of broken reality
            r = h.radius
            flicker = random.random()
            if flicker > 0.2:
                fs = pygame.Surface((r * 2, r), pygame.SRCALPHA)
                # Checkerboard transparency effect
                for bx in range(0, r * 2, 8):
                    for by in range(0, r, 8):
                        if (bx + by) // 8 % 2 == int(now * 0.005) % 2:
                            pygame.draw.rect(fs, (20, 0, 30, int(100 * fade)),
                                           (bx, by, 8, 8))
                surface.blit(fs, (sx - r, sy - r // 2))
                pygame.draw.rect(surface, (180, 50, 180, int(80 * fade)),
                               (sx - r, sy - r // 2, r * 2, r), 1)
