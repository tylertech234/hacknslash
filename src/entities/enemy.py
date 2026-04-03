import pygame
import math
import random
from src.settings import (
    ENEMY_SPEED, ENEMY_HP, ENEMY_SIZE, ENEMY_COLOR,
    ENEMY_DAMAGE, ENEMY_ATTACK_COOLDOWN,
    ENEMY_AGGRO_RANGE, ENEMY_ATTACK_RANGE,
    ENEMY_SHOOT_RANGE, ENEMY_SHOOT_COOLDOWN, ENEMY_BULLET_DAMAGE,
    ENEMY_BODY_COLOR, ENEMY_DOME_COLOR, ENEMY_EYE_COLOR, ENEMY_SKIRT_COLOR,
)
from src.systems.status_effects import StatusManager

# ── Enemy type presets ──
ENEMY_TYPES = {
    "dalek": {
        "hp": ENEMY_HP, "speed": ENEMY_SPEED, "size": ENEMY_SIZE,
        "damage": ENEMY_DAMAGE, "shoot_range": ENEMY_SHOOT_RANGE,
        "shoot_cooldown": ENEMY_SHOOT_COOLDOWN, "bullet_damage": ENEMY_BULLET_DAMAGE,
        "xp_value": 25, "status_on_hit": None,
    },
    "wraith": {
        "hp": 45, "speed": 3.2, "size": 32,
        "damage": 14, "shoot_range": 0,  # melee only
        "shoot_cooldown": 9999, "bullet_damage": 0,
        "xp_value": 35, "status_on_hit": "poison",
    },
    "mini_boss": {
        "hp": 800, "speed": 1.5, "size": 56,
        "damage": 25, "shoot_range": 350,
        "shoot_cooldown": 900, "bullet_damage": 16,
        "xp_value": 200, "status_on_hit": "fire",
    },
    "big_boss": {
        "hp": 2500, "speed": 1.2, "size": 72,
        "damage": 40, "shoot_range": 400,
        "shoot_cooldown": 600, "bullet_damage": 25,
        "xp_value": 800, "status_on_hit": "bleed",
    },
    "charger": {
        "hp": 55, "speed": 2.5, "size": 28,
        "damage": 18, "shoot_range": 0,
        "shoot_cooldown": 9999, "bullet_damage": 0,
        "xp_value": 40, "status_on_hit": None,
    },
    "shielder": {
        "hp": 120, "speed": 1.6, "size": 38,
        "damage": 12, "shoot_range": 0,
        "shoot_cooldown": 9999, "bullet_damage": 0,
        "xp_value": 50, "status_on_hit": "slow",
    },
    "spitter": {
        "hp": 40, "speed": 2.0, "size": 30,
        "damage": 8, "shoot_range": 280,
        "shoot_cooldown": 1200, "bullet_damage": 10,
        "xp_value": 35, "status_on_hit": "poison",
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
        self.aggro_range = ENEMY_AGGRO_RANGE + (20 if enemy_type in ("mini_boss", "big_boss") else 0)
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

        # Facing direction toward player
        self.face_x = 0.0
        self.face_y = 1.0

        # Knockback
        self.kb_dx = 0.0
        self.kb_dy = 0.0
        self.kb_timer = 0
        self.kb_duration = 150 if enemy_type not in ("mini_boss", "big_boss") else 60

        # Charger burst state
        self._charge_cooldown = 2500
        self._charge_duration = 400
        self._last_charge = 0
        self._charging = False
        self._charge_dx = 0.0
        self._charge_dy = 0.0

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
        self.spawn_time = 0  # set by game when spawned
        self.spawn_duration = 400  # ms to scale in

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.x - self.size // 2,
            self.y - self.size // 2,
            self.size,
            self.size,
        )

    def take_damage(self, amount: int, knockback_x: float, knockback_y: float, now: int):
        # Shielder: frontal shield reduces damage by 70%
        if self.enemy_type == "shielder" and knockback_x != 0 or knockback_y != 0:
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
            kb_str = 8 if self.enemy_type not in ("mini_boss", "big_boss") else 3
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
        elif self.enemy_type == "mini_boss":
            self._draw_mini_boss(surface, sx, sy, now)
        elif self.enemy_type == "big_boss":
            self._draw_big_boss(surface, sx, sy, now)
        elif self.enemy_type == "charger":
            self._draw_charger(surface, sx, sy, now)
        elif self.enemy_type == "shielder":
            self._draw_shielder(surface, sx, sy, now)
        elif self.enemy_type == "spitter":
            self._draw_spitter(surface, sx, sy, now)

        # Status effect particles
        self.statuses.draw_particles(surface, sx, sy, self.size)

        # HP bar
        bar_w = self.size
        bar_h = 5 if self.enemy_type not in ("mini_boss", "big_boss") else 8
        bar_x = sx - bar_w // 2
        bar_y = sy - self.size // 2 - 12
        ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(surface, (80, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        bar_color = (220, 20, 20)
        if self.enemy_type == "mini_boss":
            bar_color = (255, 160, 0)
        elif self.enemy_type == "big_boss":
            bar_color = (255, 50, 50)
        pygame.draw.rect(surface, bar_color, (bar_x, bar_y, int(bar_w * ratio), bar_h))
        if self.enemy_type in ("mini_boss", "big_boss"):
            pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 1)

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
        font = pygame.font.SysFont("consolas", 10, bold=True)
        label = font.render("ELITE", True, (255, 200, 50))
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
        font = pygame.font.SysFont("consolas", 12, bold=True)
        label = font.render("BOSS", True, (255, 60, 60))
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
