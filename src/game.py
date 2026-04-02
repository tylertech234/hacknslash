import pygame
import sys
import math
import random as _rng
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("game")

from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, BLACK,
    TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
    ENEMY_DARKNESS_HP_BONUS, XP_PER_KILL, XP_DARKNESS_BONUS,
    DROP_CHANCE,
)
from src.entities.player import Player
from src.systems.combat import CombatSystem
from src.systems.spawner import WaveSpawner
from src.systems.game_map import GameMap
from src.systems.camera import Camera
from src.systems.projectiles import ProjectileSystem, PlayerProjectileSystem
from src.systems.pickups import PickupSystem
from src.systems.environment import EnvironmentSystem
from src.systems.campfire import Campfire
from src.systems.lighting import LightingSystem
from src.systems.sounds import SoundManager
from src.systems.legacy import LegacyData
from src.ui.hud import HUD
from src.ui.radar import Radar
from src.ui.levelup import LevelUpScreen
from src.ui.charselect import CharacterSelectScreen
from src.ui.legacy_screen import LegacyScreen
from src.systems.animations import AnimationSystem
from src.systems.boss_chest import BossChest, ChestRewardScreen
from src.systems.game_actions import process_enemy_death, fire_player_projectile


class Game:
    """Main game class — owns the loop, state, and all subsystems."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        self.char_select = CharacterSelectScreen()
        self.char_class = None  # set after selection
        self.legacy = LegacyData()
        self.legacy_screen = LegacyScreen(self.legacy)
        self._legacy_points_earned = 0

        self._init_world()

    def _init_world(self):
        self.game_map = GameMap()
        world_cx = self.game_map.pixel_width // 2
        world_cy = self.game_map.pixel_height // 2
        char_class = self.char_class or "knight"
        self.player = Player(world_cx, world_cy, char_class)
        self.combat = CombatSystem()
        self.spawner = WaveSpawner()
        self.camera = Camera()
        self.projectiles = ProjectileSystem()
        self.player_projectiles = PlayerProjectileSystem()
        self.pickups = PickupSystem()
        self.environment = EnvironmentSystem()
        self.campfire = Campfire()
        self.lighting = LightingSystem()
        self.sounds = SoundManager()
        self.hud = HUD()
        self.radar = Radar()
        self.levelup_screen = LevelUpScreen()
        self.chest_reward = ChestRewardScreen()
        self.boss_chests: list[BossChest] = []
        self.animations = AnimationSystem()
        self.combat_font = pygame.font.SysFont("consolas", 18, bold=True)
        self.game_over = False
        self._last_player_pos = (world_cx, world_cy)
        self._step_accumulator = 0.0

        # Kill tracking
        self.kills = 0
        self.boss_kills = 0

        # Passive timers
        self._nano_regen_timer = 0
        self._second_wind_used = False
        self._legacy_points_earned = 0

        # Apply legacy bonuses
        bonuses = self.legacy.get_bonuses()
        if bonuses.get("max_hp", 0):
            self.player.max_hp += int(bonuses["max_hp"])
            self.player.hp = self.player.max_hp
        if bonuses.get("damage", 0):
            self.player.damage += int(bonuses["damage"])
        if bonuses.get("speed", 0):
            self.player.speed += bonuses["speed"]
        if bonuses.get("damage_reduction", 0):
            self.player.legacy_dr = bonuses["damage_reduction"]
        self._drop_chance_bonus = bonuses.get("drop_chance", 0.0)
        bonus_levels = int(bonuses.get("start_level", 0))
        if bonus_levels > 0:
            self.player.level += bonus_levels
            self.player.damage += bonus_levels * 3
            self.player.max_hp += bonus_levels * 10
            self.player.hp = self.player.max_hp

        self.sounds.start_music()

    def run(self):
        self.sounds.start_music()
        while self.running:
            dt = self.clock.tick(FPS)
            now = pygame.time.get_ticks()

            # Character select phase
            if self.char_select.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    result = self.char_select.handle_event(event)
                    if result:
                        self.char_class = result
                        log.info("Character class selected: %s", result)
                        self._init_world()
                self.char_select.draw(self.screen)
                pygame.display.flip()
                continue

            # Legacy screen phase (between runs)
            if self.legacy_screen.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    done = self.legacy_screen.handle_event(event)
                    if done:
                        self.char_select.active = True
                self.legacy_screen.draw(self.screen)
                pygame.display.flip()
                continue

            self._handle_events()
            if not self.game_over:
                self._update(dt, now)
            self._draw()
        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------------ events
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                if self.game_over:
                    if event.key == pygame.K_r:
                        self.legacy_screen.activate(
                            self.spawner.wave, self.kills,
                            self._legacy_points_earned)
                    continue

            # Chest reward screen intercepts input
            if self.chest_reward.active:
                self.chest_reward.handle_event(event)
                if not self.chest_reward.active:
                    self._apply_chest_rewards()
                continue

            # Level-up screen intercepts input
            if self.levelup_screen.active:
                choice = self.levelup_screen.handle_event(event)
                if choice is not None:
                    log.info("Level-up choice selected: %s", choice)
                    try:
                        self._apply_levelup_choice(choice)
                        log.info("Level-up choice applied OK")
                    except Exception:
                        log.exception("ERROR applying level-up choice")
                continue

            if event.type == pygame.KEYDOWN:
                now = pygame.time.get_ticks()
                # Attack — Space or Left click proxy via J key
                if event.key in (pygame.K_SPACE, pygame.K_j):
                    if self.player.try_attack(now):
                        if not fire_player_projectile(self.player, self.player_projectiles, self.sounds):
                            self.sounds.play("swing")
                            self.animations.add_screen_shake(1)
                # Dash — Shift or K
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_k):
                    if self.player.try_dash(now):
                        self.sounds.play("dash")

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.game_over:
                now = pygame.time.get_ticks()
                if self.player.try_attack(now):
                    if not fire_player_projectile(self.player, self.player_projectiles, self.sounds):
                        self.sounds.play("swing")
                        self.animations.add_screen_shake(1)

    def _apply_levelup_choice(self, choice: dict):
        p = self.player
        effect = choice["effect"]
        value = choice.get("value", 0)
        log.debug("Applying effect=%s value=%s", effect, value)
        if effect == "max_hp":
            p.max_hp += value
            p.hp = min(p.max_hp, p.hp + value)
        elif effect == "damage":
            p.damage += value
        elif effect == "speed":
            p.speed += value
        elif effect == "range":
            p.attack_range += value
        elif effect == "heal":
            p.hp = p.max_hp
        elif effect == "cooldown":
            p.attack_cooldown = max(80, p.attack_cooldown - value)
        elif effect == "weapon":
            p.equip_weapon(value)
        elif effect == "glass_cannon":
            p.damage = int(p.damage * 1.3)
            p.max_hp = max(20, p.max_hp - 20)
            p.hp = min(p.hp, p.max_hp)
            if "glass_cannon" not in p.passives:
                p.passives.append("glass_cannon")
        elif effect == "passive":
            if value not in p.passives:
                p.passives.append(value)

    def _apply_chest_rewards(self):
        """Apply all rewards from a boss chest to the player."""
        p = self.player
        for r in self.chest_reward.get_rewards():
            effect = r["effect"]
            value = r.get("value", 0)
            log.info("Chest reward: %s effect=%s value=%s", r["name"], effect, value)
            if effect == "damage":
                p.damage += value
            elif effect == "range":
                p.attack_range += value
            elif effect == "cooldown":
                p.attack_cooldown = max(80, p.attack_cooldown - value)
            elif effect == "max_hp":
                p.max_hp += value
                p.hp = min(p.max_hp, p.hp + value)
            elif effect == "heal":
                p.hp = p.max_hp
            elif effect == "speed":
                p.speed += value
            elif effect == "weapon":
                p.equip_weapon(value)
            elif effect == "passive":
                if value not in p.passives:
                    p.passives.append(value)

    # ------------------------------------------------------------------ update
    def _update(self, dt: float, now: int):
        # Pause gameplay during level-up or chest reward screen
        if self.levelup_screen.active or self.chest_reward.active:
            return

        keys = pygame.key.get_pressed()
        world_w = self.game_map.pixel_width
        world_h = self.game_map.pixel_height

        self.player.update(dt, now, keys, world_w, world_h)

        # Passive: nano_regen — heal 1 HP every 2s
        if "nano_regen" in self.player.passives:
            if now - self._nano_regen_timer >= 2000:
                self._nano_regen_timer = now
                self.player.hp = min(self.player.max_hp, self.player.hp + 1)

        # Mouse aiming — player faces toward mouse cursor
        mx, my = pygame.mouse.get_pos()
        # Convert screen mouse pos to world coords
        cx, cy = self.camera.x, self.camera.y
        world_mx = mx + cx
        world_my = my + cy
        aim_dx = world_mx - self.player.x
        aim_dy = world_my - self.player.y
        aim_len = math.hypot(aim_dx, aim_dy)
        if aim_len > 1.0:
            self.player.facing_x = aim_dx / aim_len
            self.player.facing_y = aim_dy / aim_len
        half = self.player.size // 2
        self.player.x, self.player.y = self.environment.collide_entity(
            self.player.x, self.player.y, half)

        # Footstep sounds based on distance traveled
        dx_moved = self.player.x - self._last_player_pos[0]
        dy_moved = self.player.y - self._last_player_pos[1]
        dist_moved = math.hypot(dx_moved, dy_moved)
        self._last_player_pos = (self.player.x, self.player.y)
        if dist_moved > 0.5 and not self.player.is_dashing:
            self._step_accumulator += dist_moved
            if self._step_accumulator >= 40:  # step every ~40 px
                self.sounds.play("step")
                self._step_accumulator = 0.0

        self.spawner.update(now, self.player.x, self.player.y)

        # Play boss roar on boss wave start
        if self.spawner.just_started_wave and self.spawner.boss_wave:
            self.sounds.play("boss_roar")

        # Campfire is active only between waves
        self.campfire.set_active(not self.spawner.wave_active)
        self.campfire.update(now, self.player)

        # Fruit tree regrowth
        self.environment.update_fruit(now)

        # Lighting system
        self.lighting.update(self.player.x, self.player.y)

        # Pass darkness to combat for XP/damage scaling
        self.combat.darkness_level = self.lighting.darkness

        alive = self.spawner.get_alive_enemies()
        for enemy in alive:
            enemy.update(dt, now, self.player.x, self.player.y, world_w, world_h)
            # Environment collision for enemies too
            ehalf = enemy.size // 2
            enemy.x, enemy.y = self.environment.collide_entity(
                enemy.x, enemy.y, ehalf)
            # Spawn projectile if enemy wants to shoot
            if enemy.wants_to_shoot:
                self.projectiles.spawn(
                    enemy.x, enemy.y,
                    self.player.x, self.player.y,
                    int(enemy.bullet_damage * (1.0 + self.lighting.darkness * 0.5)),
                )
                enemy.wants_to_shoot = False
                self.sounds.play("enemy_shoot")

        self.combat.process_player_attack(self.player, alive, now)

        # Parry: melee attacks deflect enemy projectiles
        if self.player.is_attacking and not self.player.weapon.get("projectile"):
            attack_rect = self.player.get_attack_rect()
            for bullet in self.projectiles.bullets:
                if bullet.alive and attack_rect.colliderect(bullet.rect):
                    bullet.alive = False
                    self.sounds.play("parry")
                    # Big flash of sparks
                    self.animations.spawn_hit_sparks(bullet.x, bullet.y, count=12)
                    self.animations.spawn_death_burst(bullet.x, bullet.y, (150, 200, 255), count=8)
                    self.animations.add_screen_shake(3)

        # Death bursts & screen shake from melee kills + passive triggers
        _kt = {"kills": self.kills, "boss_kills": self.boss_kills}
        for enemy in alive:
            if not enemy.alive:
                process_enemy_death(enemy, self.player, alive, self.animations,
                                    self.combat, self.sounds, self.lighting,
                                    self.boss_chests, _kt, now)
        self.kills = _kt["kills"]
        self.boss_kills = _kt["boss_kills"]

        # Check if player attack hits a fruit tree
        if self.player.is_attacking and not self.player.weapon.get("projectile"):
            apple_drops = self.environment.check_fruit_tree_hit(
                self.player.get_attack_rect(), now)
            for ax, ay in apple_drops:
                self.pickups.spawn_apple(ax, ay)

        # Update player-thrown projectiles (daggers, orbiters, grenades)
        thrown_hits, grenade_explosions = self.player_projectiles.update(
            now, alive, world_w, world_h, self.player.x, self.player.y)

        # Grenade explosion effects
        for gx, gy, _gdmg in grenade_explosions:
            self.animations.spawn_confetti_explosion(gx, gy)
            self.animations.add_screen_shake(4)
            self.sounds.play("confetti_boom")

        for enemy, dmg in thrown_hits:
            # Passive: crit_shots — 20% chance double damage on projectile
            if "crit_shots" in self.player.passives and _rng.random() < 0.20:
                dmg *= 2
                self.combat._add_damage_number(enemy.x, enemy.y - enemy.size - 10, dmg, (255, 100, 255))
            # Passive: lucky_crits — 15% chance triple damage
            elif "lucky_crits" in self.player.passives and _rng.random() < 0.15:
                dmg *= 3
                self.combat._add_damage_number(enemy.x, enemy.y - enemy.size - 10, dmg, (255, 215, 0))
            else:
                self.combat._add_damage_number(enemy.x, enemy.y - enemy.size, dmg, (255, 255, 100))
            self.animations.spawn_hit_sparks(enemy.x, enemy.y)
            # Passive: vampiric_strike — heal 3 per hit
            if "vampiric_strike" in self.player.passives:
                self.player.hp = min(self.player.max_hp, self.player.hp + 3)
            # Passive: chain_lightning — arc to 2 nearby enemies
            if "chain_lightning" in self.player.passives:
                chain_dmg = max(1, dmg // 2)
                chain_count = 0
                for other in alive:
                    if chain_count >= 2:
                        break
                    if other.alive and other is not enemy:
                        d = math.hypot(other.x - enemy.x, other.y - enemy.y)
                        if d < 120:
                            other.take_damage(chain_dmg, other.x - enemy.x, other.y - enemy.y, now)
                            self.combat._add_damage_number(other.x, other.y - other.size, chain_dmg, (100, 200, 255))
                            self.animations.spawn_hit_sparks(other.x, other.y, count=4)
                            chain_count += 1
                            if not other.alive:
                                process_enemy_death(other, self.player, alive, self.animations,
                                                    self.combat, self.sounds, self.lighting,
                                                    self.boss_chests, _kt, now)
                                self.kills = _kt["kills"]
                                self.boss_kills = _kt["boss_kills"]
            if not enemy.alive:
                process_enemy_death(enemy, self.player, alive, self.animations,
                                    self.combat, self.sounds, self.lighting,
                                    self.boss_chests, _kt, now)
                self.kills = _kt["kills"]
                self.boss_kills = _kt["boss_kills"]
            self.sounds.play("hit")

        # Check if enemies hit the player — play hit sound
        prev_hp = self.player.hp
        self.combat.process_enemy_attacks(self.player, alive, now)
        if self.player.hp < prev_hp:
            self.sounds.play("hit")
            self.animations.spawn_hit_sparks(self.player.x, self.player.y)
            self.animations.add_screen_shake(3)

        self.combat.update(now)

        # Handle drops from killed enemies
        effective_drop = DROP_CHANCE + self._drop_chance_bonus
        for (dx, dy) in self.combat.pending_drops:
            self.pickups.try_drop(dx, dy, effective_drop)
        self.combat.pending_drops.clear()

        # Update projectiles and pickups
        prev_hp2 = self.player.hp
        self.projectiles.update(now, self.player, world_w, world_h)
        if self.player.hp < prev_hp2:
            self.sounds.play("hit")
            self.animations.spawn_hit_sparks(self.player.x, self.player.y)
            self.animations.add_screen_shake(2)

        prev_count = len(self.pickups.pickups)
        self.pickups.update(now, self.player)
        if len(self.pickups.pickups) < prev_count:
            self.sounds.play("pickup")

        # Radar
        self.radar.update(now, self.player.x, self.player.y, alive, self.sounds)

        # Dynamic music intensity — force max during boss waves
        if alive:
            min_dist = min(math.hypot(e.x - self.player.x, e.y - self.player.y) for e in alive)
            intensity = max(0.0, min(1.0, 1.0 - (min_dist - 200) / 600))
            if self.spawner.boss_wave:
                intensity = 1.0  # full combat intensity for boss waves
        else:
            intensity = 0.0
        self.sounds.set_music_intensity(intensity)

        # Boss chest collision
        p_rect = self.player.rect
        for chest in self.boss_chests:
            if chest.alive and p_rect.colliderect(chest.rect):
                chest.alive = False
                self.chest_reward.open_chest(self.player.char_class, self.player.passives)
                log.info("Boss chest opened!")
                break
        self.boss_chests = [c for c in self.boss_chests if c.alive]

        self.animations.update(dt)
        self.camera.update(self.player.x, self.player.y, world_w, world_h)

        if self.player.hp <= 0:
            # Passive: second_wind — revive once at 30% HP
            if "second_wind" in self.player.passives and not self._second_wind_used:
                self._second_wind_used = True
                self.player.hp = max(1, int(self.player.max_hp * 0.3))
                self.player.invincible = True
                self.player.invincible_timer = now
                self.animations.add_screen_shake(6)
                self.sounds.play("levelup")
                log.info("Second Wind activated! HP restored to %d", self.player.hp)
            else:
                self.game_over = True
                self._legacy_points_earned = self.legacy.finish_run(
                    self.spawner.wave, self.kills, self.boss_kills)

        # Check for pending level-up
        if self.player.pending_levelup:
            log.info("Level-up pending! Player level=%d, weapon=%s",
                     self.player.level, self.player.weapon_name)
            self.player.pending_levelup = False
            self.levelup_screen.activate(self.player.weapon_name, self.player.char_class,
                                         self.player.passives)
            log.info("Level-up screen activated, choices=%s",
                     [c.get('name','?') for c in self.levelup_screen.choices])
            self.sounds.play("levelup")

    # ------------------------------------------------------------------ draw
    def _draw(self):
        self.screen.fill(BLACK)
        cx, cy = int(self.camera.x), int(self.camera.y)

        # Apply screen shake offset
        shake_x, shake_y = self.animations.shake_offset
        cx += shake_x
        cy += shake_y

        self.game_map.draw(self.screen, cx, cy, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Environment props (behind characters)
        self.environment.draw(self.screen, cx, cy, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Campfire
        self.campfire.draw(self.screen, cx, cy)

        # Pickups (draw under characters)
        self.pickups.draw(self.screen, cx, cy)

        # Boss chests
        for chest in self.boss_chests:
            chest.draw(self.screen, cx, cy)

        for enemy in self.spawner.get_alive_enemies():
            enemy.draw(self.screen, cx, cy)

        # Projectiles
        self.projectiles.draw(self.screen, cx, cy)
        self.player_projectiles.draw(self.screen, cx, cy)

        self.player.draw(self.screen, cx, cy)
        self.combat.draw(self.screen, cx, cy, self.combat_font)

        # Particle animations (death bursts, hit sparks)
        self.animations.draw(self.screen, cx, cy)

        # ---- Darkness overlay (after world, before UI) ----
        self.lighting.draw(self.screen, cx, cy, self.player.x, self.player.y)

        alive_count = len(self.spawner.get_alive_enemies())
        boss_enemies = [e for e in self.spawner.get_alive_enemies()
                       if e.enemy_type in ("mini_boss", "big_boss")] if self.spawner.boss_wave else None
        self.hud.draw(self.screen, self.player, self.spawner.wave, alive_count,
                      self.lighting.darkness, self.spawner.boss_wave, boss_enemies)

        # Pickup notifications
        self.pickups.draw_notifications(self.screen)

        # Radar (AVP motion tracker)
        self.radar.draw(self.screen, self.player.facing_x, self.player.facing_y)

        # Level-up overlay
        self.levelup_screen.draw(self.screen)

        # Chest reward overlay
        self.chest_reward.draw(self.screen)

        if self.game_over:
            self.hud.draw_game_over(self.screen, self.spawner.wave, self.player.level,
                                    self.kills, self._legacy_points_earned)

        pygame.display.flip()
