"""
One-shot patch for make_banner.py:
  1. Delete eldritch eye section (section 2)
  2. Delete void rift section (section 3)
  3. Replace jester's dagger with rubber chicken + add big juggling ball
"""
import math

src = open('make_banner.py', encoding='utf-8').read()

# ── 1 & 2.  Remove eye + void rift ────────────────────────────────────────
# Find where section 2 starts (the box-char header line before it) and
# where section 4 starts, then excise everything in between.

# Section 2 begins with the first occurrence of the eye section marker
EYE_START_MARKER   = '# 2.  ELDRITCH EYE in the sky'
# Section 4 begins with its own header comment
SEC4_MARKER        = '# 4.  RETRO GRID FLOOR'

i_eye  = src.find(EYE_START_MARKER)
i_sec4 = src.find(SEC4_MARKER)

if i_eye == -1 or i_sec4 == -1:
    print(f'WARNING: eye={i_eye} sec4={i_sec4} — markers not found, skipping deletion')
else:
    # Walk backwards from EYE_START_MARKER to the newline before it (strip the header box line too)
    # We want to remove from the start of that line all the way up to (not including) the # 4 header line
    sol_eye = src.rfind('\n', 0, i_eye) + 1          # start of the line containing EYE_START_MARKER
    # Walk one more line back to also remove the '# ════...' box header line
    sol_box = src.rfind('\n', 0, sol_eye - 1) + 1    # start of the box-draw line above it

    # Walk backwards from SEC4_MARKER to remove the blank lines in between
    sol_sec4 = src.rfind('\n', 0, i_sec4) + 1        # start of the line containing SEC4_MARKER
    # Also remove the box header of section 4 (it's the line before SEC4_MARKER's line)
    # Actually keep section 4 intact — just cut up to and not including its box header
    # The box header for section 4 precedes SEC4_MARKER line:
    sol_sec4_box = src.rfind('\n', 0, sol_sec4 - 1) + 1  # start of '# ════...' before sec4

    # Excise: from sol_box up to (not including) sol_sec4_box
    src = src[:sol_box] + src[sol_sec4_box:]
    print(f'Eye+rift deleted ({sol_sec4_box - sol_box} chars removed)')

# ── 3.  Replace dagger with rubber chicken + add juggling ball ─────────────
OLD_JESTER = (
    "# left arm down/out\n"
    "pygame.draw.line(surf, (80,20,100), jp(-9,-20), jp(-18,-12), max(2,int(2*js)))\n"
    "# right arm raised, holding dagger\n"
    "pygame.draw.line(surf, (80,20,100), jp(9,-20), jp(18,-32), max(2,int(2*js)))\n"
    "# dagger blade\n"
    "pygame.draw.line(surf, CYAN, jp(18,-32), jp(22,-40), max(1,int(1.5*js)))\n"
    "glow(surf, CYAN, jp(22,-40), 7, steps=3, max_alpha=100)"
)

NEW_JESTER = """\
# left arm down/out holding bright juggling ball
pygame.draw.line(surf, (80,20,100), jp(-9,-20), jp(-18,-12), max(2,int(2*js)))
# JUGGLING BALL — big vivid purple
_jball = jp(-18, -12)
_jbr = max(18, int(12*js*0.5))
pygame.draw.circle(surf, (140, 30, 230), _jball, _jbr)
pygame.draw.circle(surf, (210, 80, 255), _jball, _jbr, 3)
pygame.draw.circle(surf, (230, 180, 255), (_jball[0]-int(_jbr*0.35), _jball[1]-int(_jbr*0.35)), max(3, int(_jbr*0.28)))
glow(surf, (180, 60, 255), _jball, _jbr+10, steps=4, max_alpha=110)
# right arm raised, holding rubber chicken
pygame.draw.line(surf, (80,20,100), jp(9,-20), jp(18,-32), max(2,int(2*js)))
# RUBBER CHICKEN in raised right hand
_ck = jp(22, -40)  # tip of hand
# body — big yellow oval
pygame.draw.ellipse(surf, (255, 200, 30), (_ck[0]-10, _ck[1]-18, 32, 22))
pygame.draw.ellipse(surf, (220, 140, 0), (_ck[0]-10, _ck[1]-18, 32, 22), 2)
# wing bump
pygame.draw.arc(surf, (200, 120, 0), (_ck[0]-2, _ck[1]-10, 22, 14), math.radians(200), math.radians(360), 3)
# neck
pygame.draw.line(surf, (255, 200, 30), (_ck[0]+10, _ck[1]-18), (_ck[0]+14, _ck[1]-32), 5)
# head
pygame.draw.circle(surf, (255, 210, 40), (_ck[0]+16, _ck[1]-34), 11)
pygame.draw.circle(surf, (220, 140, 0), (_ck[0]+16, _ck[1]-34), 11, 2)
# beak
pygame.draw.polygon(surf, (255, 100, 0),
    [(_ck[0]+20, _ck[1]-37), (_ck[0]+28, _ck[1]-34), (_ck[0]+20, _ck[1]-31)])
# wattle
pygame.draw.ellipse(surf, (200, 30, 30), (_ck[0]+21, _ck[1]-31, 6, 9))
# eye dot
pygame.draw.circle(surf, (10, 10, 10), (_ck[0]+13, _ck[1]-37), 2)
# legs dangling
pygame.draw.line(surf, (220, 140, 0), (_ck[0]+4, _ck[1]+4), (_ck[0]+2, _ck[1]+14), 2)
pygame.draw.line(surf, (220, 140, 0), (_ck[0]+10, _ck[1]+4), (_ck[0]+10, _ck[1]+14), 2)
# glow halo
glow(surf, (255, 200, 30), (_ck[0]+8, _ck[1]-12), 22, steps=3, max_alpha=90)\
"""

if OLD_JESTER in src:
    src = src.replace(OLD_JESTER, NEW_JESTER, 1)
    print('Jester chicken+ball replaced OK')
else:
    print('WARNING: jester dagger block not found — check spacing/content')

open('make_banner.py', 'w', encoding='utf-8').write(src)
lines = src.count('\n') + 1
print(f'Saved. Lines: {lines}')
