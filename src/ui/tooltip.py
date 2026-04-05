"""Shared tooltip renderer for upgrade screens — shows detailed stats on hover/select."""

import pygame
import math
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, PASSIVE_INFO


# Detailed passive descriptions for tooltips
PASSIVE_DETAILS = {
    "vampiric_strike":  {"name": "Vampiric Strike",  "effect": "Heal 4 HP per melee hit", "type": "Sustain"},
    "chain_lightning":  {"name": "Chain Lightning",   "effect": "Hits arc to 2 nearby enemies (50% dmg, 120px range)", "type": "AoE"},
    "thorns":           {"name": "Thorns",            "effect": "Reflect 30% of melee damage taken back at attacker", "type": "Defense"},
    "second_wind":      {"name": "Second Wind",       "effect": "Revive once at 30% HP on death (1 use per run)", "type": "Survival"},
    "nano_regen":       {"name": "Nano Regen",        "effect": "Regenerate 1 HP every 2 seconds", "type": "Sustain"},
    "berserker":        {"name": "Berserker",         "effect": "+50% damage when below 30% HP", "type": "Offense"},
    "shield_matrix":    {"name": "Shield Matrix",     "effect": "Block one hit every 10 seconds", "type": "Defense"},
    "explosive_kills":  {"name": "Explosive Kills",   "effect": "25% chance enemies explode on death (AoE)", "type": "AoE"},
    "magnetic_field":   {"name": "Magnetic Field",    "effect": "Pickups fly to you from 3x distance", "type": "Utility"},
    "adrenaline":       {"name": "Adrenaline Rush",   "effect": "+30% speed for 3s after each kill", "type": "Mobility"},
    "parry_deflect":    {"name": "Parry Deflect",     "effect": "Parried bullets return to sender at 2x dmg (melee only)", "type": "Offense"},
    "glass_cannon":     {"name": "Glass Cannon",      "effect": "+30% damage, -20 Max HP", "type": "Risky"},
    "melee_lifesteal":  {"name": "Melee Lifesteal",   "effect": "Heal 2 HP on melee kills", "type": "Sustain"},
    "armor_plating":    {"name": "Armor Plating",     "effect": "Take 15% less damage from all sources", "type": "Defense"},
    "crit_shots":       {"name": "Critical Shots",    "effect": "20% chance for double damage on projectiles", "type": "Offense"},
    "evasion":          {"name": "Evasion",           "effect": "15% chance to dodge attacks completely", "type": "Defense"},
    "lucky_crits":      {"name": "Lucky Crits",       "effect": "15% chance for triple damage on hits", "type": "Offense"},
    "confetti_burst":   {"name": "Confetti Burst",    "effect": "Kills have 20% chance to stun nearby enemies", "type": "AoE"},
}


def calc_weapon_dps(base_damage: int, weapon: dict) -> float:
    """Calculate effective DPS for a weapon given player base damage."""
    dmg_per_hit = base_damage * weapon.get("damage_mult", 1.0)
    cooldown_s = weapon.get("cooldown", 400) / 1000.0
    count = weapon.get("proj_count", 1)
    return (dmg_per_hit * count) / cooldown_s


def format_weapon_stats(weapon: dict, base_damage: int = 20) -> list[str]:
    """Return a list of stat strings for a weapon tooltip."""
    dps = calc_weapon_dps(base_damage, weapon)
    dmg = base_damage * weapon.get("damage_mult", 1.0)
    lines = [
        f"DPS: {dps:.1f}",
        f"Damage: {dmg:.0f}  (x{weapon.get('damage_mult', 1.0):.1f})",
        f"Cooldown: {weapon.get('cooldown', 400)}ms",
        f"Range: {weapon.get('range', 60)}px",
        f"Sweep: {weapon.get('sweep_deg', 120)}\u00b0",
    ]
    if weapon.get("projectile"):
        lines.append(f"Projectile speed: {weapon.get('proj_speed', 5.0):.0f}")
        if weapon.get("proj_count", 1) > 1:
            lines.append(f"Projectiles: {weapon['proj_count']}")
        if weapon.get("piercing"):
            lines.append("Piercing: Yes")
        if weapon.get("bouncing"):
            lines.append("Bouncing: Yes")
        if weapon.get("orbiter"):
            lines.append("Type: Orbiter (max 3)")
        if weapon.get("grenade"):
            lines.append("Type: Grenade (AoE)")
    return lines


class Tooltip:
    """Draws a floating tooltip box with detailed info."""

    def __init__(self):
        self.font = pygame.font.SysFont("consolas", 14)
        self.font_title = pygame.font.SysFont("consolas", 16, bold=True)
        self.padding = 10
        self.max_width = 300
        self.line_spacing = 3

    def draw_weapon_tooltip(self, surface: pygame.Surface, x: int, y: int,
                            weapon: dict, base_damage: int = 20,
                            current_weapon: dict = None):
        """Draw a weapon stats tooltip at (x, y)."""
        title = weapon.get("name", "Unknown")
        lines = format_weapon_stats(weapon, base_damage)

        # Comparison with current weapon
        if current_weapon and current_weapon.get("name") != weapon.get("name"):
            cur_dps = calc_weapon_dps(base_damage, current_weapon)
            new_dps = calc_weapon_dps(base_damage, weapon)
            diff = new_dps - cur_dps
            if abs(diff) > 0.1:
                sign = "+" if diff > 0 else ""
                lines.append(f"vs current: {sign}{diff:.1f} DPS")

        desc = weapon.get("desc", "")
        if desc:
            lines.append("")
            lines.append(desc)

        self._draw_box(surface, x, y, title, lines, weapon.get("blade_color", (200, 200, 200)))

    def draw_passive_tooltip(self, surface: pygame.Surface, x: int, y: int,
                             passive_key: str):
        """Draw a passive ability tooltip at (x, y)."""
        info = PASSIVE_DETAILS.get(passive_key, {})
        title = info.get("name", passive_key.replace("_", " ").title())
        lines = []
        if info.get("type"):
            lines.append(f"Type: {info['type']}")
        if info.get("effect"):
            lines.append(info["effect"])
        color = PASSIVE_INFO.get(passive_key, ("?", (180, 180, 180)))[1]
        self._draw_box(surface, x, y, title, lines, color)

    def draw_stat_tooltip(self, surface: pygame.Surface, x: int, y: int,
                          name: str, desc: str, value_str: str = ""):
        """Draw a generic stat upgrade tooltip."""
        lines = []
        if value_str:
            lines.append(value_str)
        if desc:
            lines.append(desc)
        self._draw_box(surface, x, y, name, lines, (200, 200, 200))

    def _wrap_text(self, text, font, max_w):
        words = text.split(' ')
        lines = []
        current = ""
        for word in words:
            test = current + (" " if current else "") + word
            if font.size(test)[0] <= max_w:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines if lines else [""]

    def _draw_box(self, surface: pygame.Surface, x: int, y: int,
                  title: str, lines: list[str], accent_color: tuple):
        pad = self.padding
        content_w = self.max_width - pad * 2

        # Render title
        title_surf = self.font_title.render(title, True, accent_color)

        # Word-wrap all lines
        wrapped = []
        for ln in lines:
            if not ln:
                wrapped.append(self.font.render("", True, (200, 200, 200)))
            else:
                for wl in self._wrap_text(ln, self.font, content_w):
                    wrapped.append(self.font.render(wl, True, (200, 200, 200)))

        # Calculate box size
        w = max(title_surf.get_width() + pad * 2,
                max((s.get_width() + pad * 2 for s in wrapped), default=0))
        w = min(max(w, 120), self.max_width)
        line_h = self.font.get_height() + self.line_spacing
        h = pad + title_surf.get_height() + pad // 2 + len(wrapped) * line_h + pad

        # Keep on screen
        if x + w + 10 > SCREEN_WIDTH:
            x = SCREEN_WIDTH - w - 10
        if y + h + 10 > SCREEN_HEIGHT:
            y = SCREEN_HEIGHT - h - 10
        if x < 10:
            x = 10
        if y < 10:
            y = 10

        # Background
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((15, 15, 25, 230))
        pygame.draw.rect(bg, accent_color, (0, 0, w, h), 1, border_radius=4)
        pygame.draw.line(bg, accent_color, (1, 1), (w - 2, 1), 2)
        surface.blit(bg, (x, y))

        # Title
        surface.blit(title_surf, (x + pad, y + pad))

        # Lines
        cy = y + pad + title_surf.get_height() + pad // 2
        for s in wrapped:
            surface.blit(s, (x + pad, cy))
            cy += line_h
