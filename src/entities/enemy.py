import pygame
import math
import random
from src.settings import (
    ENEMY_SPEED, ENEMY_HP, ENEMY_SIZE, ENEMY_COLOR,
    ENEMY_DAMAGE, ENEMY_ATTACK_COOLDOWN,
    ENEMY_AGGRO_RANGE, ENEMY_ATTACK_RANGE,
    ENEMY_SHOOT_RANGE, ENEMY_SHOOT_COOLDOWN, ENEMY_BULLET_DAMAGE,
    ENEMY_BODY_COLOR, ENEMY_DOME_COLOR, ENEMY_EYE_COLOR, ENEMY_SKIRT_COLOR,
    SCREEN_WIDTH, SCREEN_HEIGHT,
)
from src.systems.status_effects import StatusManager
from src.font_cache import get_font

# ── Enemy type presets ──
ENEMY_TYPES = {
    "dalek": {
        "hp": 25, "speed": ENEMY_SPEED, "size": ENEMY_SIZE,
        "damage": ENEMY_DAMAGE, "shoot_range": ENEMY_SHOOT_RANGE,
        "shoot_cooldown": ENEMY_SHOOT_COOLDOWN, "bullet_damage": ENEMY_BULLET_DAMAGE,
        "xp_value": 8, "status_on_hit": None,
    },
    "wraith": {
        "hp": 15, "speed": 3.2, "size": 32,
        "damage": 14, "shoot_range": 0,  # melee only
        "shoot_cooldown": 9999, "bullet_damage": 0,
        "xp_value": 10, "status_on_hit": "poison",
    },
    "iron_sentinel": {
        "hp": 800, "speed": 1.5, "size": 56,
        "damage": 25, "shoot_range": 350,
        "shoot_cooldown": 900, "bullet_damage": 16,
        "xp_value": 200, "status_on_hit": "fire",
        "special": "ground_slam",
    },
    "warlord_kron": {
        "hp": 2500, "speed": 1.2, "size": 72,
        "damage": 40, "shoot_range": 400,
        "shoot_cooldown": 600, "bullet_damage": 25,
        "xp_value": 800, "status_on_hit": "bleed",
        "special": "war_cry",
    },
    "charger": {
        "hp": 18, "speed": 2.5, "size": 28,
        "damage": 18, "shoot_range": 0,
        "shoot_cooldown": 9999, "bullet_damage": 0,
        "xp_value": 12, "status_on_hit": None,
    },
    "shielder": {
        "hp": 40, "speed": 1.6, "size": 38,
        "damage": 12, "shoot_range": 0,
        "shoot_cooldown": 9999, "bullet_damage": 0,
        "xp_value": 16, "status_on_hit": "slow",
    },
    "spitter": {
        "hp": 14, "speed": 2.0, "size": 30,
        "damage": 8, "shoot_range": 280,
        "shoot_cooldown": 1200, "bullet_damage": 10,
        "xp_value": 10, "status_on_hit": "poison",
    },
    # ── Zone 2: Ruined City ──
    "cyber_zombie": {
        "hp": 20, "speed": 1.8, "size": 30,
        "damage": 16, "shoot_range": 0,
        "shoot_cooldown": 9999, "bullet_damage": 0,
        "xp_value": 10, "status_on_hit": None,
    },
    "cyber_dog": {
        "hp": 12, "speed": 4.0, "size": 24,
        "damage": 12, "shoot_range": 0,
        "shoot_cooldown": 9999, "bullet_damage": 0,
        "xp_value": 10, "status_on_hit": "bleed",
    },
    "drone": {
        "hp": 8, "speed": 2.8, "size": 22,
        "damage": 6, "shoot_range": 300,
        "shoot_cooldown": 800, "bullet_damage": 12,
        "xp_value": 8, "status_on_hit": None,
    },
    "cultist": {
        "hp": 28, "speed": 2.0, "size": 32,
        "damage": 10, "shoot_range": 260,
        "shoot_cooldown": 1400, "bullet_damage": 14,
        "xp_value": 14, "status_on_hit": "fire",
    },
    "shambler": {
        "hp": 50, "speed": 1.0, "size": 42,
        "damage": 22, "shoot_range": 0,
        "shoot_cooldown": 9999, "bullet_damage": 0,
        "xp_value": 18, "status_on_hit": "poison",
    },
    "preacher": {
        "hp": 1200, "speed": 1.4, "size": 52,
        "damage": 20, "shoot_range": 320,
        "shoot_cooldown": 1000, "bullet_damage": 16,
        "xp_value": 250, "status_on_hit": "fire",
        "special": "flame_pillar",
    },
    "eldritch_horror": {
        "hp": 3500, "speed": 1.0, "size": 80,
        "damage": 35, "shoot_range": 380,
        "shoot_cooldown": 700, "bullet_damage": 22,
        "xp_value": 1000, "status_on_hit": "bleed",
        "special": "tentacle_sweep",
    },
    # ── Zone 3: The Abyss ──
    "void_wisp": {
        "hp": 10, "speed": 3.5, "size": 20,
        "damage": 10, "shoot_range": 0,
        "shoot_cooldown": 9999, "bullet_damage": 0,
        "xp_value": 8, "status_on_hit": None,
    },
    "rift_walker": {
        "hp": 24, "speed": 2.2, "size": 34,
        "damage": 18, "shoot_range": 0,
        "shoot_cooldown": 9999, "bullet_damage": 0,
        "xp_value": 12, "status_on_hit": "slow",
    },
    "mirror_shade": {
        "hp": 16, "speed": 2.5, "size": 28,
        "damage": 14, "shoot_range": 0,
        "shoot_cooldown": 9999, "bullet_damage": 0,
        "xp_value": 12, "status_on_hit": None,
    },
    "gravity_warden": {
        "hp": 34, "speed": 1.5, "size": 40,
        "damage": 12, "shoot_range": 250,
        "shoot_cooldown": 1200, "bullet_damage": 15,
        "xp_value": 16, "status_on_hit": "slow",
    },
    "null_serpent": {
        "hp": 26, "speed": 2.8, "size": 36,
        "damage": 16, "shoot_range": 0,
        "shoot_cooldown": 9999, "bullet_damage": 0,
        "xp_value": 14, "status_on_hit": "poison",
    },
    "architect": {
        "hp": 1500, "speed": 1.2, "size": 56,
        "damage": 22, "shoot_range": 340,
        "shoot_cooldown": 900, "bullet_damage": 18,
        "xp_value": 300, "status_on_hit": "slow",
        "special": "void_rift",
    },
    "nexus": {
        "hp": 5000, "speed": 0.8, "size": 90,
        "damage": 45, "shoot_range": 420,
        "shoot_cooldown": 500, "bullet_damage": 28,
        "xp_value": 1500, "status_on_hit": "bleed",
        "special": "null_burst",
    },
}


class Enemy:
    def __init__(self, x: float, y: float, enemy_type: str = "dalek"):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        preset = ENEMY_TYPES[enemy_type]

        self.size = preset["size"]
        self.speed = preset["speed"]
        self.max_hp = preset["hp"]
        self.hp = self.max_hp
        self.damage = preset["damage"]
        self.attack_range = ENEMY_ATTACK_RANGE
        self.aggro_range = ENEMY_AGGRO_RANGE + (20 if self.is_boss else 0)
        self.attack_cooldown = ENEMY_ATTACK_COOLDOWN
        self.last_attack_time = 0
        self.alive = True
        self.xp_value = preset["xp_value"]
        self.status_on_hit = preset["status_on_hit"]

        # Status effects on this enemy (player weapons can apply them too)
        self.statuses = StatusManager()

        # Shooting
        self.shoot_range = preset["shoot_range"]
        self.shoot_cooldown = preset["shoot_cooldown"]
        self.last_shoot_time = 0
        self.bullet_damage = preset["bullet_damage"]
        self.wants_to_shoot = False

        # Boss spread-shot config (set below per type)
        self.shoot_spread_count = 1     # number of projectiles per shot
        self.shoot_spread_arc = 0.0     # total arc in radians

        # Facing direction toward player
        self.face_x = 0.0
        self.face_y = 1.0

        # Knockback
        self.kb_dx = 0.0
        self.kb_dy = 0.0
        self.kb_timer = 0
        self.kb_duration = 150 if not self.is_boss else 60

        # Charger burst state
        self._charge_cooldown = 2500
        self._charge_duration = 400
        self._last_charge = 0
        self._charging = False
        self._charge_dx = 0.0
        self._charge_dy = 0.0

        # Boss special attack state
        self._special = preset.get("special", None)
        self._last_special = -3000     # ready soon after spawn
        self._special_active = False
        self._special_timer = 0
        self.special_attack_hit = False
        # Per-boss special tuning
        _special_params = {
            "ground_slam":      {"cooldown": 4000, "duration": 800,  "range": 300, "aoe_mult": 3.5},
            "war_cry":          {"cooldown": 7000, "duration": 1000, "range": 450, "aoe_mult": 5.0},
            "flame_pillar":     {"cooldown": 3000, "duration": 1200, "range": 400, "aoe_mult": 2.5},
            "tentacle_sweep":   {"cooldown": 4500, "duration": 900,  "range": 350, "aoe_mult": 4.0},
            "void_rift":        {"cooldown": 5000, "duration": 1000, "range": 400, "aoe_mult": 2.0},
            "null_burst":       {"cooldown": 3500, "duration": 700,  "range": 400, "aoe_mult": 4.0},
            # Phase 2 / secondary specials
            "missile_barrage":  {"cooldown": 3500, "duration": 600,  "range": 500, "aoe_mult": 1.5},
            "bleed_storm":      {"cooldown": 5000, "duration": 800,  "range": 600, "aoe_mult": 1.0},
            "fire_ring":        {"cooldown": 5000, "duration": 1400, "range": 450, "aoe_mult": 2.0},
            "eldritch_pull":    {"cooldown": 6000, "duration": 1500, "range": 500, "aoe_mult": 3.0},
            "void_cage":        {"cooldown": 6500, "duration": 1800, "range": 450, "aoe_mult": 2.5},
            "reality_collapse": {"cooldown": 5500, "duration": 1000, "range": 500, "aoe_mult": 3.5},
        }
        sp = _special_params.get(self._special, {})
        self._special_cooldown = sp.get("cooldown", 5000)
        self._special_duration = sp.get("duration", 600)
        self._special_trigger_range = sp.get("range", 300)
        self._special_aoe_mult = sp.get("aoe_mult", 3.0)
        # Secondary (phase 2) special
        _special2_map = {
            "iron_sentinel":   "missile_barrage",
            "warlord_kron":    "bleed_storm",
            "preacher":        "fire_ring",
            "eldritch_horror": "eldritch_pull",
            "architect":       "void_cage",
            "nexus":           "reality_collapse",
        }
        self._special2 = _special2_map.get(enemy_type)
        if self._special2:
            sp2 = _special_params[self._special2]
            self._special2_cooldown = sp2["cooldown"]
            self._special2_duration = sp2["duration"]
            self._special2_trigger_range = sp2["range"]
            self._special2_aoe_mult = sp2["aoe_mult"]
        else:
            self._special2 = None
            self._special2_cooldown = 99999
            self._special2_duration = 600
            self._special2_trigger_range = 400
            self._special2_aoe_mult = 3.0
        self._last_special2 = -5000  # offset so specials don't collide immediately
        self._special2_active = False
        self._special2_timer = 0
        self.special2_attack_hit = False
        self._special2_target_x = 0.0
        self._special2_target_y = 0.0
        # Phase 2 tracking
        self._phase2_active = False
        self.wants_enrage = False   # triggers sound + visual in game.py
        # Spread shot defaults for bosses
        _boss_spread = {
            "iron_sentinel":   (3, 0.35),   # 3 shots, 20° spread
            "warlord_kron":    (5, 0.45),   # 5 shots, 26°
            "preacher":        (3, 0.50),   # 3 fire shots
            "eldritch_horror": (7, 0.70),   # 7-shot tentacle fan
            "architect":       (3, 0.40),   # 3 void bolts
            "nexus":           (9, 0.80),   # 9-shot spiral ring
        }
        if enemy_type in _boss_spread:
            self.shoot_spread_count, self.shoot_spread_arc = _boss_spread[enemy_type]
        # Ground slam / war cry AoE ring
        self._aoe_ring_timer = 0
        self._aoe_ring_radius = 0
        # Targeted specials (flame_pillar, void_rift) mark player position
        self._special_target_x = 0.0
        self._special_target_y = 0.0
        # Tentacle sweep: directional attack
        self._sweep_angle = 0.0

        # Shielder: frontal shield blocks damage
        self._shield_angle = 0.0  # angle shield faces

        # Simple wander state
        self.wander_dx = 0.0
        self.wander_dy = 0.0
        self.wander_timer = 0

        # Hit flash
        self.hit_flash = 0

        # Animation
        self.anim_offset = random.uniform(0, math.tau)
        self.gun_flash_timer = 0

        # Void wisp: 30% chance to phase through damage
        self._phase_chance = 0.30 if enemy_type == "void_wisp" else 0.0
        # Rift walker: short-range teleport
        self._teleport_cooldown = 3500
        self._last_teleport = 0
        # Cyber dog: leap attack
        self._dog_leap_state = "chase"  # "chase", "crouch", "leap"
        self._dog_crouch_start = 0
        self._dog_leap_start = 0
        self._dog_leap_dx = 0.0
        self._dog_leap_dy = 0.0
        self._dog_leap_cooldown = 3000
        self._dog_last_leap = 0
        self._dog_wants_bark = False
        self._dog_wants_growl = False
        # Mirror shade: split at 50% HP
        self.wants_to_split = False
        self._has_split = False
        self.spawn_time = 0  # set by game when spawned
        self.spawn_duration = 400  # ms to scale in

    _BOSS_TYPES = frozenset(("iron_sentinel", "warlord_kron", "preacher",
                             "eldritch_horror", "architect", "nexus"))
    _BIG_BOSS_TYPES = frozenset(("warlord_kron", "eldritch_horror", "nexus"))

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.x - self.size // 2,
            self.y - self.size // 2,
            self.size,
            self.size,
        )

    @property
    def is_boss(self) -> bool:
        return self.enemy_type in self._BOSS_TYPES

    @property
    def is_big_boss(self) -> bool:
        return self.enemy_type in self._BIG_BOSS_TYPES

    def take_damage(self, amount: int, knockback_x: float, knockback_y: float, now: int):
        # Void wisp: phase through attacks
        if self._phase_chance > 0 and random.random() < self._phase_chance:
            return
        # Shielder: frontal shield reduces damage by 70%
        if self.enemy_type == "shielder" and (knockback_x != 0 or knockback_y != 0):
            import math as _m
            hit_angle = _m.atan2(knockback_y, knockback_x)
            face_angle = _m.atan2(self.face_y, self.face_x)
            diff = abs(hit_angle - face_angle)
            if diff > _m.pi:
                diff = 2 * _m.pi - diff
            # If hit from the front (within 90 degrees of facing)
            if diff > _m.pi * 0.5:
                amount = max(1, amount * 3 // 10)
        self.hp -= amount
        self.hit_flash = now
        if self.hp <= 0:
            self.alive = False
        # Apply knockback (reduced for bosses)
        length = math.hypot(knockback_x, knockback_y)
        if length > 0:
            # Mirror shade split at 50% HP
            if (self.enemy_type == "mirror_shade" and not self._has_split
                    and self.hp > 0 and self.hp <= self.max_hp * 0.5):
                self.wants_to_split = True
                self._has_split = True
            kb_str = 8 if not self.is_boss else 3
            self.kb_dx = (knockback_x / length) * kb_str
            self.kb_dy = (knockback_y / length) * kb_str
            self.kb_timer = now

    def update(self, dt: float, now: int, player_x: float, player_y: float, world_w: int, world_h: int):
        if not self.alive:
            return

        # Status effect ticks
        status_dmg = self.statuses.update(now)
        if status_dmg > 0:
            self.hp -= status_dmg
            if self.hp <= 0:
                self.alive = False
                return

        speed_mult = self.statuses.get_speed_mult()
        effective_speed = self.speed * speed_mult

        self.wants_to_shoot = False

        # Knockback movement
        if now - self.kb_timer < self.kb_duration:
            self.x += self.kb_dx
            self.y += self.kb_dy
            self.kb_dx *= 0.85
            self.kb_dy *= 0.85
            return

        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)

        # Track facing direction
        if dist > 0:
            self.face_x = dx / dist
            self.face_y = dy / dist

        if dist > 0:
            if self.shoot_range > 0 and dist < self.shoot_range and dist > self.attack_range:
                # Strafe while shooting
                strafe = math.sin(now * 0.002 + self.anim_offset) * effective_speed * 0.4
                self.x += -self.face_y * strafe
                self.y += self.face_x * strafe
                if now - self.last_shoot_time >= self.shoot_cooldown:
                    self.wants_to_shoot = True
                    self.last_shoot_time = now
                    self.gun_flash_timer = now
            else:
                self.x += (dx / dist) * effective_speed
                self.y += (dy / dist) * effective_speed

        # Rift walker: short-range teleport
        if self.enemy_type == "rift_walker" and dist < 250:
            if now - self._last_teleport > self._teleport_cooldown:
                self._last_teleport = now
                angle = random.uniform(0, math.tau)
                td = random.uniform(60, 120)
                self.x = player_x + math.cos(angle) * td
                self.y = player_y + math.sin(angle) * td

        # Charger: burst dash toward player
        if self.enemy_type == "charger":
            if self._charging:
                if now - self._last_charge > self._charge_duration:
                    self._charging = False
                else:
                    self.x += self._charge_dx * 6.0 * speed_mult
                    self.y += self._charge_dy * 6.0 * speed_mult
            elif dist < 200 and now - self._last_charge > self._charge_cooldown:
                self._charging = True
                self._last_charge = now
                if dist > 0:
                    self._charge_dx = dx / dist
                    self._charge_dy = dy / dist

        # Cyber dog: stop → crouch → leap attack
        if self.enemy_type == "cyber_dog":
            if self._dog_leap_state == "chase":
                if (dist < 100 and dist > 30
                        and now - self._dog_last_leap > self._dog_leap_cooldown):
                    self._dog_leap_state = "crouch"
                    self._dog_crouch_start = now
                    self._dog_wants_growl = True
                    if dist > 0:
                        self._dog_leap_dx = dx / dist
                        self._dog_leap_dy = dy / dist
            elif self._dog_leap_state == "crouch":
                # Stand still for 0.5s before leaping
                self.x -= (dx / dist) * effective_speed if dist > 0 else 0
                self.y -= (dy / dist) * effective_speed if dist > 0 else 0
                if now - self._dog_crouch_start > 500:
                    self._dog_leap_state = "leap"
                    self._dog_leap_start = now
                    self._dog_wants_bark = True
            elif self._dog_leap_state == "leap":
                leap_speed = effective_speed * 8.0
                self.x += self._dog_leap_dx * leap_speed
                self.y += self._dog_leap_dy * leap_speed
                if now - self._dog_leap_start > 200:
                    self._dog_leap_state = "chase"
                    self._dog_last_leap = now

        # Boss special attacks
        if self._special and self.is_boss and not self._special_active and not self._special2_active:
            if now - self._last_special > self._special_cooldown and dist < self._special_trigger_range:
                self._special_active = True
                self._special_timer = now
                self._last_special = now
                self._aoe_ring_timer = now
                self._aoe_ring_radius = 0
                # Targeted specials remember where the player was
                if self._special in ("flame_pillar", "void_rift"):
                    self._special_target_x = player_x
                    self._special_target_y = player_y
                # Tentacle sweep: lock direction toward player
                if self._special == "tentacle_sweep":
                    self._sweep_angle = math.atan2(dy, dx)

        # Boss secondary (phase 2) special attacks
        if self._special2 and self.is_boss and not self._special_active and not self._special2_active:
            if now - self._last_special2 > self._special2_cooldown and dist < self._special2_trigger_range:
                self._special2_active = True
                self._special2_timer = now
                self._last_special2 = now
                self._aoe_ring_timer = now
                self._aoe_ring_radius = 0
                # Remember player position for targeted secondaries
                self._special2_target_x = player_x
                self._special2_target_y = player_y

        if self._special_active:
            elapsed = now - self._special_timer
            if elapsed > self._special_duration:
                self._special_active = False

        if self._special2_active:
            elapsed2 = now - self._special2_timer
            if elapsed2 > self._special2_duration:
                self._special2_active = False

        # Phase 2: boss enrages at 40% HP
        if self.is_boss and not self._phase2_active and self.hp > 0 and self.hp <= self.max_hp * 0.40:
            self._phase2_active = True
            self.wants_enrage = True
            self.speed *= 1.4
            self._special_cooldown = int(self._special_cooldown * 0.55)
            self._special2_cooldown = int(self._special2_cooldown * 0.55)
            self.shoot_cooldown = int(self.shoot_cooldown * 0.65)
            # Upgrade spread in phase 2
            if self.shoot_spread_count > 1:
                self.shoot_spread_count += 2
                self.shoot_spread_arc = min(math.pi * 0.85, self.shoot_spread_arc + 0.30)

        # Flag for game.py to check and apply damage/effects
        self.special_attack_hit = False
        if self._special_active and self._special:
            elapsed = now - self._special_timer
            mid = self._special_duration // 2
            if self._special == "null_burst":
                # Multi-burst: hits at 30%, 60%, 90% of duration
                for frac in (0.3, 0.6, 0.9):
                    t = int(self._special_duration * frac)
                    if t - 20 < elapsed < t + 20:
                        self.special_attack_hit = True
                        self._aoe_ring_radius = int(self.size * self._special_aoe_mult)
            elif mid - 20 < elapsed < mid + 20:
                self.special_attack_hit = True
                self._aoe_ring_radius = int(self.size * self._special_aoe_mult)

        self.special2_attack_hit = False
        if self._special2_active and self._special2:
            elapsed2 = now - self._special2_timer
            mid2 = self._special2_duration // 2
            if self._special2 == "missile_barrage":
                # 5 bursts spread throughout the duration
                for frac in (0.15, 0.30, 0.50, 0.70, 0.85):
                    t2 = int(self._special2_duration * frac)
                    if t2 - 18 < elapsed2 < t2 + 18:
                        self.special2_attack_hit = True
            elif self._special2 == "null_burst" or self._special2 == "reality_collapse":
                for frac in (0.3, 0.65):
                    t2 = int(self._special2_duration * frac)
                    if t2 - 20 < elapsed2 < t2 + 20:
                        self.special2_attack_hit = True
                        self._aoe_ring_radius = int(self.size * self._special2_aoe_mult)
            elif mid2 - 20 < elapsed2 < mid2 + 20:
                self.special2_attack_hit = True
                self._aoe_ring_radius = int(self.size * self._special2_aoe_mult)

        half = self.size // 2
        self.x = max(half, min(world_w - half, self.x))
        self.y = max(half, min(world_h - half, self.y))

    def can_attack(self, player_x: float, player_y: float, now: int) -> bool:
        if not self.alive:
            return False
        dist = math.hypot(player_x - self.x, player_y - self.y)
        return dist < self.attack_range and (now - self.last_attack_time >= self.attack_cooldown)

    def perform_attack(self, now: int) -> int:
        self.last_attack_time = now
        return self.damage

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        if not self.alive:
            return
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        now = pygame.time.get_ticks()

        # Spawn-in scale animation
        spawn_t = 1.0
        if self.spawn_time > 0:
            elapsed = now - self.spawn_time
            if elapsed < self.spawn_duration:
                spawn_t = elapsed / self.spawn_duration
                # Ease-out bounce
                spawn_t = 1.0 - (1.0 - spawn_t) ** 2

        if spawn_t < 1.0:
            # Draw scaled version using a temp surface
            margin = 20
            w = self.size + margin * 2
            h = self.size + margin * 2 + 30  # extra for labels/bars
            temp = pygame.Surface((w, h), pygame.SRCALPHA)
            local_sx = w // 2
            local_sy = h // 2
            self._draw_dispatch(temp, local_sx, local_sy, now)
            # Scale
            sw = max(1, int(w * spawn_t))
            sh = max(1, int(h * spawn_t))
            scaled = pygame.transform.scale(temp, (sw, sh))
            surface.blit(scaled, (sx - sw // 2, sy - sh // 2))
        else:
            self._draw_dispatch(surface, sx, sy, now)

    def _draw_dispatch(self, surface: pygame.Surface, sx: int, sy: int, now: int):
        if self.enemy_type == "dalek":
            self._draw_dalek(surface, sx, sy, now)
        elif self.enemy_type == "wraith":
            self._draw_wraith(surface, sx, sy, now)
        elif self.enemy_type == "iron_sentinel":
            self._draw_mini_boss(surface, sx, sy, now)
        elif self.enemy_type == "warlord_kron":
            self._draw_big_boss(surface, sx, sy, now)
        elif self.enemy_type == "charger":
            self._draw_charger(surface, sx, sy, now)
        elif self.enemy_type == "shielder":
            self._draw_shielder(surface, sx, sy, now)
        elif self.enemy_type == "spitter":
            self._draw_spitter(surface, sx, sy, now)
        # Zone 2
        elif self.enemy_type == "cyber_zombie":
            self._draw_cyber_zombie(surface, sx, sy, now)
        elif self.enemy_type == "cyber_dog":
            self._draw_cyber_dog(surface, sx, sy, now)
        elif self.enemy_type == "drone":
            self._draw_drone(surface, sx, sy, now)
        elif self.enemy_type == "cultist":
            self._draw_cultist(surface, sx, sy, now)
        elif self.enemy_type == "shambler":
            self._draw_shambler(surface, sx, sy, now)
        elif self.enemy_type == "preacher":
            self._draw_preacher(surface, sx, sy, now)
        elif self.enemy_type == "eldritch_horror":
            self._draw_eldritch_horror(surface, sx, sy, now)
        # Zone 3
        elif self.enemy_type == "void_wisp":
            self._draw_void_wisp(surface, sx, sy, now)
        elif self.enemy_type == "rift_walker":
            self._draw_rift_walker(surface, sx, sy, now)
        elif self.enemy_type == "mirror_shade":
            self._draw_mirror_shade(surface, sx, sy, now)
        elif self.enemy_type == "gravity_warden":
            self._draw_gravity_warden(surface, sx, sy, now)
        elif self.enemy_type == "null_serpent":
            self._draw_null_serpent(surface, sx, sy, now)
        elif self.enemy_type == "architect":
            self._draw_architect(surface, sx, sy, now)
        elif self.enemy_type == "nexus":
            self._draw_nexus(surface, sx, sy, now)

        # Status effect particles
        self.statuses.draw_particles(surface, sx, sy, self.size)

        # HP bar
        bar_w = self.size
        bar_h = 5 if not self.is_boss else 8
        bar_x = sx - bar_w // 2
        bar_y = sy - self.size // 2 - 12
        ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, (80, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        bar_color = (220, 20, 20)
        if self.is_big_boss:
            bar_color = (255, 50, 50)
        elif self.is_boss:
            bar_color = (255, 160, 0)
        pygame.draw.rect(surface, bar_color, (bar_x, bar_y, int(bar_w * ratio), bar_h))
        if self.is_boss:
            pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 1)

        # Boss special attack visuals
        if self._special_active and self._aoe_ring_timer > 0:
            elapsed = now - self._aoe_ring_timer
            progress = min(1.0, elapsed / self._special_duration)
            max_ring = int(self.size * self._special_aoe_mult)

            if self._special == "ground_slam":
                # Expanding shockwave ring with inner fill
                ring_r = int(max_ring * progress)
                alpha = int(150 * (1.0 - progress))
                if ring_r > 0 and alpha > 0:
                    ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(ring_surf, (255, 200, 50, alpha), (ring_r + 2, ring_r + 2), ring_r, 4)
                    # Inner warning fill during windup
                    if progress < 0.5:
                        fill_a = int(40 * (1.0 - progress * 2))
                        pygame.draw.circle(ring_surf, (255, 200, 50, fill_a), (ring_r + 2, ring_r + 2), ring_r)
                    surface.blit(ring_surf, (sx - ring_r - 2, sy - ring_r - 2))

            elif self._special == "war_cry":
                # Pulsing red expanding ring — buff aura
                ring_r = int(max_ring * progress)
                pulse = 0.5 + 0.5 * math.sin(now * 0.015)
                alpha = int(100 * pulse * (1.0 - progress))
                if ring_r > 0 and alpha > 0:
                    ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(ring_surf, (255, 40, 40, alpha), (ring_r + 2, ring_r + 2), ring_r, 6)
                    pygame.draw.circle(ring_surf, (255, 100, 60, alpha // 2), (ring_r + 2, ring_r + 2), ring_r)
                    surface.blit(ring_surf, (sx - ring_r - 2, sy - ring_r - 2))

            elif self._special == "flame_pillar":
                # Targeting reticle at marked position, then fire eruption
                warn_r = int(self.size * self._special_aoe_mult)
                if progress < 0.5:
                    # Targeting phase: pulsing circle on ground
                    pulse = 0.5 + 0.5 * math.sin(now * 0.02)
                    a = int(80 * pulse * progress * 2)
                    w_surf = pygame.Surface((warn_r * 2 + 4, warn_r * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(w_surf, (255, 100, 0, a), (warn_r + 2, warn_r + 2), warn_r, 2)
                    # Draw at target position relative to boss screen pos
                    # (target stored in world coords; convert to screen-relative offset)
                    off_x = int(self._special_target_x - self.x)
                    off_y = int(self._special_target_y - self.y)
                    surface.blit(w_surf, (sx + off_x - warn_r - 2, sy + off_y - warn_r - 2))
                else:
                    # Fire eruption
                    fire_p = (progress - 0.5) / 0.5
                    a = int(180 * (1.0 - fire_p))
                    f_surf = pygame.Surface((warn_r * 2 + 4, warn_r * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(f_surf, (255, 80, 0, a), (warn_r + 2, warn_r + 2), warn_r)
                    pygame.draw.circle(f_surf, (255, 200, 50, a // 2), (warn_r + 2, warn_r + 2), warn_r // 2)
                    off_x = int(self._special_target_x - self.x)
                    off_y = int(self._special_target_y - self.y)
                    surface.blit(f_surf, (sx + off_x - warn_r - 2, sy + off_y - warn_r - 2))

            elif self._special == "tentacle_sweep":
                # Wide directional cone toward player
                sweep_range = int(max_ring * progress)
                alpha = int(130 * (1.0 - progress))
                if sweep_range > 4 and alpha > 0:
                    sweep_surf = pygame.Surface((sweep_range * 2 + 4, sweep_range * 2 + 4), pygame.SRCALPHA)
                    cx_s, cy_s = sweep_range + 2, sweep_range + 2
                    # Draw 60-degree cone in sweep direction
                    spread = math.radians(30)
                    pts = [(cx_s, cy_s)]
                    for a_step in range(13):
                        a_val = self._sweep_angle - spread + (2 * spread * a_step / 12)
                        pts.append((cx_s + int(math.cos(a_val) * sweep_range),
                                    cy_s + int(math.sin(a_val) * sweep_range)))
                    if len(pts) > 2:
                        pygame.draw.polygon(sweep_surf, (80, 200, 80, alpha), pts)
                        pygame.draw.polygon(sweep_surf, (120, 255, 120, alpha), pts, 2)
                    surface.blit(sweep_surf, (sx - sweep_range - 2, sy - sweep_range - 2))

            elif self._special == "void_rift":
                # Dark portal expanding at target position
                rift_r = int(self.size * self._special_aoe_mult)
                pulse = 0.5 + 0.5 * math.sin(now * 0.012)
                a = int((100 + 40 * pulse) * (1.0 - progress * 0.3))
                off_x = int(self._special_target_x - self.x)
                off_y = int(self._special_target_y - self.y)
                v_surf = pygame.Surface((rift_r * 2 + 4, rift_r * 2 + 4), pygame.SRCALPHA)
                # Outer ring
                pygame.draw.circle(v_surf, (120, 30, 255, a), (rift_r + 2, rift_r + 2), rift_r, 3)
                # Inner dark fill
                inner_r = int(rift_r * min(1.0, progress * 1.5))
                if inner_r > 0:
                    pygame.draw.circle(v_surf, (40, 0, 80, a // 2), (rift_r + 2, rift_r + 2), inner_r)
                surface.blit(v_surf, (sx + off_x - rift_r - 2, sy + off_y - rift_r - 2))

            elif self._special == "null_burst":
                # Multiple concentric expanding rings
                for burst_i, frac in enumerate((0.3, 0.6, 0.9)):
                    t_frac = frac * self._special_duration
                    if elapsed > t_frac - 100:
                        burst_progress = min(1.0, (elapsed - t_frac + 100) / 300)
                        ring_r = int(max_ring * burst_progress)
                        a = int(100 * (1.0 - burst_progress))
                        if ring_r > 0 and a > 0:
                            r_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
                            pygame.draw.circle(r_surf, (0, 180, 255, a), (ring_r + 2, ring_r + 2), ring_r, 3)
                            surface.blit(r_surf, (sx - ring_r - 2, sy - ring_r - 2))

    # ═══════════════════════════════════════════ DALEK drawing
    def _draw_dalek(self, surface, sx, sy, now):
        bob = math.sin(now * 0.004 + self.anim_offset) * 2
        is_hit = now - self.hit_flash < 100
        half = self.size // 2

        skirt_color = (255, 255, 255) if is_hit else ENEMY_SKIRT_COLOR
        skirt_pts = [
            (sx - half - 4, sy + half + bob),
            (sx + half + 4, sy + half + bob),
            (sx + half - 2, sy + 4 + bob),
            (sx - half + 2, sy + 4 + bob),
        ]
        pygame.draw.polygon(surface, skirt_color, skirt_pts)
        for i in range(-1, 2):
            bx = sx + i * 12
            by = int(sy + half * 0.6 + bob)
            pygame.draw.circle(surface, (160, 150, 140) if not is_hit else (255, 255, 255), (bx, by), 4)

        body_color = (255, 255, 255) if is_hit else ENEMY_BODY_COLOR
        pygame.draw.rect(surface, body_color,
                         pygame.Rect(sx - half + 2, sy - 6 + bob, self.size - 4, 14))

        gun_len = 18
        gun_ex = sx + int(self.face_x * gun_len)
        gun_ey = int(sy - 2 + bob + self.face_y * gun_len)
        gun_color = ENEMY_EYE_COLOR if now - self.gun_flash_timer < 150 else (160, 150, 140)
        pygame.draw.line(surface, gun_color, (sx, int(sy - 2 + bob)), (gun_ex, gun_ey), 3)
        if now - self.gun_flash_timer < 150:
            pygame.draw.circle(surface, (0, 255, 200), (gun_ex, gun_ey), 5)

        dome_color = (255, 255, 255) if is_hit else ENEMY_DOME_COLOR
        pygame.draw.ellipse(surface, dome_color,
                            (sx - half + 6, sy - half + 2 + bob, self.size - 12, 16))

        eye_len = 14
        eye_ex = sx + int(self.face_x * eye_len)
        eye_ey = int(sy - half + 8 + bob + self.face_y * eye_len * 0.3)
        pygame.draw.line(surface, (100, 100, 100),
                         (sx, int(sy - half + 8 + bob)), (eye_ex, eye_ey), 2)
        pygame.draw.circle(surface, ENEMY_EYE_COLOR, (eye_ex, eye_ey), 3)

    # ═══════════════════════════════════════════ WRAITH drawing
    def _draw_wraith(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        # Wraith — ghostly floating entity with wispy cloak
        hover = math.sin(now * 0.005 + self.anim_offset) * 4

        # Wispy cloak bottom
        cloak_color = (60, 20, 80) if not is_hit else (255, 255, 255)
        for i in range(3):
            wave = math.sin(now * 0.004 + i * 1.5 + self.anim_offset) * 4
            pts = [
                (sx - half + i * 5 + wave, sy + half + hover),
                (sx - half + i * 5 + 8 + wave, sy + half + 6 + hover),
                (sx - half + i * 5 + 4 + wave, sy + half + 10 + hover),
            ]
            pygame.draw.polygon(surface, cloak_color, pts)

        # Main body — elongated dark shape
        body_color = (80, 30, 120) if not is_hit else (255, 255, 255)
        pygame.draw.ellipse(surface, body_color,
                            (sx - half, sy - half + hover, self.size, self.size + 6))
        # Inner glow
        glow_surf = pygame.Surface((self.size - 8, self.size - 4), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (120, 50, 180, 80),
                            (0, 0, self.size - 8, self.size - 4))
        surface.blit(glow_surf, (sx - half + 4, sy - half + 2 + hover))

        # Eyes — two glowing orbs
        eye_color = (180, 255, 100) if not is_hit else (255, 255, 200)
        pygame.draw.circle(surface, eye_color,
                           (sx - 5, int(sy - 4 + hover)), 4)
        pygame.draw.circle(surface, eye_color,
                           (sx + 5, int(sy - 4 + hover)), 4)
        # Pupils
        pygame.draw.circle(surface, (0, 0, 0),
                           (sx - 5 + int(self.face_x * 2), int(sy - 4 + hover + self.face_y * 2)), 2)
        pygame.draw.circle(surface, (0, 0, 0),
                           (sx + 5 + int(self.face_x * 2), int(sy - 4 + hover + self.face_y * 2)), 2)

        # Poison trail particles
        for i in range(2):
            trail_x = sx - int(self.face_x * (15 + i * 10))
            trail_y = sy - int(self.face_y * (15 + i * 10)) + int(hover)
            alpha = 100 - i * 40
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (80, 200, 60, max(0, alpha)), (3, 3), 3)
            surface.blit(s, (trail_x - 3, trail_y - 3))

    # ═══════════════════════════════════════════ MINI BOSS drawing
    def _draw_mini_boss(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        bob = math.sin(now * 0.003 + self.anim_offset) * 3

        # Heavy armored Dalek — bigger, gold trim
        # Skirt
        skirt_color = (200, 180, 80) if not is_hit else (255, 255, 255)
        skirt_pts = [
            (sx - half - 6, sy + half + bob),
            (sx + half + 6, sy + half + bob),
            (sx + half - 2, sy + 6 + bob),
            (sx - half + 2, sy + 6 + bob),
        ]
        pygame.draw.polygon(surface, skirt_color, skirt_pts)
        # Sensor globes (more of them)
        for i in range(-2, 3):
            bx = sx + i * 12
            by = int(sy + half * 0.5 + bob)
            pygame.draw.circle(surface, (255, 220, 100), (bx, by), 5)

        # Body
        body_color = (180, 160, 60) if not is_hit else (255, 255, 255)
        pygame.draw.rect(surface, body_color,
                         (sx - half + 2, sy - 10 + bob, self.size - 4, 20))
        # Armor plates
        pygame.draw.rect(surface, (220, 200, 100),
                         (sx - half + 2, sy - 10 + bob, self.size - 4, 20), 2)

        # Dual gun stalks
        for side in (-1, 1):
            gun_len = 24
            gx = sx + side * 8 + int(self.face_x * gun_len)
            gy = int(sy - 4 + bob + self.face_y * gun_len)
            gun_color = (255, 100, 0) if now - self.gun_flash_timer < 150 else (200, 180, 100)
            pygame.draw.line(surface, gun_color,
                             (sx + side * 8, int(sy - 4 + bob)), (gx, gy), 4)
            if now - self.gun_flash_timer < 150:
                pygame.draw.circle(surface, (255, 200, 50), (gx, gy), 6)

        # Dome
        dome_color = (230, 210, 130) if not is_hit else (255, 255, 255)
        pygame.draw.ellipse(surface, dome_color,
                            (sx - half + 8, sy - half + 4 + bob, self.size - 16, 20))

        # Crown spikes
        for i in range(-1, 2):
            spike_x = sx + i * 10
            pygame.draw.line(surface, (255, 220, 80),
                             (spike_x, int(sy - half + 4 + bob)),
                             (spike_x, int(sy - half - 8 + bob)), 2)

        # Eye
        eye_ex = sx + int(self.face_x * 16)
        eye_ey = int(sy - half + 10 + bob + self.face_y * 5)
        pygame.draw.circle(surface, (255, 80, 0), (eye_ex, eye_ey), 5)
        pygame.draw.circle(surface, (255, 200, 50), (eye_ex, eye_ey), 3)

        # "MINI BOSS" label
        label = get_font("consolas", 10, True).render("ELITE", True, (255, 200, 50))
        surface.blit(label, (sx - label.get_width() // 2, sy - half - 22))

    # ═══════════════════════════════════════════ BIG BOSS drawing
    def _draw_big_boss(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        bob = math.sin(now * 0.002 + self.anim_offset) * 4
        pulse = 0.7 + 0.3 * math.sin(now * 0.004)

        # Massive armored body — dark red with pulsing energy
        # Base
        base_color = (120, 20, 20) if not is_hit else (255, 255, 255)
        skirt_pts = [
            (sx - half - 8, sy + half + bob),
            (sx + half + 8, sy + half + bob),
            (sx + half, sy + bob),
            (sx - half, sy + bob),
        ]
        pygame.draw.polygon(surface, base_color, skirt_pts)

        # Core body
        body_color = (160, 30, 30) if not is_hit else (255, 255, 255)
        pygame.draw.rect(surface, body_color,
                         (sx - half + 4, sy - 16 + bob, self.size - 8, 28))
        # Energy veins
        vein_alpha = int(100 + 80 * pulse)
        vein_surf = pygame.Surface((self.size - 8, 28), pygame.SRCALPHA)
        for i in range(3):
            vy = 4 + i * 9
            pygame.draw.line(vein_surf, (255, 60, 20, vein_alpha),
                             (2, vy), (self.size - 10, vy), 2)
        surface.blit(vein_surf, (sx - half + 4, sy - 16 + bob))

        # Shoulder cannons
        for side in (-1, 1):
            cannon_x = sx + side * (half + 4)
            cannon_y = int(sy - 10 + bob)
            pygame.draw.rect(surface, (100, 15, 15),
                             (cannon_x - 5, cannon_y - 4, 10, 16))
            pygame.draw.rect(surface, (200, 50, 50),
                             (cannon_x - 5, cannon_y - 4, 10, 16), 1)
            # Barrel
            gun_ex = cannon_x + int(self.face_x * 20)
            gun_ey = int(cannon_y + self.face_y * 20)
            pygame.draw.line(surface, (200, 80, 40),
                             (cannon_x, cannon_y), (gun_ex, gun_ey), 4)
            if now - self.gun_flash_timer < 200:
                pygame.draw.circle(surface, (255, 100, 20), (gun_ex, gun_ey), 8)

        # Dome / Head
        dome_color = (180, 40, 40) if not is_hit else (255, 255, 255)
        pygame.draw.ellipse(surface, dome_color,
                            (sx - 20, sy - half + 4 + bob, 40, 22))
        # Crown
        for i in range(-2, 3):
            pygame.draw.line(surface, (255, 50, 20),
                             (sx + i * 8, int(sy - half + 4 + bob)),
                             (sx + i * 8, int(sy - half - 10 + bob)), 3)

        # Eye — large, menacing
        eye_ex = sx + int(self.face_x * 18)
        eye_ey = int(sy - half + 14 + bob + self.face_y * 4)
        pygame.draw.circle(surface, (255, 0, 0), (eye_ex, eye_ey), 7)
        pygame.draw.circle(surface, (255, 200, 100), (eye_ex, eye_ey), 4)

        # Pulsing aura
        aura_r = int(half + 10 + 6 * math.sin(now * 0.005))
        aura_surf = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(aura_surf, (255, 30, 0, int(30 * pulse)),
                           (aura_r, aura_r), aura_r)
        surface.blit(aura_surf, (sx - aura_r, int(sy + bob) - aura_r))

        # "BOSS" label
        label = get_font("consolas", 12, True).render("BOSS", True, (255, 60, 60))
        surface.blit(label, (sx - label.get_width() // 2, sy - half - 26))

    # ═══════════════════════════════════════════ CHARGER drawing
    def _draw_charger(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2

        # Arrow / wedge shape pointing toward player
        tip_x = sx + int(self.face_x * half)
        tip_y = sy + int(self.face_y * half)
        # Two rear points
        perp_x = -self.face_y
        perp_y = self.face_x
        rear_x = sx - int(self.face_x * half * 0.6)
        rear_y = sy - int(self.face_y * half * 0.6)
        pts = [
            (tip_x, tip_y),
            (rear_x + int(perp_x * half * 0.8), rear_y + int(perp_y * half * 0.8)),
            (rear_x - int(perp_x * half * 0.8), rear_y - int(perp_y * half * 0.8)),
        ]

        # Charge trail
        if self._charging:
            body_color = (255, 100, 50) if not is_hit else (255, 255, 255)
            # Motion blur trail
            for i in range(3):
                t = (i + 1) * 6
                trail_pts = [(px - int(self._charge_dx * t), py - int(self._charge_dy * t))
                             for px, py in pts]
                ts = pygame.Surface((self.size * 3, self.size * 3), pygame.SRCALPHA)
                offset = self.size * 3 // 2
                shifted = [(px - sx + offset, py - sy + offset) for px, py in trail_pts]
                pygame.draw.polygon(ts, (255, 100, 50, 60 - i * 20), shifted)
                surface.blit(ts, (sx - offset, sy - offset))
        else:
            body_color = (220, 60, 30) if not is_hit else (255, 255, 255)

        pygame.draw.polygon(surface, body_color, pts)
        pygame.draw.polygon(surface, (255, 150, 80), pts, 2)

        # Eye at front
        eye_x = sx + int(self.face_x * half * 0.3)
        eye_y = sy + int(self.face_y * half * 0.3)
        pygame.draw.circle(surface, (255, 200, 50), (eye_x, eye_y), 4)
        pygame.draw.circle(surface, (0, 0, 0), (eye_x, eye_y), 2)

    # ═══════════════════════════════════════════ SHIELDER drawing
    def _draw_shielder(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        bob = math.sin(now * 0.003 + self.anim_offset) * 2

        # Heavy armored body
        body_color = (60, 80, 140) if not is_hit else (255, 255, 255)
        pygame.draw.ellipse(surface, body_color,
                            (sx - half, sy - half + bob, self.size, self.size))

        # Armor plates
        plate_color = (90, 120, 180) if not is_hit else (255, 255, 255)
        pygame.draw.ellipse(surface, plate_color,
                            (sx - half, sy - half + bob, self.size, self.size), 3)

        # Frontal shield arc
        shield_cx = sx + int(self.face_x * half * 0.7)
        shield_cy = int(sy + bob + self.face_y * half * 0.7)
        shield_pulse = int(120 + 60 * math.sin(now * 0.006))
        s = pygame.Surface((self.size + 10, self.size + 10), pygame.SRCALPHA)
        sc = (self.size + 10) // 2
        # Shield arc — draw a thick arc from -60 to +60 degrees relative to facing
        face_angle = math.atan2(self.face_y, self.face_x)
        arc_start = face_angle - 1.0
        arc_end = face_angle + 1.0
        arc_points = []
        steps = 10
        for i in range(steps + 1):
            a = arc_start + (arc_end - arc_start) * i / steps
            arc_points.append((
                shield_cx + int(math.cos(a) * (half + 3)),
                shield_cy + int(math.sin(a) * (half + 3))
            ))
        if len(arc_points) >= 2:
            shield_s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.lines(shield_s, (100, 180, 255, shield_pulse), False, arc_points, 4)
            surface.blit(shield_s, (0, 0))

        # Eyes
        eye_color = (100, 200, 255) if not is_hit else (255, 255, 200)
        pygame.draw.circle(surface, eye_color, (sx - 5, int(sy - 3 + bob)), 4)
        pygame.draw.circle(surface, eye_color, (sx + 5, int(sy - 3 + bob)), 4)
        pygame.draw.circle(surface, (0, 0, 0), (sx - 5, int(sy - 3 + bob)), 2)
        pygame.draw.circle(surface, (0, 0, 0), (sx + 5, int(sy - 3 + bob)), 2)

    # ═══════════════════════════════════════════ SPITTER drawing
    def _draw_spitter(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        bob = math.sin(now * 0.005 + self.anim_offset) * 3

        # Bloated insect-like body
        body_color = (50, 120, 40) if not is_hit else (255, 255, 255)
        # Main body
        pygame.draw.ellipse(surface, body_color,
                            (sx - half, sy - half // 2 + bob, self.size, int(self.size * 0.7)))
        # Bulge (acid sac)
        sac_color = (80, 200, 50) if not is_hit else (255, 255, 255)
        sac_pulse = int(half * 0.4 + 2 * math.sin(now * 0.004))
        pygame.draw.circle(surface, sac_color,
                           (sx - int(self.face_x * 4), int(sy + bob + 2)),
                           sac_pulse)

        # Mandibles
        mand_len = half * 0.6
        for side in (-1, 1):
            perp_x = -self.face_y * side
            perp_y = self.face_x * side
            mx = sx + int(self.face_x * mand_len + perp_x * 4)
            my = int(sy + bob + self.face_y * mand_len + perp_y * 4)
            mand_color = (100, 60, 20) if not is_hit else (255, 255, 255)
            pygame.draw.line(surface, mand_color,
                             (sx + int(self.face_x * 4), int(sy + bob)),
                             (mx, my), 3)

        # Eyes (4 small spider eyes)
        eye_color = (200, 255, 50) if not is_hit else (255, 255, 200)
        for dx_off, dy_off in [(-4, -5), (4, -5), (-7, -2), (7, -2)]:
            pygame.draw.circle(surface, eye_color,
                               (sx + dx_off, int(sy + dy_off + bob)), 2)

        # Gun flash when shooting
        if now - self.gun_flash_timer < 200:
            flash_x = sx + int(self.face_x * half)
            flash_y = int(sy + bob + self.face_y * half)
            pygame.draw.circle(surface, (100, 255, 50), (flash_x, flash_y), 6)

    # ═══════════════════════════════════════════ CYBER ZOMBIE drawing
    def _draw_cyber_zombie(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        bob = math.sin(now * 0.003 + self.anim_offset) * 2

        # Hunched humanoid body
        body_color = (80, 90, 70) if not is_hit else (255, 255, 255)
        # Torso
        pygame.draw.ellipse(surface, body_color,
                            (sx - half + 2, sy - half + 4 + bob, self.size - 4, self.size - 2))
        # Red circuit veins
        for i in range(3):
            vy = sy - half + 8 + i * 8 + bob
            vx_start = sx - half + 6
            vx_end = sx + half - 6
            vx_mid = sx + int(math.sin(i * 2.1) * 4)
            pygame.draw.line(surface, (200, 30, 30), (vx_start, int(vy)), (vx_mid, int(vy + 3)), 2)
            pygame.draw.line(surface, (200, 30, 30), (vx_mid, int(vy + 3)), (vx_end, int(vy)), 2)
        # Arms dangling
        for side in (-1, 1):
            ax = sx + side * (half - 2)
            arm_sway = math.sin(now * 0.005 + side + self.anim_offset) * 3
            pygame.draw.line(surface, body_color, (ax, int(sy + bob)),
                             (ax + int(arm_sway), int(sy + half + 4 + bob)), 3)
        # Glowing red eyes
        eye_color = (255, 40, 40) if not is_hit else (255, 255, 200)
        pygame.draw.circle(surface, eye_color, (sx - 4, int(sy - 6 + bob)), 3)
        pygame.draw.circle(surface, eye_color, (sx + 4, int(sy - 6 + bob)), 3)

    # ═══════════════════════════════════════════ CYBER DOG drawing
    def _draw_cyber_dog(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        run_cycle = math.sin(now * 0.01 + self.anim_offset) * 3
        crouching = self._dog_leap_state == "crouch"
        leaping = self._dog_leap_state == "leap"

        # Crouch squash / leap stretch
        squash_y = 3 if crouching else (-4 if leaping else 0)
        stretch_x = 2 if leaping else 0

        # Angular metallic body (rectangle with bevels)
        body_color = (160, 165, 175) if not is_hit else (255, 255, 255)
        body_y = sy - 2 + run_cycle + squash_y
        bw = half + 6 + stretch_x
        bh = int(self.size * 0.45) - (2 if crouching else 0)
        pygame.draw.rect(surface, body_color, (sx - bw, int(body_y) - bh // 2, bw * 2, bh))
        # Plating lines
        plate_color = (130, 135, 145) if not is_hit else (220, 220, 220)
        pygame.draw.line(surface, plate_color,
                         (sx - bw + 3, int(body_y) - bh // 2 + 2),
                         (sx - bw + 3, int(body_y) + bh // 2 - 2), 1)
        pygame.draw.line(surface, plate_color,
                         (sx + bw - 3, int(body_y) - bh // 2 + 2),
                         (sx + bw - 3, int(body_y) + bh // 2 - 2), 1)
        # Center seam
        pygame.draw.line(surface, plate_color,
                         (sx - bw + 2, int(body_y)),
                         (sx + bw - 2, int(body_y)), 1)

        # Head — angular box at front
        head_x = sx + int(self.face_x * (half + 4))
        head_y = int(body_y - 3 + self.face_y * 4)
        hw, hh = 7, 6
        pygame.draw.rect(surface, body_color,
                         (head_x - hw, head_y - hh, hw * 2, hh * 2))
        pygame.draw.rect(surface, plate_color,
                         (head_x - hw, head_y - hh, hw * 2, hh * 2), 1)

        # Metal jaw (opens during leap)
        jaw_open = 4 if leaping else 1
        jaw_x = head_x + int(self.face_x * 8)
        jaw_y = head_y + jaw_open
        pygame.draw.polygon(surface, (140, 145, 155) if not is_hit else (255, 255, 255), [
            (jaw_x - 4, jaw_y), (jaw_x + int(self.face_x * 6), jaw_y + 3),
            (jaw_x + 4, jaw_y),
        ])
        # Teeth during leap
        if leaping:
            for tx in range(-3, 4, 2):
                pygame.draw.line(surface, (200, 200, 210),
                                 (jaw_x + tx, jaw_y), (jaw_x + tx, jaw_y + 2), 1)

        # Glowing red LED eyes
        ex = head_x + int(self.face_x * 3)
        ey = head_y - 2 + int(self.face_y * 2)
        eye_color = (255, 20, 20) if not is_hit else (255, 255, 200)
        eye_glow_a = int(180 + 75 * math.sin(now * 0.008))
        # Eye glow
        glow_s = pygame.Surface((12, 8), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (*eye_color[:2], 0, eye_glow_a), (4, 4), 4)
        pygame.draw.circle(glow_s, (*eye_color[:2], 0, eye_glow_a), (8, 4), 4)
        surface.blit(glow_s, (ex - 6, ey - 4))
        pygame.draw.circle(surface, eye_color, (ex - 2, ey), 2)
        pygame.draw.circle(surface, eye_color, (ex + 2, ey), 2)

        # Antenna on back
        ant_x = sx - int(self.face_x * (half + 2))
        ant_y = int(body_y - bh // 2)
        pygame.draw.line(surface, (120, 125, 130),
                         (ant_x, ant_y), (ant_x, ant_y - 8), 1)
        blink = (now // 400) % 2 == 0
        ant_color = (255, 50, 50) if blink else (80, 20, 20)
        pygame.draw.circle(surface, ant_color, (ant_x, ant_y - 8), 2)

        # Legs — mechanical pistons (4 legs)
        leg_color = (100, 105, 115) if not is_hit else (200, 200, 200)
        joint_color = (140, 145, 155)
        for lx_off, ly_phase in [(-7, 0), (-3, 1.5), (3, 3.0), (7, 4.5)]:
            cycle = 0 if crouching else abs(math.sin(now * 0.012 + ly_phase)) * 5
            foot_y = int(sy + half // 2 + cycle + run_cycle + squash_y)
            knee_y = int(body_y + bh // 2)
            mid_y = (knee_y + foot_y) // 2
            # Upper leg
            pygame.draw.line(surface, leg_color,
                             (sx + lx_off, knee_y), (sx + lx_off, mid_y), 2)
            # Joint
            pygame.draw.circle(surface, joint_color, (sx + lx_off, mid_y), 2)
            # Lower leg
            pygame.draw.line(surface, leg_color,
                             (sx + lx_off, mid_y), (sx + lx_off, foot_y), 2)
            # Foot pad
            pygame.draw.circle(surface, (80, 85, 95), (sx + lx_off, foot_y), 2)

    # ═══════════════════════════════════════════ DRONE drawing
    def _draw_drone(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        hover = math.sin(now * 0.006 + self.anim_offset) * 5

        # Shadow on ground
        shadow_surf = pygame.Surface((self.size + 4, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60), (0, 0, self.size + 4, 8))
        surface.blit(shadow_surf, (sx - half - 2, sy + 10))
        # Main disc body (hovering)
        disc_y = sy + hover - 10
        body_color = (180, 185, 195) if not is_hit else (255, 255, 255)
        pygame.draw.ellipse(surface, body_color,
                            (sx - half, int(disc_y) - 4, self.size, 10))
        # Propeller arms
        prop_speed = now * 0.03
        for i in range(4):
            angle = prop_speed + i * math.pi / 2
            px = sx + int(math.cos(angle) * (half + 4))
            py = int(disc_y + math.sin(angle) * 3)
            pygame.draw.line(surface, (120, 120, 130), (sx, int(disc_y)), (px, py), 1)
            pygame.draw.circle(surface, (160, 160, 170), (px, py), 2)
        # Center light
        light_color = (60, 140, 255) if not is_hit else (255, 255, 200)
        pygame.draw.circle(surface, light_color, (sx, int(disc_y)), 4)
        # Gun flash
        if now - self.gun_flash_timer < 150:
            fx = sx + int(self.face_x * half)
            fy = int(disc_y + self.face_y * half)
            pygame.draw.circle(surface, (80, 180, 255), (fx, fy), 5)

    # ═══════════════════════════════════════════ CULTIST drawing
    def _draw_cultist(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        bob = math.sin(now * 0.004 + self.anim_offset) * 2

        # Purple robe (trapezoid)
        robe_color = (80, 30, 120) if not is_hit else (255, 255, 255)
        robe_pts = [
            (sx - half + 4, sy + half + bob),
            (sx + half - 4, sy + half + bob),
            (sx + half - 8, sy - 4 + bob),
            (sx - half + 8, sy - 4 + bob),
        ]
        pygame.draw.polygon(surface, robe_color, robe_pts)
        # Hood (dark semicircle)
        hood_color = (50, 15, 80) if not is_hit else (200, 200, 200)
        pygame.draw.circle(surface, hood_color, (sx, int(sy - 8 + bob)), half // 2 + 2)
        # Glowing eyes under hood
        eye_color = (200, 100, 255) if not is_hit else (255, 255, 200)
        pygame.draw.circle(surface, eye_color, (sx - 3, int(sy - 9 + bob)), 2)
        pygame.draw.circle(surface, eye_color, (sx + 3, int(sy - 9 + bob)), 2)
        # Eldritch symbol on chest (small cross/star)
        sym_color = (220, 180, 50)
        sym_y = int(sy + 4 + bob)
        pygame.draw.line(surface, sym_color, (sx - 4, sym_y), (sx + 4, sym_y), 2)
        pygame.draw.line(surface, sym_color, (sx, sym_y - 4), (sx, sym_y + 4), 2)
        # Glowing hands
        for side in (-1, 1):
            hx = sx + side * (half - 2)
            hy = int(sy + 6 + bob)
            glow_s = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (180, 80, 255, 120), (5, 5), 5)
            surface.blit(glow_s, (hx - 5, hy - 5))
        # Gun flash
        if now - self.gun_flash_timer < 200:
            fx = sx + int(self.face_x * half)
            fy = int(sy + bob + self.face_y * half)
            pygame.draw.circle(surface, (180, 80, 255), (fx, fy), 6)

    # ═══════════════════════════════════════════ SHAMBLER drawing
    def _draw_shambler(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        bob = math.sin(now * 0.002 + self.anim_offset) * 2

        # Large bloated mass
        body_color = (70, 100, 60) if not is_hit else (255, 255, 255)
        pygame.draw.ellipse(surface, body_color,
                            (sx - half, sy - half + 4 + bob, self.size, self.size - 4))
        # Darker blotches
        for i in range(4):
            bx = sx + int(math.cos(i * 1.8 + self.anim_offset) * half * 0.4)
            by = int(sy + math.sin(i * 2.2 + self.anim_offset) * half * 0.3 + bob)
            pygame.draw.circle(surface, (50, 70, 40), (bx, by), 5)
        # Yellow pustules
        for i in range(5):
            px = sx + int(math.cos(i * 1.3 + self.anim_offset) * half * 0.6)
            py = int(sy + math.sin(i * 1.7 + self.anim_offset) * half * 0.5 + bob)
            pygame.draw.circle(surface, (200, 180, 40), (px, py), 3)
            pygame.draw.circle(surface, (220, 200, 60), (px, py), 2)
        # Tentacle appendages at base
        for i in range(3):
            wave = math.sin(now * 0.004 + i * 2.0 + self.anim_offset) * 6
            tx = sx - half // 2 + i * (half // 2)
            pygame.draw.line(surface, (60, 80, 50),
                             (tx, int(sy + half + bob)),
                             (tx + int(wave), int(sy + half + 12 + bob)), 3)
        # Small dull eyes
        pygame.draw.circle(surface, (160, 160, 80), (sx - 5, int(sy - 4 + bob)), 3)
        pygame.draw.circle(surface, (160, 160, 80), (sx + 5, int(sy - 4 + bob)), 3)

    # ═══════════════════════════════════════════ PREACHER drawing (Zone 2 mini boss)
    def _draw_preacher(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        bob = math.sin(now * 0.003 + self.anim_offset) * 3

        # Large ornate purple robe
        robe_color = (100, 40, 160) if not is_hit else (255, 255, 255)
        robe_pts = [
            (sx - half, sy + half + bob),
            (sx + half, sy + half + bob),
            (sx + half - 6, sy - 8 + bob),
            (sx - half + 6, sy - 8 + bob),
        ]
        pygame.draw.polygon(surface, robe_color, robe_pts)
        # Gold trim
        pygame.draw.line(surface, (220, 180, 50),
                         (sx - half, int(sy + half + bob)),
                         (sx + half, int(sy + half + bob)), 3)
        pygame.draw.line(surface, (220, 180, 50),
                         (sx - half + 6, int(sy - 8 + bob)),
                         (sx + half - 6, int(sy - 8 + bob)), 2)
        # Hood
        hood_color = (60, 20, 100) if not is_hit else (200, 200, 200)
        pygame.draw.circle(surface, hood_color, (sx, int(sy - 14 + bob)), half // 2 + 4)
        # Glowing halo
        halo_pulse = int(140 + 60 * math.sin(now * 0.005))
        halo_s = pygame.Surface((half * 2, half), pygame.SRCALPHA)
        pygame.draw.ellipse(halo_s, (220, 180, 50, halo_pulse),
                            (0, 0, half * 2, half // 2))
        surface.blit(halo_s, (sx - half, int(sy - half - 6 + bob)))
        # Staff
        staff_x = sx + 14
        pygame.draw.line(surface, (180, 150, 40),
                         (staff_x, int(sy - half - 4 + bob)),
                         (staff_x, int(sy + half + bob)), 3)
        pygame.draw.circle(surface, (255, 200, 80), (staff_x, int(sy - half - 8 + bob)), 5)
        # Eyes
        eye_color = (255, 180, 50) if not is_hit else (255, 255, 200)
        pygame.draw.circle(surface, eye_color, (sx - 4, int(sy - 16 + bob)), 3)
        pygame.draw.circle(surface, eye_color, (sx + 4, int(sy - 16 + bob)), 3)
        # ELITE label
        label = get_font("consolas", 10, True).render("ELITE", True, (200, 100, 255))
        surface.blit(label, (sx - label.get_width() // 2, sy - half - 24))

    # ═══════════════════════════════════════════ ELDRITCH HORROR drawing (Zone 2 boss)
    def _draw_eldritch_horror(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        pulse = 0.7 + 0.3 * math.sin(now * 0.003)

        # Tentacles (draw first, behind body)
        for i in range(6):
            base_angle = math.tau / 6 * i + now * 0.001
            length = half + 20 + math.sin(now * 0.004 + i) * 10
            segments = 5
            prev_x, prev_y = sx, sy
            for s in range(1, segments + 1):
                t = s / segments
                wave = math.sin(now * 0.005 + i * 1.5 + s * 0.8) * 8 * t
                tx = sx + int(math.cos(base_angle + wave * 0.02) * length * t)
                ty = sy + int(math.sin(base_angle + wave * 0.02) * length * t + wave)
                tent_color = (60, 30, 80) if not is_hit else (255, 255, 255)
                width = max(1, 5 - s)
                pygame.draw.line(surface, tent_color, (prev_x, prev_y), (tx, ty), width)
                prev_x, prev_y = tx, ty
            # Tip glow
            gs = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(gs, (140, 80, 200, 120), (4, 4), 4)
            surface.blit(gs, (prev_x - 4, prev_y - 4))

        # Massive dark body
        body_color = (50, 20, 60) if not is_hit else (255, 255, 255)
        pygame.draw.ellipse(surface, body_color,
                            (sx - half + 8, sy - half + 8, self.size - 16, self.size - 16))
        # Inner pulsing glow
        glow_r = int((half - 12) * pulse)
        glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (100, 40, 140, int(80 * pulse)), (glow_r, glow_r), glow_r)
        surface.blit(glow_s, (sx - glow_r, sy - glow_r))

        # Multiple eyes (8 scattered on body)
        for i in range(8):
            ea = math.tau / 8 * i + 0.3
            er = half * 0.4 + math.sin(i * 1.7) * 6
            ex = sx + int(math.cos(ea) * er)
            ey = sy + int(math.sin(ea) * er)
            eye_size = 4 if i % 3 != 0 else 6
            eye_color = (180, 220, 60) if not is_hit else (255, 255, 200)
            pygame.draw.circle(surface, eye_color, (ex, ey), eye_size)
            pygame.draw.circle(surface, (0, 0, 0), (ex, ey), max(1, eye_size - 2))

        # Gun flash
        if now - self.gun_flash_timer < 200:
            fx = sx + int(self.face_x * half)
            fy = sy + int(self.face_y * half)
            pygame.draw.circle(surface, (140, 60, 200), (fx, fy), 10)

        # BOSS label
        label = get_font("consolas", 12, True).render("BOSS", True, (180, 80, 220))
        surface.blit(label, (sx - label.get_width() // 2, sy - half - 26))

    # ═══════════════════════════════════════════ VOID WISP drawing
    def _draw_void_wisp(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        hover = math.sin(now * 0.007 + self.anim_offset) * 4
        pulse = 0.6 + 0.4 * math.sin(now * 0.008 + self.anim_offset)

        # Outer glow
        glow_r = int(half + 6 * pulse)
        gs = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(gs, (140, 80, 220, int(60 * pulse)),
                           (glow_r + 2, glow_r + 2), glow_r)
        surface.blit(gs, (sx - glow_r - 2, int(sy + hover) - glow_r - 2))
        # Core orb
        core_color = (200, 160, 255) if not is_hit else (255, 255, 255)
        pygame.draw.circle(surface, core_color, (sx, int(sy + hover)), int(half * pulse))
        # Bright center
        pygame.draw.circle(surface, (240, 220, 255), (sx, int(sy + hover)), max(2, int(half * 0.4)))
        # Trail wisps
        for i in range(3):
            tx = sx - int(self.face_x * (12 + i * 8))
            ty = int(sy + hover) - int(self.face_y * (12 + i * 8))
            alpha = max(0, 80 - i * 30)
            ts = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(ts, (160, 100, 240, alpha), (4, 4), 4 - i)
            surface.blit(ts, (tx - 4, ty - 4))

    # ═══════════════════════════════════════════ RIFT WALKER drawing
    def _draw_rift_walker(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2

        # Afterimage (slightly offset)
        ai_off = int(math.sin(now * 0.006) * 4)
        ai_s = pygame.Surface((self.size + 8, self.size + 16), pygame.SRCALPHA)
        ai_cx, ai_cy = (self.size + 8) // 2, (self.size + 16) // 2
        pygame.draw.ellipse(ai_s, (100, 50, 160, 60),
                            (ai_cx - half + ai_off, ai_cy - half, self.size, self.size + 6))
        surface.blit(ai_s, (sx - (self.size + 8) // 2, sy - (self.size + 16) // 2))

        # Main dark humanoid body
        body_color = (40, 20, 60) if not is_hit else (255, 255, 255)
        pygame.draw.ellipse(surface, body_color,
                            (sx - half + 4, sy - half, self.size - 8, self.size + 6))
        # Purple edge glow
        edge_s = pygame.Surface((self.size, self.size + 8), pygame.SRCALPHA)
        pygame.draw.ellipse(edge_s, (140, 60, 220, 100),
                            (0, 0, self.size - 8, self.size + 6), 2)
        surface.blit(edge_s, (sx - half + 4, sy - half))

        # Glitch scanlines
        for i in range(3):
            ly = sy - half + 4 + i * (self.size // 3)
            glitch_off = int(math.sin(now * 0.02 + i * 4.0) * 3)
            pygame.draw.line(surface, (160, 80, 255),
                             (sx - half + 6 + glitch_off, ly),
                             (sx + half - 6 + glitch_off, ly), 1)

        # Eyes
        eye_color = (200, 120, 255) if not is_hit else (255, 255, 200)
        pygame.draw.circle(surface, eye_color, (sx - 4, sy - 4), 3)
        pygame.draw.circle(surface, eye_color, (sx + 4, sy - 4), 3)

    # ═══════════════════════════════════════════ MIRROR SHADE drawing
    def _draw_mirror_shade(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2

        # Dark player-like silhouette
        body_color = (30, 30, 40) if not is_hit else (255, 255, 255)
        # Body
        pygame.draw.ellipse(surface, body_color,
                            (sx - half + 2, sy - half + 2, self.size - 4, self.size - 4))
        # Shifting color edge
        edge_hue = (now * 0.1) % 360
        r = int(128 + 127 * math.sin(edge_hue * 0.017))
        g = int(128 + 127 * math.sin(edge_hue * 0.017 + 2.09))
        b = int(128 + 127 * math.sin(edge_hue * 0.017 + 4.19))
        edge_s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.ellipse(edge_s, (r, g, b, 100),
                            (0, 0, self.size - 4, self.size - 4), 2)
        surface.blit(edge_s, (sx - half + 2, sy - half + 2))
        # Dark eyes that mirror the player
        pygame.draw.circle(surface, (200, 200, 220), (sx - 4, sy - 2), 3)
        pygame.draw.circle(surface, (200, 200, 220), (sx + 4, sy - 2), 3)
        pygame.draw.circle(surface, (0, 0, 0), (sx - 4, sy - 2), 2)
        pygame.draw.circle(surface, (0, 0, 0), (sx + 4, sy - 2), 2)
        # Shadow blur effect around edges
        for i in range(2):
            blur_s = pygame.Surface((self.size + 8 + i * 4, self.size + 8 + i * 4), pygame.SRCALPHA)
            pygame.draw.ellipse(blur_s, (20, 20, 30, 30 - i * 15),
                                (0, 0, self.size + 8 + i * 4, self.size + 8 + i * 4))
            surface.blit(blur_s, (sx - half - 4 - i * 2, sy - half - 4 - i * 2))

    # ═══════════════════════════════════════════ GRAVITY WARDEN drawing
    def _draw_gravity_warden(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        rot = now * 0.002 + self.anim_offset

        # Rotating diamond shape
        pts = []
        for i in range(4):
            angle = rot + i * math.pi / 2
            pts.append((sx + int(math.cos(angle) * half),
                        sy + int(math.sin(angle) * half)))
        body_color = (30, 40, 60) if not is_hit else (255, 255, 255)
        pygame.draw.polygon(surface, body_color, pts)
        # Cyan glow outline
        edge_s = pygame.Surface((self.size + 10, self.size + 10), pygame.SRCALPHA)
        offset = (self.size + 10) // 2
        edge_pts = [(px - sx + offset, py - sy + offset) for px, py in pts]
        pygame.draw.polygon(edge_s, (60, 200, 220, 140), edge_pts, 3)
        surface.blit(edge_s, (sx - offset, sy - offset))
        # Orbiting dots
        for i in range(4):
            oa = rot * 1.5 + i * math.pi / 2
            od = half + 8
            ox = sx + int(math.cos(oa) * od)
            oy = sy + int(math.sin(oa) * od)
            pygame.draw.circle(surface, (80, 220, 240), (ox, oy), 3)
        # Core
        core_pulse = int(6 + 2 * math.sin(now * 0.005))
        pygame.draw.circle(surface, (60, 200, 220), (sx, sy), core_pulse)
        pygame.draw.circle(surface, (140, 240, 255), (sx, sy), max(2, core_pulse - 3))
        # Gun flash
        if now - self.gun_flash_timer < 150:
            fx = sx + int(self.face_x * half)
            fy = sy + int(self.face_y * half)
            pygame.draw.circle(surface, (60, 220, 255), (fx, fy), 7)

    # ═══════════════════════════════════════════ NULL SERPENT drawing
    def _draw_null_serpent(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2

        # Body segments following a wave path
        segments = 6
        seg_size = 7
        for i in range(segments - 1, -1, -1):
            t = i / segments
            wave = math.sin(now * 0.006 + i * 1.2 + self.anim_offset) * 8
            seg_x = sx - int(self.face_x * i * 10) + int(-self.face_y * wave)
            seg_y = sy - int(self.face_y * i * 10) + int(self.face_x * wave)
            seg_r = seg_size - (i * 0.5) if i > 0 else seg_size + 2
            # Dark purple/black body
            body_c = (60, 30, 90) if not is_hit else (255, 255, 255)
            pygame.draw.circle(surface, body_c, (int(seg_x), int(seg_y)), int(seg_r))
            # Glowing node between segments
            if i > 0 and i < segments - 1:
                pygame.draw.circle(surface, (140, 80, 200), (int(seg_x), int(seg_y)), 2)

        # Head (slightly larger, brightest)
        head_color = (80, 40, 120) if not is_hit else (255, 255, 255)
        pygame.draw.circle(surface, head_color, (sx, sy), seg_size + 2)
        # Eyes
        ex1 = sx + int(self.face_x * 3 - self.face_y * 3)
        ey1 = sy + int(self.face_y * 3 + self.face_x * 3)
        ex2 = sx + int(self.face_x * 3 + self.face_y * 3)
        ey2 = sy + int(self.face_y * 3 - self.face_x * 3)
        eye_c = (180, 120, 255) if not is_hit else (255, 255, 200)
        pygame.draw.circle(surface, eye_c, (ex1, ey1), 2)
        pygame.draw.circle(surface, eye_c, (ex2, ey2), 2)

    # ═══════════════════════════════════════════ ARCHITECT drawing (Zone 3 mini boss)
    def _draw_architect(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        rot = now * 0.0015

        # Crystalline geometric body — multiple overlapping shapes
        # Outer octagon
        pts = []
        for i in range(8):
            angle = rot + i * math.pi / 4
            r = half - 4 + math.sin(now * 0.004 + i) * 3
            pts.append((sx + int(math.cos(angle) * r),
                        sy + int(math.sin(angle) * r)))
        body_color = (40, 50, 70) if not is_hit else (255, 255, 255)
        pygame.draw.polygon(surface, body_color, pts)
        # Cyan/magenta shifting edge
        color_shift = math.sin(now * 0.003) * 0.5 + 0.5
        r = int(60 + 140 * color_shift)
        g = int(180 - 80 * color_shift)
        b = int(220 + 35 * color_shift)
        edge_s = pygame.Surface((self.size + 8, self.size + 8), pygame.SRCALPHA)
        offset = (self.size + 8) // 2
        edge_pts = [(px - sx + offset, py - sy + offset) for px, py in pts]
        pygame.draw.polygon(edge_s, (r, g, b, 160), edge_pts, 3)
        surface.blit(edge_s, (sx - offset, sy - offset))

        # Inner diamond
        inner_pts = []
        for i in range(4):
            angle = -rot * 2 + i * math.pi / 2
            ir = half * 0.4
            inner_pts.append((sx + int(math.cos(angle) * ir),
                              sy + int(math.sin(angle) * ir)))
        pygame.draw.polygon(surface, (80, 200, 255), inner_pts)

        # Floating fragments
        for i in range(5):
            fa = rot * 0.8 + i * math.tau / 5
            fd = half + 12 + math.sin(now * 0.003 + i * 2) * 5
            fx = sx + int(math.cos(fa) * fd)
            fy = sy + int(math.sin(fa) * fd)
            frag_pts = [
                (fx - 3, fy), (fx, fy - 4), (fx + 3, fy), (fx, fy + 4)
            ]
            pygame.draw.polygon(surface, (100, 200, 255), frag_pts)

        # Eye
        pygame.draw.circle(surface, (200, 255, 255), (sx, sy), 6)
        pygame.draw.circle(surface, (0, 0, 0), (sx, sy), 3)

        # Gun flash
        if now - self.gun_flash_timer < 150:
            fx = sx + int(self.face_x * half)
            fy = sy + int(self.face_y * half)
            pygame.draw.circle(surface, (100, 220, 255), (fx, fy), 8)

        # ELITE label
        label = get_font("consolas", 10, True).render("ELITE", True, (100, 200, 255))
        surface.blit(label, (sx - label.get_width() // 2, sy - half - 24))

    # ═══════════════════════════════════════════ NEXUS drawing (Zone 3 final boss)
    def _draw_nexus(self, surface, sx, sy, now):
        is_hit = now - self.hit_flash < 100
        half = self.size // 2
        pulse = 0.6 + 0.4 * math.sin(now * 0.003)

        # Orbiting void fragments (draw behind)
        for i in range(6):
            oa = now * 0.002 + i * math.tau / 6
            od = half + 15 + math.sin(now * 0.003 + i) * 8
            ox = sx + int(math.cos(oa) * od)
            oy = sy + int(math.sin(oa) * od)
            frag_size = 6 + int(math.sin(now * 0.005 + i * 2) * 2)
            frag_color = (80, 40, 120) if not is_hit else (200, 200, 200)
            pygame.draw.circle(surface, frag_color, (ox, oy), frag_size)
            # Trail
            ts = pygame.Surface((frag_size * 2, frag_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(ts, (120, 60, 180, 60), (frag_size, frag_size), frag_size)
            surface.blit(ts, (ox - frag_size, oy - frag_size))

        # Outer ring
        ring_s = pygame.Surface((self.size + 20, self.size + 20), pygame.SRCALPHA)
        rc = (self.size + 20) // 2
        ring_color_a = int(80 + 60 * pulse)
        pygame.draw.circle(ring_s, (100, 50, 180, ring_color_a), (rc, rc), half + 4, 4)
        surface.blit(ring_s, (sx - rc, sy - rc))

        # Inner ring
        ring_s2 = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        rc2 = self.size // 2
        pygame.draw.circle(ring_s2, (140, 80, 220, int(100 * pulse)), (rc2, rc2), half - 10, 3)
        surface.blit(ring_s2, (sx - rc2, sy - rc2))

        # Core mass
        body_color = (50, 20, 70) if not is_hit else (255, 255, 255)
        pygame.draw.circle(surface, body_color, (sx, sy), half - 14)
        # Pulsing inner glow
        glow_r = int((half - 18) * pulse)
        if glow_r > 0:
            gs = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (160, 100, 255, int(120 * pulse)), (glow_r, glow_r), glow_r)
            surface.blit(gs, (sx - glow_r, sy - glow_r))

        # Central eye
        eye_r = 10 + int(4 * pulse)
        pygame.draw.circle(surface, (200, 120, 255), (sx, sy), eye_r)
        pygame.draw.circle(surface, (255, 200, 255), (sx, sy), max(2, eye_r - 4))
        pygame.draw.circle(surface, (0, 0, 0), (sx, sy), max(1, eye_r - 7))

        # Reality distortion lines
        for i in range(4):
            la = now * 0.001 + i * math.pi / 2
            lx = sx + int(math.cos(la) * half * 1.2)
            ly = sy + int(math.sin(la) * half * 1.2)
            ds = pygame.Surface((abs(lx - sx) * 2 + 4, abs(ly - sy) * 2 + 4), pygame.SRCALPHA)
            pygame.draw.line(ds, (140, 80, 220, 60),
                             (abs(lx - sx) + 2, abs(ly - sy) + 2),
                             (abs(lx - sx) + 2 + int(math.cos(la) * 20),
                              abs(ly - sy) + 2 + int(math.sin(la) * 20)), 2)
            surface.blit(ds, (min(sx, lx) - 2, min(sy, ly) - 2))

        # Gun flash
        if now - self.gun_flash_timer < 200:
            fx = sx + int(self.face_x * half)
            fy = sy + int(self.face_y * half)
            pygame.draw.circle(surface, (180, 100, 255), (fx, fy), 12)

        # BOSS label
        label = get_font("consolas", 12, True).render("BOSS", True, (180, 100, 255))
        surface.blit(label, (sx - label.get_width() // 2, sy - half - 28))
