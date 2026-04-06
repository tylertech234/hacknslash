import asyncio
import datetime
import os
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
    ENEMY_DARKNESS_HP_BONUS, ENEMY_DARKNESS_DMG_BONUS, XP_PER_KILL, XP_DARKNESS_BONUS,
    DROP_CHANCE, MAX_PASSIVES,
    SUPABASE_URL, SUPABASE_ANON_KEY, DATA_DIR,
    CAMERA_ZOOM,
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
from src.ui.minimap import Minimap
from src.ui.levelup import LevelUpScreen
from src.ui.charselect import CharacterSelectScreen
from src.ui.legacy_screen import LegacyScreen
from src.systems.animations import AnimationSystem
from src.systems.boss_chest import BossChest, ChestRewardScreen
from src.systems.game_actions import process_enemy_death, fire_player_projectile
from src.entities.enemy import Enemy, ENEMY_TYPES
from src.ui.passive_swap import PassiveSwapScreen
from src.ui.weapon_swap import WeaponSwapScreen
from src.ui.arsenal_screen import ArsenalScreen
from src.ui.main_menu import MainMenuScreen, load_settings, save_settings
from src.ui.run_summary import RunSummaryScreen
from src.ui.credits_screen import CreditsScreen
from src.ui.portal_screen import PortalMenuScreen
from src.ui.tooltip import Tooltip
from src.systems.run_stats import RunStats
from src.systems.zones import ZONES, ZONE_ORDER, get_zone, get_next_zone
from src.systems.atmosphere import AtmosphericSystem
from src.systems.hazards import HazardSystem
from src.systems.portal import Portal
from src.ui.debug_menu import DebugMenu
from src.ui.debug_overlay import DebugOverlay
from src.font_cache import get_font
from src.ui.cursor import draw_cursor as _draw_cursor_fn
from src.systems.compendium import Compendium, DISPLAY_NAMES as _CDISP, ENEMY_ZONES as _CZONES
from src.ui.toast import ToastManager
from src.ui.compendium_screen import CompendiumScreen
from src.systems.profile import PlayerProfile, create_profile
from src.ui.name_entry_screen import NameEntryScreen
from src.systems.telemetry import TelemetryClient
from src.ui.consent_screen import ConsentScreen
from src.ui.leaderboard_screen import LeaderboardScreen


class Game:
    """Main game class — owns the loop, state, and all subsystems."""

    def __init__(self, profile: PlayerProfile | None = None):
        pygame.init()
        self.game_settings = load_settings()
        flags = pygame.FULLSCREEN if self.game_settings.get("fullscreen") else 0
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        # ── Zoom viewport: world is rendered here then scaled to full screen ──
        self._vp_w = int(SCREEN_WIDTH / CAMERA_ZOOM)
        self._vp_h = int(SCREEN_HEIGHT / CAMERA_ZOOM)
        self._world_surf = pygame.Surface((self._vp_w, self._vp_h))
        self.running = True
        self.game_over = False
        self._game_over_start_time = 0
        # Profile — always present; create a local one if none was passed
        self.profile: PlayerProfile = profile or create_profile()
        self.main_menu = MainMenuScreen(display_name=self.profile.display_name)
        self.char_select = CharacterSelectScreen()
        self.char_class = None  # set after selection
        self.run_summary = RunSummaryScreen()
        self.credits_screen = CreditsScreen()
        self.portal_menu = PortalMenuScreen()
        self._portal_next_zone: str = ""
        self._portal_summary_mode: bool = False
        self.legacy = LegacyData(storage=self.profile.storage)
        self.legacy_screen = LegacyScreen(self.legacy)
        self._legacy_points_earned = 0

        self._show_loading_screen()
        self._init_world()

        # Hide OS cursor — we draw our own
        pygame.mouse.set_visible(False)

        # Controller / gamepad support
        pygame.joystick.init()
        self._joystick: object = None
        self._ctrl_aim_x = 0.0
        self._ctrl_aim_y = 0.0
        if pygame.joystick.get_count() > 0:
            self._joystick = pygame.joystick.Joystick(0)
            self._joystick.init()

        # Debug / dev tools
        self.debug_menu = DebugMenu()
        self.debug_overlay = DebugOverlay()
        self.auto_attack = False
        self._burst_queue: list[tuple[int, float, float]] = []  # (fire_at_ms, fx, fy)
        self.paused = False
        self._pause_selected = 0
        self._pause_options = ["Resume", "Switch Weapon", "Settings", "Quit to Menu", "Quit Game"]
        self._debug_mode = False

        # Compendium + notifications (persist across runs)
        self.compendium = Compendium(storage=self.profile.storage)
        self.toasts = ToastManager()
        self.compendium_screen = CompendiumScreen(self.compendium)

        # Show name entry screen on first launch (runs synchronously before main loop)
        if self.profile.needs_name():
            self._run_name_entry_sync()
            self.main_menu.display_name = self.profile.display_name

        # Analytics / leaderboard
        self.telemetry = TelemetryClient(SUPABASE_URL, SUPABASE_ANON_KEY)
        self.consent_screen = ConsentScreen()
        self.leaderboard_screen = LeaderboardScreen(self.telemetry)

    def _show_loading_screen(self):
        """Draw a loading frame so the window doesn't appear frozen."""
        self.screen.fill((8, 8, 12))
        font = pygame.font.SysFont("consolas", 28, bold=True)
        text = font.render("LOADING...", True, (160, 160, 180))
        self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
        sub = pygame.font.SysFont("consolas", 14)
        hint = sub.render("initialising systems...", True, (80, 80, 100))
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)))
        pygame.display.flip()

    def _run_name_entry_sync(self):
        """Block until the player has typed and confirmed a display name.
        Called from __init__ on first launch before the main async loop,
        and from the main menu 'Change Name' option."""
        name_entry = NameEntryScreen()
        name_entry.activate(suggested=self.profile.display_name)
        clock = pygame.time.Clock()
        while name_entry.active:
            dt = clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                name_entry.handle_event(event)
            name_entry.update(dt)
            name_entry.draw(self.screen)
            pygame.display.flip()
        self.profile.display_name = name_entry.result
        self.profile.save()

    def _submit_run_telemetry(self, wave: int, zone: str,
                              char_class: str, victory: bool) -> None:
        """Submit run analytics and leaderboard update if player consented."""
        if not self.profile.analytics_consent:
            return
        import time as _time
        rs = self.run_stats
        run_entry = {
            "timestamp": _time.strftime("%Y-%m-%d %H:%M:%S"),
            "char_class": char_class,
            "zone": zone,
            "wave": wave,
            "level": self.player.level,
            "victory": victory,
            "run_time_s": round(rs.get_run_time() / 1000, 1),
            "kills": rs.total_kills,
            "boss_kills": rs.boss_kills,
            "damage_dealt": rs.total_damage_dealt,
            "damage_taken": rs.total_damage_taken,
            "highest_hit": rs.highest_hit,
            "total_healed": rs.total_healed,
            "killed_by": rs.killed_by,
            "zones_completed": rs.zones_completed,
            "upgrades": rs.upgrades_taken,
            "weapons": {k: v for k, v in rs.weapon_stats.items()},
            "passives": {k: v["procs"] for k, v in rs.passive_stats.items()},
        }
        self.telemetry.submit_run(
            self.profile.player_id,
            self.profile.display_name,
            self.profile.platform,
            run_entry,
        )
        self.telemetry.submit_leaderboard(
            self.profile.player_id,
            self.profile.display_name,
            self.profile.platform,
            char_class,
            wave,
            _time.strftime("%Y-%m-%d"),
        )

    def _on_credits_done(self):
        """Callback after credits screen is dismissed — show run summary."""
        self.run_summary.activate(
            self.run_stats, self.spawner.wave,
            self.current_zone, self._legacy_points_earned,
            self.player.level, victory=True)

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
        self.current_zone = getattr(self, "current_zone", "wasteland")
        self.environment = EnvironmentSystem(self.current_zone)
        self.campfire = Campfire()
        self.lighting = LightingSystem()
        # Stop any lingering boss music before the old SoundManager is replaced
        if hasattr(self, 'sounds'):
            self.sounds.stop_boss_music()
        self.sounds = SoundManager()
        self.hud = HUD()
        self.minimap = Minimap()
        self.levelup_screen = LevelUpScreen()
        self.chest_reward = ChestRewardScreen()
        self.passive_swap = PassiveSwapScreen()
        self.weapon_swap = WeaponSwapScreen()
        self.arsenal_screen = ArsenalScreen()
        self.boss_chests: list[BossChest] = []
        self.animations = AnimationSystem()
        self.run_stats = RunStats()
        self.atmosphere = AtmosphericSystem()
        self.hazard_system = HazardSystem()
        self.portal: Portal | None = None
        self._zone_transition = False
        self._zone_transition_time = 0
        self.combat_font = pygame.font.SysFont("consolas", 18, bold=True)
        self.game_over = False
        self._game_over_start_time = 0
        self._last_player_pos = (world_cx, world_cy)
        self._step_accumulator = 0.0

        # Kill tracking
        self.kills = 0
        self.boss_kills = 0

        # Damage vignette feedback
        self._last_damage_time = 0
        self._last_damage_pct = 0.0
        self._dmg_vig_cache = None   # (bucket, Surface)
        # Super energy lockout — blocks energy gain for 4 s after firing
        self._super_energy_lockout_until = 0
        # Screenshot capture queue — (capture_at_ms, tag) pairs
        self._pending_auto_shots: list[tuple[int, str]] = []
        # Kill streak combo feedback
        self._kill_streak = 0
        self._kill_streak_time = 0

        # Super skill charge tracking
        self._super_charging = False
        # Frozen screenshot behind the portal menu (prevents game world animation flashing)
        self._portal_bg: pygame.Surface | None = None
        # Passive timers
        self._nano_regen_timer = 0
        self._second_wind_used = False
        self._legacy_points_earned = 0

        # Level-up fanfare state
        self._levelup_fanfare_time = 0
        self._levelup_fanfare_duration = 400

        # Player death animation state
        self._player_dying = False
        self._player_death_time = 0
        self._player_death_duration = 2200  # ms before game_over screen appears

        # Zone intro cutscene state
        self._zone_intro_active = True
        self._zone_intro_start = 0   # set on first drawn frame
        self._zone_intro_duration = 3000  # ms (fade in → hold → fade out)

        # Wave countdown state (shown between waves)
        self._wave_countdown_end = 0  # timestamp when countdown finishes
        self._wave_countdown_secs = 0

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

        # Zone setup
        zone_data = get_zone(self.current_zone)
        self.game_map.set_colors(zone_data.get("tile_colors", {}))
        self.game_map.set_zone(self.current_zone)
        self.atmosphere.set_zone(self.current_zone, zone_data)
        self.hazard_system.set_zone(self.current_zone, zone_data)
        self.run_stats.set_weapon(self.player.weapon_name, self.player.weapon.get("name", ""),
                                   self.player.weapon.get("cooldown", 500))
        self.run_stats.set_zone(self.current_zone)
        self.spawner.set_zone(zone_data)
        self.sounds.set_zone_music(self.current_zone)
        self.sounds.start_music()

    async def run(self):
        self.sounds.start_music()
        while self.running:
            dt = self.clock.tick(FPS)
            await asyncio.sleep(0)  # yield to browser each frame (pygbag)
            now = pygame.time.get_ticks()

            # Main menu phase
            if self.main_menu.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    if self.debug_menu.active:
                        dm_result = self.debug_menu.handle_event(event)
                        if dm_result == "back":
                            self.debug_menu.active = False
                        continue
                    if self.compendium_screen.active:
                        self.compendium_screen.handle_event(event)
                        continue
                    if self.leaderboard_screen.active:
                        self.leaderboard_screen.handle_event(event)
                        continue
                    if self.consent_screen.active:
                        self.consent_screen.handle_event(event)
                        if not self.consent_screen.active:
                            # Decision made — save and proceed to char select
                            self.profile.analytics_consent = self.consent_screen.result
                            self.profile.save()
                            self.char_select.active = True
                        continue
                    result = self.main_menu.handle_event(event)
                    if result == "new_run":
                        self._debug_mode = self.main_menu.settings.get("dev_options", False)
                        if self.profile.needs_consent():
                            self.consent_screen.activate()
                        else:
                            self.char_select.active = True
                    elif result == "compendium":
                        self.compendium_screen.activate()
                    elif result == "leaderboard":
                        self.leaderboard_screen.activate(self.profile.player_id)
                    elif result == "change_name":
                        self._run_name_entry_sync()
                        self.main_menu.display_name = self.profile.display_name
                    elif result == "debug_menu":
                        self.debug_menu.active = True
                    elif result == "quit":
                        self.running = False
                self._apply_settings()
                if self.debug_menu.active:
                    self.debug_menu.draw(self.screen)
                elif self.compendium_screen.active:
                    self.compendium_screen.draw(self.screen)
                elif self.leaderboard_screen.active:
                    self.leaderboard_screen.draw(self.screen)
                else:
                    self.main_menu.draw(self.screen)
                if self.consent_screen.active:
                    self.consent_screen.draw(self.screen)
                _mx, _my = pygame.mouse.get_pos()
                _draw_cursor_fn(self.screen, _mx, _my, "default", pygame.time.get_ticks())
                pygame.display.flip()
                continue

            # Credits screen phase (after final boss victory)
            if self.credits_screen.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    self.credits_screen.handle_event(event)
                self.credits_screen.draw(self.screen)
                _mx, _my = pygame.mouse.get_pos()
                _draw_cursor_fn(self.screen, _mx, _my, "default", pygame.time.get_ticks())
                pygame.display.flip()
                continue

            # Run summary phase
            if self.run_summary.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    done = self.run_summary.handle_event(event)
                    if done:
                        if self._portal_summary_mode:
                            # Return to portal menu after viewing mid-run summary
                            self._portal_summary_mode = False
                            self.portal_menu.active = True
                        else:
                            self.legacy_screen.activate(
                                self.spawner.wave, self.kills,
                                self._legacy_points_earned)
                self.run_summary.draw(self.screen)
                _mx, _my = pygame.mouse.get_pos()
                _draw_cursor_fn(self.screen, _mx, _my, "default", pygame.time.get_ticks())
                pygame.display.flip()
                continue

            # Portal menu phase (between zones)
            if self.portal_menu.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        break
                    # Route events to compendium when it's open
                    if self.compendium_screen.active:
                        result = self.compendium_screen.handle_event(event)
                        if result == "back":
                            # Compendium closed — return to portal menu
                            self.compendium_screen.active = False
                    else:
                        action = self.portal_menu.handle_event(event)
                        if action == "continue":
                            self._portal_bg = None
                            self.current_zone = self._portal_next_zone
                            self._transition_to_zone(self._portal_next_zone)
                        elif action == "summary":
                            self._portal_summary_mode = True
                            self._legacy_points_earned = 0
                            self.run_summary.activate(
                                self.run_stats, self.spawner.wave,
                                self.current_zone, 0,
                                self.player.level, victory=False)
                        elif action == "compendium":
                            self.compendium_screen.activate()
                # Draw — compendium fills its own bg; portal menu draws over frozen screenshot
                if self.compendium_screen.active:
                    self.compendium_screen.draw(self.screen)
                else:
                    if self._portal_bg is not None:
                        self.screen.blit(self._portal_bg, (0, 0))
                    else:
                        self._draw()
                    self.portal_menu.draw(self.screen)
                _mx, _my = pygame.mouse.get_pos()
                _draw_cursor_fn(self.screen, _mx, _my, "default", pygame.time.get_ticks())
                pygame.display.flip()
                continue

            # Character select phase
            if self.char_select.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    result = self.char_select.handle_event(event)
                    if result:
                        self.char_class = result
                        self.current_zone = "wasteland"
                        log.info("Character class selected: %s", result)
                        self._init_world()
                        self._apply_debug_cheats()
                self.char_select.draw(self.screen)
                _mx, _my = pygame.mouse.get_pos()
                _draw_cursor_fn(self.screen, _mx, _my, "default", pygame.time.get_ticks())
                pygame.display.flip()
                continue

            # Legacy screen phase (between runs)
            if self.legacy_screen.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    done = self.legacy_screen.handle_event(event)
                    if done:
                        self.main_menu.active = True
                        self.main_menu.settings_open = False
                        self.main_menu.selected = 0
                self.legacy_screen.draw(self.screen)
                _mx, _my = pygame.mouse.get_pos()
                _draw_cursor_fn(self.screen, _mx, _my, "default", pygame.time.get_ticks())
                pygame.display.flip()
                continue

            try:
                self._handle_events()
                if not self.game_over and not self.paused:
                    self._update(dt, now)
                self._draw()
            except Exception:
                import traceback as _tb
                _tb.print_exc()
                raise
        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------------ events
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    if self.game_over:
                        pass  # handled below
                    elif self._player_dying:
                        pass  # block pause during death animation
                    else:
                        self.paused = not self.paused
                        if self.paused:
                            self._pause_selected = 0
                        self.sounds.play("pause" if self.paused else "unpause")
                    continue

            # Pause menu navigation
            if self.paused:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_w, pygame.K_UP):
                        self._pause_selected = (self._pause_selected - 1) % len(self._pause_options)
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        self._pause_selected = (self._pause_selected + 1) % len(self._pause_options)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                        opt = self._pause_options[self._pause_selected]
                        if opt == "Resume":
                            self.paused = False
                            self.sounds.play("unpause")
                        elif opt == "Switch Weapon":
                            self.paused = False
                            self.arsenal_screen.activate(self.player.arsenal, self.player.weapon_name)
                        elif opt == "Settings":
                            self.main_menu.settings_open = True
                            self.main_menu.settings_selected = 0
                        elif opt == "Quit to Menu":
                            self.paused = False
                            self.game_over = False
                            self.main_menu.active = True
                            self.main_menu.settings_open = False
                        elif opt == "Quit Game":
                            self.paused = False
                            self.running = False
                    elif event.key == pygame.K_f:
                        self.auto_attack = not self.auto_attack
                        if self._debug_mode:
                            self.debug_overlay.log(
                                f"Auto-attack {'ON' if self.auto_attack else 'OFF'}")
                continue

            # Game-over input (R to view run summary)
            if self.game_over:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.run_summary.activate(
                        self.run_stats, self.spawner.wave,
                        self.current_zone, self._legacy_points_earned,
                        self.player.level, victory=False)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    btns = getattr(self.hud, '_gameover_btns', {})
                    if btns.get('run_summary') and btns['run_summary'].collidepoint(event.pos):
                        self.run_summary.activate(
                            self.run_stats, self.spawner.wave,
                            self.current_zone, self._legacy_points_earned,
                            self.player.level, victory=False)
                    elif btns.get('quit_to_menu') and btns['quit_to_menu'].collidepoint(event.pos):
                        self.game_over = False
                        self.main_menu.active = True
                        self.main_menu.settings_open = False
                    elif btns.get('quit') and btns['quit'].collidepoint(event.pos):
                        self.running = False
                continue

            # Chest reward screen intercepts input
            if self.chest_reward.active:
                self.chest_reward.handle_event(event)
                if not self.chest_reward.active:
                    try:
                        self._apply_chest_rewards()
                    except Exception:
                        log.exception("ERROR applying chest rewards")
                continue

            # Passive swap screen intercepts input
            if self.passive_swap.active:
                result = self.passive_swap.handle_event(event)
                if result is not None:
                    self._apply_passive_swap(result)
                continue

            # Weapon swap screen intercepts input
            if self.weapon_swap.active:
                result = self.weapon_swap.handle_event(event)
                if result is not None:
                    self._apply_weapon_swap(result)
                continue

            # Arsenal screen intercepts all input when open
            if self.arsenal_screen.active:
                result = self.arsenal_screen.handle_event(event)
                if result is not None:
                    self._apply_arsenal_equip(result)
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
                # Toggle auto-attack
                if event.key == pygame.K_f:
                    self.auto_attack = not self.auto_attack
                    if self._debug_mode:
                        self.debug_overlay.log(
                            f"Auto-attack {'ON' if self.auto_attack else 'OFF'}")
                # Screenshot — F9
                if event.key == pygame.K_F9:
                    self._save_screenshot("manual")
                # Attack — Space or Left click proxy via J key
                if event.key in (pygame.K_SPACE, pygame.K_j) and not self._player_dying and not self.game_over:
                    if self.player.try_attack(now):
                        if not fire_player_projectile(self.player, self.player_projectiles, self.sounds):
                            self.sounds.play(self.player.weapon.get("sound", "swing"))
                            self.animations.add_screen_shake(1)
                        else:
                            self._maybe_queue_burst(now)
                # Dash — Shift or K
                if event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_k):
                    if self.player.try_dash(now):
                        self.sounds.play("dash")

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self._player_dying and not self.game_over:
                now = pygame.time.get_ticks()
                if self.player.try_attack(now):
                    if not fire_player_projectile(self.player, self.player_projectiles, self.sounds):
                        self.sounds.play(self.player.weapon.get("sound", "swing"))
                        self.animations.add_screen_shake(1)
                    else:
                        self._maybe_queue_burst(now)

            # Right-click: start super skill charge when energy is full
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and not self._player_dying and not self.game_over:
                if self.player.energy >= self.player.max_energy:
                    self._super_charging = True

            # Right-click release: fire super skill
            if event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                if self._super_charging and self.player.energy >= self.player.max_energy:
                    self._fire_super_skill()
                self._super_charging = False

            # ── Gamepad: hot-plug ──
            if event.type == pygame.JOYDEVICEADDED:
                self._joystick = pygame.joystick.Joystick(event.device_index)
                self._joystick.init()
            if event.type == pygame.JOYDEVICEREMOVED:
                self._joystick = None
                self._ctrl_aim_x = 0.0
                self._ctrl_aim_y = 0.0

            # ── Gamepad buttons ──
            if event.type == pygame.JOYBUTTONDOWN and not self._player_dying and not self.game_over:
                now = pygame.time.get_ticks()
                if event.button == 0:  # A / Cross — attack
                    if self.player.try_attack(now):
                        if not fire_player_projectile(self.player, self.player_projectiles, self.sounds):
                            self.sounds.play(self.player.weapon.get("sound", "swing"))
                            self.animations.add_screen_shake(1)
                        else:
                            self._maybe_queue_burst(now)
                elif event.button == 1:  # B / Circle — dash
                    if self.player.try_dash(now):
                        self.sounds.play("dash")
                elif event.button in (5, 7):  # RB / RT — super skill charge
                    if self.player.energy >= self.player.max_energy:
                        self._super_charging = True
            if event.type == pygame.JOYBUTTONUP:
                if event.button in (5, 7):
                    if self._super_charging and self.player.energy >= self.player.max_energy:
                        self._fire_super_skill()
                    self._super_charging = False

    def _apply_levelup_choice(self, choice: dict):
        p = self.player
        effect = choice["effect"]
        value = choice.get("value", 0)
        base_name = choice.get("base_name", choice.get("name", ""))
        tier = choice.get("tier", 1)
        log.debug("Applying effect=%s value=%s tier=%s", effect, value, tier)
        # Track tier for stat upgrades
        if effect not in ("passive", "weapon", "heal") and base_name:
            p.upgrade_tiers[base_name] = tier
        # Record upgrade for run stats — skip weapon equips and skip choices
        if effect not in ("weapon", "skip"):
            self.run_stats.record_upgrade(choice.get("name", base_name or "Unknown"))
        if effect == "max_hp":
            p.max_hp += value
            p.hp = min(p.max_hp, p.hp + value)
        elif effect == "damage":
            p.damage += value
        elif effect == "speed":
            p.speed += value
        elif effect == "range":
            p.attack_range += value
            p._range_bonus += value   # persist across weapon swaps
        elif effect == "heal":
            p.hp = p.max_hp
        elif effect == "cooldown":
            p.attack_cooldown = max(80, p.attack_cooldown - value)
            p._cooldown_bonus += value  # persist across weapon swaps
        elif effect == "weapon":
            # Always add to arsenal; then ask if they want to equip it now
            if value not in p.arsenal:
                p.arsenal.append(value)
                from src.systems.weapons import WEAPONS as _WPNS
                wn = _WPNS.get(value, {}).get("name", value)
                self.toasts.show(f"Collected: {wn}", "Switch via PAUSE → Switch Weapon", (255, 200, 50))
            self.weapon_swap.activate(p.weapon_name, value)
        elif effect == "glass_cannon":
            p.damage = int(p.damage * 1.3)
            p.max_hp = max(20, p.max_hp - 20)
            p.hp = min(p.hp, p.max_hp)
            if "glass_cannon" not in p.passives:
                p.passives.append("glass_cannon")
        elif effect == "passive":
            self._try_add_passive(value, choice.get("name", value))
        elif effect == "dash_charges":
            p.dash_charges_max = min(4, p.dash_charges_max + 1)
            p._dash_charges_remaining = p.dash_charges_max
            p.upgrade_tiers[base_name] = tier
        elif effect == "skip":
            pass  # player forfeited the upgrade

    # ── Screenshots ──────────────────────────────────────────────────────────

    _SCREENSHOTS_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "screenshots")

    def _save_screenshot(self, tag: str = "manual"):
        """Save a PNG of the current frame to <project>/screenshots/."""
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        os.makedirs(self._SCREENSHOTS_DIR, exist_ok=True)
        path = os.path.join(self._SCREENSHOTS_DIR, f"{ts}_{tag}.png")
        pygame.image.save(self.screen, path)
        self.toasts.show("Screenshot", os.path.basename(path), (100, 220, 255))

    def _try_add_passive(self, key: str, display_name: str):
        """Add a passive, or open swap screen if slots are full."""
        p = self.player
        if key in p.passives:
            return
        # Count slot passives (glass_cannon doesn't occupy a slot)
        slot_passives = [k for k in p.passives if k != "glass_cannon"]
        if len(slot_passives) < MAX_PASSIVES:
            p.passives.append(key)
        else:
            self.passive_swap.activate(p.passives, key, display_name)

    def _apply_passive_swap(self, result: dict):
        """Handle result from passive swap screen."""
        if result["action"] == "swap":
            old_key = result["remove"]
            new_key = result["add"]
            if old_key in self.player.passives:
                self.player.passives.remove(old_key)
            if new_key not in self.player.passives:
                self.player.passives.append(new_key)
            log.info("Passive swapped: %s -> %s", old_key, new_key)
        else:
            log.info("Passive swap skipped")

    def _apply_weapon_swap(self, result: dict):
        """Handle result from weapon swap screen."""
        if result["action"] == "swap":
            self.player.equip_weapon(result["weapon"])
            self.run_stats.set_weapon(self.player.weapon_name, self.player.weapon.get("name", ""),
                                      self.player.weapon.get("cooldown", 500))
            log.info("Weapon swapped to: %s", result["weapon"])
        else:
            log.info("Weapon swap skipped")

    def _apply_arsenal_equip(self, result: dict):
        """Handle result from arsenal screen — equip a collected weapon."""
        if result["action"] == "equip":
            self.player.equip_weapon(result["weapon"])
            self.run_stats.set_weapon(self.player.weapon_name, self.player.weapon.get("name", ""),
                                      self.player.weapon.get("cooldown", 500))
            wn = self.player.weapon.get("name", result["weapon"])
            self.toasts.show(f"Equipped: {wn}", "", (100, 220, 100))
            log.info("Arsenal equip: %s", result["weapon"])
        self.paused = False

    def _fire_super_skill(self):
        """Fire the class super skill and consume all energy."""
        p = self.player
        now = pygame.time.get_ticks()
        p.energy = 0
        cls = getattr(p, "char_class", "knight")

        # Yellow burst particles at player — visual pop without blinding flash
        self.animations.spawn_death_burst(p.x, p.y, (255, 220, 40), count=28)
        for _ba in range(0, 360, 36):
            _br = 42
            self.animations.spawn_death_burst(
                p.x + _br * math.cos(math.radians(_ba)),
                p.y + _br * math.sin(math.radians(_ba)),
                (255, 255, 120), count=5)
        # Lock energy accumulation for 4 seconds so super can't chain instantly
        self._super_energy_lockout_until = now + 4000
        # Brief invincibility so the player can't die in their own super animation
        p.invincible = True
        p.invincible_timer = now
        p.invincible_duration = max(p.invincible_duration, 900)

        if cls == "archer":
            # STORM BARRAGE — 5 massive explosive arrows spread toward cursor
            _DEAD = 0.15
            if self._joystick and (abs(self._ctrl_aim_x) > _DEAD or abs(self._ctrl_aim_y) > _DEAD):
                aim_l = math.hypot(self._ctrl_aim_x, self._ctrl_aim_y)
                dx = self._ctrl_aim_x / aim_l if aim_l > 0 else 1.0
                dy = self._ctrl_aim_y / aim_l if aim_l > 0 else 0.0
            else:
                mx, my = pygame.mouse.get_pos()
                world_x = mx / CAMERA_ZOOM + self.camera.x
                world_y = my / CAMERA_ZOOM + self.camera.y
                dx = world_x - p.x
                dy = world_y - p.y
                length = math.hypot(dx, dy)
                if length > 0:
                    dx, dy = dx / length, dy / length
            damage = int(p.damage * p.damage_multiplier * 40)
            base_angle = math.atan2(dy, dx)
            for offset in (-0.30, -0.15, 0.0, 0.15, 0.30):
                a = base_angle + offset
                self.player_projectiles.spawn_grenades(
                    p.x, p.y, math.cos(a), math.sin(a),
                    damage=damage, count=1, speed=22.0, lifetime=1200,
                    splash_radius=240, style="bolt", is_super=True,
                )
            # Burst flash at player position
            for _ba in range(0, 360, 45):
                _r = 50
                self.animations.spawn_death_burst(
                    p.x + _r * math.cos(math.radians(_ba)),
                    p.y + _r * math.sin(math.radians(_ba)),
                    (255, 180, 40), count=8)
            self.animations.add_screen_shake(38)
            self.sounds.play("boss_roar")
            self.sounds.play("bolt_boom")

        elif cls == "knight":
            # INFERNAL CLEAVE — massive arc melee swing, blue fire DOT on all hit enemies
            _DEAD = 0.15
            if self._joystick and (abs(self._ctrl_aim_x) > _DEAD or abs(self._ctrl_aim_y) > _DEAD):
                aim_l = math.hypot(self._ctrl_aim_x, self._ctrl_aim_y)
                dx = self._ctrl_aim_x / aim_l if aim_l > 0 else 1.0
                dy = self._ctrl_aim_y / aim_l if aim_l > 0 else 0.0
            else:
                mx, my = pygame.mouse.get_pos()
                world_x = mx / CAMERA_ZOOM + self.camera.x
                world_y = my / CAMERA_ZOOM + self.camera.y
                dx = world_x - p.x
                dy = world_y - p.y
                length = math.hypot(dx, dy)
                if length > 0:
                    dx, dy = dx / length, dy / length

            ARC_RANGE = 220.0
            ARC_HALF_RAD = math.radians(80)   # 160° total sweep
            base_angle = math.atan2(dy, dx)
            damage = int(p.damage * p.damage_multiplier * 22)

            hit_count = 0
            for _e in self.spawner.get_alive_enemies():
                if not _e.alive:
                    continue
                ex = _e.x - p.x
                ey = _e.y - p.y
                dist = math.hypot(ex, ey)
                if dist > ARC_RANGE + _e.size:
                    continue
                # Angle check — is enemy within the arc cone?
                enemy_angle = math.atan2(ey, ex)
                angle_diff = abs(math.atan2(
                    math.sin(enemy_angle - base_angle),
                    math.cos(enemy_angle - base_angle)))
                if angle_diff > ARC_HALF_RAD:
                    continue
                _e.take_damage(damage, ex, ey, now)
                _e.statuses.apply("blue_fire", now)
                self.combat._add_damage_number(_e.x, _e.y - _e.size - 10, damage, (80, 180, 255))
                self.animations.spawn_death_burst(_e.x, _e.y, (60, 140, 255), count=14)
                self.animations.spawn_hit_sparks(_e.x, _e.y, count=8)
                hit_count += 1

            # Sweeping arc particle trail + shockwave ring
            self.animations.spawn_arc_sweep(p.x, p.y, dx, dy, arc_deg=160, arc_range=ARC_RANGE)
            # Central flash burst at player
            for _bi in range(0, 360, 30):
                self.animations.spawn_death_burst(
                    p.x + 30 * math.cos(math.radians(_bi)),
                    p.y + 30 * math.sin(math.radians(_bi)),
                    (100, 180, 255), count=6)
            self.animations.add_screen_shake(45)
            self.sounds.play("boss_roar")
            self.sounds.play("swing")

        elif cls == "jester":
            # CHAOS ERUPTION — 12 grenades + rainbow death bursts
            damage = int(p.damage * p.damage_multiplier * 16)
            for i in range(12):
                angle = math.radians(i * 30)
                self.player_projectiles.spawn_grenades(
                    p.x, p.y, math.cos(angle), math.sin(angle),
                    damage=damage, count=1, speed=10.0, lifetime=1000,
                    splash_radius=180,
                )
            # Inner ring of faster grenades
            damage2 = int(p.damage * p.damage_multiplier * 10)
            for i in range(6):
                angle = math.radians(i * 60 + 15)
                self.player_projectiles.spawn_grenades(
                    p.x, p.y, math.cos(angle), math.sin(angle),
                    damage=damage2, count=1, speed=6.0, lifetime=700,
                    splash_radius=140,
                )
            # Confetti death bursts in 6 directions
            _burst_colors = [(255,80,200),(80,255,80),(255,220,0),(80,200,255),(255,120,50),(200,80,255)]
            for _bi, _ba in enumerate(range(0, 360, 60)):
                _r = 60
                self.animations.spawn_death_burst(
                    p.x + _r * math.cos(math.radians(_ba)),
                    p.y + _r * math.sin(math.radians(_ba)),
                    _burst_colors[_bi], count=12)
            self.animations.add_screen_shake(42)
            self.sounds.play("boss_roar")
            self.sounds.play("confetti_boom")

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
            elif effect == "passive":
                self._try_add_passive(value, r.get("name", value))
            elif effect == "weapon":
                p.equip_weapon(value)
                self.toasts.show(f"Equipped: {r['name']}", "New weapon equipped!", (255, 200, 50))
            elif effect in ("damage", "speed", "range", "cooldown", "max_hp",
                            "weapon_upgrade", "dash_charges", "glass_cannon"):
                self._apply_levelup_choice(r)
                continue  # run_stats already recorded inside _apply_levelup_choice
            # Record all chest rewards as upgrades in run stats
            self.run_stats.record_upgrade(r.get("name", effect))

    # ------------------------------------------------------------------ update
    _ZONE_TOAST_COLORS = {"wasteland": (80, 180, 80), "city": (100, 140, 220), "abyss": (160, 80, 240)}

    def _maybe_queue_burst(self, now: int) -> None:
        """Queue follow-up burst shots for weapons with burst_count > 1."""
        w = self.player.weapon
        burst_count = w.get("burst_count", 1)
        if burst_count <= 1:
            return
        delay = w.get("burst_delay_ms", 120)
        fx, fy = self.player.facing_x, self.player.facing_y
        for i in range(1, burst_count):
            self._burst_queue.append((now + i * delay, fx, fy))

    def _record_kill_compendium(self, enemy) -> None:
        """Record enemy kill; show toast on first encounter."""
        if self.compendium.on_kill(enemy.enemy_type, self.spawner.wave):
            name = _CDISP.get(enemy.enemy_type, enemy.enemy_type)
            zc = self._ZONE_TOAST_COLORS.get(_CZONES.get(enemy.enemy_type, ""), (200, 200, 200))
            self.toasts.show(f"NEW: {name}", "Added to Compendium", zc)

    def _update(self, dt: float, now: int):
        # Burst fire queue (e.g. double dagger in quick succession)
        for _bt, _bfx, _bfy in list(self._burst_queue):
            if now >= _bt:
                self._burst_queue.remove((_bt, _bfx, _bfy))
                _bw = self.player.weapon
                if _bw.get("projectile") and not _bw.get("orbiter") and not _bw.get("grenade"):
                    _bdmg = int(self.player.damage * _bw["damage_mult"] * self.player.damage_multiplier)
                    self.player_projectiles.spawn_daggers(
                        self.player.x, self.player.y, _bfx, _bfy, _bdmg,
                        1, _bw.get("proj_speed", 7.0), _bw.get("proj_lifetime", 800),
                        _bw.get("proj_visual", "dagger"), _bw.get("piercing", False))
                    self.sounds.play("throw")

        # Auto-attack: fire at fastest interval when toggled or mouse held
        if self.auto_attack or pygame.mouse.get_pressed()[0]:
            if not (self.levelup_screen.active or self.chest_reward.active
                    or self.passive_swap.active or self.weapon_swap.active
                    or self.arsenal_screen.active
                    or self.paused or self._player_dying or self.game_over):
                if self.player.try_attack(now):
                    from src.systems.game_actions import fire_player_projectile as _fpp
                    if not _fpp(self.player, self.player_projectiles, self.sounds):
                        self.sounds.play(self.player.weapon.get("sound", "swing"))
                        self.animations.add_screen_shake(1)
                    else:
                        self._maybe_queue_burst(now)

        # Debug cheats: god mode and no cooldown
        if self._debug_mode:
            if self.debug_menu.cheats.get("god_mode"):
                self.player.hp = self.player.max_hp
            if self.debug_menu.cheats.get("no_cooldown"):
                self.player.attack_cooldown = 0
                self.player.last_attack_time = 0

        # Level-up fanfare timer: open choices after freeze completes
        if self._levelup_fanfare_time and now - self._levelup_fanfare_time >= self._levelup_fanfare_duration:
            self._levelup_fanfare_time = 0
            self.levelup_screen.activate(self.player.weapon_name, self.player.char_class,
                                         self.player.passives,
                                         base_damage=self.player.damage,
                                         current_weapon=self.player.weapon,
                                         upgrade_tiers=self.player.upgrade_tiers,
                                         arsenal=self.player.arsenal)
            log.info("Level-up screen activated, choices=%s",
                     [c.get('name','?') for c in self.levelup_screen.choices])

        # Pause gameplay during level-up, chest reward, passive swap, or fanfare
        if (self.levelup_screen.active or self.chest_reward.active
                or self.passive_swap.active or self.weapon_swap.active
                or self.arsenal_screen.active
                or self._levelup_fanfare_time):
            return

        keys = pygame.key.get_pressed()
        world_w = self.game_map.pixel_width
        world_h = self.game_map.pixel_height

        # ── Controller axis reading ──
        if self._joystick:
            _DEAD = 0.15
            try:
                _lx = self._joystick.get_axis(0)
                _ly = self._joystick.get_axis(1)
                _rx = self._joystick.get_axis(2) if self._joystick.get_numaxes() > 2 else 0.0
                _ry = self._joystick.get_axis(3) if self._joystick.get_numaxes() > 3 else 0.0
            except Exception:
                _lx = _ly = _rx = _ry = 0.0
            # Left stick → merge into movement keys
            if abs(_lx) > _DEAD or abs(_ly) > _DEAD:
                _base_keys = keys
                _lx_c, _ly_c = _lx, _ly
                class _MergedKeys:
                    def __getitem__(self_, k):
                        if k in (pygame.K_w, pygame.K_UP):    return 1 if _ly_c < -_DEAD else _base_keys[k]
                        if k in (pygame.K_s, pygame.K_DOWN):  return 1 if _ly_c > _DEAD  else _base_keys[k]
                        if k in (pygame.K_a, pygame.K_LEFT):  return 1 if _lx_c < -_DEAD else _base_keys[k]
                        if k in (pygame.K_d, pygame.K_RIGHT): return 1 if _lx_c > _DEAD  else _base_keys[k]
                        return _base_keys[k]
                keys = _MergedKeys()
            # Right stick → store aim direction for mouse-aim override below
            if abs(_rx) > _DEAD or abs(_ry) > _DEAD:
                self._ctrl_aim_x = _rx
                self._ctrl_aim_y = _ry
            else:
                self._ctrl_aim_x = 0.0
                self._ctrl_aim_y = 0.0

        # During player death animation, freeze player input (no movement)
        _dying_keys = None
        if self._player_dying:
            class _FrozenKeys:
                def __getitem__(self, _): return 0
            _dying_keys = _FrozenKeys()
        self.player.update(dt, now, _dying_keys if _dying_keys else keys, world_w, world_h)

        # Wind trail while dashing
        if self.player.is_dashing:
            self.animations.spawn_dash_trail(
                self.player.x, self.player.y,
                self.player.dash_dx, self.player.dash_dy)

        # Track HP this frame to detect any damage for vignette
        _frame_start_hp = self.player.hp

        # Passive: nano_regen — heal 1 HP every 2s
        if "nano_regen" in self.player.passives:
            if now - self._nano_regen_timer >= 2000:
                self._nano_regen_timer = now
                self.player.hp = min(self.player.max_hp, self.player.hp + 1)

        # Aiming — controller right stick takes priority, then mouse
        _DEAD = 0.15
        if self._joystick and (abs(self._ctrl_aim_x) > _DEAD or abs(self._ctrl_aim_y) > _DEAD):
            aim_len = math.hypot(self._ctrl_aim_x, self._ctrl_aim_y)
            if aim_len > 0.0:
                self.player.facing_x = self._ctrl_aim_x / aim_len
                self.player.facing_y = self._ctrl_aim_y / aim_len
        else:
            # Mouse aiming: unzoom screen coords → viewport coords → world coords
            mx, my = pygame.mouse.get_pos()
            cx, cy = self.camera.x, self.camera.y
            world_mx = mx / CAMERA_ZOOM + cx
            world_my = my / CAMERA_ZOOM + cy
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

        # Zone intro: start timer on first update, end it after duration
        if self._zone_intro_active:
            if self._zone_intro_start == 0:
                self._zone_intro_start = now
            elif now - self._zone_intro_start >= self._zone_intro_duration:
                self._zone_intro_active = False
                self.spawner.last_wave_end = now  # countdown starts fresh after intro
        else:
            self.spawner.update(now, self.player.x, self.player.y)

        # Track wave countdown: when spawner is idle, countdown until next wave
        if not self.spawner.wave_active and not self._zone_intro_active:
            time_since_wave_end = now - self.spawner.last_wave_end
            remaining_ms = max(0, self.spawner.wave_delay - time_since_wave_end)
            self._wave_countdown_secs = math.ceil(remaining_ms / 1000)
        else:
            self._wave_countdown_secs = 0

        # Sync wave to atmosphere and hazards
        self.atmosphere.set_wave(self.spawner.wave)
        self.hazard_system.set_wave(self.spawner.wave)
        self.atmosphere.update(dt, now, int(self.camera.x), int(self.camera.y),
                               world_w, world_h)

        # Environmental hazards
        hazard_events = self.hazard_system.update(
            now, self.player.x, self.player.y,
            int(self.camera.x), int(self.camera.y),
            world_w, world_h)
        for hev in hazard_events:
            hx, hy = hev["x"], hev["y"]
            hr = hev["radius"]
            hdmg = hev["damage"]
            # Check player in range
            pdist = math.hypot(self.player.x - hx, self.player.y - hy)
            if pdist < hr and not self.player.invincible:
                self.player.hp -= hdmg
                self.player.last_hit_by = hev.get("type", "hazard")
                self.run_stats.record_damage_taken(hdmg)
                self.animations.spawn_hit_sparks(self.player.x, self.player.y)
                self.sounds.play("hit")
            # Pull effect (void rift)
            if hev.get("pull"):
                px, py = hev["pull"]
                self.player.x += px
                self.player.y += py
            # Damage enemies if applicable
            if hev.get("hits_enemies"):
                for enemy in self.spawner.get_alive_enemies():
                    edist = math.hypot(enemy.x - hx, enemy.y - hy)
                    if edist < hr:
                        enemy.take_damage(hdmg, enemy.x - hx, enemy.y - hy, now)

        # Entropic decay (abyss passive damage)
        if self.hazard_system.is_entropic_decay_active():
            # Check if player is near campfire (safe zone)
            cf_dist = math.hypot(self.player.x - self.campfire.x, self.player.y - self.campfire.y)
            if cf_dist > 200 and not self.player.invincible:
                decay_dmg = 2 + (self.spawner.wave - 7)
                if now % 1000 < dt:  # Roughly once per second
                    self.player.hp -= decay_dmg
                    self.player.last_hit_by = "entropic_decay"
                    self.run_stats.record_damage_taken(decay_dmg)

        # Play boss roar on boss wave start + switch to boss music
        if self.spawner.just_started_wave and self.spawner.boss_wave:
            self.sounds.play("boss_roar")
            self.sounds.start_boss_music(self.current_zone)

        # Stop boss music when boss wave ends (no more boss enemies alive)
        if self.sounds.boss_music_playing:
            alive_bosses = [e for e in self.spawner.get_alive_enemies() if e.is_boss]
            if not alive_bosses and not self.spawner.wave_active:
                self.sounds.stop_boss_music()

        # Campfire is active only between waves
        self.campfire.set_active(not self.spawner.wave_active)
        self.campfire.update(now, self.player)

        # Healing prop regrowth
        self.environment.update_healing(now)

        # Lighting system
        self.lighting.update(self.player.x, self.player.y)

        # Pass darkness to combat for XP/damage scaling
        self.combat.darkness_level = self.lighting.darkness

        alive = self.spawner.get_alive_enemies()
        for enemy in alive:
            enemy.update(dt, now, self.player.x, self.player.y, world_w, world_h)
            # Architect: shard split at 30% HP
            if getattr(enemy, '_wants_split', False):
                enemy._wants_split = False
                for _ in range(2):
                    ang = _rng.uniform(0, math.tau)
                    sd = _rng.uniform(80, 160)
                    shard = Enemy(enemy.x + math.cos(ang) * sd,
                                  enemy.y + math.sin(ang) * sd, "rift_walker")
                    shard.hp = int(shard.max_hp * 1.5)
                    self.spawner.enemies.append(shard)
            # Environment collision for enemies too
            ehalf = enemy.size // 2
            enemy.x, enemy.y = self.environment.collide_entity(
                enemy.x, enemy.y, ehalf)
            # Spawn projectile if enemy wants to shoot
            if enemy.wants_to_shoot:
                base_dmg = int(enemy.bullet_damage * (1.0 + self.lighting.darkness * ENEMY_DARKNESS_DMG_BONUS))
                spread_n = getattr(enemy, 'shoot_spread_count', 1)
                spread_arc = getattr(enemy, 'shoot_spread_arc', 0.0)
                # D-lack family fires beam bursts (2 shots side by side)
                is_dlack = enemy.enemy_type == "d_lek"
                proj_style = "beam" if is_dlack else "circle"
                if spread_n <= 1:
                    if is_dlack:
                        # Burst: two parallel beams with slight perpendicular offset
                        dx = self.player.x - enemy.x
                        dy = self.player.y - enemy.y
                        dist_ = math.hypot(dx, dy) or 1
                        nx, ny = -dy / dist_, dx / dist_  # perpendicular unit
                        off = 6
                        for sign in (-1, 1):
                            ox, oy = enemy.x + nx * off * sign, enemy.y + ny * off * sign
                            self.projectiles.spawn(ox, oy, self.player.x, self.player.y,
                                                   base_dmg, proj_style, enemy.enemy_type)
                    else:
                        self.projectiles.spawn(enemy.x, enemy.y,
                                               self.player.x, self.player.y, base_dmg,
                                               proj_style, enemy.enemy_type)
                else:
                    # Fan spread: evenly distribute shots across the arc
                    base_angle = math.atan2(self.player.y - enemy.y,
                                            self.player.x - enemy.x)
                    for s in range(spread_n):
                        offset = (s - (spread_n - 1) / 2.0) * (spread_arc / max(1, spread_n - 1))
                        angle = base_angle + offset
                        tx = enemy.x + math.cos(angle) * 300
                        ty = enemy.y + math.sin(angle) * 300
                        self.projectiles.spawn(enemy.x, enemy.y, tx, ty, base_dmg, proj_style, enemy.enemy_type)
                enemy.wants_to_shoot = False
                self.sounds.play("enemy_shoot")

            # Boss enrage at phase 2 activation
            if getattr(enemy, 'wants_enrage', False):
                enemy.wants_enrage = False
                self.animations.spawn_death_burst(enemy.x, enemy.y, (255, 60, 0), count=24)
                self.animations.add_screen_shake(8)
                self.sounds.play("boss_roar")

            # Cyber dog bark/growl sounds
            if enemy._dog_wants_growl:
                enemy._dog_wants_growl = False
                self.sounds.play("dog_growl")
            if enemy._dog_wants_bark:
                enemy._dog_wants_bark = False
                self.sounds.play("dog_bark")

            # Boss special attack damage + unique effects per type
            if enemy.special_attack_hit and enemy.is_boss:
                spec = enemy._special
                spec_dmg = enemy.damage
                pdist = math.hypot(self.player.x - enemy.x, self.player.y - enemy.y)
                aoe_range = int(enemy.size * enemy._special_aoe_mult)
                hit_player = False

                if spec == "flame_pillar":
                    # Check distance to targeted position
                    tdist = math.hypot(self.player.x - enemy._special_target_x,
                                       self.player.y - enemy._special_target_y)
                    if tdist < aoe_range and not self.player.invincible:
                        hit_player = True
                        self.player.statuses.apply("fire", now)
                elif spec == "void_rift":
                    tdist = math.hypot(self.player.x - enemy._special_target_x,
                                       self.player.y - enemy._special_target_y)
                    if tdist < aoe_range and not self.player.invincible:
                        hit_player = True
                        self.player.statuses.apply("slow", now)
                elif spec == "tentacle_sweep":
                    # Cone check: must be in range AND within sweep angle
                    if pdist < aoe_range and not self.player.invincible:
                        angle_to_player = math.atan2(self.player.y - enemy.y,
                                                     self.player.x - enemy.x)
                        angle_diff = abs((angle_to_player - enemy._sweep_angle + math.pi) % (2 * math.pi) - math.pi)
                        if angle_diff < math.radians(35):
                            hit_player = True
                            # Heavy knockback away from boss
                            kb_str = 15.0
                            kx = math.cos(angle_to_player) * kb_str
                            ky = math.sin(angle_to_player) * kb_str
                            self.player.x += kx
                            self.player.y += ky
                elif spec == "war_cry":
                    # Knockback player + buff nearby enemies
                    if pdist < aoe_range and not self.player.invincible:
                        hit_player = True
                        spec_dmg = enemy.damage // 3  # less damage, more utility
                        angle_away = math.atan2(self.player.y - enemy.y,
                                                self.player.x - enemy.x)
                        self.player.x += math.cos(angle_away) * 12
                        self.player.y += math.sin(angle_away) * 12
                    # Buff nearby enemies with speed boost
                    for ally in alive:
                        if ally is not enemy and ally.alive:
                            adist = math.hypot(ally.x - enemy.x, ally.y - enemy.y)
                            if adist < aoe_range:
                                ally.speed = ENEMY_TYPES[ally.enemy_type]["speed"] * 1.5
                elif spec == "ground_slam":
                    if pdist < aoe_range and not self.player.invincible:
                        hit_player = True
                        # Knockback based on distance (closer = stronger)
                        if pdist > 0:
                            kb = 10.0 * (1.0 - pdist / aoe_range)
                            angle_away = math.atan2(self.player.y - enemy.y,
                                                    self.player.x - enemy.x)
                            self.player.x += math.cos(angle_away) * kb
                            self.player.y += math.sin(angle_away) * kb
                elif spec == "null_burst":
                    if pdist < aoe_range and not self.player.invincible:
                        hit_player = True
                        spec_dmg = enemy.damage // 2  # less per burst since multiple hits
                        self.player.vision_debuff_until = now + 5000
                        self.player.statuses.apply("slow", now)
                        # ── Insanity: lose control for up to 2 s ──
                        self.player.insanity_until = now + _rng.randint(1000, 2000)
                        self.player.statuses.apply("insanity", now)
                elif spec == "buck_charge":
                    # Mega Cyber Deer charges — knockback in the charge direction + heavy dmg
                    if pdist < aoe_range and not self.player.invincible:
                        hit_player = True
                        charge_dx = getattr(enemy, "_charge_dx", 0.0)
                        charge_dy = getattr(enemy, "_charge_dy", 0.0)
                        kb = 22.0
                        self.player.x += charge_dx * kb
                        self.player.y += charge_dy * kb
                        self.animations.add_screen_shake(10)
                elif spec == "elite_volley":
                    # Emperor's Elite Guard: 5-shot fan burst toward player
                    if pdist < aoe_range and not self.player.invincible:
                        hit_player = True
                    dmg = int(enemy.bullet_damage * 1.2)
                    base_ang = math.atan2(self.player.y - enemy.y, self.player.x - enemy.x)
                    for _ei in range(5):
                        _ang = base_ang + (_ei - 2) * 0.20
                        _tx = enemy.x + math.cos(_ang) * 400
                        _ty = enemy.y + math.sin(_ang) * 400
                        self.projectiles.spawn(enemy.x, enemy.y, _tx, _ty, dmg, enemy_type=enemy.enemy_type)
                    self.sounds.play("enemy_shoot")
                else:
                    # Fallback generic AoE
                    if pdist < aoe_range and not self.player.invincible:
                        hit_player = True

                if hit_player:
                    self.player.last_hit_by = enemy.enemy_type
                    self.player.hp -= spec_dmg
                    self.run_stats.record_damage_taken(spec_dmg)
                    self.animations.spawn_hit_sparks(self.player.x, self.player.y, count=8)
                    self.animations.add_screen_shake(5)
                    self.sounds.play("hit")
                enemy.special_attack_hit = False

            # ---- Secondary (phase 2) special attack ----
            if getattr(enemy, 'special2_attack_hit', False) and enemy.is_boss:
                spec2 = enemy._special2
                aoe_range2 = int(enemy.size * enemy._special2_aoe_mult)
                pdist2 = math.hypot(self.player.x - enemy.x, self.player.y - enemy.y)
                hit_player2 = False
                spec2_dmg = enemy.damage

                if spec2 == "missile_barrage":
                    # Fire 3 clustered projectiles toward player with slight spread
                    dmg = int(enemy.bullet_damage * 1.3)
                    for mi in range(3):
                        offset_ang = (mi - 1) * 0.18
                        base_ang = math.atan2(self.player.y - enemy.y, self.player.x - enemy.x)
                        ang = base_ang + offset_ang
                        tx = enemy.x + math.cos(ang) * 400
                        ty = enemy.y + math.sin(ang) * 400
                        self.projectiles.spawn(enemy.x, enemy.y, tx, ty, dmg, enemy_type=enemy.enemy_type)
                    self.sounds.play("enemy_shoot")

                elif spec2 == "bleed_storm":
                    # Ring of 12 projectiles in all directions from boss
                    dmg = int(enemy.bullet_damage * 0.9)
                    for bi in range(12):
                        ang = bi * math.pi * 2 / 12
                        tx = enemy.x + math.cos(ang) * 500
                        ty = enemy.y + math.sin(ang) * 500
                        self.projectiles.spawn(enemy.x, enemy.y, tx, ty, dmg, enemy_type=enemy.enemy_type)
                    self.animations.spawn_death_burst(enemy.x, enemy.y, (200, 50, 50), count=16)
                    self.sounds.play("enemy_shoot")

                elif spec2 == "fire_ring":
                    # 8 fire pillars placed around the player's position
                    for fi in range(8):
                        ang = fi * math.pi / 4
                        ring_r = 80
                        fx = enemy._special2_target_x + math.cos(ang) * ring_r
                        fy = enemy._special2_target_y + math.sin(ang) * ring_r
                        tdist = math.hypot(self.player.x - fx, self.player.y - fy)
                        if tdist < 50 and not self.player.invincible:
                            hit_player2 = True
                            self.player.statuses.apply("fire", now)
                    self.animations.spawn_death_burst(
                        enemy._special2_target_x, enemy._special2_target_y,
                        (255, 100, 20), count=20)

                elif spec2 == "eldritch_pull":
                    # Gravitational pull — yank player toward boss, damage at close range
                    pull_str = 18.0
                    if pdist2 > 0:
                        pull_x = (enemy.x - self.player.x) / pdist2 * pull_str
                        pull_y = (enemy.y - self.player.y) / pdist2 * pull_str
                        self.player.x += pull_x
                        self.player.y += pull_y
                    new_pdist = math.hypot(self.player.x - enemy.x, self.player.y - enemy.y)
                    if new_pdist < aoe_range2 * 0.6 and not self.player.invincible:
                        hit_player2 = True
                        self.player.statuses.apply("bleed", now)
                    self.animations.add_screen_shake(7)

                elif spec2 == "void_cage":
                    # 6 void zones ring the player — deal slow + damage if any hit
                    for ci in range(6):
                        ang = ci * math.pi / 3
                        cage_r = 60
                        cx = enemy._special2_target_x + math.cos(ang) * cage_r
                        cy = enemy._special2_target_y + math.sin(ang) * cage_r
                        tdist = math.hypot(self.player.x - cx, self.player.y - cy)
                        if tdist < 55 and not self.player.invincible:
                            hit_player2 = True
                            self.player.statuses.apply("slow", now)
                    self.animations.spawn_confetti_explosion(
                        enemy._special2_target_x, enemy._special2_target_y)

                elif spec2 == "reality_collapse":
                    # 16-shot burst ring from nexus
                    dmg = int(enemy.bullet_damage * 0.75)
                    for ri in range(16):
                        ang = ri * math.pi * 2 / 16
                        tx = enemy.x + math.cos(ang) * 500
                        ty = enemy.y + math.sin(ang) * 500
                        self.projectiles.spawn(enemy.x, enemy.y, tx, ty, dmg, enemy_type=enemy.enemy_type)
                    # Plus direct vision/slow + insanity at close range
                    if pdist2 < aoe_range2 and not self.player.invincible:
                        hit_player2 = True
                        spec2_dmg = enemy.damage // 2
                        self.player.vision_debuff_until = now + 4000
                        self.player.statuses.apply("slow", now)
                        self.player.insanity_until = now + _rng.randint(800, 1500)
                        self.player.statuses.apply("insanity", now)
                    self.animations.spawn_death_burst(enemy.x, enemy.y, (80, 60, 220), count=24)
                    self.sounds.play("enemy_shoot")

                elif spec2 == "antler_slam":
                    # Mega Cyber Deer phase-2: massive ground slam, freezes player
                    if pdist2 < aoe_range2 and not self.player.invincible:
                        hit_player2 = True
                        spec2_dmg = int(enemy.damage * 1.4)
                        # Radial knockback away from deer
                        angle_away = math.atan2(self.player.y - enemy.y, self.player.x - enemy.x)
                        self.player.x += math.cos(angle_away) * 18
                        self.player.y += math.sin(angle_away) * 18
                        self.player.statuses.apply("freeze", now)
                    self.animations.spawn_death_burst(enemy.x, enemy.y, (140, 210, 255), count=18)
                    self.animations.add_screen_shake(12)

                elif spec2 == "imperial_barrage":
                    # Emperor's Guard phase-2: heavy 5-shot fan at wide spread
                    dmg = int(enemy.bullet_damage * 1.4)
                    base_ang2 = math.atan2(self.player.y - enemy.y, self.player.x - enemy.x)
                    for _ii in range(5):
                        _oang = base_ang2 + (_ii - 2) * 0.22
                        _tx2 = enemy.x + math.cos(_oang) * 450
                        _ty2 = enemy.y + math.sin(_oang) * 450
                        self.projectiles.spawn(enemy.x, enemy.y, _tx2, _ty2, dmg, enemy_type=enemy.enemy_type)
                    self.sounds.play("enemy_shoot")

                else:
                    # Generic fallback
                    if pdist2 < aoe_range2 and not self.player.invincible:
                        hit_player2 = True

                if hit_player2:
                    self.player.last_hit_by = enemy.enemy_type
                    self.player.hp -= spec2_dmg
                    self.run_stats.record_damage_taken(spec2_dmg)
                    self.animations.spawn_hit_sparks(self.player.x, self.player.y, count=10)
                    self.animations.add_screen_shake(6)
                    self.sounds.play("hit")
                enemy.special2_attack_hit = False

            # ---- Supreme D-Lek laser beam ----
            if (enemy.enemy_type == "supreme_d_lek" and enemy._laser_firing):
                # Beam is a line from enemy in _laser_angle direction, ~500px long
                beam_len = 500
                beam_width = 30
                bx = enemy.x + math.cos(enemy._laser_angle) * beam_len
                by = enemy.y + math.sin(enemy._laser_angle) * beam_len
                # Point-to-line-segment distance for player
                px, py = self.player.x, self.player.y
                ax, ay = enemy.x, enemy.y
                t = max(0, min(1, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) /
                                  max(1, (bx - ax) ** 2 + (by - ay) ** 2)))
                closest_x = ax + t * (bx - ax)
                closest_y = ay + t * (by - ay)
                ldist = math.hypot(px - closest_x, py - closest_y)
                # Tick damage every 100ms
                elapsed_lf = now - enemy._laser_fire_start
                if ldist < beam_width and not self.player.invincible and elapsed_lf % 100 < dt:
                    laser_dmg = enemy.damage // 2
                    self.player.last_hit_by = enemy.enemy_type
                    self.player.hp -= laser_dmg
                    self.run_stats.record_damage_taken(laser_dmg)
                    self.player.statuses.apply("fire", now)
                    self.animations.spawn_hit_sparks(self.player.x, self.player.y, count=4)
                    self.sounds.play("hit")
                # Visual: screen shake while beam is active
                if elapsed_lf % 150 < dt:
                    self.animations.add_screen_shake(3)

            # ---- Wind-up shake for sentinel / d-lek ----
            if (enemy.enemy_type in ("iron_sentinel", "supreme_d_lek")
                    and enemy._windup_active):
                elapsed_wu = now - enemy._windup_start
                if elapsed_wu % 200 < dt:
                    self.animations.add_screen_shake(2)

        self.combat.process_player_attack(self.player, alive, now)
        # Screen shake + sparks on every successful melee hit
        if self.combat.damage_log:
            self.animations.add_screen_shake(3)
            self.animations.spawn_hit_sparks(
                self.player.x + self.player.facing_x * 30,
                self.player.y + self.player.facing_y * 30, count=6)
        # Drain melee hit log into run stats + energy-from-damage
        _dmg_energy = 0
        for _wkey, _wdmg in self.combat.damage_log:
            self.run_stats.record_hit(_wkey, _wdmg)
            _dmg_energy += _wdmg
        if _dmg_energy > 0 and now > self._super_energy_lockout_until:
            self.player.energy = min(
                self.player.max_energy,
                self.player.energy + _dmg_energy // 20,   # 1 energy per 20 damage
            )
        self.combat.damage_log.clear()

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
                    # Passive: parry_deflect — fire the bullet back at nearest enemy
                    if "parry_deflect" in self.player.passives:
                        _alive_e = [e for e in self.spawner.get_alive_enemies() if e.alive]
                        if _alive_e:
                            _tgt = min(_alive_e,
                                       key=lambda e: math.hypot(e.x - bullet.x, e.y - bullet.y))
                            _rdx = _tgt.x - bullet.x
                            _rdy = _tgt.y - bullet.y
                            _rdist = math.hypot(_rdx, _rdy)
                            if _rdist > 0:
                                self.player_projectiles.spawn_daggers(
                                    bullet.x, bullet.y,
                                    _rdx / _rdist, _rdy / _rdist,
                                    max(1, bullet.damage * 2),
                                    count=1, speed=10.0, lifetime=1500, visual="bolt")

        # Death bursts & screen shake from melee kills + passive triggers
        _kt = {"kills": self.kills, "boss_kills": self.boss_kills}
        _death_processed: set = set()  # enemy ids processed this frame — prevents double drops
        _kills_before = self.kills
        _boss_kills_before = self.boss_kills
        for enemy in alive:
            if not enemy.alive:
                _eid = id(enemy)
                if _eid not in _death_processed:
                    _death_processed.add(_eid)
                    self._record_kill_compendium(enemy)
                    process_enemy_death(enemy, self.player, alive, self.animations,
                                        self.combat, self.sounds, self.lighting,
                                        self.boss_chests, _kt, self.pickups, now,
                                        toasts=self.toasts)
        self.kills = _kt["kills"]
        self.boss_kills = _kt["boss_kills"]

        # Kill streak combo tracker
        new_kills = self.kills - _kills_before
        new_boss_kills = self.boss_kills - _boss_kills_before
        if new_kills > 0:
            if now - self._kill_streak_time < 2500:
                self._kill_streak += new_kills
            else:
                self._kill_streak = new_kills
            self._kill_streak_time = now

        # Super energy — 10 per kill, 60 per boss kill
        if new_kills > 0 and now > self._super_energy_lockout_until:
            self.player.energy = min(
                self.player.max_energy,
                self.player.energy + new_kills * 10 + new_boss_kills * 60
            )

        # Mirror shade splitting
        for enemy in alive:
            if enemy.wants_to_split:
                enemy.wants_to_split = False
                for _ in range(2):
                    offset_x = _rng.uniform(-40, 40)
                    offset_y = _rng.uniform(-40, 40)
                    clone = Enemy(enemy.x + offset_x, enemy.y + offset_y, "mirror_shade")
                    clone.max_hp = enemy.max_hp // 3
                    clone.hp = clone.max_hp
                    clone.damage = max(1, enemy.damage * 2 // 3)
                    clone._has_split = True
                    clone.spawn_time = now
                    self.spawner.enemies.append(clone)

        # Check if player attack hits a healing prop (any weapon type)
        if self.player.is_attacking:
            healing_drops = self.environment.check_healing_prop_hit(
                self.player.get_attack_rect(), now)
            for ax, ay, kind in healing_drops:
                self._spawn_healing_drop(ax, ay, kind)

        # Check if player projectiles hit healing props
        for proj in self.player_projectiles.daggers:
            if not proj.alive:
                continue
            proj_rect = pygame.Rect(proj.x - 6, proj.y - 6, 12, 12)
            healing_drops = self.environment.check_healing_prop_hit(proj_rect, now)
            for ax, ay, kind in healing_drops:
                self._spawn_healing_drop(ax, ay, kind)

        # Update player-thrown projectiles (daggers, orbiters, grenades)
        thrown_hits, grenade_explosions = self.player_projectiles.update(
            now, alive, world_w, world_h, self.player.x, self.player.y)

        # Grenade explosion effects
        for gx, gy, _gdmg, _splash_r, gstyle in grenade_explosions:
            if gstyle == "bolt":
                self.animations.spawn_bolt_explosion(gx, gy)
                self.sounds.play("bolt_boom")
            else:
                self.animations.spawn_confetti_explosion(gx, gy)
                self.sounds.play("confetti_boom")
            self.animations.add_screen_shake(4)

        for enemy, dmg in thrown_hits:
            # ── Mirror Shade: reflect the hit back as an enemy projectile ──
            if enemy.enemy_type == "mirror_shade":
                ref_dmg = max(1, dmg // 2)
                self.projectiles.spawn(enemy.x, enemy.y, self.player.x, self.player.y, ref_dmg, enemy_type=enemy.enemy_type)
                self.animations.spawn_hit_sparks(enemy.x, enemy.y, count=14)
                self.sounds.play("hit")
                # mirror_shade still takes the damage — just continue to normal processing

            # Record projectile hit in run stats (before crit display modifier)
            self.run_stats.record_hit(self.player.weapon_name, dmg)
            # Weapon on-hit status (fire / poison / etc.)
            _on_hit_s = self.player.weapon.get("on_hit_status")
            if _on_hit_s and enemy.alive:
                enemy.statuses.apply(_on_hit_s, now)
            # Passive: fire_strikes — 35% chance to ignite on any projectile hit
            if "fire_strikes" in self.player.passives and enemy.alive and _rng.random() < 0.35:
                enemy.statuses.apply("fire", now)
            # Passive: poison_strikes — 35% chance to poison on any projectile hit
            if "poison_strikes" in self.player.passives and enemy.alive and _rng.random() < 0.35:
                enemy.statuses.apply("poison", now)
            # Energy from projectile damage (1 per 20 dmg, no minimum)
            if now > self._super_energy_lockout_until:
                self.player.energy = min(
                    self.player.max_energy,
                    self.player.energy + dmg // 20)
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
            # Passive: vampiric_strike — heal 4 per hit
            if "vampiric_strike" in self.player.passives:
                self.player.hp = min(self.player.max_hp, self.player.hp + 4)
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
                                _oid = id(other)
                                if _oid not in _death_processed:
                                    _death_processed.add(_oid)
                                    self._record_kill_compendium(other)
                                    process_enemy_death(other, self.player, alive, self.animations,
                                                        self.combat, self.sounds, self.lighting,
                                                        self.boss_chests, _kt, self.pickups, now,
                                                        toasts=self.toasts)
                                    self.kills = _kt["kills"]
                                    self.boss_kills = _kt["boss_kills"]
            if not enemy.alive:
                _eid2 = id(enemy)
                if _eid2 not in _death_processed:
                    _death_processed.add(_eid2)
                    self._record_kill_compendium(enemy)
                    process_enemy_death(enemy, self.player, alive, self.animations,
                                        self.combat, self.sounds, self.lighting,
                                        self.boss_chests, _kt, self.pickups, now,
                                        toasts=self.toasts)
                    self.kills = _kt["kills"]
                    self.boss_kills = _kt["boss_kills"]
            self.sounds.play("hit")

        # Check if enemies hit the player — play hit sound
        prev_hp = self.player.hp
        self.combat.process_enemy_attacks(self.player, alive, now)
        if self.player.hp < prev_hp:
            self.run_stats.record_damage_taken(prev_hp - self.player.hp)
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
        for _bx, _by in self.projectiles.blocked_positions:
            self.sounds.play("plink")
            self.animations.spawn_hit_sparks(_bx, _by, count=5)
        if self.player.hp < prev_hp2:
            self.run_stats.record_damage_taken(prev_hp2 - self.player.hp)
            self.sounds.play("hit")
            self.animations.spawn_hit_sparks(self.player.x, self.player.y)
            self.animations.add_screen_shake(2)

        prev_count = len(self.pickups.pickups)
        self.pickups.update(now, self.player)
        if len(self.pickups.pickups) < prev_count:
            self.sounds.play("pickup")

        # Minimap needs no per-frame update — it reads positions at draw time

        # Dynamic music intensity — only ramp during boss waves, keep ambient otherwise
        if alive:
            if self.spawner.boss_wave:
                intensity = 1.0  # full combat intensity for boss waves
            else:
                min_dist = min(math.hypot(e.x - self.player.x, e.y - self.player.y) for e in alive)
                intensity = max(0.0, min(0.25, 0.25 - (min_dist - 150) / 500))
        else:
            intensity = 0.0
        self.sounds.set_music_intensity(intensity)

        # Portal collision (zone transition)
        if self.portal and self.portal.check_collision(self.player.rect):
            next_zone = get_next_zone(self.current_zone)
            if next_zone:
                # Show portal menu before transitioning
                self.run_stats.complete_zone(self.current_zone)
                self._portal_next_zone = next_zone
                self.portal_menu.activate(self.current_zone, next_zone)
                self._draw()
                self._portal_bg = self.screen.copy()
                self.portal.entered = True  # prevent re-trigger
            else:
                # Completed all zones — victory!
                self.run_stats.complete_zone(self.current_zone)
                self._legacy_points_earned = self.legacy.finish_run(
                    self.spawner.wave, self.kills, self.boss_kills)
                self.run_stats.finalize()
                self.run_stats.save_to_log(
                    self.spawner.wave, self.current_zone,
                    self.player.level, self.player.char_class, victory=True)
                self._submit_run_telemetry(
                    self.spawner.wave, self.current_zone,
                    self.player.char_class, victory=True)
                self.sounds.stop_boss_music()
                self.credits_screen.activate(
                    done_callback=self._on_credits_done)

        # Boss chest collision (skip if a reward/upgrade screen is already open)
        if not (self.chest_reward.active or self.levelup_screen.active
                or self.passive_swap.active or self.weapon_swap.active):
            p_rect = self.player.rect
            for chest in self.boss_chests:
                if chest.alive and p_rect.colliderect(chest.rect):
                    chest.alive = False
                    self.chest_reward.open_chest(
                        self.player.char_class, self.player.passives, self.sounds,
                    )
                    log.info("Boss chest opened!")
                    break
            self.boss_chests = [c for c in self.boss_chests if c.alive]

        self.animations.update(dt)
        self.camera.update(self.player.x, self.player.y, world_w, world_h,
                           self._vp_w, self._vp_h)

        # Spawn portal after clearing the boss wave (wave == boss_wave of zone)
        zone_data = get_zone(self.current_zone)
        boss_wave = zone_data.get("boss_wave", 10)
        if (self.spawner.wave >= boss_wave
                and not self.spawner.wave_active
                and self.portal is None
                and len(self.spawner.get_alive_enemies()) == 0):
            # Spawn portal at map center
            self.portal = Portal(world_w // 2, world_h // 2)
            log.info("Portal spawned for zone transition! zone=%s wave=%d",
                     self.current_zone, self.spawner.wave)

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
            elif not self._player_dying:
                # Start death animation — actual game_over set after delay
                self._player_dying = True
                self._player_death_time = now
                self.player.hp = 0
                self.run_stats.killed_by = self.player.last_hit_by
                self.sounds.stop_boss_music()
                self.sounds.play("player_death")
                self.animations.spawn_death_burst(
                    self.player.x, self.player.y, (255, 80, 80), count=28)
                self.animations.add_screen_shake(14)
                self._legacy_points_earned = self.legacy.finish_run(
                    self.spawner.wave, self.kills, self.boss_kills)
            elif now - self._player_death_time >= self._player_death_duration:
                self.run_stats.finalize()
                self.run_stats.save_to_log(
                    self.spawner.wave, self.current_zone,
                    self.player.level, self.player.char_class, victory=False)
                self._submit_run_telemetry(
                    self.spawner.wave, self.current_zone,
                    self.player.char_class, victory=False)
                self.game_over = True
                self._game_over_start_time = now

        # Detect any damage taken this frame for vignette
        if self.player.hp < _frame_start_hp:
            self._last_damage_time = now
            self._last_damage_pct = (_frame_start_hp - self.player.hp) / max(1, self.player.max_hp)
            self.sounds.play("player_hit")

        # Check for pending level-up -- start fanfare
        if self.player.pending_levelup:
            log.info("Level-up pending! Player level=%d, weapon=%s",
                     self.player.level, self.player.weapon_name)
            self.player.pending_levelup = False
            self._levelup_fanfare_time = now
            self.animations.spawn_death_burst(
                self.player.x, self.player.y, (255, 255, 100), count=24)
            self.animations.add_screen_shake(4)
            self.sounds.play("levelup")

    def _spawn_healing_drop(self, x: float, y: float, kind: str):
        """Spawn the appropriate healing pickup for a healing prop type."""
        if kind == "fruit_tree":
            self.pickups.spawn_apple(x, y)
        elif kind == "first_aid_box":
            self.pickups.spawn_medkit(x, y)
        elif kind == "void_bloom":
            self.pickups.spawn_void_essence(x, y)

    def _transition_to_zone(self, zone_name: str):
        """Reset world for new zone, keeping player stats."""
        log.info("Transitioning to zone: %s", zone_name)
        # Save player state
        p = self.player
        saved = {
            "hp": p.hp, "max_hp": p.max_hp, "damage": p.damage,
            "speed": p.speed, "attack_range": p.attack_range,
            "attack_cooldown": p.attack_cooldown,
            "weapon_name": p.weapon_name, "weapon": p.weapon,
            "passives": list(p.passives), "level": p.level,
            "xp": p.xp, "xp_to_next": p.xp_to_next,
        }
        # Reinit world
        self._init_world()
        # Restore player state
        p = self.player
        for k, v in saved.items():
            setattr(p, k, v)
        # Reset portal
        self.portal = None
        # Setup new zone
        zone_data = get_zone(zone_name)
        self.game_map.set_colors(zone_data.get("tile_colors", {}))
        self.game_map.set_zone(zone_name)
        self.atmosphere.set_zone(zone_name, zone_data)
        self.hazard_system.set_zone(zone_name, zone_data)
        self.spawner.set_zone(zone_data)
        self.run_stats.set_zone(zone_name)
        self.sounds.set_zone_music(zone_name)
        # Trigger zone intro for the new zone
        self._zone_intro_active = True
        self._zone_intro_start = 0


    def _apply_settings(self):
        """Sync display/audio with current menu settings."""
        s = self.main_menu.settings
        # Fullscreen toggle
        is_fs = bool(pygame.display.get_surface().get_flags() & pygame.FULLSCREEN)
        want_fs = s.get("fullscreen", False)
        if want_fs != is_fs:
            flags = pygame.FULLSCREEN if want_fs else 0
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
            self._vp_w = int(SCREEN_WIDTH / CAMERA_ZOOM)
            self._vp_h = int(SCREEN_HEIGHT / CAMERA_ZOOM)
            self._world_surf = pygame.Surface((self._vp_w, self._vp_h))

    # ------------------------------------------------------------------ draw
    def _draw(self):
        # ── World rendering → smaller viewport surface, then scaled to screen ──
        ws = self._world_surf
        ws.fill(BLACK)
        cx, cy = int(self.camera.x), int(self.camera.y)

        # Apply screen shake offset
        shake_x, shake_y = self.animations.shake_offset
        cx += shake_x
        cy += shake_y

        self.game_map.draw(ws, cx, cy, self._vp_w, self._vp_h)

        # Environment props (behind characters)
        self.environment.draw(ws, cx, cy, self._vp_w, self._vp_h)

        # Campfire
        self.campfire.draw(ws, cx, cy)

        # Pickups (draw under characters)
        self.pickups.draw(ws, cx, cy)

        # Boss chests
        for chest in self.boss_chests:
            chest.draw(ws, cx, cy)

        for enemy in self.spawner.enemies:  # includes dead enemies for corpse rendering
            enemy.draw(ws, cx, cy)

        # Projectiles
        self.projectiles.draw(ws, cx, cy)
        self.player_projectiles.draw(ws, cx, cy)

        # Don't draw the standing player during dying — squash handles visuals
        if not self._player_dying:
            self.player.draw(ws, cx, cy)
        if self._player_dying:
            self._draw_player_dying_squash(cx, cy, pygame.time.get_ticks(), ws)
        self.combat.draw(ws, cx, cy, self.combat_font)

        # Particle animations (death bursts, hit sparks)
        self.animations.draw(ws, cx, cy)

        # Atmospheric particles & zone effects
        self.atmosphere.draw(ws, pygame.time.get_ticks(), self._vp_w, self._vp_h)

        # Environmental hazards
        self.hazard_system.draw(ws, cx, cy, pygame.time.get_ticks(),
                                self._vp_w, self._vp_h)

        # Portal
        if self.portal:
            self.portal.draw(ws, cx, cy)

        # ---- Darkness overlay (after world, before UI) ----
        self.lighting.draw(ws, cx, cy, self.player.x, self.player.y,
                           self._vp_w, self._vp_h)

        # ---- Vision debuff overlay (Nexus null_burst) ----
        now_draw = pygame.time.get_ticks()
        if now_draw < self.player.vision_debuff_until:
            self._draw_vision_debuff(now_draw, ws)

        # ---- Insanity overlay (Nexus null_burst / reality_collapse) ----
        if now_draw < self.player.insanity_until:
            self._draw_insanity_overlay(now_draw, ws)

        # ── Scale world surface to full screen ──────────────────────────────
        pygame.transform.scale(ws, (SCREEN_WIDTH, SCREEN_HEIGHT), self.screen)

        alive_count = len(self.spawner.get_alive_enemies())
        boss_enemies = [e for e in self.spawner.get_alive_enemies()
                       if e.is_boss] if self.spawner.boss_wave else None
        self.hud.draw(self.screen, self.player, self.spawner.wave, alive_count,
                      self.lighting.darkness, self.spawner.boss_wave, boss_enemies)

        # Pickup notifications
        self.pickups.draw_notifications(self.screen)

        # Minimap
        alive_for_map = self.spawner.get_alive_enemies()
        self.minimap.draw(self.screen, self.player.x, self.player.y, alive_for_map,
                        campfire_x=getattr(self.campfire, 'x', None),
                        campfire_y=getattr(self.campfire, 'y', None))

        # Level-up fanfare flash overlay
        if self._levelup_fanfare_time:
            elapsed = pygame.time.get_ticks() - self._levelup_fanfare_time
            # White flash that fades out
            flash_alpha = max(0, 180 - int(elapsed * 0.6))
            if flash_alpha > 0:
                flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, flash_alpha))
                self.screen.blit(flash_surf, (0, 0))
            # "LEVEL UP!" text that scales up
            scale = min(2.0, 0.5 + elapsed / 300)
            font_size = max(12, int(48 * scale))
            text = get_font("consolas", font_size, True).render("LEVEL UP!", True, (255, 255, 100))
            tr = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, tr)

        # Level-up overlay
        self.levelup_screen.draw(self.screen)

        # Weapon swap overlay
        self.weapon_swap.draw(self.screen)

        # Arsenal screen overlay
        self.arsenal_screen.draw(self.screen)

        # Passive swap overlay
        self.passive_swap.draw(self.screen)

        # Chest reward overlay
        self.chest_reward.draw(self.screen)

        # Run summary overlay
        self.run_summary.draw(self.screen)

        # Zone intro cutscene (over full gameplay view, under pause)
        if self._zone_intro_active:
            self._draw_zone_intro()
        elif self._wave_countdown_secs > 0:
            overlay_open = (
                self.chest_reward.active or self.levelup_screen.active
                or self.passive_swap.active or self.weapon_swap.active
            )
            self._draw_wave_countdown(top_only=overlay_open)

        if self.game_over:
            self.hud.draw_game_over(self.screen, self.spawner.wave, self.player.level,
                                    self.kills, self._legacy_points_earned,
                                    game_over_start=self._game_over_start_time)
        elif self._player_dying:
            self._draw_player_death_overlay()

        # Pause overlay
        if self.paused:
            self._draw_pause_overlay()

        # Auto-attack indicator
        if self.auto_attack and not self.game_over:
            aa_text = get_font("consolas", 14, True).render("[F] AUTO-ATTACK ON", True, (255, 200, 50))
            self.screen.blit(aa_text, (SCREEN_WIDTH // 2 - aa_text.get_width() // 2,
                                       SCREEN_HEIGHT - 30))

        # Debug overlay
        if self._debug_mode:
            alive = self.spawner.get_alive_enemies()
            fps = self.clock.get_fps()
            self.debug_overlay.draw(
                self.screen, int(self.camera.x), int(self.camera.y),
                self.player, alive,
                self.projectiles, self.player_projectiles,
                fps, self.spawner.wave, self.boss_chests)

        # ---- Damage vignette ----
        now_draw = pygame.time.get_ticks()
        vignette_age = now_draw - self._last_damage_time
        _VIG_DUR = 700
        if vignette_age < _VIG_DUR and not self.game_over:
            vfade = max(0.0, 1.0 - vignette_age / _VIG_DUR)
            dmg_pct = self._last_damage_pct
            peak_alpha = int((18 + dmg_pct * 145) * vfade)
            if peak_alpha > 1:
                bucket = peak_alpha // 8
                cached = self._dmg_vig_cache
                if cached is None or cached[0] != bucket:
                    vig = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    steps = 40
                    half = min(SCREEN_WIDTH, SCREEN_HEIGHT) // 2
                    for i in range(steps):
                        frac = (1.0 - i / steps) ** 1.8
                        a = int(peak_alpha * frac)
                        if a < 1:
                            continue
                        inset = i * half // steps
                        rect = pygame.Rect(inset, inset,
                                           SCREEN_WIDTH - 2 * inset,
                                           SCREEN_HEIGHT - 2 * inset)
                        if rect.width < 4 or rect.height < 4:
                            break
                        pygame.draw.rect(vig, (215, 10, 10, a), rect, 2,
                                         border_radius=max(1, 28 - i // 2))
                    self._dmg_vig_cache = (bucket, vig)
                self.screen.blit(self._dmg_vig_cache[1], (0, 0))

        # ---- Kill streak combo text ----
        streak_age = now_draw - self._kill_streak_time
        if self._kill_streak >= 2 and streak_age < 1800 and not self.game_over:
            sfade = max(0.0, 1.0 - streak_age / 1800)
            scale = min(1.0, 0.4 + streak_age / 200) if streak_age < 200 else max(0.6, 1.0 - (streak_age - 1400) / 400)
            fs = max(12, int(32 * scale))
            if self._kill_streak >= 10:
                streak_color = (255, 50, 50)
                tag = f"{self._kill_streak}x RAMPAGE!"
            elif self._kill_streak >= 5:
                streak_color = (255, 160, 30)
                tag = f"{self._kill_streak}x SLAUGHTER!"
            elif self._kill_streak >= 3:
                streak_color = (255, 230, 50)
                tag = f"{self._kill_streak}x KILL!"
            else:
                streak_color = (200, 255, 100)
                tag = f"{self._kill_streak}x DOUBLE!"
            streak_surf = get_font("consolas", fs, True).render(tag, True, streak_color)
            sa = max(0, int(255 * sfade))
            streak_surf.set_alpha(sa)
            sx_pos = SCREEN_WIDTH // 2 - streak_surf.get_width() // 2
            sy_pos = SCREEN_HEIGHT // 2 - 80 - int(20 * (1.0 - sfade))
            self.screen.blit(streak_surf, (sx_pos, sy_pos))

        # ---- Toast notifications ----
        self.toasts.draw(self.screen)

        # ---- Auto-screenshot queue ----
        if self._pending_auto_shots:
            for _shot_at, _shot_tag in list(self._pending_auto_shots):
                if now_draw >= _shot_at:
                    self._save_screenshot(_shot_tag)
                    self._pending_auto_shots.remove((_shot_at, _shot_tag))

        # ---- Custom cursor (always drawn last) ----
        mx_c, my_c = pygame.mouse.get_pos()
        _draw_cursor_fn(self.screen, mx_c, my_c, self.current_zone, now_draw)

        pygame.display.flip()

    def _draw_vision_debuff(self, now: int, surface: pygame.Surface = None):
        """Render eldritch vision distortion when hit by Nexus null_burst."""
        surf = surface if surface is not None else self.screen
        sw, sh = surf.get_size()
        remaining = self.player.vision_debuff_until - now
        intensity = min(1.0, remaining / 5000)
        t = now * 0.001

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)

        # Purple-green color shift bands
        for i in range(0, sh, 40):
            wave = math.sin(t * 3.0 + i * 0.05) * 0.5 + 0.5
            alpha = int(45 * intensity * wave)
            color = (120, 30, 180, alpha) if i % 80 < 40 else (30, 160, 80, alpha)
            pygame.draw.rect(overlay, color, (0, i, sw, 40))

        # Wobbly scan lines
        for y in range(0, sh, 3):
            offset = int(math.sin(t * 8.0 + y * 0.1) * 4 * intensity)
            if offset != 0:
                pygame.draw.line(overlay, (100, 40, 160, int(30 * intensity)),
                                 (offset, y), (sw + offset, y), 1)

        # Pulsing vignette
        pulse = 0.5 + 0.5 * math.sin(t * 5.0)
        vig_alpha = int(80 * intensity * pulse)
        vig = pygame.Surface((sw, sh), pygame.SRCALPHA)
        vig.fill((80, 0, 120, vig_alpha))
        cx, cy = sw // 2, sh // 2
        for r in range(min(cx, cy), 0, -20):
            fade = int(vig_alpha * (r / min(cx, cy)))
            pygame.draw.circle(vig, (80, 0, 120, fade), (cx, cy), r)
        surf.blit(vig, (0, 0))
        surf.blit(overlay, (0, 0))

    def _draw_insanity_overlay(self, now: int, surface: pygame.Surface = None):
        """Crimson-static overlay during Nexus insanity — conveys lost control."""
        surf = surface if surface is not None else self.screen
        sw, sh = surf.get_size()
        remaining = self.player.insanity_until - now
        intensity = min(1.0, remaining / 2000)
        t = now * 0.001

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)

        # Rapid noise bars in crimson/magenta
        for i in range(0, sh, 20):
            noise_off = int(math.sin(t * 18.0 + i * 0.12) * 12 * intensity)
            bar_alpha = int(50 * intensity * (0.4 + 0.6 * abs(math.sin(t * 7 + i * 0.07))))
            color = (220, 20, 100, bar_alpha) if (i // 20) % 2 == 0 else (160, 0, 200, bar_alpha)
            pygame.draw.rect(overlay, color, (noise_off, i, sw, 20))

        cx, cy = sw // 2, sh // 2
        for k in range(6):
            crack_angle = t * 4.5 + k * math.tau / 6
            length = int((100 + 60 * math.sin(t * 9 + k)) * intensity)
            ex2 = cx + int(math.cos(crack_angle) * length)
            ey2 = cy + int(math.sin(crack_angle) * length)
            c_alpha = int(180 * intensity)
            pygame.draw.line(overlay, (255, 20, 80, c_alpha), (cx, cy), (ex2, ey2), 2)
        surf.blit(overlay, (0, 0))

        # Pulsing red vignette border
        pulse = 0.5 + 0.5 * math.sin(t * 12.0)
        vig_alpha = int(100 * intensity * pulse)
        vig = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for r in range(min(cx, cy), max(0, min(cx, cy) - 120), -8):
            fade = int(vig_alpha * (1.0 - r / min(cx, cy)))
            pygame.draw.circle(vig, (200, 0, 60, fade), (cx, cy), r)
        surf.blit(vig, (0, 0))

        if int(now * 0.006) % 3 != 0:
            warn = get_font("consolas", 22, True).render(
                "LOSING CONTROL", True, (255, 60, 100))
            warn.set_alpha(int(200 * intensity))
            surf.blit(warn, (cx - warn.get_width() // 2, cy - warn.get_height() // 2))

    def _draw_player_dying_squash(self, cx: int, cy: int, now: int,
                                   surface: pygame.Surface = None):
        """Full 2200ms death animation: squash/fall (0-450ms) then flat corpse (450ms+)."""
        elapsed = now - self._player_death_time
        total = self._player_death_duration  # 2200ms
        if elapsed >= total:
            return
        sx = int(self.player.x - cx)
        sy = int(self.player.y - cy)
        half = max(1, self.player.size // 2)
        surf = surface if surface is not None else self.screen

        cc = self.player.char_class
        col = (0, 180, 255) if cc == "knight" else \
              (0, 255, 150) if cc == "archer" else \
              (200, 50, 200)

        FALL_DUR = 450  # ms for squash/fall phase

        if elapsed < FALL_DUR:
            # ── Phase 1: squash, rotate 90°, spark burst ──
            t = elapsed / FALL_DUR  # 0..1

            ew = max(4, int(self.player.size * (1.0 + t * 0.80)))
            eh = max(2, int(self.player.size * (1.0 - t * 0.92)))
            tilt_deg = t * 90

            tsz = self.player.size * 5
            tc = tsz // 2
            tmp = pygame.Surface((tsz, tsz), pygame.SRCALPHA)

            # Body squash
            pygame.draw.ellipse(tmp, (*col, 220), (tc - ew // 2, tc - eh // 2, ew, eh))

            # White impact flash
            if t < 0.30:
                fa = int(255 * (1.0 - t / 0.30) ** 2.0)
                pygame.draw.ellipse(tmp, (255, 255, 255, fa),
                                    (tc - ew // 2, tc - eh // 2, ew, eh))

            # Sparks fly out
            if t < 0.80:
                sa = int(255 * (1.0 - t / 0.80) ** 0.7)
                ao = (now * 0.008) % math.tau
                for i in range(6):
                    angle = i * math.tau / 6 + ao
                    slen = max(2, int(half * 1.8 * (1.0 - t / 0.80)))
                    ex1 = tc + int(math.cos(angle) * (half * 0.6))
                    ey1 = tc + int(math.sin(angle) * (half * 0.6))
                    ex2 = ex1 + int(math.cos(angle) * slen)
                    ey2 = ey1 + int(math.sin(angle) * slen)
                    sc = [(255, 240, 60), (255, 120, 30), (160, 255, 100)][i % 3]
                    pygame.draw.line(tmp, (*sc, sa), (ex1, ey1), (ex2, ey2), 2)

            rotated = pygame.transform.rotate(tmp, tilt_deg)
            rw, rh = rotated.get_size()
            y_drop = int(half * 0.5 * t)
            surf.blit(rotated, (sx - rw // 2, sy - rh // 2 + y_drop))

        else:
            # ── Phase 2: flat corpse on ground, fades slowly ──
            t2 = (elapsed - FALL_DUR) / max(1, total - FALL_DUR)  # 0..1
            alpha = int(200 * (1.0 - t2) ** 1.5)
            if alpha <= 1:
                return
            cw = max(6, int(self.player.size * 1.4))
            ch = max(3, int(self.player.size * 0.28))
            # Dark tinted corpse ellipse
            dc = (max(0, col[0] // 4), max(0, col[1] // 4), max(0, col[2] // 4))
            csurf = pygame.Surface((cw + 4, ch + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(csurf, (*dc, alpha), (2, 2, cw, ch))
            pygame.draw.ellipse(csurf, (60, 20, 20, alpha // 2), (2, 2, cw, ch), 1)
            surf.blit(csurf, (sx - cw // 2, sy + half // 2 - ch // 2))

    def _draw_player_death_overlay(self):
        """Zoom-in + fade-to-black death transition before game over screen."""
        now = pygame.time.get_ticks()
        elapsed = now - self._player_death_time
        t = min(1.0, elapsed / self._player_death_duration)  # 0..1

        # Phase 1 (0-50%): vignette darkening + red tint
        # Phase 2 (50-100%): fade to full black
        if t < 0.5:
            # Darkening red vignette
            vign_alpha = int(180 * (t / 0.5))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((80, 0, 0, vign_alpha))
            self.screen.blit(overlay, (0, 0))
        else:
            # Fade to black
            fade_t = (t - 0.5) / 0.5
            black_alpha = int(255 * fade_t ** 1.5)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, black_alpha))
            self.screen.blit(overlay, (0, 0))

        # "YOU DIED" text fades in at 60% through
        if t >= 0.6:
            text_t = (t - 0.6) / 0.4
            text_alpha = int(255 * text_t ** 0.7)
            font = get_font("consolas", 72, True)
            text = font.render("YOU DIED", True, (220, 40, 40))
            text.set_alpha(text_alpha)
            tr = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, tr)

    def _draw_zone_intro(self):
        """Full-screen zone name cutscene: fade in → hold → fade out."""
        now = pygame.time.get_ticks()
        if self._zone_intro_start == 0:
            return
        t = min(1.0, (now - self._zone_intro_start) / self._zone_intro_duration)

        # Three phases: fade-in (0-0.30), hold (0.30-0.70), fade-out (0.70-1.0)
        if t < 0.30:
            overlay_alpha = int(200 * (t / 0.30))
            text_alpha = int(255 * (t / 0.30))
        elif t < 0.70:
            overlay_alpha = 200
            text_alpha = 255
        else:
            fade = (t - 0.70) / 0.30
            overlay_alpha = int(200 * (1.0 - fade))
            text_alpha = int(255 * (1.0 - fade))

        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, overlay_alpha))
        self.screen.blit(overlay, (0, 0))

        zone_data = get_zone(self.current_zone)
        zone_name = zone_data.get("name", self.current_zone.replace("_", " ").title())
        zone_desc = zone_data.get("desc", "")

        # Zone name (large)
        font_big = get_font("consolas", 54, True)
        name_surf = font_big.render(zone_name, True, (255, 230, 80))
        name_surf.set_alpha(text_alpha)
        nx = SCREEN_WIDTH // 2 - name_surf.get_width() // 2
        ny = SCREEN_HEIGHT // 2 - name_surf.get_height() // 2 - 20
        self.screen.blit(name_surf, (nx, ny))

        # Zone desc (small, slightly delayed)
        if t > 0.15:
            desc_t = min(1.0, (t - 0.15) / 0.20)
            desc_alpha = min(text_alpha, int(180 * desc_t))
            font_sm = get_font("consolas", 18)
            desc_surf = font_sm.render(zone_desc, True, (180, 180, 200))
            desc_surf.set_alpha(desc_alpha)
            dx = SCREEN_WIDTH // 2 - desc_surf.get_width() // 2
            dy = ny + name_surf.get_height() + 12
            self.screen.blit(desc_surf, (dx, dy))

    def _draw_wave_countdown(self, top_only: bool = False):
        """Show countdown seconds before next wave starts."""
        secs = self._wave_countdown_secs
        if secs <= 0:
            return
        cx = SCREEN_WIDTH // 2
        zone_data = get_zone(self.current_zone)
        boss_wave = zone_data.get("boss_wave", 10)
        if self.spawner.wave >= boss_wave:
            return  # portal handles progression — no countdown after final wave
        label = f"WAVE {self.spawner.wave + 1} INCOMING"
        if top_only:
            # Compact single-line banner at the top so it doesn't overlap overlays
            font_sm = get_font("consolas", 20, True)
            text = f"{label}  —  {secs}s"
            surf = font_sm.render(text, True, (255, 220, 60))
            bg = pygame.Surface((surf.get_width() + 20, surf.get_height() + 8), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            bx = cx - bg.get_width() // 2
            self.screen.blit(bg, (bx, 8))
            self.screen.blit(surf, (cx - surf.get_width() // 2, 12))
        else:
            # Full center display
            font_big = get_font("consolas", 72, True)
            num_surf = font_big.render(str(secs), True, (255, 220, 60))
            self.screen.blit(num_surf, (cx - num_surf.get_width() // 2,
                                        SCREEN_HEIGHT // 2 - 70))
            font_sm = get_font("consolas", 18, True)
            label_surf = font_sm.render(label, True, (200, 200, 220))
            self.screen.blit(label_surf, (cx - label_surf.get_width() // 2,
                                          SCREEN_HEIGHT // 2 + 20))

    def _draw_pause_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        font_big = get_font("consolas", 48, True)
        font_med = get_font("consolas", 18, True)
        font = get_font("consolas", 15)
        font_small = get_font("consolas", 13)

        # Title
        text = font_big.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 30))

        # ── Left panel: Player stats ──
        lx = 60
        ly = 100
        section_color = (255, 215, 0)
        label_color = (180, 180, 200)
        value_color = (255, 255, 255)

        header = font_med.render("PLAYER STATS", True, section_color)
        self.screen.blit(header, (lx, ly))
        ly += 30

        p = self.player
        stats = [
            ("Class", p.char_class.title()),
            ("Level", str(p.level)),
            ("HP", f"{p.hp}/{p.max_hp}"),
            ("Damage", str(p.damage)),
            ("Speed", f"{p.speed:.1f}"),
            ("Attack CD", f"{p.attack_cooldown}ms"),
            ("Weapon", p.weapon.get("name", "?")),
            ("Zone", self.current_zone.replace("_", " ").title()),
            ("Wave", str(self.spawner.wave)),
        ]
        for label, val in stats:
            ls = font.render(f"{label}:", True, label_color)
            vs = font.render(val, True, value_color)
            self.screen.blit(ls, (lx, ly))
            self.screen.blit(vs, (lx + 120, ly))
            ly += 22

        # Passives
        ly += 8
        ph = font_med.render("PASSIVES", True, section_color)
        self.screen.blit(ph, (lx, ly))
        ly += 26
        if p.passives:
            for pname in p.passives:
                ps = font.render(f"• {pname.replace('_', ' ').title()}", True, (180, 220, 180))
                self.screen.blit(ps, (lx + 4, ly))
                ly += 20
        else:
            ps = font.render("(none)", True, (120, 120, 140))
            self.screen.blit(ps, (lx + 4, ly))
            ly += 20

        # Upgrade tiers
        if p.upgrade_tiers:
            ly += 8
            uh = font_med.render("UPGRADES", True, section_color)
            self.screen.blit(uh, (lx, ly))
            ly += 26
            for uname, tier in p.upgrade_tiers.items():
                tier_str = {1: "I", 2: "II", 3: "III"}.get(tier, str(tier))
                us = font.render(f"• {uname} [{tier_str}]", True, (200, 200, 180))
                self.screen.blit(us, (lx + 4, ly))
                ly += 20

        # ── Right panel: Hotkeys ──
        rx = SCREEN_WIDTH // 2 + 60
        ry = 100
        hh = font_med.render("HOTKEYS", True, section_color)
        self.screen.blit(hh, (rx, ry))
        ry += 30

        hotkeys = [
            ("W/A/S/D", "Move"),
            ("Space / Click", "Attack"),
            ("Shift", "Dash"),
            ("F", "Toggle auto-attack"),
            ("P / ESC", "Pause / Resume"),
            ("R", "View run summary (on death)"),
            ("Mouse", "Aim direction"),
        ]
        for key, desc in hotkeys:
            ks = font.render(key, True, (255, 215, 0))
            ds = font.render(f"  {desc}", True, label_color)
            self.screen.blit(ks, (rx, ry))
            self.screen.blit(ds, (rx + 140, ry))
            ry += 22

        # ── Run stats ──
        ry += 16
        rsh = font_med.render("RUN STATS", True, section_color)
        self.screen.blit(rsh, (rx, ry))
        ry += 30

        rs = self.run_stats
        elapsed = (pygame.time.get_ticks() - rs.time_started) // 1000
        mins, secs = divmod(elapsed, 60)
        run_info = [
            ("Time", f"{mins}:{secs:02d}"),
            ("Kills", str(rs.total_kills)),
            ("Boss Kills", str(rs.boss_kills)),
            ("Damage Dealt", str(rs.total_damage_dealt)),
            ("Damage Taken", str(rs.total_damage_taken)),
            ("Highest Hit", str(rs.highest_hit)),
        ]
        for label, val in run_info:
            ls = font.render(f"{label}:", True, label_color)
            vs = font.render(val, True, value_color)
            self.screen.blit(ls, (rx, ry))
            self.screen.blit(vs, (rx + 120, ry))
            ry += 22

        # ── Debug extras (only when debug mode is active) ──
        if self._debug_mode:
            ry += 16
            dh = font_med.render("DEBUG INFO", True, (255, 80, 80))
            self.screen.blit(dh, (rx, ry))
            ry += 30

            alive_count = len(self.spawner.get_alive_enemies())
            fps = self.clock.get_fps()
            cheats = self.debug_menu.cheats if hasattr(self, 'debug_menu') else {}
            active_cheats = [k for k, v in cheats.items() if v]

            debug_info = [
                ("FPS", f"{fps:.0f}"),
                ("Alive Enemies", str(alive_count)),
                ("Player Pos", f"({int(p.x)}, {int(p.y)})"),
                ("Darkness", f"{self.lighting.darkness:.2f}"),
                ("Active Cheats", ", ".join(active_cheats) if active_cheats else "none"),
            ]
            for label, val in debug_info:
                ls = font_small.render(f"{label}:", True, (255, 100, 100))
                vs = font_small.render(val, True, (255, 180, 180))
                self.screen.blit(ls, (rx, ry))
                self.screen.blit(vs, (rx + 120, ry))
                ry += 18

        # ── Pause menu ──
        menu_y = SCREEN_HEIGHT - 160
        for i, opt in enumerate(self._pause_options):
            is_sel = i == self._pause_selected
            color = (255, 215, 0) if is_sel else (140, 140, 160)
            prefix = "> " if is_sel else "  "
            opt_txt = get_font("consolas", 18, True).render(f"{prefix}{opt}", True, color)
            ox = SCREEN_WIDTH // 2 - opt_txt.get_width() // 2
            oy = menu_y + i * 34
            if is_sel:
                bar = pygame.Surface((opt_txt.get_width() + 30, 28), pygame.SRCALPHA)
                bar.fill((255, 215, 0, 20))
                self.screen.blit(bar, (ox - 15, oy - 2))
            self.screen.blit(opt_txt, (ox, oy))

        hint_font = get_font("consolas", 14)
        h1 = hint_font.render("W/S to navigate  |  Enter / E to select  |  P or Esc to resume", True, (80, 80, 100))
        self.screen.blit(h1, (SCREEN_WIDTH // 2 - h1.get_width() // 2, SCREEN_HEIGHT - 26))

    def _apply_debug_cheats(self):
        if not self._debug_mode:
            return
        cheats = self.debug_menu.cheats
        self.debug_overlay.active = True
        self.debug_overlay.set_cheats(cheats)
        self.debug_overlay.log("Debug mode active")
        if cheats.get("double_speed"):
            self.player.speed *= 2
            self.debug_overlay.log("Cheat: 2x speed")
        if cheats.get("double_damage"):
            self.player.damage *= 2
            self.debug_overlay.log("Cheat: 2x damage")
        if cheats.get("one_hit_kills"):
            self.player.damage = 99999
            self.debug_overlay.log("Cheat: one-hit kills")
        if cheats.get("infinite_dash"):
            self.player.dash_cooldown = 0
            self.debug_overlay.log("Cheat: infinite dash")
        if cheats.get("max_level"):
            for _ in range(10):
                self.player.level += 1
                self.player.damage += 3
                self.player.max_hp += 10
            self.player.hp = self.player.max_hp
            self.debug_overlay.log("Cheat: max level (10)")
        # Zone override
        zone_name = self.debug_menu.zone_names[self.debug_menu.start_zone]
        if zone_name != self.current_zone:
            self.current_zone = zone_name
            self._transition_to_zone(zone_name)
            self.debug_overlay.log(f"Zone override: {zone_name}")
        # Wave override
        if self.debug_menu.start_wave > 1:
            self.spawner.wave = self.debug_menu.start_wave - 1
            self.debug_overlay.log(f"Wave override: {self.debug_menu.start_wave}")
        # Skip to boss
        if cheats.get("skip_to_boss"):
            from src.systems.zones import get_zone as _gz
            zd = _gz(self.current_zone)
            bw = zd.get("boss_wave", 10)
            self.spawner.wave = bw - 1
            self.debug_overlay.log(f"Skip to boss wave {bw}")

