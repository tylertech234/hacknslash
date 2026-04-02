# -- Display --
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Hack 'n Slash"

# -- Colors --
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (220, 20, 60)
GREEN = (34, 139, 34)
BLUE = (30, 144, 255)
YELLOW = (255, 215, 0)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (180, 180, 180)

# -- Player --
PLAYER_SPEED = 4
PLAYER_MAX_HP = 100
PLAYER_SIZE = 40
PLAYER_COLOR = BLUE
PLAYER_ATTACK_DAMAGE = 20
PLAYER_ATTACK_RANGE = 60
PLAYER_ATTACK_COOLDOWN = 400        # ms
PLAYER_DASH_SPEED = 12
PLAYER_DASH_DURATION = 150          # ms
PLAYER_DASH_COOLDOWN = 800          # ms

# -- Enemies --
ENEMY_SPEED = 2
ENEMY_HP = 60
ENEMY_SIZE = 36
ENEMY_COLOR = RED
ENEMY_DAMAGE = 10
ENEMY_ATTACK_COOLDOWN = 1000        # ms
ENEMY_AGGRO_RANGE = 250
ENEMY_ATTACK_RANGE = 45
ENEMY_SHOOT_RANGE = 300             # px – Daleks prefer ranged
ENEMY_SHOOT_COOLDOWN = 1500         # ms
ENEMY_BULLET_SPEED = 4
ENEMY_BULLET_DAMAGE = 8
ENEMY_BULLET_SIZE = 8
ENEMY_BULLET_COLOR = (0, 255, 180)
ENEMY_BODY_COLOR = (120, 110, 100)  # Dalek body grey
ENEMY_DOME_COLOR = (180, 170, 155)  # Dalek dome
ENEMY_EYE_COLOR = (0, 200, 255)     # Dalek eyestalk glow
ENEMY_SKIRT_COLOR = (90, 82, 74)    # Dalek skirt

# -- Spawning --
WAVE_BASE_COUNT = 5
WAVE_GROWTH = 3
SPAWN_MARGIN = 80                   # px from screen edge

# -- XP / Leveling --
XP_PER_KILL = 25
XP_TO_LEVEL = 100
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
DARKNESS_GROW_RATE = 0.0004         # darkness per frame away from campfire (0→1)
DARKNESS_DECAY_RATE = 0.003         # darkness lost per frame near campfire
DARKNESS_MAX = 0.85                 # max darkness alpha (0..1)
XP_DARKNESS_BONUS = 2.0             # max XP multiplier at full darkness
ENEMY_DARKNESS_HP_BONUS = 0.6       # extra HP fraction at full darkness
ENEMY_DARKNESS_DMG_BONUS = 0.5      # extra damage fraction at full darkness

# -- Map --
TILE_SIZE = 64
MAP_WIDTH = 50                      # tiles
MAP_HEIGHT = 50                     # tiles
FLOOR_COLOR = (50, 50, 55)
WALL_COLOR = (90, 85, 80)
