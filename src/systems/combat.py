import math
import random
import pygame
from src.settings import (
    XP_PER_KILL, DROP_CHANCE,
    XP_DARKNESS_BONUS, ENEMY_DARKNESS_DMG_BONUS,
)


class CombatSystem:
    """Handles attack resolution, damage, and XP rewards."""

    def __init__(self):
        self.damage_numbers: list[dict] = []  # floating damage text
        self.pending_drops: list[tuple] = []  # (x, y) of enemies that just died
        self.darkness_level = 0.0  # set each frame by game.py
        self.damage_log: list[tuple[str, int]] = []  # (weapon_key, damage) drained by game.py

    def process_player_attack(self, player, enemies: list, now: int):
        """Check if the player's attack hits any enemies."""
        if not player.is_attacking:
            return
        # Projectile weapons are handled by PlayerProjectileSystem
        if player.weapon.get("projectile"):
            return

        attack_rect = player.get_attack_rect()
        weapon_mult = player.weapon.get("damage_mult", 1.0)
        dmg_mult = getattr(player, 'damage_multiplier', 1.0)

        for enemy in enemies:
            if not enemy.alive:
                continue
            if attack_rect.colliderect(enemy.rect):
                kb_x = enemy.x - player.x
                kb_y = enemy.y - player.y
                total_dmg = int(player.damage * weapon_mult * dmg_mult)
                kb_mult = getattr(player, 'knockback_bonus', 1.0)
                enemy.take_damage(total_dmg, kb_x, kb_y, now, kb_mult)
                self.damage_log.append((player.weapon_name, total_dmg))
                self._add_damage_number(enemy.x, enemy.y - enemy.size, total_dmg, (255, 255, 100))
                # Passive: vampiric_strike — heal 3 per hit
                if "vampiric_strike" in getattr(player, 'passives', []):
                    player.hp = min(player.max_hp, player.hp + 3)
                # Passive: chain_lightning — arc to 2 nearby enemies
                if "chain_lightning" in getattr(player, 'passives', []):
                    chain_dmg = max(1, total_dmg // 2)
                    chain_count = 0
                    for other in enemies:
                        if chain_count >= 2:
                            break
                        if other.alive and other is not enemy:
                            d = math.hypot(other.x - enemy.x, other.y - enemy.y)
                            if d < 120:
                                other.take_damage(chain_dmg, other.x - enemy.x, other.y - enemy.y, now)
                                self._add_damage_number(other.x, other.y - other.size, chain_dmg, (100, 200, 255))
                                chain_count += 1
                                if not other.alive:
                                    xp_m = 1.0 + self.darkness_level * XP_DARKNESS_BONUS
                                    player.gain_xp(int(getattr(other, "xp_value", XP_PER_KILL) * xp_m))
                                    self.pending_drops.append((other.x, other.y))
                if not enemy.alive:
                    # XP scales with darkness; use enemy-specific xp_value
                    xp_mult = 1.0 + self.darkness_level * XP_DARKNESS_BONUS
                    xp_base = getattr(enemy, "xp_value", XP_PER_KILL)
                    player.gain_xp(int(xp_base * xp_mult))
                    self.pending_drops.append((enemy.x, enemy.y))

    def process_enemy_attacks(self, player, enemies: list, now: int):
        """Check if any enemy can hit the player."""
        dmg_mult = 1.0 + self.darkness_level * ENEMY_DARKNESS_DMG_BONUS
        for enemy in enemies:
            if enemy.can_attack(player.x, player.y, now):
                dmg = int(enemy.perform_attack(now) * dmg_mult)
                prev_hp = player.hp
                player.take_damage(dmg, now)
                self._add_damage_number(player.x, player.y - player.size, dmg, (255, 80, 80))
                # Enemy applies its status effect on melee hit
                status_key = getattr(enemy, "status_on_hit", None)
                if status_key and hasattr(player, "statuses"):
                    player.statuses.apply(status_key, now)
                # Passive: thorns — reflect 75% of actual damage taken back at attacker
                if player.hp < prev_hp and "thorns" in getattr(player, 'passives', []):
                    actual = prev_hp - player.hp
                    reflected = max(1, int(actual * 0.75))
                    enemy.take_damage(reflected, enemy.x - player.x, enemy.y - player.y, now)
                    self._add_damage_number(enemy.x, enemy.y - enemy.size, reflected, (255, 150, 50))
                    if not enemy.alive:
                        xp_m = 1.0 + self.darkness_level * XP_DARKNESS_BONUS
                        player.gain_xp(int(getattr(enemy, "xp_value", XP_PER_KILL) * xp_m))
                        self.pending_drops.append((enemy.x, enemy.y))

    def _add_damage_number(self, x: float, y: float, amount: int, color: tuple):
        self.damage_numbers.append({
            "x": x + random.randint(-8, 8),
            "y": y + random.randint(-4, 4),
            "text": str(amount),
            "color": color,
            "timer": pygame.time.get_ticks(),
            "duration": 800,
        })

    def update(self, now: int):
        self.damage_numbers = [
            d for d in self.damage_numbers
            if now - d["timer"] < d["duration"]
        ]

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int, font: pygame.font.Font):
        now = pygame.time.get_ticks()
        for d in self.damage_numbers:
            elapsed = now - d["timer"]
            t = elapsed / d["duration"]  # 0..1
            if t >= 1.0:
                continue
            alpha = max(0, 1.0 - t)
            # Rise fast at first, slow down
            offset_y = -40 * (1.0 - (1.0 - t) ** 2)
            sx = int(d["x"] - camera_x)
            sy = int(d["y"] - camera_y + offset_y)

            # Scale pop: start at 1.6x, settle to 1.0x over first 20%
            if t < 0.2:
                scale = 1.6 - 3.0 * t
            else:
                scale = 1.0
            text_surf = font.render(d["text"], True, d["color"])
            if scale != 1.0:
                w = int(text_surf.get_width() * scale)
                h = int(text_surf.get_height() * scale)
                if w > 0 and h > 0:
                    text_surf = pygame.transform.smoothscale(text_surf, (w, h))

            # Black outline via offset blits
            outline = font.render(d["text"], True, (0, 0, 0))
            if scale != 1.0:
                ow = int(outline.get_width() * scale)
                oh = int(outline.get_height() * scale)
                if ow > 0 and oh > 0:
                    outline = pygame.transform.smoothscale(outline, (ow, oh))
            outline.set_alpha(int(alpha * 200))
            ox = sx - outline.get_width() // 2
            oy = sy
            for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                surface.blit(outline, (ox + ddx, oy + ddy))

            text_surf.set_alpha(int(alpha * 255))
            surface.blit(text_surf, (sx - text_surf.get_width() // 2, sy))
