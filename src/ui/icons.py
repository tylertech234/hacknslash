"""
Procedural pygame.draw icons for weapons and passives.
All surfaces are cached by (key, size) — drawn once, reused every frame.
"""
import pygame
import math

_cache: dict[tuple, pygame.Surface] = {}


def _new(size: int) -> pygame.Surface:
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    return s


def get_passive_icon(key: str, size: int, color: tuple) -> pygame.Surface:
    cache_key = ("passive", key, size)
    if cache_key in _cache:
        return _cache[cache_key]
    s = _new(size)
    _draw_passive(s, key, size, color)
    _cache[cache_key] = s
    return s


def get_weapon_icon(weapon_key: str, size: int) -> pygame.Surface:
    cache_key = ("weapon", weapon_key, size)
    if cache_key in _cache:
        return _cache[cache_key]
    s = _new(size)
    _draw_weapon_icon(s, weapon_key, size)
    _cache[cache_key] = s
    return s


# ─────────────────────────────────────────────
#  PASSIVE ICONS
# ─────────────────────────────────────────────

def _draw_passive(surf: pygame.Surface, key: str, sz: int, col: tuple):
    c = col
    cx, cy = sz // 2, sz // 2
    _fn = {
        "vampiric_strike":  _pi_vampire,
        "chain_lightning":  _pi_lightning,
        "thorns":           _pi_thorns,
        "second_wind":      _pi_second_wind,
        "nano_regen":       _pi_regen,
        "berserker":        _pi_berserker,
        "shield_matrix":    _pi_shield,
        "explosive_kills":  _pi_explosion,
        "magnetic_field":   _pi_magnet,
        "adrenaline":       _pi_adrenaline,
        "melee_lifesteal":  _pi_heart,
        "armor_plating":    _pi_armor,
        "crit_shots":       _pi_crosshair,
        "evasion":          _pi_evasion,
        "lucky_crits":      _pi_star,
        "confetti_burst":   _pi_confetti,
    }.get(key)
    if _fn:
        _fn(surf, cx, cy, sz, c)
    else:
        # Fallback: filled circle with first letter
        pygame.draw.circle(surf, c, (cx, cy), sz // 2 - 2)


def _pi_vampire(s, cx, cy, sz, c):
    """Blood drop."""
    r = sz // 2 - 2
    # Drop: circle at bottom, triangle tip at top
    drop_y = cy + r // 4
    pygame.draw.circle(s, c, (cx, drop_y), r * 2 // 3)
    pts = [(cx, cy - r), (cx - r // 2, cy), (cx + r // 2, cy)]
    pygame.draw.polygon(s, c, pts)


def _pi_lightning(s, cx, cy, sz, c):
    """Zigzag bolt."""
    w = sz // 2
    pts = [
        (cx + w // 3, 2),
        (cx - 2, cy - 1),
        (cx + 4, cy - 1),
        (cx - w // 3, sz - 2),
        (cx + 2, cy + 3),
        (cx - 4, cy + 3),
    ]
    pygame.draw.polygon(s, c, pts)


def _pi_thorns(s, cx, cy, sz, c):
    """8-point spiky star."""
    r_out = sz // 2 - 2
    r_in  = r_out // 2
    pts = []
    for i in range(16):
        angle = math.pi * i / 8 - math.pi / 2
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    pygame.draw.polygon(s, c, pts)


def _pi_second_wind(s, cx, cy, sz, c):
    """Heart with upward line (second life)."""
    r = sz // 2 - 3
    # Two circles for heart top
    pygame.draw.circle(s, c, (cx - r // 2, cy - r // 4), r // 2)
    pygame.draw.circle(s, c, (cx + r // 2, cy - r // 4), r // 2)
    # Bottom triangle
    pts = [(cx - r, cy - r // 4), (cx, cy + r // 2), (cx + r, cy - r // 4)]
    pygame.draw.polygon(s, c, pts)
    # Arrow up
    pygame.draw.line(s, (255, 255, 255), (cx, cy - r // 4), (cx, 2), 2)
    pygame.draw.line(s, (255, 255, 255), (cx, 2), (cx - 3, 6), 2)
    pygame.draw.line(s, (255, 255, 255), (cx, 2), (cx + 3, 6), 2)


def _pi_regen(s, cx, cy, sz, c):
    """Green plus/cross."""
    t = max(2, sz // 8)
    b = sz // 4
    pygame.draw.rect(s, c, (cx - t, b, t * 2, sz - b * 2))
    pygame.draw.rect(s, c, (b, cy - t, sz - b * 2, t * 2))


def _pi_berserker(s, cx, cy, sz, c):
    """Flame shape."""
    r = sz // 2 - 2
    # Main flame body
    pts = [
        (cx, 2),
        (cx + r, cy + r // 2),
        (cx + r // 2, cy + r),
        (cx, cy + r // 4),
        (cx - r // 2, cy + r),
        (cx - r, cy + r // 2),
    ]
    pygame.draw.polygon(s, c, pts)
    # Inner bright tip
    inner = tuple(min(255, v + 80) for v in c)
    ipts = [(cx, 4), (cx + r // 3, cy), (cx, cy - r // 4), (cx - r // 3, cy)]
    pygame.draw.polygon(s, inner, ipts)


def _pi_shield(s, cx, cy, sz, c):
    """Hexagonal shield."""
    r = sz // 2 - 2
    pts = []
    for i in range(6):
        a = math.pi / 2 + i * math.pi / 3
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pygame.draw.polygon(s, c, pts)
    # Inner cross
    dim = tuple(max(0, v - 80) for v in c)
    t = max(1, sz // 10)
    pygame.draw.rect(s, dim, (cx - t, cy - r // 2, t * 2, r))
    pygame.draw.rect(s, dim, (cx - r // 2, cy - t, r, t * 2))


def _pi_explosion(s, cx, cy, sz, c):
    """Starburst explosion."""
    r_out = sz // 2 - 1
    r_in  = r_out // 3
    pts = []
    for i in range(20):
        angle = math.pi * i / 10 - math.pi / 2
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    pygame.draw.polygon(s, c, pts)
    # Bright core
    pygame.draw.circle(s, (255, 255, 200), (cx, cy), r_in)


def _pi_magnet(s, cx, cy, sz, c):
    """U-shaped magnet."""
    r  = sz // 2 - 3
    th = max(2, sz // 7)
    # Outer arc (U shape): left arm, bottom arc, right arm
    pygame.draw.rect(s, c, (cx - r, cy - r // 2, th, r))
    pygame.draw.rect(s, c, (cx + r - th, cy - r // 2, th, r))
    pygame.draw.arc(s, c, (cx - r, cy - r // 2, r * 2, r), math.pi, 0, th)
    # Red/blue poles
    pygame.draw.rect(s, (255, 80, 80), (cx - r, cy - r // 2 - th, th, th))
    pygame.draw.rect(s, (80, 120, 255), (cx + r - th, cy - r // 2 - th, th, th))


def _pi_adrenaline(s, cx, cy, sz, c):
    """Upward dash arrow."""
    w = sz // 3
    # Arrow body
    pygame.draw.rect(s, c, (cx - w // 3, cy, w * 2 // 3, sz // 2 - 2))
    # Arrow head
    pts = [(cx, 2), (cx - w, cy + 2), (cx + w, cy + 2)]
    pygame.draw.polygon(s, c, pts)
    # Speed lines
    lc = tuple(min(255, v + 60) for v in c)
    for i in range(3):
        lx = cx - w + i * (w // 2 + 2)
        pygame.draw.line(s, lc, (lx, cy + sz // 4), (lx - 3, sz - 3), 1)


def _pi_heart(s, cx, cy, sz, c):
    """Simple heart."""
    r = sz // 2 - 2
    pygame.draw.circle(s, c, (cx - r // 2, cy - r // 4), r // 2)
    pygame.draw.circle(s, c, (cx + r // 2, cy - r // 4), r // 2)
    pts = [(cx - r, cy - r // 4), (cx, cy + r // 2), (cx + r, cy - r // 4)]
    pygame.draw.polygon(s, c, pts)


def _pi_armor(s, cx, cy, sz, c):
    """Square shield with horizontal bar."""
    r = sz // 2 - 2
    # Shield outline
    pts = [(cx - r, cy - r), (cx + r, cy - r),
           (cx + r, cy + r // 2), (cx, cy + r), (cx - r, cy + r // 2)]
    pygame.draw.polygon(s, c, pts)
    # Horizontal stripe
    dim = tuple(max(0, v - 70) for v in c)
    t = max(1, sz // 10)
    pygame.draw.rect(s, dim, (cx - r + 2, cy - t, (r - 2) * 2, t * 2))


def _pi_crosshair(s, cx, cy, sz, c):
    """Crosshair circle with lines."""
    r = sz // 2 - 2
    pygame.draw.circle(s, c, (cx, cy), r, 2)
    pygame.draw.circle(s, c, (cx, cy), r // 4)
    g = r // 2
    pygame.draw.line(s, c, (cx - r, cy), (cx - g, cy), 2)
    pygame.draw.line(s, c, (cx + g, cy), (cx + r, cy), 2)
    pygame.draw.line(s, c, (cx, cy - r), (cx, cy - g), 2)
    pygame.draw.line(s, c, (cx, cy + g), (cx, cy + r), 2)


def _pi_evasion(s, cx, cy, sz, c):
    """Ghost silhouette (dodge)."""
    r = sz // 2 - 2
    # Head circle
    pygame.draw.circle(s, c, (cx, cy - r // 3), r * 2 // 3)
    # Body rect
    pygame.draw.rect(s, c, (cx - r * 2 // 3, cy - r // 3, r * 4 // 3, r))
    # Wavy bottom: three bumps
    bw = r * 4 // 3
    bx = cx - bw // 2
    by = cy + r * 2 // 3
    bh = r // 3
    for i in range(3):
        pygame.draw.circle(s, c, (bx + i * (bw // 3) + bw // 6, by), bh)
    # Eye holes
    ec = (0, 0, 0, 0)
    pygame.draw.circle(s, (0, 0, 0), (cx - r // 4, cy - r // 3), max(1, r // 5))
    pygame.draw.circle(s, (0, 0, 0), (cx + r // 4, cy - r // 3), max(1, r // 5))


def _pi_star(s, cx, cy, sz, c):
    """5-point star."""
    r_out = sz // 2 - 1
    r_in  = int(r_out * 0.4)
    pts = []
    for i in range(10):
        a = math.pi * i / 5 - math.pi / 2
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pygame.draw.polygon(s, c, pts)


def _pi_confetti(s, cx, cy, sz, c):
    """Sparkle burst from center."""
    r = sz // 2 - 2
    colors = [c,
              (min(255, c[0] + 80), max(0, c[1] - 40), min(255, c[2] + 80)),
              (max(0, c[0] - 40), min(255, c[1] + 80), max(0, c[2] - 40)),
              (255, 220, 50)]
    for i in range(8):
        a = i * math.pi / 4
        ex = cx + int(r * math.cos(a))
        ey = cy + int(r * math.sin(a))
        col = colors[i % len(colors)]
        pygame.draw.line(s, col, (cx, cy), (ex, ey), 2)
        pygame.draw.circle(s, col, (ex, ey), max(1, sz // 8))


# ─────────────────────────────────────────────
#  WEAPON ICONS
# ─────────────────────────────────────────────

def _draw_weapon_icon(surf: pygame.Surface, key: str, sz: int):
    _fn = {
        "sword":            _wi_sword,
        "battle_axe":       _wi_axe,
        "spear":            _wi_spear,
        "plasma_blade":     _wi_plasma_blade,
        "gravity_maul":     _wi_gravity_maul,
        "blade_barrier":    _wi_blade_barrier,
        "shield_bash":      _wi_shield_bash,
        "dagger":           _wi_dagger,
        "cyber_bow":        _wi_cyber_bow,
        "pulse_rifle":      _wi_pulse_rifle,
        "scatter_shot":     _wi_scatter_shot,
        "ricochet_disc":    _wi_ricochet_disc,
        "rubber_chicken":   _wi_rubber_chicken,
        "banana_rang":      _wi_banana_rang,
        "joy_buzzer":       _wi_joy_buzzer,
        "pie_launcher":     _wi_pie_launcher,
        "confetti_grenade": _wi_confetti_grenade,
        "jack_in_box":      _wi_jack_in_box,
        "spud_gun":         _wi_spud_gun,
    }.get(key)
    if _fn:
        _fn(surf, sz // 2, sz // 2, sz)
    else:
        # Generic: diamond
        cx, cy, r = sz // 2, sz // 2, sz // 2 - 2
        pygame.draw.polygon(surf, (200, 200, 200),
                            [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)])


def _wi_sword(s, cx, cy, sz):
    """Classic diagonal sword."""
    sc = (200, 200, 220)
    gc = (180, 140, 60)
    r = sz // 2 - 2
    # Blade: diagonal line from top-right to center-left
    pygame.draw.line(s, sc, (cx + r, cy - r), (cx - r + 4, cy + r - 4), 3)
    # Guard: perpendicular bar
    gx, gy = cx, cy
    pygame.draw.line(s, gc, (gx - 5, gy + 5), (gx + 5, gy - 5), 3)
    # Handle
    pygame.draw.line(s, gc, (cx - r + 4, cy + r - 4), (cx - r, cy + r), 3)
    # Tip highlight
    pygame.draw.circle(s, (240, 240, 255), (cx + r, cy - r), 2)


def _wi_axe(s, cx, cy, sz):
    """Axe head + handle."""
    hc = (160, 160, 170)
    wc = (120, 80, 40)
    r = sz // 2 - 2
    # Handle
    pygame.draw.line(s, wc, (cx - r // 2, cy + r), (cx + r // 2, cy - r), 3)
    # Axe head: crescent-ish polygon
    pts = [
        (cx + r // 2, cy - r),
        (cx + r, cy - r // 3),
        (cx + r // 3, cy + r // 3),
        (cx + r // 3 - 4, cy + r // 3 - 4),
    ]
    pygame.draw.polygon(s, hc, pts)


def _wi_spear(s, cx, cy, sz):
    """Long vertical spear."""
    sc = (190, 170, 140)
    wc = (110, 75, 35)
    r = sz // 2 - 1
    # Shaft
    pygame.draw.line(s, wc, (cx, cy + r), (cx, cy - r + 6), 3)
    # Tip triangle
    pts = [(cx, 2), (cx - 4, cy - r + 8), (cx + 4, cy - r + 8)]
    pygame.draw.polygon(s, sc, pts)


def _wi_hammer(s, cx, cy, sz):
    """War hammer T-shape."""
    hc = (140, 130, 130)
    wc = (100, 65, 30)
    r = sz // 2 - 2
    # Handle
    pygame.draw.line(s, wc, (cx, cy + r), (cx, cy - r // 3), 3)
    # Hammerhead
    hw = r
    hh = r // 2
    pygame.draw.rect(s, hc, (cx - hw // 2, cy - r, hw, hh))
    # Side reinforcement lines
    pygame.draw.line(s, (100, 95, 95), (cx - hw // 2, cy - r), (cx - hw // 2, cy - r + hh), 1)
    pygame.draw.line(s, (100, 95, 95), (cx + hw // 2 - 1, cy - r), (cx + hw // 2 - 1, cy - r + hh), 1)


def _wi_plasma_blade(s, cx, cy, sz):
    """Glowing cyan blade."""
    r = sz // 2 - 2
    # Glow aura
    pygame.draw.line(s, (0, 80, 120), (cx + r, cy - r), (cx - r + 4, cy + r - 4), 7)
    # Blade
    pygame.draw.line(s, (0, 200, 255), (cx + r, cy - r), (cx - r + 4, cy + r - 4), 3)
    # Core
    pygame.draw.line(s, (180, 240, 255), (cx + r - 2, cy - r + 2), (cx - r + 6, cy + r - 6), 1)
    # Guard
    pygame.draw.line(s, (0, 140, 200), (cx - 6, cy + 6), (cx + 6, cy - 6), 3)


def _wi_gravity_maul(s, cx, cy, sz):
    """Purple swirling maul head."""
    pc = (180, 50, 255)
    wc = (100, 65, 30)
    r = sz // 2 - 2
    # Handle
    pygame.draw.line(s, wc, (cx, cy + r), (cx, 2), 3)
    # Maul head
    pygame.draw.circle(s, pc, (cx, cy - r // 3), r // 2)
    # Swirl lines
    for i in range(3):
        a = i * 2 * math.pi / 3
        ex = cx + int((r // 2) * math.cos(a))
        ey = (cy - r // 3) + int((r // 2) * math.sin(a))
        pygame.draw.line(s, (220, 140, 255), (cx, cy - r // 3), (ex, ey), 1)


def _wi_blade_barrier(s, cx, cy, sz):
    """Three small orbiting blades."""
    bc = (180, 220, 255)
    r = sz // 2 - 3
    for i in range(3):
        a = i * 2 * math.pi / 3
        bx = cx + int(r * 0.65 * math.cos(a))
        by = cy + int(r * 0.65 * math.sin(a))
        # Small diamond blade
        br = r // 3
        pts = [(bx, by - br), (bx + br, by), (bx, by + br), (bx - br, by)]
        pygame.draw.polygon(s, bc, pts)
    # Center orbit circle
    pygame.draw.circle(s, (100, 140, 200), (cx, cy), r // 4, 1)


def _wi_shield_bash(s, cx, cy, sz):
    """Round shield with impact lines."""
    sc = (150, 200, 255)
    r = sz // 2 - 2
    pygame.draw.circle(s, sc, (cx, cy), r)
    pygame.draw.circle(s, (80, 130, 200), (cx, cy), r, 2)
    pygame.draw.circle(s, (80, 130, 200), (cx, cy), r // 2, 2)
    # Impact lines on right
    ic = (200, 230, 255)
    pygame.draw.line(s, ic, (cx + r - 2, cy - 4), (cx + r + 2, cy - 6), 2)
    pygame.draw.line(s, ic, (cx + r - 1, cy + 2), (cx + r + 3, cy + 4), 2)
    pygame.draw.line(s, ic, (cx + r, cy - 1), (cx + r + 4, cy - 1), 2)


def _wi_dagger(s, cx, cy, sz):
    """Small throwing dagger."""
    sc = (180, 220, 220)
    r = sz // 2 - 2
    # Blade: tall thin diamond
    pts = [(cx, 2), (cx + 3, cy), (cx, sz - 4), (cx - 3, cy)]
    pygame.draw.polygon(s, sc, pts)
    # Guard
    pygame.draw.line(s, (120, 160, 160), (cx - 5, cy - 2), (cx + 5, cy - 2), 2)


def _wi_cyber_bow(s, cx, cy, sz):
    """Bow arc with arrow."""
    bc = (0, 255, 180)
    r = sz // 2 - 2
    # Bow arc
    pygame.draw.arc(s, bc, (2, 2, (sz - 4) // 2, sz - 4), math.pi * 0.2, math.pi * 1.8, 3)
    # String
    pygame.draw.line(s, (0, 180, 130), (sz // 4, 3), (sz // 4, sz - 3), 1)
    # Arrow shaft
    ax = sz // 4 + 2
    pygame.draw.line(s, (200, 200, 180), (ax, cy), (sz - 3, cy), 2)
    # Arrowhead
    pts = [(sz - 2, cy), (sz - 7, cy - 3), (sz - 7, cy + 3)]
    pygame.draw.polygon(s, bc, pts)
    # Fletching
    pygame.draw.line(s, (180, 160, 100), (ax, cy), (ax + 4, cy - 3), 2)
    pygame.draw.line(s, (180, 160, 100), (ax, cy), (ax + 4, cy + 3), 2)


def _wi_pulse_rifle(s, cx, cy, sz):
    """Side-view pixel gun."""
    gc = (255, 100, 50)
    bc = (60, 55, 55)
    r = sz // 2 - 2
    # Body
    pygame.draw.rect(s, bc, (4, cy - r // 3, sz - 10, r * 2 // 3))
    # Barrel
    pygame.draw.rect(s, (80, 75, 75), (sz - 10, cy - r // 5, 10, r * 2 // 5))
    # Energy glow at barrel
    pygame.draw.circle(s, gc, (sz - 3, cy), r // 4)
    # Scope
    pygame.draw.rect(s, (90, 85, 85), (cx - 4, cy - r // 2 - 3, 10, 5))
    # Handle
    pygame.draw.rect(s, bc, (cx - r // 2, cy + r // 3 - 2, r // 2, r // 2 + 2))


def _wi_scatter_shot(s, cx, cy, sz):
    """Fan of 5 bolts."""
    bc = (255, 200, 0)
    r = sz // 2 - 2
    angles = [-40, -20, 0, 20, 40]
    for a in angles:
        rad = math.radians(a)
        ex = cx + int(r * math.cos(rad))
        ey = cy + int(r * math.sin(rad))
        pygame.draw.line(s, bc, (cx - r // 2, cy), (ex, ey), 2)
        pygame.draw.circle(s, (255, 240, 120), (ex, ey), 2)


def _wi_ricochet_disc(s, cx, cy, sz):
    """Spinning disc with bounce marks."""
    dc = (255, 180, 0)
    r = sz // 2 - 2
    pygame.draw.circle(s, dc, (cx, cy), r)
    pygame.draw.circle(s, (200, 130, 0), (cx, cy), r - 3)
    # Ridges
    for i in range(4):
        a = i * math.pi / 4
        x1 = cx + int((r - 4) * math.cos(a))
        y1 = cy + int((r - 4) * math.sin(a))
        pygame.draw.line(s, dc, (cx, cy), (x1, y1), 2)
    # Bounce spark marks
    for offset in [(r - 2, -2), (-r + 2, 2)]:
        px, py = cx + offset[0], cy + offset[1]
        pygame.draw.line(s, (255, 240, 120), (px, py), (px + 3, py - 3), 2)
        pygame.draw.line(s, (255, 240, 120), (px, py), (px - 3, py - 3), 2)


def _wi_rubber_chicken(s, cx, cy, sz):
    """Chicken silhouette: body + head + beak."""
    yc = (255, 220, 50)
    r = sz // 2 - 2
    # Body oval
    body_rect = (cx - r * 3 // 4, cy - r // 3, r * 3 // 2, r * 4 // 3)
    pygame.draw.ellipse(s, yc, body_rect)
    # Head
    pygame.draw.circle(s, yc, (cx + r // 2, cy - r // 2), r // 3)
    # Beak
    pts = [(cx + r // 2 + r // 4, cy - r // 2),
           (cx + r // 2 + r // 4 + r // 4, cy - r // 2 - 2),
           (cx + r // 2 + r // 4 + r // 4, cy - r // 2 + 2)]
    pygame.draw.polygon(s, (255, 150, 0), pts)
    # Eye
    pygame.draw.circle(s, (0, 0, 0), (cx + r // 2 + 3, cy - r // 2 - 2), max(1, r // 8))
    # Wing hint
    pygame.draw.arc(s, (220, 190, 30), (cx - r * 3 // 4 + 4, cy - r // 4, r, r // 2), 0, math.pi, 2)


def _wi_banana_rang(s, cx, cy, sz):
    """Banana / boomerang curve."""
    yc = (255, 230, 0)
    r = sz // 2 - 2
    # Outer arc
    pygame.draw.arc(s, yc, (2, 2, sz - 4, sz - 4), math.pi * 0.1, math.pi * 1.1, 5)
    # Inner arc (thicker banana)
    pygame.draw.arc(s, (220, 190, 0), (5, 5, sz - 10, sz - 10), math.pi * 0.15, math.pi * 1.05, 3)
    # Tips
    pygame.draw.circle(s, yc, (cx + int(r * math.cos(math.pi * 0.1)), cy - int(r * math.sin(math.pi * 0.1))), 3)
    pygame.draw.circle(s, yc, (cx + int(r * math.cos(math.pi * 1.1)), cy - int(r * math.sin(math.pi * 1.1))), 3)


def _wi_joy_buzzer(s, cx, cy, sz):
    """Electric spiral disc."""
    cc = (0, 255, 255)
    r = sz // 2 - 2
    # Base disc
    pygame.draw.circle(s, (30, 30, 50), (cx, cy), r)
    pygame.draw.circle(s, cc, (cx, cy), r, 2)
    # Spiral (3 arcs radiating out)
    for i in range(3):
        sr = r * (i + 1) // 4
        pygame.draw.arc(s, cc, (cx - sr, cy - sr, sr * 2, sr * 2),
                        i * math.pi * 2 / 3, i * math.pi * 2 / 3 + math.pi, 2)
    # Center zap
    pygame.draw.circle(s, (200, 255, 255), (cx, cy), r // 5)


def _wi_pie_launcher(s, cx, cy, sz):
    """Pie / launcher circle."""
    pc = (255, 200, 150)
    r = sz // 2 - 2
    # Pie base
    pygame.draw.circle(s, pc, (cx, cy), r)
    pygame.draw.circle(s, (220, 160, 100), (cx, cy), r, 2)
    # Pie crust top
    pygame.draw.arc(s, (200, 140, 80), (cx - r + 2, cy - r + 2, (r - 2) * 2, (r - 2) * 2),
                    math.pi * 0.2, math.pi * 0.9, 3)
    # Cream fill
    pygame.draw.circle(s, (255, 240, 220), (cx, cy), r - 5)
    # Slice line
    pygame.draw.line(s, (200, 140, 80), (cx, cy), (cx + r - 2, cy - r // 2), 2)
    pygame.draw.line(s, (200, 140, 80), (cx, cy), (cx, cy - r + 2), 2)


def _wi_confetti_grenade(s, cx, cy, sz):
    """Round grenade with burst top."""
    gc = (255, 100, 200)
    r = sz // 2 - 3
    # Body
    pygame.draw.circle(s, gc, (cx, cy + 3), r)
    pygame.draw.circle(s, (200, 60, 160), (cx, cy + 3), r, 2)
    # Pin / top
    pygame.draw.rect(s, (200, 180, 50), (cx - 1, 2, 3, r - 1))
    # Confetti sparks
    colors = [(255, 255, 50), (50, 255, 200), (255, 150, 0), (200, 100, 255)]
    for i in range(6):
        a = i * math.pi / 3
        ex = cx + int((r + 4) * math.cos(a))
        ey = (cy + 3) + int((r + 4) * math.sin(a))
        pygame.draw.circle(s, colors[i % 4], (ex, ey), 2)


def _wi_jack_in_box(s, cx, cy, sz):
    """Box with spring + head popping out."""
    bc = (255, 50, 100)
    r = sz // 2 - 2
    # Box body
    bx, by, bw, bh = cx - r // 2, cy, r, r
    pygame.draw.rect(s, bc, (bx, by, bw, bh))
    pygame.draw.rect(s, (200, 30, 70), (bx, by, bw, bh), 2)
    # Checkerboard on box
    hw = bw // 2
    pygame.draw.rect(s, (200, 30, 70), (bx, by, hw, bh // 2))
    pygame.draw.rect(s, (200, 30, 70), (bx + hw, by + bh // 2, hw, bh // 2))
    # Spring
    for i in range(3):
        sy1 = cy - 1 - i * 4
        sy2 = sy1 - 2
        pygame.draw.line(s, (200, 200, 200), (cx - 3, sy1), (cx + 3, sy2), 2)
    # Head (circle)
    pygame.draw.circle(s, (255, 220, 150), (cx, cy - 10), r // 3)
    # Jester hat
    pts = [(cx - r // 3, cy - 10 - r // 3),
           (cx, cy - 10 - r * 2 // 3),
           (cx + r // 3, cy - 10 - r // 3)]
    pygame.draw.polygon(s, bc, pts)


def _wi_spud_gun(s, cx, cy, sz):
    """Potato gun — barrel + lumpy potato projectile."""
    r = sz // 2 - 2
    # Barrel (pipe)
    barrel_len = r
    pygame.draw.rect(s, (120, 90, 50), (cx - barrel_len // 2, cy - 3, barrel_len, 6))
    pygame.draw.rect(s, (80, 60, 30), (cx - barrel_len // 2, cy - 3, barrel_len, 6), 1)
    # Stock/handle
    pygame.draw.rect(s, (100, 75, 40), (cx - barrel_len // 2, cy + 3, barrel_len // 2, 5))
    # Potato lump (oval) at muzzle
    potato_x = cx + barrel_len // 2 + 4
    pygame.draw.ellipse(s, (180, 145, 80), (potato_x - 5, cy - 4, 10, 9))
    pygame.draw.ellipse(s, (140, 110, 55), (potato_x - 5, cy - 4, 10, 9), 1)
    # Potato eyes (two tiny dots)
    pygame.draw.circle(s, (100, 70, 30), (potato_x - 1, cy - 1), 1)
    pygame.draw.circle(s, (100, 70, 30), (potato_x + 2, cy + 1), 1)
