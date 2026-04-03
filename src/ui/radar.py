import pygame
import math
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Radar:
    """AVP-style motion tracker with sweep pulse and enemy blips."""

    def __init__(self):
        self.radius = 90
        self.x = SCREEN_WIDTH - self.radius - 25
        self.y = SCREEN_HEIGHT - self.radius - 25
        self.range = 1200  # world-pixel detection range (long range)
        self.sweep_speed = 0.0025  # radians per ms
        self.sweep_angle = 0.0
        self.blip_fade = 2000  # ms blips remain visible after sweep
        self.blips: list[dict] = []  # {"angle", "dist", "time"}

    def update(self, now: int, player_x: float, player_y: float, enemies: list,
               sounds=None):
        prev_angle = self.sweep_angle
        self.sweep_angle = (now * self.sweep_speed) % (math.tau)

        # Check which enemies the sweep line just passed over
        for enemy in enemies:
            if not enemy.alive:
                continue
            dx = enemy.x - player_x
            dy = enemy.y - player_y
            dist = math.hypot(dx, dy)
            if dist > self.range:
                continue
            # Angle from player to enemy
            angle = math.atan2(dy, dx) % math.tau
            # Did the sweep just cross this angle?
            if self._sweep_crossed(prev_angle, self.sweep_angle, angle):
                self.blips.append({
                    "angle": angle,
                    "dist": dist / self.range,
                    "time": now,
                })
                # Proximity beep
                if sounds:
                    sounds.play_radar_beep(dist / self.range)

        # Expire old blips
        self.blips = [b for b in self.blips if now - b["time"] < self.blip_fade]

    def _sweep_crossed(self, prev: float, curr: float, target: float) -> bool:
        if curr >= prev:
            return prev <= target <= curr
        else:
            # Wrapped around tau
            return target >= prev or target <= curr

    def draw(self, surface: pygame.Surface, player_facing_x: float, player_facing_y: float):
        now = pygame.time.get_ticks()
        cx, cy = self.x, self.y
        r = self.radius

        # Transparent background circle
        radar_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        rcx, rcy = r + 2, r + 2

        # Dark green background
        pygame.draw.circle(radar_surf, (0, 15, 0, 180), (rcx, rcy), r)

        # Range rings
        for ring in (0.33, 0.66, 1.0):
            pygame.draw.circle(radar_surf, (0, 50, 0, 120), (rcx, rcy), int(r * ring), 1)

        # Cross hairs
        pygame.draw.line(radar_surf, (0, 50, 0, 100), (rcx - r, rcy), (rcx + r, rcy), 1)
        pygame.draw.line(radar_surf, (0, 50, 0, 100), (rcx, rcy - r), (rcx, rcy + r), 1)

        # Sweep line
        sweep_ex = rcx + int(math.cos(self.sweep_angle) * r)
        sweep_ey = rcy + int(math.sin(self.sweep_angle) * r)
        pygame.draw.line(radar_surf, (0, 200, 0, 200), (rcx, rcy), (sweep_ex, sweep_ey), 2)

        # Sweep fade trail (wedge behind the sweep)
        for i in range(20):
            trail_angle = self.sweep_angle - i * 0.04
            alpha = max(0, 180 - i * 9)
            tx = rcx + int(math.cos(trail_angle) * r)
            ty = rcy + int(math.sin(trail_angle) * r)
            pygame.draw.line(radar_surf, (0, 160, 0, alpha), (rcx, rcy), (tx, ty), 1)

        # Enemy blips
        for blip in self.blips:
            age = now - blip["time"]
            alpha = max(0, 255 - int(255 * age / self.blip_fade))
            bx = rcx + int(math.cos(blip["angle"]) * blip["dist"] * r)
            by = rcy + int(math.sin(blip["angle"]) * blip["dist"] * r)
            # Bright blip
            size = 4 if age < 300 else 3
            pygame.draw.circle(radar_surf, (0, 255, 0, alpha), (bx, by), size)
            # Glow
            if age < 500:
                pygame.draw.circle(radar_surf, (0, 255, 0, alpha // 3), (bx, by), size + 3)

        # Center dot (player)
        pygame.draw.circle(radar_surf, (0, 255, 0, 255), (rcx, rcy), 3)

        # Outer ring
        pygame.draw.circle(radar_surf, (0, 120, 0, 200), (rcx, rcy), r, 2)

        surface.blit(radar_surf, (cx - r - 2, cy - r - 2))

        # Label
        from src.font_cache import get_font
        label = get_font("consolas", 11).render("MOTION TRACKER", True, (0, 140, 0))
        surface.blit(label, (cx - label.get_width() // 2, cy - r - 16))
