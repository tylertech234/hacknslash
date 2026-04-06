# -- Display --
# NOTE: SCREEN_WIDTH / SCREEN_HEIGHT are patched by main.py at startup
# to match the user's chosen resolution (default: native desktop).
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
NATIVE_WIDTH = 0   # filled in by main.py
NATIVE_HEIGHT = 0  # filled in by main.py
RESOLUTIONS: dict = {}  # filled in by main.py
FPS = 60
TITLE = "Cyber Survivor"
VERSION = "0.9.11"

# -- User data directory (%APPDATA%/CyberSurvivor on Windows) --
import os as _os

def _resolve_data_dir() -> str:
    if _os.name == "nt":
        # Prefer APPDATA; fall back to LOCALAPPDATA then expanduser so we
        # never silently resolve to a relative path when the env var is unset.
        appdata = (_os.environ.get("APPDATA")
                   or _os.environ.get("LOCALAPPDATA")
                   or _os.path.join(_os.path.expanduser("~"), "AppData", "Roaming"))
        return _os.path.join(appdata, "CyberSurvivor")
    return _os.path.join(_os.path.expanduser("~"), ".cyber_survivor")

DATA_DIR = _resolve_data_dir()
try:
    _os.makedirs(DATA_DIR, exist_ok=True)
except OSError:
    # Fallback: if the preferred location isn't writable (e.g. read-only
    # filesystem or missing permissions) use a writable temp directory so
    # the game can still start; saves won't persist across sessions.
    import tempfile as _tempfile
    DATA_DIR = _os.path.join(_tempfile.gettempdir(), "CyberSurvivor")
    _os.makedirs(DATA_DIR, exist_ok=True)

# -- Colors --
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (220, 20, 60)
GREEN = (34, 139, 34)
BLUE = (30, 144, 255)
YELLOW = (255, 215, 0)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (180, 180, 180)

# -- Passives --
MAX_PASSIVES = 5

# icon letter + color for HUD display  (key → (icon, color))
PASSIVE_INFO = {
    "vampiric_strike":  ("V", (200, 0, 80)),
    "chain_lightning":  ("Z", (100, 200, 255)),
    "thorns":           ("T", (180, 100, 50)),
    "second_wind":      ("L", (255, 100, 100)),
    "nano_regen":       ("N", (100, 255, 100)),
    "berserker":        ("B", (255, 60, 60)),
    "shield_matrix":    ("M", (100, 150, 255)),
    "explosive_kills":  ("E", (255, 150, 0)),
    "magnetic_field":   ("F", (150, 150, 255)),
    "adrenaline":       ("A", (0, 255, 100)),
    # Class built-in passives
    "melee_lifesteal":  ("♥", (255, 80, 80)),
    "armor_plating":    ("■", (120, 180, 255)),
    "crit_shots":       ("!", (255, 200, 50)),
    "evasion":          ("~", (180, 255, 180)),
    "lucky_crits":      ("★", (255, 215, 0)),
    "confetti_burst":   ("✦", (255, 100, 255)),
}

# -- Player --
PLAYER_SPEED = 4
PLAYER_MAX_HP = 100
PLAYER_SIZE = 40
PLAYER_COLOR = BLUE
PLAYER_ATTACK_DAMAGE = 16
PLAYER_ATTACK_RANGE = 60
PLAYER_ATTACK_COOLDOWN = 400        # ms
PLAYER_MAX_SPEED = 9                # hard cap — prevents melee from feeling weightless
PLAYER_MAX_RANGE = 135              # hard cap on attack range
PLAYER_DASH_SPEED = 18
PLAYER_DASH_DURATION = 150          # ms
PLAYER_DASH_COOLDOWN = 1000          # ms

# -- Enemies --
ENEMY_SPEED = 2.8
ENEMY_HP = 130
ENEMY_SIZE = 36
ENEMY_COLOR = RED
ENEMY_DAMAGE = 15
ENEMY_ATTACK_COOLDOWN = 800         # ms
ENEMY_AGGRO_RANGE = 350
ENEMY_ATTACK_RANGE = 45
ENEMY_SHOOT_RANGE = 320             # px – Daleks prefer ranged
ENEMY_SHOOT_COOLDOWN = 1200         # ms
ENEMY_BULLET_SPEED = 4
ENEMY_BULLET_DAMAGE = 10
ENEMY_BULLET_SIZE = 8
ENEMY_BULLET_COLOR = (0, 255, 180)
ENEMY_BODY_COLOR = (120, 110, 100)  # Dalek body grey
ENEMY_DOME_COLOR = (180, 170, 155)  # Dalek dome
ENEMY_EYE_COLOR = (0, 200, 255)     # Dalek eyestalk glow
ENEMY_SKIRT_COLOR = (90, 82, 74)    # Dalek skirt

# -- Spawning --
WAVE_BASE_COUNT = 8
WAVE_GROWTH = 4
SPAWN_MARGIN = 120                  # px from screen edge (larger on bigger map)

# -- XP / Leveling --
XP_PER_KILL = 8
XP_TO_LEVEL = 200                   # doubled — level up half as often
XP_LEVEL_SCALE = 1.4                # multiplier per level

# -- Pickups --
DROP_CHANCE = 0.40                   # 40% chance an enemy drops something
PICKUP_SIZE = 20
PICKUP_LIFETIME = 8000              # ms before despawn
PICKUP_BOB_SPEED = 0.005            # bobbing animation speed

# -- Camera --
CAMERA_LERP = 0.08                  # smoothing factor

# -- Lighting / Darkness --
CAMPFIRE_LIGHT_RADIUS = 250         # px – bright zone around campfire
PLAYER_LIGHT_RADIUS_MAX = 180       # px – starting personal light radius
PLAYER_LIGHT_RADIUS_MIN = 50        # px – minimum light radius
LIGHT_SHRINK_RATE = 0.015           # px lost per frame away from campfire
LIGHT_RESTORE_RATE = 0.6            # px gained per frame near campfire
DARKNESS_GROW_RATE = 0.0002         # darkness per frame away from campfire (0→1)
DARKNESS_DECAY_RATE = 0.003         # darkness lost per frame near campfire

# -- Backend (Supabase) --
# Values are loaded from src/secrets.py (gitignored).
# That file is never committed — fill it in locally.
try:
    from src.secrets import SUPABASE_URL, SUPABASE_ANON_KEY  # type: ignore
except ImportError:
    SUPABASE_URL = ""
    SUPABASE_ANON_KEY = ""
DARKNESS_MAX = 0.65                 # max darkness alpha (0..1) — capped at old 2.3x visual level
XP_DARKNESS_BONUS = 1.54            # at DARKNESS_MAX (0.65) gives exactly 2x XP
ENEMY_DARKNESS_HP_BONUS = 0.6       # extra HP fraction at full darkness
ENEMY_DARKNESS_DMG_BONUS = 1.54     # at DARKNESS_MAX (0.65) gives exactly 2x enemy damage

# -- Map --
TILE_SIZE = 64
MAP_WIDTH = 88                      # tiles  (was 50)
MAP_HEIGHT = 88                     # tiles
FLOOR_COLOR = (34, 60, 28)
WALL_COLOR = (20, 35, 18)

# -- Camera zoom --
# Render world to a smaller surface then scale up so entities look larger.
# 1.0 = no zoom, 1.4 = 40% larger (see fewer world pixels per screen pixel).
CAMERA_ZOOM = 1.40
