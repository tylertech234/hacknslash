import pygame
import math
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    CAMPFIRE_LIGHT_RADIUS,
    PLAYER_LIGHT_RADIUS_MAX, PLAYER_LIGHT_RADIUS_MIN,
    LIGHT_SHRINK_RATE, LIGHT_RESTORE_RATE,
    DARKNESS_GROW_RATE, DARKNESS_DECAY_RATE, DARKNESS_MAX,
    TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
)


class LightingSystem:
    """Dynamic darkness overlay.

    - Darkness increases while the player is away from the campfire.
    - Player carries a personal light that shrinks over time away from camp.
    - Returning to the campfire restores light and reduces darkness.
    """

    def __init__(self):
        self.darkness = 0.0  # 0 = bright, 1 = max dark
        self.player_light_radius = float(PLAYER_LIGHT_RADIUS_MAX)

        # Campfire world position (center of map)
        self.campfire_x = (MAP_WIDTH * TILE_SIZE) // 2
        self.campfire_y = (MAP_HEIGHT * TILE_SIZE) // 2

        # Pre-build the overlay surface (reused each frame)
        self._overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # Cache small SRCALPHA circles keyed by radius → avoid per-frame allocs
        self._cut_cache: dict[int, pygame.Surface] = {}

    # ------------------------------------------------------------------

    def update(self, player_x: float, player_y: float):
        dist = math.hypot(player_x - self.campfire_x, player_y - self.campfire_y)
        near_campfire = dist < CAMPFIRE_LIGHT_RADIUS

        if near_campfire:
            # Restore light & reduce darkness
            self.player_light_radius = min(
                PLAYER_LIGHT_RADIUS_MAX,
                self.player_light_radius + LIGHT_RESTORE_RATE,
            )
            self.darkness = max(0.0, self.darkness - DARKNESS_DECAY_RATE)
        else:
            # Shrink light & grow darkness
            self.player_light_radius = max(
                PLAYER_LIGHT_RADIUS_MIN,
                self.player_light_radius - LIGHT_SHRINK_RATE,
            )
            self.darkness = min(DARKNESS_MAX, self.darkness + DARKNESS_GROW_RATE)

    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int,
             player_x: float, player_y: float,
             vp_w: int = 0, vp_h: int = 0):
        if self.darkness < 0.01:
            return  # nothing to draw

        sw = vp_w if vp_w > 0 else SCREEN_WIDTH
        sh = vp_h if vp_h > 0 else SCREEN_HEIGHT
        # Rebuild overlay when viewport size changes (e.g. first frame or resize)
        if self._overlay.get_size() != (sw, sh):
            self._overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)

        alpha = int(self.darkness * 255)
        self._overlay.fill((0, 0, 0, alpha))

        # Cut out player light (radial gradient → concentric transparent circles)
        px = int(player_x - camera_x)
        py = int(player_y - camera_y)
        r = int(self.player_light_radius)
        self._cut_light(self._overlay, px, py, r, alpha)

        # Cut out campfire light (always full radius when visible)
        cx = int(self.campfire_x - camera_x)
        cy = int(self.campfire_y - camera_y)
        self._cut_light(self._overlay, cx, cy, CAMPFIRE_LIGHT_RADIUS, alpha)

        surface.blit(self._overlay, (0, 0))

    # ------------------------------------------------------------------

    def _cut_light(self, overlay: pygame.Surface, cx: int, cy: int, radius: int, base_alpha: int):
        """Punch a soft radial hole in the overlay using BLEND_RGBA_MIN.

        pygame.draw.circle has no special_flags; we blit a cached filled
        circle surface with BLEND_RGBA_MIN instead, which sets each pixel's
        alpha to min(overlay_alpha, target), carving a smooth gradient hole.
        """
        steps = 5  # 5 steps is indistinguishable from 8 and ~37% fewer blits
        for i in range(steps, 0, -1):
            ratio = i / steps          # 1.0 … 0.2
            r = int(radius * ratio)
            if r < 4:
                continue
            # Quadratic falloff: edge stays at base_alpha, centre approaches 0
            target = int(base_alpha * ratio ** 2)
            s = self._cut_cache.get(r)
            if s is None:
                # Cap cache size to prevent unbounded growth / GC stutter
                if len(self._cut_cache) > 60:
                    self._cut_cache.clear()
                s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                self._cut_cache[r] = s
            s.fill((0, 0, 0, 255))
            pygame.draw.circle(s, (0, 0, 0, target), (r + 1, r + 1), r)
            overlay.blit(s, (cx - r - 1, cy - r - 1),
                         special_flags=pygame.BLEND_RGBA_MIN)
