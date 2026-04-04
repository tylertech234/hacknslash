"""Custom cyberpunk crosshair cursor — zone-aware, procedurally drawn."""

import pygame
import math

# Bright/dim color pairs per zone
_ZONE_COLORS: dict[str, tuple] = {
    "wasteland": ((255, 165, 50),   (100, 55, 10)),   # amber
    "city":      ((50, 230, 220),   (10, 80, 80)),    # cyan
    "abyss":     ((190, 80, 255),   (70, 20, 120)),   # violet
    "default":   ((220, 220, 230),  (70, 70, 85)),    # silver (menus)
}

_GAP     = 7   # pixels from center before lines start
_LEN     = 11  # length of each crosshair arm line
_DOT_R   = 2   # center dot radius
_RING_R  = 19  # base outer indicator ring radius
_ROT_SPD = 0.0007  # radians per ms — slow clockwise rotation


def draw_cursor(surface: pygame.Surface, mx: int, my: int,
                zone: str = "default", now: int = 0) -> None:
    """Draw the custom crosshair at screen position (mx, my).

    Call this last in the draw chain so it sits above all other elements.
    """
    bright, dim = _ZONE_COLORS.get(zone, _ZONE_COLORS["default"])

    # Slow rotation makes it feel alive
    rot = (now * _ROT_SPD) % (math.pi / 2)

    # Four arms at 0°, 90°, 180°, 270° + rotation offset
    for i in range(4):
        angle = rot + i * math.pi / 2
        ca, sa = math.cos(angle), math.sin(angle)
        ix = int(mx + ca * _GAP)
        iy = int(my + sa * _GAP)
        ox = int(mx + ca * (_GAP + _LEN))
        oy = int(my + sa * (_GAP + _LEN))
        # Thick bright outer line + thin dim shadow for legibility
        pygame.draw.line(surface, dim,    (ix + 1, iy + 1), (ox + 1, oy + 1), 2)
        pygame.draw.line(surface, bright, (ix, iy),         (ox, oy),         2)

    # Center dot
    pygame.draw.circle(surface, bright, (mx, my), _DOT_R)

    # Outer pulsing ring (slower pulse, subtle)
    pulse = int(_RING_R + 3 * math.sin(now * 0.003))
    pygame.draw.circle(surface, dim, (mx, my), pulse, 1)
