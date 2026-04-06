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
    "battle_axe": {
        "name": "Battle Axe",
        "damage_mult": 1.7,
        "range": 54,
        "cooldown": 620,
        "duration": 300,
        "sweep_deg": 100,
        "blade_color": (160, 165, 180),
        "trail_color": (255, 180, 60),
        "desc": "Double-bit axe. Each swing cleaves through armor.",
        "class": "knight",
    },
    "flail": {
        "name": "Flail",
        "damage_mult": 1.8,
        "range": 78,
        "cooldown": 580,
        "duration": 300,
        "sweep_deg": 200,
        "blade_color": (200, 175, 120),
        "trail_color": (255, 210, 90),
        "desc": "Spiked chain ball. Massive arc, sends enemies flying.",
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
        "desc": "Superheated edge. Sets foes ablaze.",
        "class": "knight",
        "on_hit_status": "fire",
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
        "cooldown": 550,
        "duration": 120,
        "sweep_deg": 60,
        "blade_color": (180, 220, 220),
        "trail_color": (150, 255, 200),
        "desc": "Twin throw. Two daggers one after the other.",
        "projectile": True,
        "proj_speed": 8.0,
        "proj_lifetime": 900,
        "proj_count": 1,
        "burst_count": 2,
        "burst_delay_ms": 120,
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
        "damage_mult": 3.2,
        "range": 45,
        "cooldown": 900,
        "duration": 220,
        "sweep_deg": 20,
        "blade_color": (255, 160, 40),
        "trail_color": (255, 220, 100),
        "desc": "Explosive-tipped bolt. Arcs and detonates on impact.",
        "projectile": True,
        "grenade": True,
        "proj_speed": 8.0,
        "proj_lifetime": 700,
        "proj_count": 1,
        "proj_style": "bolt",
        "splash_radius": 140,
        "sound": "bolt_boom",
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
        "sound": "chicken",
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
        "desc": "ZAP! Electric handshake of doom. Applies shock.",
        "class": "jester",
        "on_hit_status": "shock",
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
        "desc": "Toxic cream pies. Poisons on hit.",
        "projectile": True,
        "proj_speed": 5.0,
        "proj_lifetime": 800,
        "proj_count": 1,
        "class": "jester",
        "on_hit_status": "poison",
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
    "spud_gun": {
        "name": "Spud Gun",
        "damage_mult": 1.6,
        "range": 50,
        "cooldown": 480,
        "duration": 150,
        "sweep_deg": 40,
        "blade_color": (180, 140, 80),
        "trail_color": (220, 190, 120),
        "desc": "Launches potatoes at high velocity. Surprisingly lethal.",
        "projectile": True,
        "proj_speed": 8.5,
        "proj_lifetime": 850,
        "proj_count": 1,
        "proj_visual": "potato",
        "class": "jester",
        "sound": "thump",
    },
}

# ── Character class definitions ──
CHARACTER_CLASSES = {
    "knight": {
        "name": "Knight",
        "desc": "Heavy armor. Each blow sends foes flying. Born to fight up close.",
        "color": (0, 180, 255),
        "start_weapon": "sword",
        "hp_bonus": 10,
        "damage_bonus": -2,
        "speed_bonus": 0,
        "knockback_bonus": 2.0,
        "passives": ["melee_lifesteal"],
    },
    "archer": {
        "name": "Ranger",
        "desc": "Fast and deadly at range. Keep your distance.",
        "color": (0, 255, 150),
        "start_weapon": "dagger",
        "hp_bonus": 5,
        "damage_bonus": 0,
        "speed_bonus": 0.5,
        "passives": ["evasion"],
    },
    "jester": {
        "name": "Jester",
        "desc": "Chaos incarnate. Funny weapons, unpredictable power.",
        "color": (255, 50, 255),
        "start_weapon": "rubber_chicken",
        "hp_bonus": 10,
        "damage_bonus": 0,
        "speed_bonus": 0.8,
        "passives": ["lucky_crits"],
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
        elif "Crossbow" in wname:
            _draw_crossbow_swing(surface, sx, sy, sword_angle, blade_len, blade_color, trail_color, progress)
        elif "Dagger" in wname or "Bow" in wname or "Rifle" in wname or "Scatter" in wname or "Banana" in wname or "Pie" in wname or "Ricochet" in wname or "Jack" in wname:
            _draw_dagger_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, sword_angle, sweep)
        elif "Shield" in wname:
            _draw_shield_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, sword_angle, sweep)
        elif "Flail" in wname:
            _draw_flail_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, sword_angle, sweep)
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
        elif "Crossbow" in wname:
            _draw_crossbow_idle(surface, sx, sy, sword_angle, blade_len, blade_color)
        elif "Dagger" in wname or "Bow" in wname or "Rifle" in wname or "Scatter" in wname or "Banana" in wname or "Pie" in wname or "Ricochet" in wname or "Jack" in wname or "Spud" in wname:
            _draw_dagger_idle(surface, sx, sy, sword_angle, blade_len, blade_color)
        elif "Shield" in wname:
            _draw_shield_idle(surface, sx, sy, idle_angle, blade_len, blade_color)
        elif "Flail" in wname:
            _draw_flail_idle(surface, sx, sy, idle_angle, blade_len, blade_color)
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
    pygame.draw.line(surface, (100, 55, 18), (sx, sy), (bx, by), 5)
    # Double-bit axe head — two crescent blades on each side of shaft tip
    perp = swing_angle + math.pi / 2
    hs, tip = 15, 10  # half-size, tip forward length
    for sign in (1, -1):
        pts = [
            (bx, by),
            (bx + int(math.cos(perp) * hs * 1.3 * sign), by + int(math.sin(perp) * hs * 1.3 * sign)),
            (bx + int(math.cos(perp) * hs * 0.7 * sign + math.cos(swing_angle) * tip),
             by + int(math.sin(perp) * hs * 0.7 * sign + math.sin(swing_angle) * tip)),
        ]
        pygame.draw.polygon(surface, blade_color, pts)
        pygame.draw.polygon(surface, (230, 230, 240), pts, 1)
    # Impact spark at end of swing
    if progress > 0.75:
        spark_size = int(12 * (progress - 0.75) / 0.25)
        pygame.draw.circle(surface, (255, 200, 80), (bx, by), spark_size)
    # Trail
    for i in range(5):
        t = max(0, progress - i * 0.07)
        ta = base_angle - sweep / 2 + sweep * min(1.0, t)
        tr = blade_len - i * 3
        tx = sx + int(math.cos(ta) * tr)
        ty = sy + int(math.sin(ta) * tr)
        alpha = max(20, 200 - i * 40)
        ts = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(ts, (*trail_color, alpha), (6, 6), max(1, 6 - i))
        surface.blit(ts, (tx - 6, ty - 6))


def _draw_axe_idle(surface, sx, sy, idle_angle, blade_len, blade_color):
    bx = sx + int(math.cos(idle_angle) * blade_len)
    by = sy + int(math.sin(idle_angle) * blade_len)
    pygame.draw.line(surface, (100, 55, 18), (sx, sy), (bx, by), 5)
    perp = idle_angle + math.pi / 2
    for sign in (1, -1):
        pts = [
            (bx, by),
            (bx + int(math.cos(perp) * 11 * sign), by + int(math.sin(perp) * 11 * sign)),
            (bx + int(math.cos(perp) * 7 * sign + math.cos(idle_angle) * 7),
             by + int(math.sin(perp) * 7 * sign + math.sin(idle_angle) * 7)),
        ]
        pygame.draw.polygon(surface, blade_color, pts)
        pygame.draw.polygon(surface, (200, 200, 210), pts, 1)


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


# ---- Crossbow ----
def _draw_crossbow_swing(surface, sx, sy, angle, blade_len, blade_color, trail_color, progress):
    """T-shaped crossbow: stock goes back, limbs are perpendicular at the front."""
    # Stock (points away from target — toward player's body)
    stock_len = 16
    stock_x = sx - int(math.cos(angle) * stock_len)
    stock_y = sy - int(math.sin(angle) * stock_len)
    pygame.draw.line(surface, (90, 60, 25), (sx, sy), (stock_x, stock_y), 4)
    # Tiller (body forward)
    til_x = sx + int(math.cos(angle) * 14)
    til_y = sy + int(math.sin(angle) * 14)
    pygame.draw.line(surface, (90, 60, 25), (sx, sy), (til_x, til_y), 3)
    # Prod (limbs) — snap from relaxed to fired as progress increases
    prod_len = int(16 * (1.0 - progress * 0.35))
    perp = angle + math.pi / 2
    l1x = sx + int(math.cos(perp) * prod_len)
    l1y = sy + int(math.sin(perp) * prod_len)
    l2x = sx - int(math.cos(perp) * prod_len)
    l2y = sy - int(math.sin(perp) * prod_len)
    pygame.draw.line(surface, blade_color, (l1x, l1y), (l2x, l2y), 4)
    # Bowstring to tiller tip
    pygame.draw.line(surface, (200, 175, 130), (l1x, l1y), (til_x, til_y), 1)
    pygame.draw.line(surface, (200, 175, 130), (l2x, l2y), (til_x, til_y), 1)
    # Bolt in flight after 0.3 progress
    if progress > 0.3:
        fly = min(1.0, (progress - 0.3) / 0.7)
        bolt_dist = int(blade_len * 0.8 * fly)
        bx = sx + int(math.cos(angle) * bolt_dist)
        by = sy + int(math.sin(angle) * bolt_dist)
        bolt_tip_x = bx + int(math.cos(angle) * 10)
        bolt_tip_y = by + int(math.sin(angle) * 10)
        pygame.draw.line(surface, blade_color, (bx, by), (bolt_tip_x, bolt_tip_y), 3)
        # Glowing tip
        pygame.draw.circle(surface, (255, 200, 80), (bolt_tip_x, bolt_tip_y), 3)
        # Trail
        trail_alpha = int(180 * (1 - fly))
        if trail_alpha > 10:
            trail_len = int(bolt_dist * 0.3)
            t1x = bx - int(math.cos(angle) * trail_len)
            t1y = by - int(math.sin(angle) * trail_len)
            ts = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.line(surface, (*trail_color, trail_alpha), (t1x, t1y), (bx, by), 2)


def _draw_crossbow_idle(surface, sx, sy, angle, blade_len, blade_color):
    # Stock
    stock_x = sx - int(math.cos(angle) * 15)
    stock_y = sy - int(math.sin(angle) * 15)
    pygame.draw.line(surface, (90, 60, 25), (sx, sy), (stock_x, stock_y), 4)
    # Tiller
    til_x = sx + int(math.cos(angle) * 14)
    til_y = sy + int(math.sin(angle) * 14)
    pygame.draw.line(surface, (90, 60, 25), (sx, sy), (til_x, til_y), 3)
    # Prod (limbs — cocked and ready)
    perp = angle + math.pi / 2
    l1x = sx + int(math.cos(perp) * 16)
    l1y = sy + int(math.sin(perp) * 16)
    l2x = sx - int(math.cos(perp) * 16)
    l2y = sy - int(math.sin(perp) * 16)
    pygame.draw.line(surface, blade_color, (l1x, l1y), (l2x, l2y), 4)
    # Bowstring
    pygame.draw.line(surface, (200, 175, 130), (l1x, l1y), (til_x, til_y), 1)
    pygame.draw.line(surface, (200, 175, 130), (l2x, l2y), (til_x, til_y), 1)
    # Bolt on track
    bt_x = sx + int(math.cos(angle) * 5)
    bt_y = sy + int(math.sin(angle) * 5)
    bt_tip_x = sx + int(math.cos(angle) * 14)
    bt_tip_y = sy + int(math.sin(angle) * 14)
    pygame.draw.line(surface, blade_color, (bt_x, bt_y), (bt_tip_x, bt_tip_y), 2)
    pygame.draw.circle(surface, (255, 180, 50), (bt_x, bt_y), 2)


# ---- Flail ----
def _draw_flail_swing(surface, sx, sy, swing_angle, blade_len, blade_color, trail_color, progress, base_angle, sweep):
    """Chain links from player ending in a spiked ball that lags behind the arm."""
    ball_lag = 0.18
    ball_angle = base_angle - sweep / 2 + sweep * max(0.0, progress - ball_lag)
    n_links = 5
    prev_x, prev_y = sx, sy
    for i in range(n_links):
        t_frac = (i + 1) / n_links
        # Links lag progressively more near the ball
        lag = ball_lag * (n_links - i) / n_links
        link_angle = base_angle - sweep / 2 + sweep * max(0.0, progress - lag)
        lx = sx + int(math.cos(link_angle) * blade_len * 0.88 * t_frac)
        ly = sy + int(math.sin(link_angle) * blade_len * 0.88 * t_frac)
        pygame.draw.line(surface, (155, 135, 95), (prev_x, prev_y), (lx, ly), 2)
        if i < n_links - 1:
            pygame.draw.rect(surface, (185, 165, 115), (lx - 2, ly - 2, 4, 4))
        prev_x, prev_y = lx, ly
    # Spiked ball
    ball_len = blade_len * 0.90
    bx = sx + int(math.cos(ball_angle) * ball_len)
    by = sy + int(math.sin(ball_angle) * ball_len)
    pygame.draw.circle(surface, blade_color, (bx, by), 8)
    pygame.draw.circle(surface, (235, 215, 160), (bx, by), 8, 2)
    for si in range(6):
        spike_a = ball_angle + si * math.pi / 3
        spx = bx + int(math.cos(spike_a) * 12)
        spy = by + int(math.sin(spike_a) * 12)
        pygame.draw.line(surface, (220, 200, 145), (bx, by), (spx, spy), 2)
        pygame.draw.circle(surface, blade_color, (spx, spy), 2)
    # Ball trail
    for i in range(5):
        t = max(0, progress - i * 0.07 - ball_lag)
        ta = base_angle - sweep / 2 + sweep * min(1.0, max(0, t))
        tr = ball_len - i * 3
        tx = sx + int(math.cos(ta) * tr)
        ty = sy + int(math.sin(ta) * tr)
        alpha = max(20, 190 - i * 42)
        ts = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(ts, (*trail_color, alpha), (6, 6), max(1, 6 - i))
        surface.blit(ts, (tx - 6, ty - 6))


def _draw_flail_idle(surface, sx, sy, idle_angle, blade_len, blade_color):
    n_links = 5
    now_f = pygame.time.get_ticks()
    prev_x, prev_y = sx, sy
    for i in range(n_links):
        t_frac = (i + 1) / n_links
        wobble = math.sin(now_f * 0.004 + i * 0.8) * 3
        lx = sx + int(math.cos(idle_angle) * blade_len * 0.82 * t_frac) + int(wobble)
        ly = sy + int(math.sin(idle_angle) * blade_len * 0.82 * t_frac)
        pygame.draw.line(surface, (155, 135, 95), (prev_x, prev_y), (lx, ly), 2)
        if i < n_links - 1:
            pygame.draw.rect(surface, (185, 165, 115), (lx - 2, ly - 2, 4, 4))
        prev_x, prev_y = lx, ly
    bx = sx + int(math.cos(idle_angle) * blade_len * 0.82)
    by = sy + int(math.sin(idle_angle) * blade_len * 0.82)
    pygame.draw.circle(surface, blade_color, (bx, by), 7)
    pygame.draw.circle(surface, (235, 215, 160), (bx, by), 7, 2)
    for si in range(6):
        spike_a = idle_angle + si * math.pi / 3
        spx = bx + int(math.cos(spike_a) * 10)
        spy = by + int(math.sin(spike_a) * 10)
        pygame.draw.line(surface, (220, 200, 145), (bx, by), (spx, spy), 2)


# ---- Spear (kept for save-file compat, mapped identically to sword) ----
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
