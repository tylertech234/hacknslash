import pygame
import math
from src.settings import (
    PLAYER_SPEED, PLAYER_MAX_HP, PLAYER_SIZE,
    PLAYER_ATTACK_DAMAGE, PLAYER_ATTACK_RANGE, PLAYER_ATTACK_COOLDOWN,
    PLAYER_DASH_SPEED, PLAYER_DASH_DURATION, PLAYER_DASH_COOLDOWN,
    XP_TO_LEVEL, XP_LEVEL_SCALE,
)
from src.systems.weapons import get_weapon, draw_weapon, DEFAULT_WEAPON
from src.systems.status_effects import StatusManager


class Player:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.size = PLAYER_SIZE
        self.speed = PLAYER_SPEED
        self.max_hp = PLAYER_MAX_HP
        self.hp = self.max_hp
        self.damage = PLAYER_ATTACK_DAMAGE
        self.attack_range = PLAYER_ATTACK_RANGE

        # Weapon
        self.weapon_name = DEFAULT_WEAPON
        self.weapon = get_weapon(self.weapon_name)
        self._apply_weapon_stats()

        # Direction the player is facing (unit vector)
        self.facing_x = 0.0
        self.facing_y = 1.0

        # Attack state
        self.attack_cooldown = PLAYER_ATTACK_COOLDOWN
        self.last_attack_time = 0
        self.is_attacking = False
        self.attack_timer = 0
        self.attack_duration = 200  # ms visual duration

        # Dash state
        self.dash_speed = PLAYER_DASH_SPEED
        self.dash_duration = PLAYER_DASH_DURATION
        self.dash_cooldown = PLAYER_DASH_COOLDOWN
        self.last_dash_time = 0
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_dx = 0.0
        self.dash_dy = 0.0

        # XP / Level
        self.xp = 0
        self.level = 1
        self.xp_to_next = XP_TO_LEVEL
        self.pending_levelup = False  # flag for game to show level-up screen

        # Invincibility frames
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 300  # ms

        # Status effects
        self.statuses = StatusManager()
        self._status_font = None  # lazy init

    def _apply_weapon_stats(self):
        self.attack_cooldown = self.weapon["cooldown"]
        self.attack_duration = self.weapon["duration"]
        self.attack_range = self.weapon["range"]

    def equip_weapon(self, weapon_key: str):
        self.weapon_name = weapon_key
        self.weapon = get_weapon(weapon_key)
        self._apply_weapon_stats()

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.x - self.size // 2,
            self.y - self.size // 2,
            self.size,
            self.size,
        )

    # ---- actions ----

    def try_attack(self, now: int) -> bool:
        if now - self.last_attack_time >= self.attack_cooldown:
            self.is_attacking = True
            self.attack_timer = now
            self.last_attack_time = now
            return True
        return False

    def try_dash(self, now: int) -> bool:
        if self.is_dashing:
            return False
        if now - self.last_dash_time >= self.dash_cooldown:
            self.is_dashing = True
            self.dash_timer = now
            self.last_dash_time = now
            self.dash_dx = self.facing_x
            self.dash_dy = self.facing_y
            self.invincible = True
            self.invincible_timer = now
            return True
        return False

    def gain_xp(self, amount: int):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(XP_TO_LEVEL * (XP_LEVEL_SCALE ** (self.level - 1)))
            self.pending_levelup = True

    def take_damage(self, amount: int, now: int):
        if self.invincible:
            return
        self.hp = max(0, self.hp - amount)
        self.invincible = True
        self.invincible_timer = now

    # ---- update ----

    def update(self, dt: float, now: int, keys, world_w: int, world_h: int):
        # Status effect ticks (damage over time)
        status_dmg = self.statuses.update(now)
        if status_dmg > 0:
            self.hp = max(0, self.hp - status_dmg)

        speed_mult = self.statuses.get_speed_mult()

        # Movement input
        dx, dy = 0.0, 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1

        # Normalize
        length = math.hypot(dx, dy)
        if length > 0:
            dx /= length
            dy /= length
            self.facing_x = dx
            self.facing_y = dy

        # Dash movement overrides normal movement
        if self.is_dashing:
            if now - self.dash_timer < self.dash_duration:
                self.x += self.dash_dx * self.dash_speed
                self.y += self.dash_dy * self.dash_speed
            else:
                self.is_dashing = False
        else:
            self.x += dx * self.speed * speed_mult
            self.y += dy * self.speed * speed_mult

        # Clamp to world bounds
        half = self.size // 2
        self.x = max(half, min(world_w - half, self.x))
        self.y = max(half, min(world_h - half, self.y))

        # Attack timer
        if self.is_attacking and now - self.attack_timer > self.attack_duration:
            self.is_attacking = False

        # Invincibility timer
        if self.invincible and now - self.invincible_timer > self.invincible_duration:
            self.invincible = False

    # ---- draw ----

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        now = pygame.time.get_ticks()

        # Blink when invincible
        if self.invincible and (now // 80) % 2 == 0:
            armor_color = (180, 200, 255)
            trim_color = (220, 240, 255)
        else:
            armor_color = (40, 55, 90)      # dark steel blue
            trim_color = (0, 180, 255)       # cyan energy trim

        half = self.size // 2

        # Dash trail — energy streaks
        if self.is_dashing:
            for i in range(4):
                t = (i + 1) * 7
                tx = sx - int(self.dash_dx * t)
                ty = sy - int(self.dash_dy * t)
                trail_surf = pygame.Surface((self.size, self.size + 6), pygame.SRCALPHA)
                a = 55 - i * 14
                pygame.draw.rect(trail_surf, (*trim_color, max(0, a)),
                                 (4, 2, self.size - 8, self.size + 2), border_radius=4)
                surface.blit(trail_surf, (tx - half, ty - half - 3))

        # ---- Cyberknight body ----

        # Armored legs (two narrow rects)
        leg_w, leg_h = 8, 12
        pygame.draw.rect(surface, (30, 40, 60), (sx - 8, sy + half - 10, leg_w, leg_h))
        pygame.draw.rect(surface, (30, 40, 60), (sx + 1, sy + half - 10, leg_w, leg_h))
        # Knee energy lines
        pygame.draw.line(surface, trim_color, (sx - 7, sy + half - 4), (sx - 1, sy + half - 4), 1)
        pygame.draw.line(surface, trim_color, (sx + 2, sy + half - 4), (sx + 8, sy + half - 4), 1)

        # Torso — trapezoidal armored core
        torso_top = sy - half + 6
        torso_bot = sy + half - 10
        torso_pts = [
            (sx - half + 6, torso_bot),
            (sx + half - 6, torso_bot),
            (sx + half - 3, torso_top),
            (sx - half + 3, torso_top),
        ]
        pygame.draw.polygon(surface, armor_color, torso_pts)
        # Chest plate highlight
        pygame.draw.polygon(surface, (armor_color[0] + 20, armor_color[1] + 20, min(255, armor_color[2] + 30)),
                            torso_pts, 2)

        # Energy core in chest (pulsing)
        pulse = int(6 + 3 * math.sin(now * 0.006))
        core_color = (0, 220, 255, 140 + int(60 * math.sin(now * 0.008)))
        core_surf = pygame.Surface((pulse * 2, pulse * 2), pygame.SRCALPHA)
        pygame.draw.circle(core_surf, core_color, (pulse, pulse), pulse)
        surface.blit(core_surf, (sx - pulse, sy - 6 - pulse))
        # Core bright center
        pygame.draw.circle(surface, (200, 255, 255), (sx, sy - 6), 3)

        # Energy trim lines on torso
        pygame.draw.line(surface, trim_color, (sx - half + 5, torso_bot - 1), (sx - half + 5, torso_top + 2), 1)
        pygame.draw.line(surface, trim_color, (sx + half - 5, torso_bot - 1), (sx + half - 5, torso_top + 2), 1)
        pygame.draw.line(surface, trim_color, (sx - 6, torso_top + 6), (sx + 6, torso_top + 6), 1)

        # Shoulder pauldrons
        shldr_w, shldr_h = 12, 8
        # Left
        pygame.draw.ellipse(surface, (50, 65, 100),
                            (sx - half - 2, torso_top - 2, shldr_w, shldr_h))
        pygame.draw.ellipse(surface, trim_color,
                            (sx - half - 2, torso_top - 2, shldr_w, shldr_h), 1)
        # Right
        pygame.draw.ellipse(surface, (50, 65, 100),
                            (sx + half - shldr_w + 2, torso_top - 2, shldr_w, shldr_h))
        pygame.draw.ellipse(surface, trim_color,
                            (sx + half - shldr_w + 2, torso_top - 2, shldr_w, shldr_h), 1)

        # Helmet
        head_y = sy - half - 2
        # Helmet base
        pygame.draw.circle(surface, armor_color, (sx, head_y), 10)
        pygame.draw.circle(surface, (50, 65, 100), (sx, head_y), 10, 2)
        # Visor (T-shape, glowing)
        visor_glow = int(180 + 60 * math.sin(now * 0.005))
        visor_color = (0, min(255, visor_glow), 255)
        pygame.draw.line(surface, visor_color, (sx - 6, head_y - 1), (sx + 6, head_y - 1), 2)
        pygame.draw.line(surface, visor_color, (sx, head_y - 1), (sx, head_y + 4), 2)
        # Helmet crest
        pygame.draw.line(surface, trim_color, (sx, head_y - 10), (sx, head_y - 5), 2)

        # ---- Weapon (delegated to weapons module) ----
        draw_weapon(surface, sx, sy,
                    self.facing_x, self.facing_y,
                    self.is_attacking, self.attack_timer,
                    self.weapon, self.attack_range)

        # Status effect particles
        self.statuses.draw_particles(surface, sx, sy, self.size)
        # Status icons above head
        if self.statuses.effects:
            if self._status_font is None:
                self._status_font = pygame.font.SysFont("consolas", 12, bold=True)
            self.statuses.draw_icons(surface, sx - 12, sy - half - 24, self._status_font)

    def get_attack_rect(self) -> pygame.Rect:
        """Return the hitbox of the current attack swing."""
        cx = self.x + self.facing_x * self.attack_range * 0.6
        cy = self.y + self.facing_y * self.attack_range * 0.6
        # Scale hitbox with weapon sweep
        sweep_deg = self.weapon.get("sweep_deg", 120)
        r = int(28 * (sweep_deg / 120))
        r = max(20, min(45, r))
        return pygame.Rect(cx - r, cy - r, r * 2, r * 2)
