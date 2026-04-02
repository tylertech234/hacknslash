import math
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

    def process_player_attack(self, player, enemies: list, now: int):
        """Check if the player's attack hits any enemies."""
        if not player.is_attacking:
            return
        # Projectile weapons are handled by PlayerProjectileSystem
        if player.weapon.get("projectile"):
            return

        attack_rect = player.get_attack_rect()
        weapon_mult = player.weapon.get("damage_mult", 1.0)

        for enemy in enemies:
            if not enemy.alive:
                continue
            if attack_rect.colliderect(enemy.rect):
                kb_x = enemy.x - player.x
                kb_y = enemy.y - player.y
                total_dmg = int(player.damage * weapon_mult)
                enemy.take_damage(total_dmg, kb_x, kb_y, now)
                self._add_damage_number(enemy.x, enemy.y - enemy.size, total_dmg, (255, 255, 100))
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
                player.take_damage(dmg, now)
                self._add_damage_number(player.x, player.y - player.size, dmg, (255, 80, 80))
                # Enemy applies its status effect on melee hit
                status_key = getattr(enemy, "status_on_hit", None)
                if status_key and hasattr(player, "statuses"):
                    player.statuses.apply(status_key, now)

    def _add_damage_number(self, x: float, y: float, amount: int, color: tuple):
        self.damage_numbers.append({
            "x": x, "y": y,
            "text": str(amount),
            "color": color,
            "timer": pygame.time.get_ticks(),
            "duration": 600,
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
            alpha = max(0, 1.0 - elapsed / d["duration"])
            offset_y = -elapsed * 0.04
            sx = int(d["x"] - camera_x)
            sy = int(d["y"] - camera_y + offset_y)
            text_surf = font.render(d["text"], True, d["color"])
            text_surf.set_alpha(int(alpha * 255))
            surface.blit(text_surf, (sx - text_surf.get_width() // 2, sy))
