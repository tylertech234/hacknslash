import pygame
import random
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW, BLACK, MAX_PASSIVES
from src.systems.weapons import WEAPONS
from src.ui.tooltip import Tooltip, calc_weapon_dps, PASSIVE_DETAILS


# Interesting upgrades — a mix of stats, powerful passives, and risky gambles
LEVEL_UPGRADES = [
    # Stat upgrades
    {"name": "Iron Skin",       "icon": "H", "color": (180, 180, 200), "effect": "max_hp",       "value": 25,  "desc": "+25 Max HP and instant heal"},
    {"name": "Power Surge",     "icon": "D", "color": (255, 80, 60),   "effect": "damage",       "value": 8,   "desc": "+8 base damage"},
    {"name": "Quick Trigger",   "icon": "C", "color": (180, 140, 255), "effect": "cooldown",     "value": 60,  "desc": "-60ms attack cooldown"},
    {"name": "Full Repair",     "icon": "+", "color": (50, 220, 50),   "effect": "heal",         "value": 0,   "desc": "Restore all HP"},
    {"name": "Leg Servos",      "icon": "S", "color": (80, 180, 255),  "effect": "speed",        "value": 0.5, "desc": "+0.5 movement speed"},
    # Risky / high-impact
    {"name": "Glass Cannon",    "icon": "G", "color": (255, 50, 50),   "effect": "glass_cannon", "value": 0,   "desc": "+30% damage but lose 20 Max HP"},
    # Passive abilities
    {"name": "Vampiric Strike", "icon": "V", "color": (200, 0, 80),    "effect": "passive", "value": "vampiric_strike", "desc": "Heal 3 HP on each hit"},
    {"name": "Chain Lightning", "icon": "Z", "color": (100, 200, 255), "effect": "passive", "value": "chain_lightning", "desc": "Hits arc to 2 nearby enemies"},
    {"name": "Thorns",          "icon": "T", "color": (180, 100, 50),  "effect": "passive", "value": "thorns",          "desc": "Reflect 30% melee damage taken"},
    {"name": "Second Wind",     "icon": "L", "color": (255, 100, 100), "effect": "passive", "value": "second_wind",     "desc": "Revive once at 30% HP on death"},
    {"name": "Nano Regen",      "icon": "N", "color": (100, 255, 100), "effect": "passive", "value": "nano_regen",      "desc": "Regenerate 1 HP every 2 seconds"},
    {"name": "Berserker",       "icon": "B", "color": (255, 60, 60),   "effect": "passive", "value": "berserker",       "desc": "+50% damage when below 30% HP"},
    {"name": "Shield Matrix",   "icon": "M", "color": (100, 150, 255), "effect": "passive", "value": "shield_matrix",   "desc": "Block one hit every 10 seconds"},
    {"name": "Explosive Kills", "icon": "E", "color": (255, 150, 0),   "effect": "passive", "value": "explosive_kills", "desc": "25% chance for enemies to explode on death"},
    {"name": "Magnetic Field",  "icon": "F", "color": (150, 150, 255), "effect": "passive", "value": "magnetic_field",  "desc": "Pickups fly to you from further away"},
    {"name": "Adrenaline Rush", "icon": "A", "color": (0, 255, 100),   "effect": "passive", "value": "adrenaline",      "desc": "+30% speed for 3s after each kill"},
]


# Weapon-specific upgrades — only offered when the player has the matching weapon
WEAPON_UPGRADES = {
    # Knight weapons
    "sword":          {"name": "Flame Slash",      "icon": "🗡", "color": (255, 120, 30),  "effect": "damage",   "value": 12, "desc": "+12 damage with fire sword strikes"},
    "axe":            {"name": "Cleaving Arc",     "icon": "🪓", "color": (200, 80, 50),   "effect": "range",    "value": 15, "desc": "+15 attack range — wider axe arc"},
    "spear":          {"name": "Piercing Thrust",  "icon": "⟶", "color": (140, 200, 255), "effect": "damage",   "value": 10, "desc": "+10 damage — spear pierces deeper"},
    "hammer":         {"name": "Shockwave",        "icon": "⚡", "color": (255, 220, 50),  "effect": "damage",   "value": 14, "desc": "+14 damage — hammer shockwave"},
    "plasma_blade":   {"name": "Plasma Overcharge","icon": "⚡", "color": (0, 255, 200),   "effect": "cooldown", "value": 80, "desc": "-80ms cooldown — rapid plasma cuts"},
    "gravity_maul":   {"name": "Gravity Well",     "icon": "◉", "color": (150, 0, 255),   "effect": "damage",   "value": 16, "desc": "+16 damage — gravity crush"},
    "blade_barrier":  {"name": "Razor Vortex",     "icon": "✦", "color": (255, 100, 100), "effect": "range",    "value": 20, "desc": "+20 range — spinning blade reach"},
    "shield_bash":    {"name": "Fortified Bash",   "icon": "■", "color": (100, 160, 255), "effect": "max_hp",   "value": 30, "desc": "+30 Max HP — shield reinforcement"},
    # Archer weapons
    "dagger":         {"name": "Poison Tips",      "icon": "☠", "color": (80, 220, 80),   "effect": "damage",   "value": 8,  "desc": "+8 damage — venomous strikes"},
    "cyber_bow":      {"name": "Rapid Volley",     "icon": "➤", "color": (100, 200, 255), "effect": "cooldown", "value": 70, "desc": "-70ms cooldown — faster arrows"},
    "pulse_rifle":    {"name": "Overcharged Pulse", "icon": "⚡", "color": (255, 80, 200),  "effect": "damage",   "value": 10, "desc": "+10 damage — supercharged pulses"},
    "scatter_shot":   {"name": "Wide Scatter",     "icon": "✧", "color": (255, 200, 100), "effect": "range",    "value": 15, "desc": "+15 range — wider scatter pattern"},
    "ricochet_disc":  {"name": "Multi-Bounce",     "icon": "◎", "color": (255, 160, 0),   "effect": "damage",   "value": 10, "desc": "+10 damage — extra ricochet hits"},
    # Jester weapons
    "rubber_chicken": {"name": "Extra Bouncy",     "icon": "🐔", "color": (255, 220, 50),  "effect": "damage",   "value": 10, "desc": "+10 damage — bouncier chicken"},
    "banana_rang":    {"name": "Banana Split",     "icon": "🍌", "color": (255, 255, 80),  "effect": "range",    "value": 15, "desc": "+15 range — wider banana arc"},
    "joy_buzzer":     {"name": "Megavolt Buzz",    "icon": "⚡", "color": (255, 255, 0),   "effect": "cooldown", "value": 80, "desc": "-80ms cooldown — rapid buzzing"},
    "pie_launcher":   {"name": "Cream Explosion",  "icon": "◉", "color": (255, 180, 200), "effect": "damage",   "value": 12, "desc": "+12 damage — bigger pie splash"},
    "confetti_grenade":{"name": "Party Bomb",      "icon": "✦", "color": (255, 100, 255), "effect": "damage",   "value": 14, "desc": "+14 damage — extra confetti boom"},
    "jack_in_box":    {"name": "Spring Loaded",    "icon": "★", "color": (200, 80, 255),  "effect": "cooldown", "value": 70, "desc": "-70ms cooldown — faster spring"},
}


class LevelUpScreen:
    """Pauses the game and presents 3 random upgrade choices."""

    def __init__(self):
        self.active = False
        self.choices: list[dict] = []
        self.selected = 0
        self.font_big = pygame.font.SysFont("consolas", 32, bold=True)
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 14)
        self._tooltip = Tooltip()

    def activate(self, player_weapon_name: str, player_class: str = "knight",
                 player_passives: list = None, base_damage: int = 20,
                 current_weapon: dict = None, upgrade_tiers: dict = None):
        """Generate 3 random choices: mix of stat upgrades, passives, and weapon swaps."""
        self.active = True
        self.selected = 0
        self._base_damage = base_damage
        self._current_weapon = current_weapon
        owned = set(player_passives or [])
        slot_passives = [k for k in (player_passives or []) if k != "glass_cannon"]
        self._passives_full = len(slot_passives) >= MAX_PASSIVES
        tiers = upgrade_tiers or {}
        pool = []

        TIER_NAMES = {1: "I", 2: "II", 3: "III"}

        # Add stat + passive upgrades (filter out already-owned passives and maxed tiers)
        for u in LEVEL_UPGRADES:
            if u["effect"] == "passive" and u["value"] in owned:
                continue
            if u["effect"] == "glass_cannon" and "glass_cannon" in owned:
                continue
            if u["effect"] == "passive":
                pool.append({"type": "stat", **u})
                continue
            # Stat upgrades can be taken up to tier 3
            current_tier = tiers.get(u["name"], 0)
            if current_tier >= 3:
                continue
            next_tier = current_tier + 1
            tier_mult = {1: 1.0, 2: 1.5, 3: 2.0}[next_tier]
            tier_label = TIER_NAMES[next_tier]
            entry = dict(u)
            entry["type"] = "stat"
            entry["tier"] = next_tier
            if next_tier > 1:
                entry["name"] = f"{u['name']} {tier_label}"
                scaled_val = u["value"]
                if isinstance(scaled_val, (int, float)) and scaled_val != 0:
                    scaled_val = type(scaled_val)(scaled_val * tier_mult)
                entry["value"] = scaled_val
                entry["desc"] = f"[Tier {tier_label}] {u['desc']}"
            entry["base_name"] = u["name"]
            pool.append(entry)

        # Add weapon-specific upgrade for current weapon (if available and not already taken)
        if player_weapon_name in WEAPON_UPGRADES:
            wu = WEAPON_UPGRADES[player_weapon_name]
            wu_name = wu["name"]
            current_tier = tiers.get(wu_name, 0)
            if current_tier < 3:
                next_tier = current_tier + 1
                tier_mult = {1: 1.0, 2: 1.5, 3: 2.0}[next_tier]
                entry = dict(wu)
                entry["type"] = "weapon_upgrade"
                entry["tier"] = next_tier
                entry["base_name"] = wu_name
                if next_tier > 1:
                    tier_label = {1: "I", 2: "II", 3: "III"}[next_tier]
                    entry["name"] = f"{wu_name} {tier_label}"
                    scaled_val = wu["value"]
                    if isinstance(scaled_val, (int, float)) and scaled_val != 0:
                        scaled_val = type(scaled_val)(scaled_val * tier_mult)
                    entry["value"] = scaled_val
                    entry["desc"] = f"[Tier {tier_label}] {wu['desc']}"
                pool.append(entry)

        # Add 1-2 weapon options (class-appropriate weapons the player doesn't currently have)
        available_weapons = [k for k in WEAPONS
                           if k != player_weapon_name
                           and WEAPONS[k].get("class") == player_class]
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

        # Mouse hover - update selection based on card positions
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            card_w, card_h = 380, 90
            start_y = 200
            cx = SCREEN_WIDTH // 2 - card_w // 2
            for i in range(len(self.choices)):
                cy = start_y + i * (card_h + 15)
                if cx <= mx <= cx + card_w and cy <= my <= cy + card_h:
                    self.selected = i
                    break
            return None

        # Mouse click - select card
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            card_w, card_h = 380, 90
            start_y = 200
            cx_card = SCREEN_WIDTH // 2 - card_w // 2
            for i in range(len(self.choices)):
                cy = start_y + i * (card_h + 15)
                if cx_card <= mx <= cx_card + card_w and cy <= my <= cy + card_h:
                    choice = self.choices[i]
                    self.active = False
                    return choice
            return None

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_w, pygame.K_UP):
                self.selected = (self.selected - 1) % len(self.choices)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.selected = (self.selected + 1) % len(self.choices)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
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
            ctype = choice.get("type", "stat")
            tier = choice.get("tier", 0)
            if ctype == "weapon":
                tag = "WEAPON"
            elif ctype == "weapon_upgrade":
                tag = "WEAPON UPGRADE"
            elif tier > 1:
                tag = f"TIER {tier}"
            else:
                tag = "STAT"
            tag_surf = self.font_small.render(tag, True, (100, 100, 100))
            surface.blit(tag_surf, (cx + card_w - tag_surf.get_width() - 10, cy + 65))

            # Passives full warning on passive choices
            if self._passives_full and choice.get("effect") == "passive":
                warn_color = (255, 180, 50)
                warn_text = self.font_small.render("\u26a0 SLOTS FULL — SWAP", True, warn_color)
                wx = cx + 95
                wy = cy + 62
                pygame.draw.rect(surface, (60, 40, 10), (wx - 3, wy - 1, warn_text.get_width() + 6, warn_text.get_height() + 2), border_radius=3)
                surface.blit(warn_text, (wx, wy))

        # Hint
        hint = self.font_small.render("W/S or Mouse to select  |  Enter/Click or 1-3 to confirm", True, (120, 120, 120))
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, start_y + 3 * (card_h + 15) + 20))

        # Tooltip for selected upgrade
        if 0 <= self.selected < len(self.choices):
            choice = self.choices[self.selected]
            tip_x = SCREEN_WIDTH // 2 + card_w // 2 + 12
            tip_y = start_y + self.selected * (card_h + 15)
            if choice.get("effect") == "weapon":
                wkey = choice.get("value", "")
                from src.systems.weapons import WEAPONS as _W
                wpn = _W.get(wkey, {})
                if wpn:
                    self._tooltip.draw_weapon_tooltip(
                        surface, tip_x, tip_y, wpn,
                        self._base_damage, self._current_weapon)
            elif choice.get("effect") == "passive":
                pkey = choice.get("value", "")
                self._tooltip.draw_passive_tooltip(surface, tip_x, tip_y, pkey)
            elif choice.get("type") == "weapon_upgrade":
                self._tooltip.draw_stat_tooltip(
                    surface, tip_x, tip_y,
                    choice.get("name", ""),
                    choice.get("desc", ""),
                    f"Weapon: {self._current_weapon.get('name', '?') if self._current_weapon else '?'}")
            else:
                self._tooltip.draw_stat_tooltip(
                    surface, tip_x, tip_y,
                    choice.get("name", ""),
                    choice.get("desc", ""),
                    f"Value: {choice.get('value', '')}") 
