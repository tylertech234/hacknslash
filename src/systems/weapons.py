import pygame
import math


# ---- Weapon definitions ----

# === SHARED / CYBER KNIGHT (melee-focused) ===
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
        "class": "knight",
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
        "class": "knight",
    },
    "spear": {
        "name": "Spear",
        "damage_mult": 1.3,
        "range": 90,
        "cooldown": 500,
        "duration": 250,
        "sweep_deg": 40,
        "blade_color": (190, 170, 140),
        "trail_color": (200, 200, 150),
        "desc": "Long thrust, narrow arc.",
        "class": "knight",
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
        "class": "knight",
    },
    # Knight cyber upgrades
    "plasma_blade": {
        "name": "Plasma Blade",
        "damage_mult": 1.4,
        "range": 65,
        "cooldown": 350,
        "duration": 180,
        "sweep_deg": 130,
        "blade_color": (0, 200, 255),
        "trail_color": (100, 220, 255),
        "desc": "Superheated edge. Fast & deadly.",
        "class": "knight",
    },
    "gravity_maul": {
        "name": "Gravity Maul",
        "damage_mult": 3.5,
        "range": 60,
        "cooldown": 1000,
        "duration": 450,
        "sweep_deg": 180,
        "blade_color": (180, 50, 255),
        "trail_color": (200, 100, 255),
        "desc": "Warps space on impact. Massive.",
        "class": "knight",
    },
    "blade_barrier": {
        "name": "Blade Barrier",
        "damage_mult": 0.7,
        "range": 50,
        "cooldown": 400,
        "duration": 150,
        "sweep_deg": 60,
        "blade_color": (180, 220, 255),
        "trail_color": (150, 200, 255),
        "desc": "Orbiting blades. Throw up to 3!",
        "projectile": True,
        "orbiter": True,
        "orbiter_type": "blade",
        "class": "knight",
    },
    "shield_bash": {
        "name": "Shield Bash",
        "damage_mult": 0.9,
        "range": 40,
        "cooldown": 280,
        "duration": 140,
        "sweep_deg": 180,
        "blade_color": (150, 200, 255),
        "trail_color": (180, 220, 255),
        "desc": "Fast shield slam. Huge knockback.",
        "class": "knight",
    },

    # === CYBER ARCHER (ranged-focused) ===
    "dagger": {
        "name": "Throwing Dagger",
        "damage_mult": 1.4,
        "range": 40,
        "cooldown": 350,
        "duration": 120,
        "sweep_deg": 60,
        "blade_color": (180, 220, 220),
        "trail_color": (150, 255, 200),
        "desc": "Precision throw. Single deadly dagger.",
        "projectile": True,
        "proj_speed": 8.0,
        "proj_lifetime": 900,
        "proj_count": 1,
        "proj_visual": "dagger",
        "class": "archer",
    },
    "cyber_bow": {
        "name": "Cyber Bow",
        "damage_mult": 2.4,
        "range": 50,
        "cooldown": 550,
        "duration": 200,
        "sweep_deg": 30,
        "blade_color": (0, 255, 180),
        "trail_color": (100, 255, 200),
        "desc": "Piercing energy arrow. Passes through enemies.",
        "projectile": True,
        "proj_speed": 11.0,
        "proj_lifetime": 1500,
        "proj_count": 1,
        "proj_visual": "arrow",
        "piercing": True,
        "class": "archer",
    },
    "pulse_rifle": {
        "name": "Pulse Rifle",
        "damage_mult": 1.0,
        "range": 35,
        "cooldown": 220,
        "duration": 80,
        "sweep_deg": 15,
        "blade_color": (255, 100, 50),
        "trail_color": (255, 180, 80),
        "desc": "Rapid-fire energy bolts. Hold the line.",
        "projectile": True,
        "proj_speed": 10.0,
        "proj_lifetime": 700,
        "proj_count": 1,
        "proj_visual": "bolt",
        "class": "archer",
    },
    "scatter_shot": {
        "name": "Scatter Shot",
        "damage_mult": 0.9,
        "range": 30,
        "cooldown": 600,
        "duration": 100,
        "sweep_deg": 60,
        "blade_color": (255, 200, 0),
        "trail_color": (255, 255, 100),
        "desc": "5-bolt spread. Covers wide area.",
        "projectile": True,
        "proj_speed": 7.0,
        "proj_lifetime": 600,
        "proj_count": 5,
        "proj_visual": "pellet",
        "class": "archer",
    },
    "ricochet_disc": {
        "name": "Ricochet Disc",
        "damage_mult": 1.5,
        "range": 40,
        "cooldown": 500,
        "duration": 150,
        "sweep_deg": 30,
        "blade_color": (255, 180, 0),
        "trail_color": (255, 220, 80),
        "desc": "Bouncing energy disc. Hits walls & keeps going.",
        "projectile": True,
        "proj_speed": 9.0,
        "proj_lifetime": 2000,
        "proj_count": 1,
        "proj_visual": "disc",
        "bouncing": True,
        "class": "archer",
    },
    "explosive_crossbow": {
        "name": "Explosive Crossbow",
        "damage_mult": 2.2,
        "range": 45,
        "cooldown": 900,
        "duration": 220,
        "sweep_deg": 20,
        "blade_color": (255, 160, 40),
        "trail_color": (255, 220, 100),
        "desc": "Explosive-tipped bolt. Arcs and detonates on impact.",
        "projectile": True,
        "grenade": True,
        "proj_speed": 7.0,
        "proj_lifetime": 700,
        "proj_count": 1,
        "class": "archer",
    },
    "burst_crossbow": {
        "name": "Tri-Burst Crossbow",
        "damage_mult": 1.1,
        "range": 42,
        "cooldown": 480,
        "duration": 100,
        "sweep_deg": 30,
        "blade_color": (100, 220, 255),
        "trail_color": (180, 240, 255),
        "desc": "Fires 3 bolts per trigger pull in a tight burst.",
        "projectile": True,
        "proj_speed": 10.5,
        "proj_lifetime": 800,
        "proj_count": 3,
        "proj_visual": "arrow",
        "class": "archer",
    },

    # === CYBER JESTER (chaotic mix) ===
    "rubber_chicken": {
        "name": "Rubber Chicken",
        "damage_mult": 0.8,
        "range": 55,
        "cooldown": 350,
        "duration": 200,
        "sweep_deg": 140,
        "blade_color": (255, 220, 50),
        "trail_color": (255, 255, 100),
        "desc": "BAWK! Surprisingly effective.",
        "class": "jester",
    },
    "banana_rang": {
        "name": "Banana-Rang",
        "damage_mult": 0.9,
        "range": 45,
        "cooldown": 450,
        "duration": 150,
        "sweep_deg": 50,
        "blade_color": (255, 230, 0),
        "trail_color": (255, 255, 120),
        "desc": "Orbiting banana. Throw up to 3!",
        "projectile": True,
        "orbiter": True,
        "orbiter_type": "banana",
        "class": "jester",
    },
    "joy_buzzer": {
        "name": "Joy Buzzer",
        "damage_mult": 1.3,
        "range": 35,
        "cooldown": 500,
        "duration": 250,
        "sweep_deg": 360,
        "blade_color": (0, 255, 255),
        "trail_color": (150, 255, 255),
        "desc": "ZAP! Electric handshake of doom.",
        "class": "jester",
    },
    "pie_launcher": {
        "name": "Pie Launcher",
        "damage_mult": 2.2,
        "range": 40,
        "cooldown": 700,
        "duration": 200,
        "sweep_deg": 45,
        "blade_color": (255, 200, 150),
        "trail_color": (255, 255, 220),
        "desc": "Cream pies. Deals splash damage.",
        "projectile": True,
        "proj_speed": 5.0,
        "proj_lifetime": 800,
        "proj_count": 1,
        "class": "jester",
    },
    "confetti_grenade": {
        "name": "Confetti Grenade",
        "damage_mult": 2.8,
        "range": 40,
        "cooldown": 600,
        "duration": 180,
        "sweep_deg": 30,
        "blade_color": (255, 100, 200),
        "trail_color": (255, 200, 255),
        "desc": "Thrown explosive. SURPRISE! Confetti!",
        "projectile": True,
        "grenade": True,
        "proj_speed": 5.5,
        "proj_lifetime": 600,
        "proj_count": 1,
        "class": "jester",
    },
    "jack_in_box": {
        "name": "Jack-in-the-Box",
        "damage_mult": 0.8,
        "range": 45,
        "cooldown": 450,
        "duration": 160,
        "sweep_deg": 50,
        "blade_color": (255, 50, 100),
        "trail_color": (255, 100, 200),
        "desc": "Orbiting surprise boxes! Pop goes the weasel!",
        "projectile": True,
        "orbiter": True,
        "orbiter_type": "box",
        "class": "jester",
    },
}

# ── Character class definitions ──
CHARACTER_CLASSES = {
    "knight": {
        "name": "Knight",
        "desc": "Heavy armor. Each blow sends foes flying. Born to fight up close.",
        "color": (0, 180, 255),
        "start_weapon": "sword",
        "hp_bonus": 15,
        "damage_bonus": -2,
        "speed_bonus": 0,
        "knockback_bonus": 3.0,
        "passives": ["melee_lifesteal", "armor_plating"],
    },
    "archer": {
        "name": "Ranger",
        "desc": "Fast and deadly at range. Keep your distance.",
        "color": (0, 255, 150),
        "start_weapon": "dagger",
        "hp_bonus": -10,
        "damage_bonus": 0,
        "speed_bonus": 1.0,
        "passives": ["crit_shots", "evasion"],
    },
    "jester": {
        "name": "Jester",
        "desc": "Chaos incarnate. Funny weapons, unpredictable power.",
        "color": (255, 50, 255),
        "start_weapon": "rubber_chicken",
        "hp_bonus": 0,
        "damage_bonus": 0,
        "speed_bonus": 1.5,
        "passives": ["lucky_crits", "confetti_burst"],
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

    # Visual blade length is capped regardless of attack_range upgrades.
    # Extra range shows as an energy arc instead of a longer weapon.
    BASE_VISUAL_LEN = 42
    visual_len = min(attack_range, BASE_VISUAL_LEN)

    if is_attacking:
        progress = min(1.0, (now - attack_timer) / duration)
        swing_angle = sword_angle - sweep / 2 + sweep * progress
        blade_len = visual_len + 10

        # Strike-zone arc: drawn at actual attack_range if range > base
        if attack_range > BASE_VISUAL_LEN:
            _draw_strike_arc(surface, sx, sy, attack_range,
                             swing_angle, base_angle=sword_angle - sweep / 2,
                             sweep=sweep, progress=progress,
                             color=blade_color)

        if "Hammer" in wname or "Maul" in wname:
            _draw_hammer_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, sword_angle, sweep)
        elif "Axe" in wname:
            _draw_axe_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, sword_angle, sweep)
        elif "Grenade" in wname:
            _draw_grenade_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, sword_angle, sweep)
        elif "Dagger" in wname or "Bow" in wname or "Rifle" in wname or "Scatter" in wname or "Banana" in wname or "Pie" in wname or "Ricochet" in wname or "Jack" in wname:
            _draw_dagger_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, sword_angle, sweep)
        elif "Shield" in wname:
            _draw_shield_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, sword_angle, sweep)
        elif "Spear" in wname:
            _draw_spear_thrust(surface, sx, sy, sword_angle, blade_len, blade_color, trail_color, progress)
        elif "Chicken" in wname:
            _draw_chicken_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, sword_angle, sweep)
        elif "Buzzer" in wname:
            _draw_buzzer_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, sword_angle, sweep)
        else:
            _draw_sword_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, sword_angle, sweep)
    else:
        blade_len = visual_len - 10
        idle_angle = sword_angle + 0.3

        if "Hammer" in wname or "Maul" in wname:
            _draw_hammer_idle(surface, sx, sy, idle_angle, blade_len, blade_color)
        elif "Axe" in wname:
            _draw_axe_idle(surface, sx, sy, idle_angle, blade_len, blade_color)
        elif "Grenade" in wname:
            _draw_grenade_idle(surface, sx, sy, sword_angle, blade_len, blade_color)
        elif "Dagger" in wname or "Bow" in wname or "Rifle" in wname or "Scatter" in wname or "Banana" in wname or "Pie" in wname or "Ricochet" in wname or "Jack" in wname:
            _draw_dagger_idle(surface, sx, sy, sword_angle, blade_len, blade_color)
        elif "Shield" in wname:
            _draw_shield_idle(surface, sx, sy, idle_angle, blade_len, blade_color)
        elif "Spear" in wname:
            _draw_spear_idle(surface, sx, sy, idle_angle, blade_len, blade_color)
        elif "Chicken" in wname:
            _draw_chicken_idle(surface, sx, sy, idle_angle, blade_len, blade_color)
        elif "Buzzer" in wname:
            _draw_buzzer_idle(surface, sx, sy, idle_angle, blade_len, blade_color)
        else:
            _draw_sword_idle(surface, sx, sy, idle_angle, blade_len, blade_color)


def _draw_strike_arc(surface, sx, sy, attack_range, swing_angle, base_angle, sweep, progress, color):
    """Draw a translucent energy arc at attack_range showing the extended hit zone."""
    # Sweep so far: from start angle to current swing angle
    arc_start = base_angle
    arc_end = swing_angle
    arc_len = max(0.05, abs(arc_end - arc_start))
    # Number of points along the arc
    steps = max(3, int(arc_len / 0.12))
    pts = []
    for i in range(steps + 1):
        t = i / steps
        a = arc_start + (arc_end - arc_start) * t
        px = sx + int(math.cos(a) * attack_range)
        py = sy + int(math.sin(a) * attack_range)
        pts.append((px, py))
    if len(pts) >= 2:
        alpha = int(100 + 80 * progress)
        arc_color = (min(255, color[0] + 80), min(255, color[1] + 80), min(255, color[2] + 80))
        pygame.draw.lines(surface, arc_color, False, pts, 3)
        # Bright tip dot
        tip = pts[-1]
        pygame.draw.circle(surface, arc_color, tip, 5)


# ---- Sword ----
def _draw_sword_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, base_angle, sweep):
    bx = sx + int(math.cos(swing_angle) * blade_len)
    by = sy + int(math.sin(swing_angle) * blade_len)
    pygame.draw.line(surface, blade_color, (sx, sy), (bx, by), 4)
    pygame.draw.line(surface, (255, 255, 255), (sx, sy), (bx, by), 2)
    pygame.draw.circle(surface, (255, 255, 200), (bx, by), 4)
    # Draw simple trail dots (no SRCALPHA)
    for i in range(4):
        t = max(0, progress - i * 0.08)
        ta = base_angle - sweep / 2 + sweep * min(1.0, t)
        tr = blade_len - i * 4
        tx = sx + int(math.cos(ta) * tr)
        ty = sy + int(math.sin(ta) * tr)
        fade = max(60, 200 - i * 50)
        pygame.draw.circle(surface, (min(255, trail_color[0]), min(255, trail_color[1]), min(255, trail_color[2])), (tx, ty), max(1, 3 - i))


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


# ---- Rubber Chicken ----
def _draw_chicken_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, base_angle, sweep):
    bx = sx + int(math.cos(swing_angle) * blade_len * 0.8)
    by = sy + int(math.sin(swing_angle) * blade_len * 0.8)
    mid_x = (sx + bx) // 2 + int(math.sin(progress * 12) * 4)
    mid_y = (sy + by) // 2 + int(math.cos(progress * 12) * 4)
    pygame.draw.line(surface, (255, 200, 50), (sx, sy), (mid_x, mid_y), 3)
    pygame.draw.line(surface, (255, 220, 80), (mid_x, mid_y), (bx, by), 3)
    pygame.draw.circle(surface, blade_color, (bx, by), 7)
    beak_x = bx + int(math.cos(swing_angle) * 8)
    beak_y = by + int(math.sin(swing_angle) * 8)
    pygame.draw.polygon(surface, (255, 150, 0), [(bx, by), (beak_x, beak_y - 2), (beak_x, beak_y + 2)])
    pygame.draw.circle(surface, (0, 0, 0), (bx + int(math.cos(swing_angle - 0.5) * 4),
                                              by + int(math.sin(swing_angle - 0.5) * 4)), 2)
    for i in range(3):
        t = max(0, progress - i * 0.1)
        ta = base_angle - sweep / 2 + sweep * min(1.0, t)
        tx = sx + int(math.cos(ta) * blade_len * 0.5)
        ty = sy + int(math.sin(ta) * blade_len * 0.5)
        alpha = max(20, 150 - i * 50)
        ts = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(ts, (*trail_color, alpha), (4, 4), 4)
        surface.blit(ts, (tx - 4, ty - 4))


def _draw_chicken_idle(surface, sx, sy, idle_angle, blade_len, blade_color):
    bob_now = pygame.time.get_ticks()
    wobble = math.sin(bob_now * 0.005) * 3
    bx = sx + int(math.cos(idle_angle) * blade_len * 0.7)
    by = sy + int(math.sin(idle_angle) * blade_len * 0.7 + wobble)
    pygame.draw.line(surface, (255, 200, 50), (sx, sy), (bx, by), 3)
    pygame.draw.circle(surface, blade_color, (bx, by), 6)
    beak_x = bx + int(math.cos(idle_angle) * 7)
    beak_y = by + int(math.sin(idle_angle) * 7)
    pygame.draw.polygon(surface, (255, 150, 0), [(bx, by), (beak_x, beak_y - 2), (beak_x, beak_y + 2)])
    pygame.draw.circle(surface, (0, 0, 0), (bx + int(math.cos(idle_angle - 0.5) * 3),
                                              by + int(math.sin(idle_angle - 0.5) * 3)), 2)


# ---- Joy Buzzer ----
def _draw_buzzer_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, base_angle, sweep):
    for i in range(6):
        angle = base_angle + (math.tau / 6) * i + progress * 4
        length = blade_len * (0.5 + 0.5 * math.sin(progress * 8 + i))
        zx = sx + int(math.cos(angle) * length)
        zy = sy + int(math.sin(angle) * length)
        mid_x = sx + int(math.cos(angle) * length * 0.5 + math.sin(angle * 3) * 6)
        mid_y = sy + int(math.sin(angle) * length * 0.5 + math.cos(angle * 3) * 6)
        pygame.draw.line(surface, blade_color, (sx, sy), (mid_x, mid_y), 2)
        pygame.draw.line(surface, (255, 255, 255), (mid_x, mid_y), (zx, zy), 2)
        if progress > 0.3:
            spark_s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(spark_s, (*trail_color, 180), (3, 3), 3)
            surface.blit(spark_s, (zx - 3, zy - 3))
    flash_r = int(5 + 8 * progress)
    flash_s = pygame.Surface((flash_r * 2, flash_r * 2), pygame.SRCALPHA)
    pygame.draw.circle(flash_s, (*blade_color, int(120 * progress)), (flash_r, flash_r), flash_r)
    surface.blit(flash_s, (sx - flash_r, sy - flash_r))


def _draw_buzzer_idle(surface, sx, sy, idle_angle, blade_len, blade_color):
    bx = sx + int(math.cos(idle_angle) * 12)
    by = sy + int(math.sin(idle_angle) * 12)
    pygame.draw.circle(surface, blade_color, (bx, by), 5)
    pygame.draw.circle(surface, (255, 255, 255), (bx, by), 3)
    bob_now = pygame.time.get_ticks()
    if (bob_now // 200) % 3 == 0:
        spark_a = idle_angle + math.sin(bob_now * 0.01) * 1.5
        spark_x = bx + int(math.cos(spark_a) * 8)
        spark_y = by + int(math.sin(spark_a) * 8)
        pygame.draw.line(surface, (0, 255, 255), (bx, by), (spark_x, spark_y), 1)


# ---- Confetti Grenade ----
def _draw_grenade_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, base_angle, sweep):
    # Lobbing motion — arm arcs up then throws
    extend = 0.3 + 0.7 * progress
    arc_y = -16 * math.sin(progress * math.pi)  # arc upward during throw
    bx = sx + int(math.cos(base_angle) * blade_len * 0.4 * extend)
    by = sy + int(math.sin(base_angle) * blade_len * 0.4 * extend) + int(arc_y)
    # Arm
    pygame.draw.line(surface, blade_color, (sx, sy), (bx, by), 3)
    # Grenade in hand
    if progress < 0.6:
        pygame.draw.circle(surface, (80, 80, 80), (bx, by), 5)
        pygame.draw.circle(surface, blade_color, (bx, by), 5, 2)
        # Fuse spark
        spark_s = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(spark_s, (255, 255, 100, 200), (3, 3), 3)
        surface.blit(spark_s, (bx - 3, by - 8))
    else:
        # Release flash — confetti burst hint
        fx = sx + int(math.cos(base_angle) * blade_len * 0.5)
        fy = sy + int(math.sin(base_angle) * blade_len * 0.5)
        alpha = int(200 * max(0, 1.0 - (progress - 0.6) / 0.4))
        for color in [(255, 100, 200), (100, 255, 100), (255, 255, 0)]:
            ts = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(ts, (*color, alpha), (3, 3), 3)
            import random as _rng
            surface.blit(ts, (fx - 3 + _rng.randint(-6, 6), fy - 3 + _rng.randint(-6, 6)))


def _draw_grenade_idle(surface, sx, sy, angle, blade_len, blade_color):
    bx = sx + int(math.cos(angle) * 14)
    by = sy + int(math.sin(angle) * 14)
    # Grenade in hand
    pygame.draw.circle(surface, (80, 80, 80), (bx, by), 5)
    pygame.draw.circle(surface, blade_color, (bx, by), 5, 2)
    # Pin/ring
    pygame.draw.circle(surface, (200, 200, 200), (bx, by - 6), 2, 1)
    # Decorative confetti dots
    bob_now = pygame.time.get_ticks()
    for i in range(3):
        a = bob_now * 0.004 + i * 2.1
        cx = bx + int(math.cos(a) * 3)
        cy = by + int(math.sin(a) * 3)
        colors = [(255, 100, 200), (100, 255, 100), (255, 255, 0)]
        pygame.draw.circle(surface, colors[i], (cx, cy), 1)


# ---- Shield Bash ----
def _draw_shield_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, base_angle, sweep):
    # Draw a curved shield shape being thrust forward
    shield_dist = int(blade_len * 0.6 * (0.5 + progress * 0.5))
    cx = sx + int(math.cos(swing_angle) * shield_dist)
    cy = sy + int(math.sin(swing_angle) * shield_dist)
    # Shield as a wide arc
    pts = []
    perp = swing_angle + math.pi / 2
    for i in range(-3, 4):
        angle = swing_angle + i * 0.15
        d = shield_dist + abs(i) * 2
        pts.append((sx + int(math.cos(angle) * d), sy + int(math.sin(angle) * d)))
    if len(pts) >= 2:
        pygame.draw.lines(surface, blade_color, False, pts, 5)
        pygame.draw.lines(surface, (255, 255, 255), False, pts, 2)
    # Impact flash at full extension
    if progress > 0.7:
        flash_r = int(8 * (progress - 0.7) / 0.3)
        pygame.draw.circle(surface, (255, 255, 200), (cx, cy), flash_r)
    # Trail
    for i in range(4):
        t = max(0, progress - i * 0.08)
        ta = base_angle - sweep / 2 + sweep * min(1.0, t)
        tr = shield_dist - i * 5
        tx = sx + int(math.cos(ta) * tr)
        ty = sy + int(math.sin(ta) * tr)
        alpha = max(20, 140 - i * 35)
        ts = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(ts, (*trail_color, alpha), (4, 4), 4)
        surface.blit(ts, (tx - 4, ty - 4))


def _draw_shield_idle(surface, sx, sy, idle_angle, blade_len, blade_color):
    # Shield held in front
    shield_dist = int(blade_len * 0.5)
    cx = sx + int(math.cos(idle_angle) * shield_dist)
    cy = sy + int(math.sin(idle_angle) * shield_dist)
    pts = []
    for i in range(-3, 4):
        angle = idle_angle + i * 0.15
        d = shield_dist + abs(i) * 2
        pts.append((sx + int(math.cos(angle) * d), sy + int(math.sin(angle) * d)))
    if len(pts) >= 2:
        pygame.draw.lines(surface, blade_color, False, pts, 4)
        pygame.draw.lines(surface, (200, 220, 255), False, pts, 1)
