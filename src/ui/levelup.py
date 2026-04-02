import pygame
import random
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW, BLACK
from src.systems.weapons import WEAPONS


# Stat upgrades offered at level up (non-weapon)
STAT_UPGRADES = [
    {"name": "+20 Max HP",     "icon": "H", "color": (220, 50, 220),  "effect": "max_hp",  "value": 20},
    {"name": "+5 Damage",      "icon": "D", "color": (255, 80, 60),   "effect": "damage",  "value": 5},
    {"name": "+0.5 Speed",     "icon": "S", "color": (80, 180, 255),  "effect": "speed",   "value": 0.5},
    {"name": "+10 Range",      "icon": "R", "color": (255, 200, 50),  "effect": "range",   "value": 10},
    {"name": "Full Heal",      "icon": "+", "color": (50, 220, 50),   "effect": "heal",    "value": 0},
    {"name": "-50ms Cooldown", "icon": "C", "color": (180, 140, 255), "effect": "cooldown", "value": 50},
]


class LevelUpScreen:
    """Pauses the game and presents 3 random upgrade choices."""

    def __init__(self):
        self.active = False
        self.choices: list[dict] = []
        self.selected = 0
        self.font_big = pygame.font.SysFont("consolas", 32, bold=True)
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 14)

    def activate(self, player_weapon_name: str):
        """Generate 3 random choices: mix of stat upgrades and weapon swaps."""
        self.active = True
        self.selected = 0
        pool = []

        # Add stat upgrades
        stats = random.sample(STAT_UPGRADES, min(4, len(STAT_UPGRADES)))
        for s in stats:
            pool.append({"type": "stat", **s})

        # Add 1-2 weapon options (weapons the player doesn't currently have)
        available_weapons = [k for k in WEAPONS if k != player_weapon_name]
        if available_weapons:
            wpn_picks = random.sample(available_weapons, min(2, len(available_weapons)))
            for wk in wpn_picks:
                w = WEAPONS[wk]
                pool.append({
                    "type": "weapon",
                    "name": w["name"],
                    "icon": "W",
                    "color": w["blade_color"],
                    "effect": "weapon",
                    "value": wk,
                    "desc": w["desc"],
                })

        # Pick 3
        self.choices = random.sample(pool, min(3, len(pool)))

    def handle_event(self, event: pygame.event.Event) -> dict | None:
        """Returns the chosen upgrade dict, or None if still choosing."""
        if not self.active:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_w, pygame.K_UP):
                self.selected = (self.selected - 1) % len(self.choices)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.selected = (self.selected + 1) % len(self.choices)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                choice = self.choices[self.selected]
                self.active = False
                return choice
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                idx = event.key - pygame.K_1
                if 0 <= idx < len(self.choices):
                    choice = self.choices[idx]
                    self.active = False
                    return choice
        return None

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return

        # Darken background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        surface.blit(overlay, (0, 0))

        # Title
        title = self.font_big.render("LEVEL UP — Choose an Upgrade", True, YELLOW)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))

        # Cards
        card_w, card_h = 380, 90
        start_y = 200
        for i, choice in enumerate(self.choices):
            cy = start_y + i * (card_h + 15)
            cx = SCREEN_WIDTH // 2 - card_w // 2

            # Highlight selected
            if i == self.selected:
                pygame.draw.rect(surface, (60, 60, 80), (cx - 4, cy - 4, card_w + 8, card_h + 8), border_radius=8)
                pygame.draw.rect(surface, YELLOW, (cx - 4, cy - 4, card_w + 8, card_h + 8), 2, border_radius=8)

            # Card background
            pygame.draw.rect(surface, (30, 30, 40), (cx, cy, card_w, card_h), border_radius=6)
            pygame.draw.rect(surface, choice.get("color", (150, 150, 150)), (cx, cy, card_w, card_h), 2, border_radius=6)

            # Number
            num = self.font.render(f"[{i + 1}]", True, (120, 120, 120))
            surface.blit(num, (cx + 10, cy + 10))

            # Icon
            icon_color = choice.get("color", WHITE)
            icon = self.font_big.render(choice["icon"], True, icon_color)
            surface.blit(icon, (cx + 50, cy + 15))

            # Name
            name = self.font.render(choice["name"], True, WHITE)
            surface.blit(name, (cx + 95, cy + 15))

            # Description
            desc = choice.get("desc", "")
            if desc:
                desc_surf = self.font_small.render(desc, True, (160, 160, 160))
                surface.blit(desc_surf, (cx + 95, cy + 42))

            # Type tag
            tag = "WEAPON" if choice["type"] == "weapon" else "STAT"
            tag_surf = self.font_small.render(tag, True, (100, 100, 100))
            surface.blit(tag_surf, (cx + card_w - tag_surf.get_width() - 10, cy + 65))

        # Hint
        hint = self.font_small.render("W/S or Up/Down to select  |  Enter/Space or 1-3 to confirm", True, (120, 120, 120))
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, start_y + 3 * (card_h + 15) + 20))
