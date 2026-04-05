import pygame
import math
import random
from src.settings import (
    PLAYER_SPEED, PLAYER_MAX_HP, PLAYER_SIZE,
    PLAYER_ATTACK_DAMAGE, PLAYER_ATTACK_RANGE, PLAYER_ATTACK_COOLDOWN,
    PLAYER_DASH_SPEED, PLAYER_DASH_DURATION, PLAYER_DASH_COOLDOWN,
    XP_TO_LEVEL, XP_LEVEL_SCALE,
    PLAYER_MAX_SPEED, PLAYER_MAX_RANGE,
)
from src.systems.weapons import get_weapon, draw_weapon, DEFAULT_WEAPON, CHARACTER_CLASSES
from src.systems.status_effects import StatusManager


class Player:
    def __init__(self, x: float, y: float, char_class: str = "knight"):
        self.x = x
        self.y = y
        self.char_class = char_class
        cls = CHARACTER_CLASSES.get(char_class, CHARACTER_CLASSES["knight"])

        self.size = PLAYER_SIZE
        self.speed = PLAYER_SPEED + cls["speed_bonus"]
        self.max_hp = PLAYER_MAX_HP + cls["hp_bonus"]
        self.hp = self.max_hp
        self.damage = PLAYER_ATTACK_DAMAGE + cls["damage_bonus"]
        self.attack_range = PLAYER_ATTACK_RANGE
        self.knockback_bonus = cls.get("knockback_bonus", 1.0)

        # Weapon — from class starting weapon
        self.weapon_name = cls["start_weapon"]
        self.weapon = get_weapon(self.weapon_name)
        # Stat bonuses accumulated from upgrades — persist across weapon swaps
        self._range_bonus: int = 0
        self._cooldown_bonus: int = 0
        self._apply_weapon_stats()
        # Arsenal — all weapons the player has collected this run
        self.arsenal: list[str] = [self.weapon_name]

        # Passives
        self.passives = list(cls["passives"])

        # Upgrade tier tracking: {upgrade_name: tier} (1 = first take, max 3)
        self.upgrade_tiers: dict[str, int] = {}

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
        self.dash_charges_max = 1
        self._dash_charges_remaining = 1
        self.dash_dx = 0.0
        self.dash_dy = 0.0
        self.move_dx = 0.0   # last WASD direction (for dash)
        self.move_dy = -1.0  # default: up

        # XP / Level
        self.xp = 0
        self.level = 1
        self.xp_to_next = XP_TO_LEVEL
        self.pending_levelup = False  # flag for game to show level-up screen

        # Run currency
        self.coins = 0

        # Super / Energy system — fills on kills, used for class super skill
        self.energy: int = 0
        self.max_energy: int = 100
        # Invincibility frames
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 300  # ms

        # Status effects
        self.statuses = StatusManager()
        self._status_font = None  # lazy init

        # Walking state
        self.moving = False
        self.walk_cycle = 0.0

        # Passive tracking
        self._adrenaline_until = 0
        self._shield_matrix_last = -10000  # ready immediately
        self.legacy_dr = 0.0  # legacy damage reduction bonus

        # Vision debuff (from Nexus boss)
        self.vision_debuff_until = 0

        # Insanity (from Nexus null_burst) — stores end time; control is randomised
        self.insanity_until = 0
        self._insane_dir_change = 0   # timestamp of last forced direction change
        self._insane_dx = 0.0
        self._insane_dy = 1.0

    def _apply_weapon_stats(self):
        """Reset weapon stats from the equipped weapon, then restore accumulated bonuses."""
        self.attack_cooldown = max(80, self.weapon["cooldown"] - self._cooldown_bonus)
        self.attack_duration = self.weapon["duration"]
        self.attack_range = self.weapon["range"] + self._range_bonus

    def equip_weapon(self, weapon_key: str):
        self.weapon_name = weapon_key
        self.weapon = get_weapon(weapon_key)
        if weapon_key not in self.arsenal:
            self.arsenal.append(weapon_key)
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
        if self._dash_charges_remaining > 0:
            self.is_dashing = True
            self.dash_timer = now
            self._dash_charges_remaining -= 1
            # Start the cooldown clock only once all charges are spent
            if self._dash_charges_remaining == 0:
                self.last_dash_time = now
            # Dash in movement (WASD) direction, not mouse facing direction
            self.dash_dx = self.move_dx
            self.dash_dy = self.move_dy
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

    @property
    def damage_multiplier(self) -> float:
        """Extra damage multiplier from passives (e.g. berserker)."""
        mult = 1.0
        if "berserker" in self.passives and self.hp < self.max_hp * 0.3:
            mult *= 1.5
        return mult

    def take_damage(self, amount: int, now: int):
        if self.invincible:
            return
        # Passive: shield_matrix — absorb one hit every 10s
        if "shield_matrix" in self.passives and now - self._shield_matrix_last >= 10000:
            self._shield_matrix_last = now
            return
        # Passive: evasion — 20% dodge chance
        if "evasion" in self.passives and random.random() < 0.20:
            return  # dodged!
        # Passive: armor_plating — 15% damage reduction
        if "armor_plating" in self.passives:
            amount = max(1, int(amount * 0.85))
        # Legacy: permanent damage reduction
        if self.legacy_dr > 0:
            amount = max(1, int(amount * (1.0 - self.legacy_dr)))
        # Global incoming damage multiplier — hits land harder for more exciting play
        amount = int(amount * 1.45)
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
        # Passive: adrenaline — +30% speed for 3s after kill
        if "adrenaline" in self.passives and now < self._adrenaline_until:
            speed_mult *= 1.3

        # ── Insanity: override player input with random lurching movement ──
        if now < self.insanity_until:
            # Change forced direction every 300-450 ms for erratic feel
            if now - self._insane_dir_change > 350:
                angle = random.uniform(0, math.tau)
                self._insane_dx = math.cos(angle)
                self._insane_dy = math.sin(angle)
                self._insane_dir_change = now
            dx, dy = self._insane_dx, self._insane_dy
            self.moving = True
            self.move_dx = dx
            self.move_dy = dy
            self.walk_cycle += dt * 0.012
        else:
            # Normal movement input
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
            self.moving = length > 0
            if length > 0:
                dx /= length
                dy /= length
                self.move_dx = dx   # remember last movement direction for dash
                self.move_dy = dy
                self.walk_cycle += dt * 0.012
            else:
                self.walk_cycle = 0.0

        # Dash movement overrides normal movement
        if self.is_dashing:
            if now - self.dash_timer < self.dash_duration:
                self.x += self.dash_dx * self.dash_speed
                self.y += self.dash_dy * self.dash_speed
            else:
                self.is_dashing = False
        else:
            self.x += dx * min(self.speed, PLAYER_MAX_SPEED) * speed_mult
            self.y += dy * min(self.speed, PLAYER_MAX_SPEED) * speed_mult

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

        # Refill dash charges after cooldown
        if (self._dash_charges_remaining < self.dash_charges_max
                and now - self.last_dash_time >= self.dash_cooldown):
            self._dash_charges_remaining = self.dash_charges_max

    # ---- draw ----

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        now = pygame.time.get_ticks()

        # Walking bob
        bob = 0
        if self.moving and not self.is_dashing:
            bob = int(math.sin(self.walk_cycle * 8) * 3)
        sy += bob

        # Blink when invincible
        if self.invincible and (now // 80) % 2 == 0:
            armor_color = (180, 200, 255)
            trim_color = (220, 240, 255)
        else:
            armor_color = (40, 55, 90)      # dark steel blue
            trim_color = (0, 180, 255)       # cyan energy trim

        half = self.size // 2

        # Dash trail — energy streaks (reuse single surface)
        if self.is_dashing:
            ts = self.size
            trail_surf = pygame.Surface((ts, ts + 6), pygame.SRCALPHA)
            for i in range(4):
                t = (i + 1) * 7
                tx = sx - int(self.dash_dx * t)
                ty = sy - int(self.dash_dy * t)
                trail_surf.fill((0, 0, 0, 0))
                a = 55 - i * 14
                pygame.draw.rect(trail_surf, (*trim_color, max(0, a)),
                                 (4, 2, ts - 8, ts + 2), border_radius=4)
                surface.blit(trail_surf, (tx - half, ty - half - 3))

        # ---- Cyberknight body ----
        if self.char_class == "knight":
            self._draw_knight(surface, sx, sy, now, armor_color, trim_color, half)
        elif self.char_class == "archer":
            self._draw_archer(surface, sx, sy, now, half)
        elif self.char_class == "jester":
            self._draw_jester(surface, sx, sy, now, half)

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

    def _draw_knight(self, surface, sx, sy, now, armor_color, trim_color, half):
        # Armored legs
        leg_w, leg_h = 8, 12
        pygame.draw.rect(surface, (30, 40, 60), (sx - 8, sy + half - 10, leg_w, leg_h))
        pygame.draw.rect(surface, (30, 40, 60), (sx + 1, sy + half - 10, leg_w, leg_h))
        pygame.draw.line(surface, trim_color, (sx - 7, sy + half - 4), (sx - 1, sy + half - 4), 1)
        pygame.draw.line(surface, trim_color, (sx + 2, sy + half - 4), (sx + 8, sy + half - 4), 1)

        # Torso
        torso_top = sy - half + 6
        torso_bot = sy + half - 10
        torso_pts = [
            (sx - half + 6, torso_bot), (sx + half - 6, torso_bot),
            (sx + half - 3, torso_top), (sx - half + 3, torso_top),
        ]
        pygame.draw.polygon(surface, armor_color, torso_pts)
        pygame.draw.polygon(surface, (armor_color[0] + 20, armor_color[1] + 20, min(255, armor_color[2] + 30)),
                            torso_pts, 2)

        # Energy core
        pulse = int(6 + 3 * math.sin(now * 0.006))
        core_color = (0, 220, 255, 140 + int(60 * math.sin(now * 0.008)))
        core_surf = pygame.Surface((pulse * 2, pulse * 2), pygame.SRCALPHA)
        pygame.draw.circle(core_surf, core_color, (pulse, pulse), pulse)
        surface.blit(core_surf, (sx - pulse, sy - 6 - pulse))
        pygame.draw.circle(surface, (200, 255, 255), (sx, sy - 6), 3)

        # Trim lines
        pygame.draw.line(surface, trim_color, (sx - half + 5, torso_bot - 1), (sx - half + 5, torso_top + 2), 1)
        pygame.draw.line(surface, trim_color, (sx + half - 5, torso_bot - 1), (sx + half - 5, torso_top + 2), 1)
        pygame.draw.line(surface, trim_color, (sx - 6, torso_top + 6), (sx + 6, torso_top + 6), 1)

        # Shoulder pauldrons
        shldr_w, shldr_h = 12, 8
        pygame.draw.ellipse(surface, (50, 65, 100), (sx - half - 2, torso_top - 2, shldr_w, shldr_h))
        pygame.draw.ellipse(surface, trim_color, (sx - half - 2, torso_top - 2, shldr_w, shldr_h), 1)
        pygame.draw.ellipse(surface, (50, 65, 100), (sx + half - shldr_w + 2, torso_top - 2, shldr_w, shldr_h))
        pygame.draw.ellipse(surface, trim_color, (sx + half - shldr_w + 2, torso_top - 2, shldr_w, shldr_h), 1)

        # Helmet
        head_y = sy - half - 2
        pygame.draw.circle(surface, armor_color, (sx, head_y), 10)
        pygame.draw.circle(surface, (50, 65, 100), (sx, head_y), 10, 2)
        visor_glow = int(180 + 60 * math.sin(now * 0.005))
        visor_color = (0, min(255, visor_glow), 255)
        pygame.draw.line(surface, visor_color, (sx - 6, head_y - 1), (sx + 6, head_y - 1), 2)
        pygame.draw.line(surface, visor_color, (sx, head_y - 1), (sx, head_y + 4), 2)
        pygame.draw.line(surface, trim_color, (sx, head_y - 10), (sx, head_y - 5), 2)

    def _draw_archer(self, surface, sx, sy, now, half):
        inv = self.invincible and (now // 80) % 2 == 0
        body_color = (180, 255, 200) if inv else (30, 60, 50)
        trim = (220, 255, 220) if inv else (0, 255, 150)

        # Slim legs
        pygame.draw.rect(surface, (20, 50, 40), (sx - 5, sy + half - 10, 3, 10))
        pygame.draw.rect(surface, (20, 50, 40), (sx + 3, sy + half - 10, 3, 10))

        # Sleek torso
        torso_top = sy - half + 6
        torso_bot = sy + half - 10
        pygame.draw.polygon(surface, body_color, [
            (sx - half + 8, torso_bot), (sx + half - 8, torso_bot),
            (sx + half - 5, torso_top), (sx - half + 5, torso_top)])
        # Targeting reticle on chest
        r = int(4 + 2 * math.sin(now * 0.005))
        pygame.draw.circle(surface, trim, (sx, sy - 2), r, 1)
        pygame.draw.circle(surface, trim, (sx, sy - 2), 1)

        # Light shoulder guards
        pygame.draw.ellipse(surface, (40, 70, 55), (sx - half, torso_top - 1, 8, 6))
        pygame.draw.ellipse(surface, (40, 70, 55), (sx + half - 8, torso_top - 1, 8, 6))

        # Hooded head
        head_y = sy - half - 2
        pygame.draw.circle(surface, body_color, (sx, head_y), 8)
        pygame.draw.polygon(surface, (25, 55, 45), [
            (sx - 8, head_y + 2), (sx + 8, head_y + 2), (sx, head_y - 12)])
        # Glowing eyes
        eye_glow = int(200 + 55 * math.sin(now * 0.006))
        pygame.draw.circle(surface, (0, min(255, eye_glow), 100), (sx - 3, head_y), 2)
        pygame.draw.circle(surface, (0, min(255, eye_glow), 100), (sx + 3, head_y), 2)

    def _draw_jester(self, surface, sx, sy, now, half):
        inv = self.invincible and (now // 80) % 2 == 0
        left_color = (255, 200, 255) if inv else (200, 50, 200)
        right_color = (255, 200, 255) if inv else (80, 30, 80)
        trim = (255, 255, 100) if inv else (255, 220, 0)

        # ---- Rolling ball under the jester ----
        ball_r = 10
        ball_cx = sx
        ball_cy = sy + half + ball_r - 4
        # Ball rolls in movement direction
        ball_spin = now * 0.008 + self.walk_cycle * 3
        pygame.draw.circle(surface, (60, 20, 100), (ball_cx, ball_cy), ball_r)
        pygame.draw.circle(surface, (100, 40, 160), (ball_cx, ball_cy), ball_r, 2)
        # Rolling pattern lines on the ball
        for i in range(3):
            angle = ball_spin + i * (math.tau / 3)
            lx = ball_cx + int(math.cos(angle) * ball_r * 0.7)
            ly = ball_cy + int(math.sin(angle) * ball_r * 0.5)
            pygame.draw.circle(surface, trim, (lx, ly), 2)
        # Highlight
        pygame.draw.circle(surface, (180, 120, 255), (ball_cx - 3, ball_cy - 3), 3)

        # ---- Legs running on top of ball ----
        leg_cycle = math.sin(now * 0.012) * 6  # legs pumping
        # Left leg
        l_foot_x = sx - 4 + int(leg_cycle)
        l_foot_y = sy + half - 2
        pygame.draw.line(surface, left_color, (sx - 3, sy + half - 10), (l_foot_x, l_foot_y), 3)
        # Right leg (opposite phase)
        r_foot_x = sx + 4 - int(leg_cycle)
        r_foot_y = sy + half - 2
        pygame.draw.line(surface, right_color, (sx + 3, sy + half - 10), (r_foot_x, r_foot_y), 3)
        # Curled shoes
        pygame.draw.circle(surface, trim, (l_foot_x, l_foot_y + 1), 2)
        pygame.draw.circle(surface, trim, (r_foot_x, r_foot_y + 1), 2)

        # Two-tone torso
        torso_top = sy - half + 6
        torso_bot = sy + half - 10
        pygame.draw.polygon(surface, right_color, [
            (sx, torso_bot), (sx + half - 4, torso_bot),
            (sx + half - 2, torso_top), (sx, torso_top)])
        pygame.draw.polygon(surface, left_color, [
            (sx, torso_bot), (sx - half + 4, torso_bot),
            (sx - half + 2, torso_top), (sx, torso_top)])

        # Diamond pattern on chest
        for dy_off in range(-4, 8, 8):
            pygame.draw.polygon(surface, trim, [
                (sx, sy + dy_off - 4), (sx + 4, sy + dy_off),
                (sx, sy + dy_off + 4), (sx - 4, sy + dy_off)], 1)

        # Ruffled collar
        for a in range(0, 360, 30):
            rx = sx + int(math.cos(math.radians(a)) * (half - 2))
            ry = torso_top + int(math.sin(math.radians(a)) * 3)
            pygame.draw.circle(surface, trim, (rx, ry), 2)

        # Head
        head_y = sy - half - 2
        pygame.draw.circle(surface, left_color, (sx, head_y), 9)
        # Grin
        pygame.draw.arc(surface, trim,
                       (sx - 5, head_y - 2, 10, 8), 3.14, 6.28, 2)
        # Mischievous eyes
        pygame.draw.circle(surface, (255, 255, 255), (sx - 3, head_y - 2), 2)
        pygame.draw.circle(surface, (255, 255, 255), (sx + 3, head_y - 2), 2)
        pygame.draw.circle(surface, (0, 0, 0), (sx - 3, head_y - 2), 1)
        pygame.draw.circle(surface, (0, 0, 0), (sx + 3, head_y - 2), 1)

        # Jester hat with bells
        for side in (-1, 1):
            bx = sx + side * 12
            by = head_y - 14 + int(math.sin(now * 0.006 + side) * 3)
            hat_color = left_color if side == -1 else right_color
            pygame.draw.line(surface, hat_color, (sx + side * 4, head_y - 8), (bx, by), 3)
            pygame.draw.circle(surface, trim, (bx, by), 3)

    def get_attack_rect(self) -> pygame.Rect:
        """Return the hitbox of the current attack swing."""
        eff_range = min(self.attack_range, PLAYER_MAX_RANGE)
        cx = self.x + self.facing_x * eff_range * 0.6
        cy = self.y + self.facing_y * eff_range * 0.6
        sweep_deg = self.weapon.get("sweep_deg", 120)
        r = int(28 * (sweep_deg / 120))
        r = max(20, min(45, r))
        return pygame.Rect(cx - r, cy - r, r * 2, r * 2)
