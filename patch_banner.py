"""One-shot patch for make_banner.py — applies all requested changes."""
import re, pathlib

f = pathlib.Path('make_banner.py')
txt = f.read_text(encoding='utf-8')

# ─────────────────────────────────────────────────────────────────
# 1. Delete ELDRITCH EYE section (section 2)
# ─────────────────────────────────────────────────────────────────
txt = re.sub(
    r'# ={78}\n# 2\.  ELDRITCH EYE.*?(?=# ={78}\n# 3\.  VOID RIFT)',
    '', txt, flags=re.DOTALL
)

# ─────────────────────────────────────────────────────────────────
# 2. Delete VOID RIFT section (section 3)
# ─────────────────────────────────────────────────────────────────
txt = re.sub(
    r'# ={78}\n# 3\.  VOID RIFT.*?(?=# ={78}\n# 4\.  RETRO GRID)',
    '', txt, flags=re.DOTALL
)

# ─────────────────────────────────────────────────────────────────
# 3. Make Jester ball BIGGER and BRIGHTER
# ─────────────────────────────────────────────────────────────────
txt = txt.replace(
    'ball_r  = max(9, int(7 * js * 0.5))',
    'ball_r  = max(20, int(14 * js * 0.5))'
)
# Brighten the ball colours
txt = txt.replace(
    'pygame.draw.circle(surf, (60, 20, 100),  (ball_cx, ball_cy), ball_r)',
    'pygame.draw.circle(surf, (100, 30, 170), (ball_cx, ball_cy), ball_r)'
)
txt = txt.replace(
    'pygame.draw.circle(surf, (100, 40, 160), (ball_cx, ball_cy), ball_r, 2)',
    'pygame.draw.circle(surf, (200, 80, 255), (ball_cx, ball_cy), ball_r, 3)'
)
# Bigger highlight
txt = txt.replace(
    'pygame.draw.circle(surf, (140, 60, 200),\n    (ball_cx - max(1, int(js*0.6)), ball_cy - max(1, int(js*0.6))),\n    max(1, int(js * 0.45)))',
    'pygame.draw.circle(surf, (220, 150, 255),\n    (ball_cx - max(2, int(js*1.2)), ball_cy - max(2, int(js*1.2))),\n    max(3, int(js * 0.9)))'
)

# ─────────────────────────────────────────────────────────────────
# 4. Replace rubber chicken with a BIG, obvious one
# ─────────────────────────────────────────────────────────────────
chicken_new = r"""# ──── RUBBER CHICKEN — large and unmistakable ────────────────
ck_x, ck_y = jp(14, -38)   # grip point (end of raised arm)
# golden halo behind chicken
glow(surf, (255, 230, 60), (ck_x + 22, ck_y - 18), 38, steps=5, max_alpha=75)
# body — big yellow oval
pygame.draw.ellipse(surf, (255, 200, 10), (ck_x - 4, ck_y - 8, 46, 28))
pygame.draw.ellipse(surf, (20,  10, 30),  (ck_x - 4, ck_y - 8, 46, 28), 3)
# wing dip arc
pygame.draw.arc(surf, (210, 155, 10),
    (ck_x + 4, ck_y + 4, 26, 16),
    math.radians(185), math.radians(355), 3)
# neck
pygame.draw.line(surf, (255, 200, 10), (ck_x + 40, ck_y - 6), (ck_x + 52, ck_y - 24), 8)
# head — round yellow
pygame.draw.circle(surf, (255, 200, 10), (ck_x + 60, ck_y - 32), 16)
pygame.draw.circle(surf, (20,  10, 30),  (ck_x + 60, ck_y - 32), 16, 2)
# eye
pygame.draw.circle(surf, WHITE,         (ck_x + 67, ck_y - 39), 6)
pygame.draw.circle(surf, (10, 10, 10),  (ck_x + 69, ck_y - 39), 3)
# beak — wide orange triangle pointing right
pygame.draw.polygon(surf, (240, 90,  0), [
    (ck_x + 74, ck_y - 32),
    (ck_x + 90, ck_y - 27),
    (ck_x + 74, ck_y - 22),
])
pygame.draw.line(surf, (170, 50, 0), (ck_x + 74, ck_y - 27), (ck_x + 88, ck_y - 27), 2)
# wattle — red blob
pygame.draw.ellipse(surf, (215, 25, 25), (ck_x + 72, ck_y - 24, 10, 18))
# legs — two yellow twigs
for _lo in (-5, 5):
    pygame.draw.line(surf, (220, 160, 10),
        (ck_x + 20 + _lo, ck_y + 20), (ck_x + 20 + _lo, ck_y + 34), 3)
    pygame.draw.line(surf, (220, 160, 10),
        (ck_x + 20 + _lo, ck_y + 34), (ck_x + 28 + _lo, ck_y + 34), 3)
"""

# Find and replace the old chicken block
old_chicken_pat = re.compile(
    r'# RUBBER CHICKEN in raised right hand.*?glow\(surf, \(255, 220, 30\).*?\)\n',
    re.DOTALL
)
if old_chicken_pat.search(txt):
    txt = old_chicken_pat.sub(chicken_new, txt)
    print("Chicken replaced (pattern 1)")
else:
    # Try alternate end marker
    old_chicken_pat2 = re.compile(
        r'# RUBBER CHICKEN.*?(?=\n# head \(magenta like game\))',
        re.DOTALL
    )
    if old_chicken_pat2.search(txt):
        txt = old_chicken_pat2.sub(chicken_new.rstrip(), txt)
        print("Chicken replaced (pattern 2)")
    else:
        print("WARNING: chicken pattern not found")

# ─────────────────────────────────────────────────────────────────
# 5. Tagline — add readable background box
# ─────────────────────────────────────────────────────────────────
old_tagline = '''# tagline
tagline = "Survive the void. Level up. Conquer the Abyss."
tl_surf = sub_font.render(tagline, True, (180, 175, 210))
tl_rect = tl_surf.get_rect(center=(W//2, title_y + 52))
# clamp if too wide
if tl_surf.get_width() > W - MARGIN*2:
    sub_font2 = get_font(sub_font_names, 17, bold=False)
    tl_surf   = sub_font2.render(tagline, True, (180, 175, 210))
    tl_rect   = tl_surf.get_rect(center=(W//2, title_y + 52))
surf.blit(tl_surf, tl_rect)'''

new_tagline = '''# tagline with dark backing for readability
tagline = "Survive the void. Level up. Conquer the Abyss."
tl_surf = sub_font.render(tagline, True, (215, 215, 245))
tl_rect = tl_surf.get_rect(center=(W//2, title_y + 52))
if tl_surf.get_width() > W - MARGIN*2:
    sub_font2 = get_font(sub_font_names, 17, bold=False)
    tl_surf   = sub_font2.render(tagline, True, (215, 215, 245))
    tl_rect   = tl_surf.get_rect(center=(W//2, title_y + 52))
_tl_pad = 12
_tl_bg  = pygame.Surface((tl_rect.width + _tl_pad*2, tl_rect.height + 10), pygame.SRCALPHA)
pygame.draw.rect(_tl_bg, (0, 0, 25, 195), (0, 0, _tl_bg.get_width(), _tl_bg.get_height()), border_radius=5)
pygame.draw.rect(_tl_bg, (0, 150, 190, 130), (0, 0, _tl_bg.get_width(), _tl_bg.get_height()), 1, border_radius=5)
surf.blit(_tl_bg, (tl_rect.x - _tl_pad, tl_rect.y - 5))
surf.blit(tl_surf, tl_rect)'''

if old_tagline in txt:
    txt = txt.replace(old_tagline, new_tagline)
    print("Tagline replaced")
else:
    print("WARNING: tagline pattern not found — check whitespace")

# ─────────────────────────────────────────────────────────────────
# 6. Replace centered EARLY ACCESS badge with diagonal corner ribbon
# ─────────────────────────────────────────────────────────────────
old_badge = '''# Early access badge
badge_text  = "EARLY ACCESS  v0.9.2"
badge_surf2 = tag_font.render(badge_text, True, ORANGE)
badge_rect2 = badge_surf2.get_rect(center=(W//2, title_y + 80))
bg_rect2    = badge_rect2.inflate(22, 10)
pygame.draw.rect(surf, (40, 18, 0), bg_rect2, border_radius=5)
pygame.draw.rect(surf, ORANGE, bg_rect2, 2, border_radius=5)
surf.blit(badge_surf2, badge_rect2)'''

new_badge = '''# EARLY ACCESS — diagonal corner ribbon, bottom-right
_rib_reach = 115            # reach along edge from corner
_rib_w     = 48             # ribbon band width
_rib_pts   = [
    (W - _rib_reach,           H),
    (W,                        H - _rib_reach),
    (W,                        H - _rib_reach + _rib_w),
    (W - _rib_reach + _rib_w,  H),
]
_rib_overlay = pygame.Surface((W, H), pygame.SRCALPHA)
pygame.draw.polygon(_rib_overlay, (195, 85, 0, 235), _rib_pts)
pygame.draw.polygon(_rib_overlay, (255, 165, 0, 200), _rib_pts, 2)
surf.blit(_rib_overlay, (0, 0))
_rib_tfont = get_font(tag_font_names, 14, bold=True)
_rib_tsurf = _rib_tfont.render("EARLY ACCESS", True, (255, 255, 255))
_rib_trot  = pygame.transform.rotate(_rib_tsurf, 45)
_rib_cx    = W - _rib_reach // 2 + _rib_w // 4
_rib_cy    = H - _rib_reach // 2 + _rib_w // 4
surf.blit(_rib_trot, _rib_trot.get_rect(center=(_rib_cx, _rib_cy)))'''

if old_badge in txt:
    txt = txt.replace(old_badge, new_badge)
    print("Badge replaced")
else:
    print("WARNING: badge pattern not found")

f.write_text(txt, encoding='utf-8')
print(f"Saved. Lines: {len(txt.splitlines())}")
