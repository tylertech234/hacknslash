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
        "hp": 300, "speed": 1.5, "size": 56,
        "damage": 20, "shoot_range": 350,
        "shoot_cooldown": 1000, "bullet_damage": 14,
        "xp_value": 150, "status_on_hit": "fire",
    },
    "big_boss": {
        "hp": 800, "speed": 1.2, "size": 72,
        "damage": 30, "shoot_range": 400,
        "shoot_cooldown": 700, "bullet_damage": 20,
        "xp_value": 500, "status_on_hit": "bleed",
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

        # Simple wander state
        self.wander_dx = 0.0
        self.wander_dy = 0.0
        self.wander_timer = 0

        # Hit flash
        self.hit_flash = 0

        # Animation
        self.anim_offset = random.uniform(0, math.tau)
        self.gun_flash_timer = 0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.x - self.size // 2,
            self.y - self.size // 2,
            self.size,
            self.size,
        )

    def take_damage(self, amount: int, knockback_x: float, knockback_y: float, now: int):
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

        if dist < self.aggro_range and dist > 0:
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
        else:
            if now - self.wander_timer > 2000:
                angle = random.uniform(0, math.tau)
                self.wander_dx = math.cos(angle) * effective_speed * 0.5
                self.wander_dy = math.sin(angle) * effective_speed * 0.5
                self.wander_timer = now
            self.x += self.wander_dx
            self.y += self.wander_dy

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

        if self.enemy_type == "dalek":
            self._draw_dalek(surface, sx, sy, now)
        elif self.enemy_type == "wraith":
            self._draw_wraith(surface, sx, sy, now)
        elif self.enemy_type == "mini_boss":
            self._draw_mini_boss(surface, sx, sy, now)
        elif self.enemy_type == "big_boss":
            self._draw_big_boss(surface, sx, sy, now)

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

