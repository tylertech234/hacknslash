import pygame
import sys
import math
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
from src.ui.hud import HUD
from src.ui.radar import Radar
from src.ui.levelup import LevelUpScreen


class Game:
    """Main game class — owns the loop, state, and all subsystems."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False

        self._init_world()

    def _init_world(self):
        self.game_map = GameMap()
        world_cx = self.game_map.pixel_width // 2
        world_cy = self.game_map.pixel_height // 2
        self.player = Player(world_cx, world_cy)
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
        self.combat_font = pygame.font.SysFont("consolas", 18, bold=True)
        self.game_over = False
        self._last_player_pos = (world_cx, world_cy)
        self._step_accumulator = 0.0

    def run(self):
        self.sounds.start_music()
        while self.running:
            dt = self.clock.tick(FPS)
            now = pygame.time.get_ticks()
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
                        self._init_world()
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
                        if self.player.weapon.get("projectile"):
                            dmg = int(self.player.damage * self.player.weapon["damage_mult"])
                            self.player_projectiles.spawn_daggers(
                                self.player.x, self.player.y,
                                self.player.facing_x, self.player.facing_y, dmg)
                            self.sounds.play("throw")
                        else:
                            self.sounds.play("swing")
                # Dash — Shift or K
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_k):
                    if self.player.try_dash(now):
                        self.sounds.play("dash")

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.game_over:
                now = pygame.time.get_ticks()
                if self.player.try_attack(now):
                    if self.player.weapon.get("projectile"):
                        dmg = int(self.player.damage * self.player.weapon["damage_mult"])
                        self.player_projectiles.spawn_daggers(
                            self.player.x, self.player.y,
                            self.player.facing_x, self.player.facing_y, dmg)
                        self.sounds.play("throw")
                    else:
                        self.sounds.play("swing")

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

    # ------------------------------------------------------------------ update
    def _update(self, dt: float, now: int):
        # Pause gameplay during level-up screen
        if self.levelup_screen.active:
            return

        keys = pygame.key.get_pressed()
        world_w = self.game_map.pixel_width
        world_h = self.game_map.pixel_height

        self.player.update(dt, now, keys, world_w, world_h)

        # Environment collision (trees, rocks)
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

        self.spawner.update(now)

        # Play boss roar on boss wave start
        if self.spawner.just_started_wave and self.spawner.boss_wave:
            self.sounds.play("boss_roar")

        # Campfire is active only between waves
        self.campfire.set_active(not self.spawner.wave_active)
        self.campfire.update(now, self.player)

        # Lighting system
        self.lighting.update(self.player.x, self.player.y)

        # Pass darkness to combat for XP/damage scaling
        self.combat.darkness_level = self.lighting.darkness

        # Scale enemy HP on spawn based on darkness
        hp_mult = 1.0 + self.lighting.darkness * ENEMY_DARKNESS_HP_BONUS

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

        # Update player-thrown projectiles (daggers)
        thrown_hits = self.player_projectiles.update(now, alive, world_w, world_h)
        for enemy, dmg in thrown_hits:
            self.combat._add_damage_number(enemy.x, enemy.y - enemy.size, dmg, (255, 255, 100))
            if not enemy.alive:
                xp_mult = 1.0 + self.lighting.darkness * XP_DARKNESS_BONUS
                xp_base = getattr(enemy, "xp_value", XP_PER_KILL)
                self.player.gain_xp(int(xp_base * xp_mult))
                self.combat.pending_drops.append((enemy.x, enemy.y))
            self.sounds.play("hit")

        # Check if enemies hit the player — play hit sound
        prev_hp = self.player.hp
        self.combat.process_enemy_attacks(self.player, alive, now)
        if self.player.hp < prev_hp:
            self.sounds.play("hit")

        self.combat.update(now)

        # Handle drops from killed enemies
        from src.settings import DROP_CHANCE
        for (dx, dy) in self.combat.pending_drops:
            self.pickups.try_drop(dx, dy, DROP_CHANCE)
        self.combat.pending_drops.clear()

        # Update projectiles and pickups
        prev_hp2 = self.player.hp
        self.projectiles.update(now, self.player, world_w, world_h)
        if self.player.hp < prev_hp2:
            self.sounds.play("hit")

        prev_count = len(self.pickups.pickups)
        self.pickups.update(now, self.player)
        if len(self.pickups.pickups) < prev_count:
            self.sounds.play("pickup")

        # Radar
        self.radar.update(now, self.player.x, self.player.y, alive, self.sounds)

        # Dynamic music intensity based on nearest enemy
        if alive:
            min_dist = min(math.hypot(e.x - self.player.x, e.y - self.player.y) for e in alive)
            intensity = max(0.0, min(1.0, 1.0 - (min_dist - 200) / 600))
        else:
            intensity = 0.0
        self.sounds.set_music_intensity(intensity)

        self.camera.update(self.player.x, self.player.y, world_w, world_h)

        if self.player.hp <= 0:
            self.game_over = True

        # Check for pending level-up
        if self.player.pending_levelup:
            log.info("Level-up pending! Player level=%d, weapon=%s",
                     self.player.level, self.player.weapon_name)
            self.player.pending_levelup = False
            self.levelup_screen.activate(self.player.weapon_name)
            log.info("Level-up screen activated, choices=%s",
                     [c.get('name','?') for c in self.levelup_screen.choices])
            self.sounds.play("levelup")

    # ------------------------------------------------------------------ draw
    def _draw(self):
        self.screen.fill(BLACK)
        cx, cy = int(self.camera.x), int(self.camera.y)

        self.game_map.draw(self.screen, cx, cy, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Environment props (behind characters)
        self.environment.draw(self.screen, cx, cy, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Campfire
        self.campfire.draw(self.screen, cx, cy)

        # Pickups (draw under characters)
        self.pickups.draw(self.screen, cx, cy)

        for enemy in self.spawner.get_alive_enemies():
            enemy.draw(self.screen, cx, cy)

        # Projectiles
        self.projectiles.draw(self.screen, cx, cy)
        self.player_projectiles.draw(self.screen, cx, cy)

        self.player.draw(self.screen, cx, cy)
        self.combat.draw(self.screen, cx, cy, self.combat_font)

        # ---- Darkness overlay (after world, before UI) ----
        self.lighting.draw(self.screen, cx, cy, self.player.x, self.player.y)

        alive_count = len(self.spawner.get_alive_enemies())
        self.hud.draw(self.screen, self.player, self.spawner.wave, alive_count,
                      self.lighting.darkness, self.spawner.boss_wave)

        # Pickup notifications
        self.pickups.draw_notifications(self.screen)

        # Radar (AVP motion tracker)
        self.radar.draw(self.screen, self.player.facing_x, self.player.facing_y)

        # Level-up overlay
        self.levelup_screen.draw(self.screen)

        if self.game_over:
            self.hud.draw_game_over(self.screen, self.spawner.wave, self.player.level)

        pygame.display.flip()
