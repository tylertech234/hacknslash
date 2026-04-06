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
    {"name": "Vampiric Strike", "icon": "V", "color": (200, 0, 80),    "effect": "passive", "value": "vampiric_strike", "desc": "Heal 4 HP on each hit"},
    {"name": "Chain Lightning", "icon": "Z", "color": (100, 200, 255), "effect": "passive", "value": "chain_lightning", "desc": "Hits arc to 2 nearby enemies"},
    {"name": "Thorns",          "icon": "T", "color": (180, 100, 50),  "effect": "passive", "value": "thorns",          "desc": "Reflect 75% melee damage taken back at attacker"},
    {"name": "Second Wind",     "icon": "L", "color": (255, 100, 100), "effect": "passive", "value": "second_wind",     "desc": "Revive once at 30% HP on death"},
    {"name": "Nano Regen",      "icon": "N", "color": (100, 255, 100), "effect": "passive", "value": "nano_regen",      "desc": "Regenerate 1 HP every 2 seconds"},
    {"name": "Berserker",       "icon": "B", "color": (255, 60, 60),   "effect": "passive", "value": "berserker",       "desc": "+50% damage when below 30% HP"},
    {"name": "Shield Matrix",   "icon": "M", "color": (100, 150, 255), "effect": "passive", "value": "shield_matrix",   "desc": "Block one hit every 10 seconds"},
    {"name": "Explosive Kills", "icon": "E", "color": (255, 150, 0),   "effect": "passive", "value": "explosive_kills", "desc": "25% chance for enemies to explode on death"},
    {"name": "Magnetic Field",  "icon": "F", "color": (150, 150, 255), "effect": "passive", "value": "magnetic_field",  "desc": "ALL pickups fly to you from much further away"},
    {"name": "Adrenaline Rush", "icon": "A", "color": (0, 255, 100),   "effect": "passive", "value": "adrenaline",      "desc": "+30% speed for 3s after each kill"},
    {"name": "Rapid Dash",      "icon": ">", "color": (100, 220, 255), "effect": "dash_charges", "value": 1, "desc": "+1 dash charge before cooldown (max 4 total)"},
    {"name": "Armor Plating",   "icon": "M", "color": (120, 180, 255), "effect": "passive", "value": "armor_plating",   "desc": "Take 15% less damage from all sources"},
    {"name": "Critical Shots",   "icon": "!", "color": (255, 200, 50),  "effect": "passive", "value": "crit_shots",     "class_restrict": ["archer", "jester"], "desc": "20% chance for double damage on projectiles. Not available to Knight."},
    {"name": "Melee Lifesteal",   "icon": "K", "color": (255, 80, 80),   "effect": "passive", "value": "melee_lifesteal", "class_restrict": ["knight", "jester"], "desc": "Heal 2 HP on melee kills. Not available to Ranger."},
    {"name": "Confetti Burst",   "icon": "E", "color": (255, 100, 255), "effect": "passive", "value": "confetti_burst", "class_restrict": "jester", "desc": "Kills have 20% chance to stun nearby enemies"},
    {"name": "Parry Deflect",   "icon": "P", "color": (200, 255, 180), "effect": "passive", "value": "parry_deflect", "class_restrict": "knight", "desc": "Parried bullets fire back at nearest enemy (2x damage). Knight only."},
]


# Weapon-specific upgrades — offered when the player has the matching weapon (or it's in arsenal).
# Each weapon has a LIST so players get 2 different upgrade types per weapon.
# Generic upgrades (damage, range, cooldown) persist across weapon swaps — they buff the player, not the weapon.
WEAPON_UPGRADES: dict[str, list[dict]] = {
    # Knight weapons
    "sword": [
        {"name": "Flame Slash",    "icon": "D", "color": (255, 120, 30),  "effect": "damage",   "value": 12, "desc": "+12 damage — burning sword strikes"},
        {"name": "Strike Tempo",   "icon": "C", "color": (255, 180, 80),  "effect": "cooldown", "value": 70, "desc": "-70ms cooldown — faster swing rhythm"},
    ],
    "battle_axe": [
        {"name": "Cleaving Arc",   "icon": "R", "color": (200, 80, 50),   "effect": "range",    "value": 18, "desc": "+18 range — wider axe arc"},
        {"name": "Executioner",    "icon": "D", "color": (220, 60, 40),   "effect": "damage",   "value": 14, "desc": "+14 damage — decapitating blow"},
    ],
    "flail": [
        {"name": "Chain Momentum", "icon": "D", "color": (220, 190, 90),  "effect": "damage",   "value": 12, "desc": "+12 damage — spiked ball gathers momentum"},
        {"name": "Whip Extension", "icon": "R", "color": (200, 175, 120), "effect": "range",    "value": 16, "desc": "+16 range — longer chain, wider arc"},
    ],

    "plasma_blade": [
        {"name": "Plasma Overcharge","icon":"C", "color": (0, 255, 200),  "effect": "cooldown", "value": 80, "desc": "-80ms cooldown — rapid plasma cuts"},
        {"name": "Thermal Edge",   "icon": "D", "color": (0, 200, 255),   "effect": "damage",   "value": 12, "desc": "+12 damage — superheated edge"},
    ],
    "gravity_maul": [
        {"name": "Gravity Well",   "icon": "D", "color": (150, 0, 255),   "effect": "damage",   "value": 18, "desc": "+18 damage — gravity crush"},
        {"name": "Null Field",     "icon": "R", "color": (180, 60, 255),  "effect": "range",    "value": 22, "desc": "+22 range — warp field expands"},
    ],
    "blade_barrier": [
        {"name": "Razor Vortex",   "icon": "R", "color": (255, 100, 100), "effect": "range",    "value": 20, "desc": "+20 range — spinning blade reach"},
        {"name": "Barrier Storm",  "icon": "C", "color": (255, 80, 80),   "effect": "cooldown", "value": 65, "desc": "-65ms cooldown — faster orbit cycle"},
    ],
    "shield_bash": [
        {"name": "Fortified Bash", "icon": "H", "color": (100, 160, 255), "effect": "max_hp",   "value": 35, "desc": "+35 Max HP — shield reinforcement"},
        {"name": "Counter Strike", "icon": "D", "color": (80, 140, 255),  "effect": "damage",   "value": 10, "desc": "+10 damage — retaliatory bash"},
    ],
    # Archer weapons
    "dagger": [
        {"name": "Poison Tips",    "icon": "D", "color": (80, 220, 80),   "effect": "damage",   "value": 9,  "desc": "+9 damage — venomous strikes"},
        {"name": "Rapid Release",  "icon": "C", "color": (60, 200, 60),   "effect": "cooldown", "value": 65, "desc": "-65ms cooldown — faster throw cycle"},
    ],
    "cyber_bow": [
        {"name": "Rapid Volley",   "icon": "C", "color": (100, 200, 255), "effect": "cooldown", "value": 70, "desc": "-70ms cooldown — faster draw"},
        {"name": "Piercing Light", "icon": "D", "color": (80, 220, 255),  "effect": "damage",   "value": 12, "desc": "+12 damage — laser-sharp arrow"},
    ],
    "pulse_rifle": [
        {"name": "Overcharged Pulse","icon":"D","color": (255, 80, 200),  "effect": "damage",   "value": 10, "desc": "+10 damage — supercharged pulses"},
        {"name": "Heat Sink",      "icon": "C", "color": (200, 50, 180),  "effect": "cooldown", "value": 50, "desc": "-50ms cooldown — improved cooling"},
    ],
    "scatter_shot": [
        {"name": "Wide Scatter",   "icon": "R", "color": (255, 200, 100), "effect": "range",    "value": 18, "desc": "+18 range — wider spread"},
        {"name": "Pellet Storm",   "icon": "D", "color": (220, 170, 80),  "effect": "damage",   "value": 8,  "desc": "+8 damage — heavier pellets"},
    ],
    "ricochet_disc": [
        {"name": "Multi-Bounce",   "icon": "D", "color": (255, 160, 0),   "effect": "damage",   "value": 11, "desc": "+11 damage — extra ricochet hits"},
        {"name": "Gyro Spin",      "icon": "C", "color": (220, 140, 0),   "effect": "cooldown", "value": 70, "desc": "-70ms cooldown — faster disc cycle"},
    ],
    "explosive_crossbow": [
        {"name": "Warhead Tips",   "icon": "D", "color": (255, 120, 30),  "effect": "damage",   "value": 14, "desc": "+14 damage — bigger detonation"},
        {"name": "Short Fuse",     "icon": "C", "color": (220, 100, 20),  "effect": "cooldown", "value": 70, "desc": "-70ms cooldown — primed and ready"},
    ],
    "burst_crossbow": [
        {"name": "Rapid Chamber",  "icon": "C", "color": (100, 220, 255), "effect": "cooldown", "value": 70, "desc": "-70ms cooldown — faster burst cycle"},
        {"name": "Burst Cluster",  "icon": "D", "color": (80, 200, 255),  "effect": "damage",   "value": 10, "desc": "+10 damage — tighter burst cluster"},
    ],
    # Jester weapons
    "rubber_chicken": [
        {"name": "Extra Bouncy",   "icon": "D", "color": (255, 220, 50),  "effect": "damage",   "value": 10, "desc": "+10 damage — bouncier chicken"},
        {"name": "Turbo Cluck",    "icon": "C", "color": (220, 200, 40),  "effect": "cooldown", "value": 70, "desc": "-70ms cooldown — rapid clucking"},
    ],
    "banana_rang": [
        {"name": "Banana Split",   "icon": "R", "color": (255, 255, 80),  "effect": "range",    "value": 18, "desc": "+18 range — wider banana arc"},
        {"name": "Peel Out",       "icon": "C", "color": (220, 220, 60),  "effect": "cooldown", "value": 70, "desc": "-70ms cooldown — faster peel cycle"},
    ],
    "joy_buzzer": [
        {"name": "Megavolt Buzz",  "icon": "C", "color": (255, 255, 0),   "effect": "cooldown", "value": 80, "desc": "-80ms cooldown — rapid buzzing"},
        {"name": "Chain Shock",    "icon": "D", "color": (220, 220, 0),   "effect": "damage",   "value": 11, "desc": "+11 damage — arcing shock damage"},
    ],
    "pie_launcher": [
        {"name": "Cream Explosion","icon": "D", "color": (255, 180, 200), "effect": "damage",   "value": 13, "desc": "+13 damage — bigger pie splash"},
        {"name": "Rapid Reload",   "icon": "C", "color": (220, 150, 180), "effect": "cooldown", "value": 75, "desc": "-75ms cooldown — pre-loaded pies"},
    ],
    "confetti_grenade": [
        {"name": "Party Bomb",     "icon": "D", "color": (255, 100, 255), "effect": "damage",   "value": 14, "desc": "+14 damage — explosive confetti boom"},
        {"name": "Rapid Fire",     "icon": "C", "color": (220, 80, 220),  "effect": "cooldown", "value": 70, "desc": "-70ms cooldown — party non-stop"},
    ],
    "jack_in_box": [
        {"name": "Spring Loaded",  "icon": "C", "color": (200, 80, 255),  "effect": "cooldown", "value": 70, "desc": "-70ms cooldown — faster spring"},
        {"name": "Pop Goes Boom",  "icon": "D", "color": (180, 60, 220),  "effect": "damage",   "value": 12, "desc": "+12 damage — surprise explosion"},
    ],    "spud_gun": [
        {"name": "Starch Rounds",  "icon": "D", "color": (180, 140, 60),  "effect": "damage",   "value": 11, "desc": "+11 damage \u2014 heavyweight potatoes"},
        {"name": "Spud Salvo",     "icon": "C", "color": (160, 120, 50),  "effect": "cooldown", "value": 65, "desc": "-65ms cooldown \u2014 rapid-fire spuds"},
    ],}


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
                 current_weapon: dict = None, upgrade_tiers: dict = None,
                 arsenal: list = None):
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

        # Add stat + passive upgrades (filter out already-owned passives, maxed tiers, and class-restricted upgrades)
        for u in LEVEL_UPGRADES:
            cr = u.get("class_restrict")
            if cr:
                allowed = cr if isinstance(cr, list) else [cr]
                if player_class not in allowed:
                    continue
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

        # Add weapon-specific upgrades for current weapon AND any arsenal weapons
        # (2 upgrade slots per weapon, tiered up to 3 each — they buff the player globally)
        seen_weapon_keys = set(player_passives or [])  # reuse to avoid duplicate weapon upg names
        weapons_to_check = ([player_weapon_name] +
                            [k for k in (arsenal or []) if k != player_weapon_name])
        for wk in weapons_to_check:
            if wk not in WEAPON_UPGRADES:
                continue
            for wu in WEAPON_UPGRADES[wk]:
                wu_name = wu["name"]
                if wu_name in seen_weapon_keys:
                    continue
                current_tier = tiers.get(wu_name, 0)
                if current_tier >= 3:
                    seen_weapon_keys.add(wu_name)
                    continue
                next_tier = current_tier + 1
                tier_mult = {1: 1.0, 2: 1.5, 3: 2.0}[next_tier]
                tier_label = TIER_NAMES[next_tier]
                entry = dict(wu)
                entry["type"] = "weapon_upgrade"
                entry["tier"] = next_tier
                entry["base_name"] = wu_name
                if next_tier > 1:
                    entry["name"] = f"{wu_name} {tier_label}"
                    scaled_val = wu["value"]
                    if isinstance(scaled_val, (int, float)) and scaled_val != 0:
                        scaled_val = type(scaled_val)(scaled_val * tier_mult)
                    entry["value"] = scaled_val
                    entry["desc"] = f"[Tier {tier_label}] {wu['desc']}"
                pool.append(entry)
                seen_weapon_keys.add(wu_name)

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
            card_w, card_h = 360, 130
            gap = 18
            n = len(self.choices)
            start_x = SCREEN_WIDTH // 2 - (n * card_w + (n - 1) * gap) // 2
            card_y = SCREEN_HEIGHT // 2 - card_h // 2 - 20
            for i in range(n):
                cx = start_x + i * (card_w + gap)
                if cx <= mx <= cx + card_w and card_y <= my <= card_y + card_h:
                    self.selected = i
                    break
            return None

        # Mouse click - select card
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            card_w, card_h = 360, 130
            gap = 18
            n = len(self.choices)
            start_x = SCREEN_WIDTH // 2 - (n * card_w + (n - 1) * gap) // 2
            card_y = SCREEN_HEIGHT // 2 - card_h // 2 - 20
            for i in range(n):
                cx_card = start_x + i * (card_w + gap)
                if cx_card <= mx <= cx_card + card_w and card_y <= my <= card_y + card_h:
                    choice = self.choices[i]
                    self.active = False
                    return choice
            return None

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_a, pygame.K_LEFT, pygame.K_w, pygame.K_UP):
                self.selected = (self.selected - 1) % len(self.choices)
            elif event.key in (pygame.K_d, pygame.K_RIGHT, pygame.K_s, pygame.K_DOWN):
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
            elif event.key in (pygame.K_BACKSPACE, pygame.K_TAB):
                # Skip / forfeit this upgrade
                self.active = False
                return {"effect": "skip", "name": "Skip", "value": None}

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

        # Cards — horizontal 3-column layout
        card_w, card_h = 360, 130
        gap = 18
        n = len(self.choices)
        start_x = SCREEN_WIDTH // 2 - (n * card_w + (n - 1) * gap) // 2
        card_y = SCREEN_HEIGHT // 2 - card_h // 2 - 20
        for i, choice in enumerate(self.choices):
            cx = start_x + i * (card_w + gap)
            cy = card_y

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
            surface.blit(icon, (cx + 50, cy + 18))

            # Name — centered in the right text area (cx+90 .. cx+card_w-10)
            text_x = cx + 90
            text_w = card_w - 100
            name = self.font.render(choice["name"], True, WHITE)
            name_x = text_x + (text_w - name.get_width()) // 2
            surface.blit(name, (max(text_x, name_x), cy + 18))

            # Description — pixel-width word-wrap, each line centered
            desc = choice.get("desc", "")
            if desc:
                words = desc.split()
                lines, line_buf = [], []
                for word in words:
                    test = " ".join(line_buf + [word])
                    if self.font_small.size(test)[0] > text_w and line_buf:
                        lines.append(" ".join(line_buf))
                        line_buf = [word]
                    else:
                        line_buf.append(word)
                if line_buf:
                    lines.append(" ".join(line_buf))
                for li, line_text in enumerate(lines[:2]):
                    dl = self.font_small.render(line_text, True, (160, 160, 160))
                    dl_x = text_x + (text_w - dl.get_width()) // 2
                    surface.blit(dl, (max(text_x, dl_x), cy + 46 + li * 16))

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
            surface.blit(tag_surf, (cx + card_w - tag_surf.get_width() - 10, cy + card_h - 22))

            # Passives full warning on passive choices
            if self._passives_full and choice.get("effect") == "passive":
                warn_color = (255, 180, 50)
                warn_text = self.font_small.render("\u26a0 SLOTS FULL \u2014 SWAP", True, warn_color)
                wx = text_x + (text_w - warn_text.get_width()) // 2
                wy = cy + 80
                pygame.draw.rect(surface, (60, 40, 10), (wx - 3, wy - 1, warn_text.get_width() + 6, warn_text.get_height() + 2), border_radius=3)
                surface.blit(warn_text, (wx, wy))

        # Hint
        hint = self.font_small.render("A/D or Mouse to select  |  E/Enter/Click or 1-3 to confirm  |  Backspace to skip", True, (120, 120, 120))
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, card_y + card_h + 10))

        # Tooltip for selected upgrade
        if 0 <= self.selected < len(self.choices):
            choice = self.choices[self.selected]
            tip_x = start_x + self.selected * (card_w + gap)
            tip_y = card_y + card_h + 30
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
