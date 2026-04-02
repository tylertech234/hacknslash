import pygame
import math


# ---- Weapon definitions ----
WEAPONS = {
    "sword": {
        "name": "Sword",
        "damage_mult": 1.0,
        "range": 60,
        "cooldown": 400,
        "duration": 200,
        "sweep_deg": 120,
        "blade_color": (200, 200, 210),
        "trail_color": (255, 255, 150),
        "desc": "Balanced blade. Reliable swing.",
    },
    "axe": {
        "name": "Battle Axe",
        "damage_mult": 1.6,
        "range": 50,
        "cooldown": 650,
        "duration": 300,
        "sweep_deg": 90,
        "blade_color": (160, 160, 170),
        "trail_color": (255, 180, 80),
        "desc": "Heavy hits, slower swing.",
    },
    "dagger": {
        "name": "Throwing Daggers",
        "damage_mult": 0.7,
        "range": 40,
        "cooldown": 300,
        "duration": 120,
        "sweep_deg": 60,
        "blade_color": (180, 220, 220),
        "trail_color": (150, 255, 200),
        "desc": "Throw twin daggers at enemies.",
        "projectile": True,
    },
    "spear": {
        "name": "Spear",
        "damage_mult": 1.1,
        "range": 90,
        "cooldown": 500,
        "duration": 250,
        "sweep_deg": 40,
        "blade_color": (190, 170, 140),
        "trail_color": (200, 200, 150),
        "desc": "Long thrust, narrow arc.",
    },
    "hammer": {
        "name": "War Hammer",
        "damage_mult": 2.2,
        "range": 55,
        "cooldown": 900,
        "duration": 400,
        "sweep_deg": 160,
        "blade_color": (140, 130, 130),
        "trail_color": (255, 120, 60),
        "desc": "Devastating slam, very slow.",
    },
}

DEFAULT_WEAPON = "sword"


def get_weapon(name: str) -> dict:
    return WEAPONS.get(name, WEAPONS[DEFAULT_WEAPON])


def draw_weapon(surface: pygame.Surface, sx: int, sy: int,
                facing_x: float, facing_y: float,
                is_attacking: bool, attack_timer: int,
                weapon: dict, attack_range: int):
    """Draw the weapon attached to the player."""
    now = pygame.time.get_ticks()
    sword_angle = math.atan2(facing_y, facing_x)
    blade_color = weapon["blade_color"]
    trail_color = weapon["trail_color"]
    sweep = math.radians(weapon["sweep_deg"])
    duration = weapon["duration"]
    wname = weapon["name"]

    if is_attacking:
        progress = min(1.0, (now - attack_timer) / duration)
        swing_angle = sword_angle - sweep / 2 + sweep * progress
        blade_len = attack_range + 10

        if "Hammer" in wname:
            _draw_hammer_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, sword_angle, sweep)
        elif "Axe" in wname:
            _draw_axe_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, sword_angle, sweep)
        elif "Dagger" in wname:
            _draw_dagger_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, sword_angle, sweep)
        elif "Spear" in wname:
            _draw_spear_thrust(surface, sx, sy, sword_angle, blade_len, blade_color, trail_color, progress)
        else:
            _draw_sword_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, sword_angle, sweep)
    else:
        blade_len = attack_range - 10
        idle_angle = sword_angle + 0.3

        if "Hammer" in wname:
            _draw_hammer_idle(surface, sx, sy, idle_angle, blade_len, blade_color)
        elif "Axe" in wname:
            _draw_axe_idle(surface, sx, sy, idle_angle, blade_len, blade_color)
        elif "Dagger" in wname:
            _draw_dagger_idle(surface, sx, sy, sword_angle, blade_len, blade_color)
        elif "Spear" in wname:
            _draw_spear_idle(surface, sx, sy, idle_angle, blade_len, blade_color)
        else:
            _draw_sword_idle(surface, sx, sy, idle_angle, blade_len, blade_color)


# ---- Sword ----
def _draw_sword_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, base_angle, sweep):
    bx = sx + int(math.cos(swing_angle) * blade_len)
    by = sy + int(math.sin(swing_angle) * blade_len)
    pygame.draw.line(surface, blade_color, (sx, sy), (bx, by), 4)
    pygame.draw.line(surface, (255, 255, 255), (sx, sy), (bx, by), 2)
    pygame.draw.circle(surface, (255, 255, 200), (bx, by), 4)
    for i in range(5):
        t = max(0, progress - i * 0.06)
        ta = base_angle - sweep / 2 + sweep * min(1.0, t)
        tr = blade_len - i * 3
        tx = sx + int(math.cos(ta) * tr)
        ty = sy + int(math.sin(ta) * tr)
        alpha = max(20, 160 - i * 35)
        ts = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(ts, (*trail_color, alpha), (3, 3), 3)
        surface.blit(ts, (tx - 3, ty - 3))


def _draw_sword_idle(surface, sx, sy, idle_angle, blade_len, blade_color):
    bx = sx + int(math.cos(idle_angle) * blade_len)
    by = sy + int(math.sin(idle_angle) * blade_len)
    hx = sx + int(math.cos(idle_angle) * 8)
    hy = sy + int(math.sin(idle_angle) * 8)
    pygame.draw.line(surface, (139, 90, 43), (sx, sy), (hx, hy), 5)
    pygame.draw.line(surface, blade_color, (hx, hy), (bx, by), 3)
    perp = idle_angle + math.pi / 2
    g1x = hx + int(math.cos(perp) * 6)
    g1y = hy + int(math.sin(perp) * 6)
    g2x = hx - int(math.cos(perp) * 6)
    g2y = hy - int(math.sin(perp) * 6)
    pygame.draw.line(surface, (160, 140, 60), (g1x, g1y), (g2x, g2y), 3)


# ---- Axe ----
def _draw_axe_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, base_angle, sweep):
    bx = sx + int(math.cos(swing_angle) * blade_len)
    by = sy + int(math.sin(swing_angle) * blade_len)
    # Shaft
    pygame.draw.line(surface, (120, 80, 40), (sx, sy), (bx, by), 4)
    # Axe head
    perp = swing_angle + math.pi / 2
    h1x = bx + int(math.cos(perp) * 10)
    h1y = by + int(math.sin(perp) * 10)
    h2x = bx - int(math.cos(perp) * 4)
    h2y = by - int(math.sin(perp) * 4)
    h3x = bx + int(math.cos(swing_angle) * 6)
    h3y = by + int(math.sin(swing_angle) * 6)
    pygame.draw.polygon(surface, blade_color, [(bx, by), (h1x, h1y), (h3x, h3y)])
    pygame.draw.polygon(surface, blade_color, [(bx, by), (h2x, h2y), (h3x, h3y)])
    # Trail
    for i in range(4):
        t = max(0, progress - i * 0.08)
        ta = base_angle - sweep / 2 + sweep * min(1.0, t)
        tr = blade_len - i * 4
        tx = sx + int(math.cos(ta) * tr)
        ty = sy + int(math.sin(ta) * tr)
        alpha = max(20, 180 - i * 45)
        ts = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(ts, (*trail_color, alpha), (4, 4), 4)
        surface.blit(ts, (tx - 4, ty - 4))


def _draw_axe_idle(surface, sx, sy, idle_angle, blade_len, blade_color):
    bx = sx + int(math.cos(idle_angle) * blade_len)
    by = sy + int(math.sin(idle_angle) * blade_len)
    pygame.draw.line(surface, (120, 80, 40), (sx, sy), (bx, by), 4)
    perp = idle_angle + math.pi / 2
    h1x = bx + int(math.cos(perp) * 8)
    h1y = by + int(math.sin(perp) * 8)
    h3x = bx + int(math.cos(idle_angle) * 5)
    h3y = by + int(math.sin(idle_angle) * 5)
    pygame.draw.polygon(surface, blade_color, [(bx, by), (h1x, h1y), (h3x, h3y)])


# ---- Daggers ----
def _draw_dagger_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, base_angle, sweep):
    # Quick throwing motion — arms extend then release
    extend = 0.5 + 0.5 * progress
    for offset in (-0.2, 0.2):
        a = base_angle + offset
        reach = blade_len * 0.4 * extend
        bx = sx + int(math.cos(a) * reach)
        by = sy + int(math.sin(a) * reach)
        pygame.draw.line(surface, blade_color, (sx, sy), (bx, by), 2)
    # Release flash
    if progress > 0.5:
        fx = sx + int(math.cos(base_angle) * blade_len * 0.5)
        fy = sy + int(math.sin(base_angle) * blade_len * 0.5)
        alpha = int(255 * max(0, 1.0 - progress))
        ts = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(ts, (*trail_color, alpha), (4, 4), 4)
        surface.blit(ts, (fx - 4, fy - 4))


def _draw_dagger_idle(surface, sx, sy, angle, blade_len, blade_color):
    bl = blade_len * 0.6
    for offset in (-0.35, 0.35):
        a = angle + offset
        bx = sx + int(math.cos(a) * bl)
        by = sy + int(math.sin(a) * bl)
        pygame.draw.line(surface, blade_color, (sx, sy), (bx, by), 2)


# ---- Spear ----
def _draw_spear_thrust(surface, sx, sy, angle, blade_len, blade_color, trail_color, progress):
    # Thrust forward
    extend = blade_len * (0.5 + 0.5 * progress)
    bx = sx + int(math.cos(angle) * extend)
    by = sy + int(math.sin(angle) * extend)
    pygame.draw.line(surface, (120, 90, 50), (sx, sy), (bx, by), 3)
    # Spear tip
    tip_len = 10
    tx = bx + int(math.cos(angle) * tip_len)
    ty = by + int(math.sin(angle) * tip_len)
    perp = angle + math.pi / 2
    p1x = bx + int(math.cos(perp) * 4)
    p1y = by + int(math.sin(perp) * 4)
    p2x = bx - int(math.cos(perp) * 4)
    p2y = by - int(math.sin(perp) * 4)
    pygame.draw.polygon(surface, blade_color, [(tx, ty), (p1x, p1y), (p2x, p2y)])
    # Trail
    for i in range(3):
        t = max(0, progress - i * 0.12)
        tr = blade_len * (0.5 + 0.5 * t)
        ttx = sx + int(math.cos(angle) * tr)
        tty = sy + int(math.sin(angle) * tr)
        alpha = max(20, 120 - i * 40)
        ts = pygame.Surface((4, 4), pygame.SRCALPHA)
        pygame.draw.circle(ts, (*trail_color, alpha), (2, 2), 2)
        surface.blit(ts, (ttx - 2, tty - 2))


def _draw_spear_idle(surface, sx, sy, idle_angle, blade_len, blade_color):
    bx = sx + int(math.cos(idle_angle) * blade_len)
    by = sy + int(math.sin(idle_angle) * blade_len)
    pygame.draw.line(surface, (120, 90, 50), (sx, sy), (bx, by), 3)
    tip_len = 8
    tx = bx + int(math.cos(idle_angle) * tip_len)
    ty = by + int(math.sin(idle_angle) * tip_len)
    perp = idle_angle + math.pi / 2
    p1x = bx + int(math.cos(perp) * 3)
    p1y = by + int(math.sin(perp) * 3)
    p2x = bx - int(math.cos(perp) * 3)
    p2y = by - int(math.sin(perp) * 3)
    pygame.draw.polygon(surface, blade_color, [(tx, ty), (p1x, p1y), (p2x, p2y)])


# ---- Hammer ----
def _draw_hammer_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, base_angle, sweep):
    bx = sx + int(math.cos(swing_angle) * blade_len)
    by = sy + int(math.sin(swing_angle) * blade_len)
    pygame.draw.line(surface, (100, 70, 40), (sx, sy), (bx, by), 5)
    # Hammer head
    perp = swing_angle + math.pi / 2
    hw, hh = 14, 8
    pts = [
        (bx + int(math.cos(perp) * hw) + int(math.cos(swing_angle) * hh),
         by + int(math.sin(perp) * hw) + int(math.sin(swing_angle) * hh)),
        (bx - int(math.cos(perp) * hw) + int(math.cos(swing_angle) * hh),
         by - int(math.sin(perp) * hw) + int(math.sin(swing_angle) * hh)),
        (bx - int(math.cos(perp) * hw) - int(math.cos(swing_angle) * 3),
         by - int(math.sin(perp) * hw) - int(math.sin(swing_angle) * 3)),
        (bx + int(math.cos(perp) * hw) - int(math.cos(swing_angle) * 3),
         by + int(math.sin(perp) * hw) - int(math.sin(swing_angle) * 3)),
    ]
    pygame.draw.polygon(surface, blade_color, pts)
    pygame.draw.polygon(surface, (180, 170, 160), pts, 2)
    # Impact spark at end of swing
    if progress > 0.85:
        spark_size = int(8 * (progress - 0.85) / 0.15)
        pygame.draw.circle(surface, (255, 200, 50), (bx, by), spark_size)
    # Trail
    for i in range(3):
        t = max(0, progress - i * 0.1)
        ta = base_angle - sweep / 2 + sweep * min(1.0, t)
        tr = blade_len - i * 5
        tx = sx + int(math.cos(ta) * tr)
        ty = sy + int(math.sin(ta) * tr)
        alpha = max(20, 200 - i * 60)
        ts = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(ts, (*trail_color, alpha), (5, 5), 5)
        surface.blit(ts, (tx - 5, ty - 5))


def _draw_hammer_idle(surface, sx, sy, idle_angle, blade_len, blade_color):
    bx = sx + int(math.cos(idle_angle) * blade_len)
    by = sy + int(math.sin(idle_angle) * blade_len)
    pygame.draw.line(surface, (100, 70, 40), (sx, sy), (bx, by), 5)
    perp = idle_angle + math.pi / 2
    hw, hh = 10, 6
    pts = [
        (bx + int(math.cos(perp) * hw) + int(math.cos(idle_angle) * hh),
         by + int(math.sin(perp) * hw) + int(math.sin(idle_angle) * hh)),
        (bx - int(math.cos(perp) * hw) + int(math.cos(idle_angle) * hh),
         by - int(math.sin(perp) * hw) + int(math.sin(idle_angle) * hh)),
        (bx - int(math.cos(perp) * hw),
         by - int(math.sin(perp) * hw)),
        (bx + int(math.cos(perp) * hw),
         by + int(math.sin(perp) * hw)),
    ]
    pygame.draw.polygon(surface, blade_color, pts)
