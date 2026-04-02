import pygame
import math
import random
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW
from src.systems.weapons import WEAPONS


# Big upgrades that can come from boss chests
CHEST_UPGRADES = [
    # Stat boosts (stronger than level-up versions)
    {"name": "Overclocked Blade",  "icon": "D", "color": (255, 80, 60),   "effect": "damage",   "value": 15},
    {"name": "Extended Reach",     "icon": "R", "color": (255, 200, 50),  "effect": "range",    "value": 20},
    {"name": "Turbo Hands",        "icon": "C", "color": (180, 140, 255), "effect": "cooldown", "value": 100},
    {"name": "Reinforced Chassis", "icon": "H", "color": (220, 50, 220),  "effect": "max_hp",   "value": 60},
    {"name": "Emergency Repair",   "icon": "+", "color": (50, 220, 50),   "effect": "heal",     "value": 0},
    {"name": "Overdrive",          "icon": "S", "color": (80, 180, 255),  "effect": "speed",    "value": 1.0},
    # Powerful passive upgrades
    {"name": "Nano Regen",         "icon": "N", "color": (100, 255, 100), "effect": "passive",  "value": "nano_regen"},
    {"name": "Berserker Core",     "icon": "B", "color": (255, 60, 60),   "effect": "passive",  "value": "berserker"},
    {"name": "Shield Matrix",      "icon": "M", "color": (100, 150, 255), "effect": "passive",  "value": "shield_matrix"},
    {"name": "Vampiric Circuits",  "icon": "V", "color": (200, 0, 80),    "effect": "passive",  "value": "vampiric_strike"},
    {"name": "Chain Lightning",    "icon": "Z", "color": (100, 230, 255), "effect": "passive",  "value": "chain_lightning"},
    {"name": "Second Wind",        "icon": "L", "color": (255, 100, 100), "effect": "passive",  "value": "second_wind"},
    {"name": "Explosive Rounds",   "icon": "E", "color": (255, 150, 0),   "effect": "passive",  "value": "explosive_kills"},
]


class BossChest:
    """A glowing chest dropped by a boss, containing 1-5 upgrades."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.alive = True
        self.spawn_time = pygame.time.get_ticks()
        self.size = 28
        self.opened = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2,
                           self.size, self.size)

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        if not self.alive:
            return
        now = pygame.time.get_ticks()
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        bob = math.sin(now * 0.003) * 4

        # Outer glow
        glow_r = int(20 + 6 * math.sin(now * 0.004))
        glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (255, 200, 50, 40), (glow_r, glow_r), glow_r)
        surface.blit(glow_s, (sx - glow_r, int(sy + bob) - glow_r))

        # Chest body
        half = self.size // 2
        body_rect = pygame.Rect(sx - half, int(sy + bob) - half // 2, self.size, half + 4)
        pygame.draw.rect(surface, (120, 80, 30), body_rect, border_radius=3)
        pygame.draw.rect(surface, (180, 140, 50), body_rect, 2, border_radius=3)

        # Lid
        lid_rect = pygame.Rect(sx - half - 2, int(sy + bob) - half // 2 - 6, self.size + 4, 8)
        pygame.draw.rect(surface, (160, 120, 40), lid_rect, border_radius=2)
        pygame.draw.rect(surface, (200, 160, 60), lid_rect, 1, border_radius=2)

        # Lock/gem
        pygame.draw.circle(surface, (255, 220, 50),
                          (sx, int(sy + bob) - half // 2 + 2), 4)
        pygame.draw.circle(surface, (255, 255, 200),
                          (sx, int(sy + bob) - half // 2 + 2), 2)

        # Sparkles
        for i in range(3):
            angle = now * 0.002 + i * 2.1
            sr = 16 + math.sin(now * 0.005 + i) * 4
            sparkx = sx + int(math.cos(angle) * sr)
            sparky = int(sy + bob) + int(math.sin(angle) * sr)
            ss = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(ss, (255, 255, 200, 160), (2, 2), 2)
            surface.blit(ss, (sparkx - 2, sparky - 2))


class ChestRewardScreen:
    """Shows the upgrades from opening a boss chest."""

    def __init__(self):
        self.active = False
        self.rewards: list[dict] = []
        self.selected = 0
        self.font_big = pygame.font.SysFont("consolas", 28, bold=True)
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 14)
        self.open_time = 0

    def open_chest(self, player_class: str, player_passives: list = None):
        """Generate 3-5 random upgrades from a boss chest."""
        self.active = True
        self.open_time = pygame.time.get_ticks()
        count = random.randint(3, 5)

        owned = set(player_passives or [])
        pool = []
        for u in CHEST_UPGRADES:
            if u["effect"] == "passive" and u["value"] in owned:
                continue
            pool.append(dict(u))

        # Also offer a class-appropriate weapon upgrade
        class_weapons = [k for k, v in WEAPONS.items()
                        if v.get("class") == player_class]
        for wk in class_weapons:
            w = WEAPONS[wk]
            pool.append({
                "name": w["name"],
                "icon": "W",
                "color": w["blade_color"],
                "effect": "weapon",
                "value": wk,
            })

        self.rewards = random.sample(pool, min(count, len(pool)))
        self.selected = 0

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True when player dismisses the screen (after choosing)."""
        if not self.active:
            return False
        if event.type == pygame.KEYDOWN:
            # Number keys to pick a specific reward
            num_keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]
            for i, k in enumerate(num_keys):
                if event.key == k and i < len(self.rewards):
                    self.selected = i
                    self.active = False
                    return True
            # Arrow / WASD navigation
            if event.key in (pygame.K_w, pygame.K_UP):
                self.selected = (self.selected - 1) % len(self.rewards)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.selected = (self.selected + 1) % len(self.rewards)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.active = False
                return True
        return False

    def get_rewards(self) -> list[dict]:
        """Return only the selected reward."""
        if 0 <= self.selected < len(self.rewards):
            return [self.rewards[self.selected]]
        return self.rewards

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return
        now = pygame.time.get_ticks()

        # Darken background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        # Title
        title = self.font_big.render("BOSS CHEST OPENED!", True, (255, 220, 50))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        count_text = self.font.render(f"Choose an upgrade ({len(self.rewards)} available):", True, WHITE)
        surface.blit(count_text, (SCREEN_WIDTH // 2 - count_text.get_width() // 2, 145))

        # Rewards
        card_w, card_h = 380, 60
        start_y = 190
        for i, reward in enumerate(self.rewards):
            cy = start_y + i * (card_h + 10)
            cx = SCREEN_WIDTH // 2 - card_w // 2

            # Reveal animation
            elapsed = now - self.open_time
            reveal_delay = i * 200
            if elapsed < reveal_delay:
                continue

            # Highlight selected
            if i == self.selected:
                pygame.draw.rect(surface, (60, 60, 80), (cx - 4, cy - 4, card_w + 8, card_h + 8), border_radius=8)
                pygame.draw.rect(surface, (255, 215, 0), (cx - 4, cy - 4, card_w + 8, card_h + 8), 2, border_radius=8)

            # Card
            pygame.draw.rect(surface, (25, 25, 35), (cx, cy, card_w, card_h), border_radius=6)
            pygame.draw.rect(surface, reward.get("color", (150, 150, 150)),
                           (cx, cy, card_w, card_h), 2, border_radius=6)

            # Number key
            num = self.font.render(f"[{i + 1}]", True, (120, 120, 120))
            surface.blit(num, (cx + 10, cy + 16))

            # Icon
            icon_color = reward.get("color", WHITE)
            icon = self.font_big.render(reward["icon"], True, icon_color)
            surface.blit(icon, (cx + 50, cy + 10))

            # Name
            name = self.font.render(reward["name"], True, WHITE)
            surface.blit(name, (cx + 90, cy + 16))

            # Type tag
            if reward["effect"] == "weapon":
                tag = "WEAPON"
            elif reward["effect"] == "passive":
                tag = "PASSIVE"
            else:
                tag = "STAT"
            tag_surf = self.font_small.render(tag, True, (100, 100, 100))
            surface.blit(tag_surf, (cx + card_w - tag_surf.get_width() - 10, cy + 22))

        # Hint
        hint = self.font_small.render("W/S or Up/Down to select  |  Enter/Space or 1-5 to confirm", True, (100, 100, 100))
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                           start_y + len(self.rewards) * (card_h + 10) + 30))
