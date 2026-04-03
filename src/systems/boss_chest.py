import pygame
import math
import random
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW
from src.systems.weapons import WEAPONS
from src.ui.tooltip import Tooltip


# Big upgrades that can come from boss chests
CHEST_UPGRADES = [
    # Stat boosts (stronger than level-up versions)
    {"name": "Overclocked Blade",  "icon": "D", "color": (255, 80, 60),   "effect": "damage",   "value": 15},
    {"name": "Extended Reach",     "icon": "R", "color": (255, 200, 50),  "effect": "range",    "value": 20},
    {"name": "Turbo Hands",        "icon": "C", "color": (180, 140, 255), "effect": "cooldown", "value": 100},
    {"name": "Reinforced Chassis", "icon": "H", "color": (220, 50, 220),  "effect": "max_hp",   "value": 60},
    {"name": "Emergency Repair",   "icon": "+", "color": (50, 220, 50),   "effect": "heal",     "value": 0},
    {"name": "Overdrive",          "icon": "S", "color": (80, 180, 255),  "effect": "speed",    "value": 1.0},
    # Powerful passive upgrades
    {"name": "Nano Regen",         "icon": "N", "color": (100, 255, 100), "effect": "passive",  "value": "nano_regen"},
    {"name": "Berserker Core",     "icon": "B", "color": (255, 60, 60),   "effect": "passive",  "value": "berserker"},
    {"name": "Shield Matrix",      "icon": "M", "color": (100, 150, 255), "effect": "passive",  "value": "shield_matrix"},
    {"name": "Vampiric Circuits",  "icon": "V", "color": (200, 0, 80),    "effect": "passive",  "value": "vampiric_strike"},
    {"name": "Chain Lightning",    "icon": "Z", "color": (100, 230, 255), "effect": "passive",  "value": "chain_lightning"},
    {"name": "Second Wind",        "icon": "L", "color": (255, 100, 100), "effect": "passive",  "value": "second_wind"},
    {"name": "Explosive Rounds",   "icon": "E", "color": (255, 150, 0),   "effect": "passive",  "value": "explosive_kills"},
]


class BossChest:
    """A glowing chest dropped by a boss, containing 1-5 upgrades."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.alive = True
        self.spawn_time = pygame.time.get_ticks()
        self.size = 28
        self.opened = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2,
                           self.size, self.size)

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        if not self.alive:
            return
        now = pygame.time.get_ticks()
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y)
        bob = math.sin(now * 0.003) * 4

        # Outer glow
        glow_r = int(20 + 6 * math.sin(now * 0.004))
        glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (255, 200, 50, 40), (glow_r, glow_r), glow_r)
        surface.blit(glow_s, (sx - glow_r, int(sy + bob) - glow_r))

        # Chest body
        half = self.size // 2
        body_rect = pygame.Rect(sx - half, int(sy + bob) - half // 2, self.size, half + 4)
        pygame.draw.rect(surface, (120, 80, 30), body_rect, border_radius=3)
        pygame.draw.rect(surface, (180, 140, 50), body_rect, 2, border_radius=3)

        # Lid
        lid_rect = pygame.Rect(sx - half - 2, int(sy + bob) - half // 2 - 6, self.size + 4, 8)
        pygame.draw.rect(surface, (160, 120, 40), lid_rect, border_radius=2)
        pygame.draw.rect(surface, (200, 160, 60), lid_rect, 1, border_radius=2)

        # Lock/gem
        pygame.draw.circle(surface, (255, 220, 50),
                          (sx, int(sy + bob) - half // 2 + 2), 4)
        pygame.draw.circle(surface, (255, 255, 200),
                          (sx, int(sy + bob) - half // 2 + 2), 2)

        # Sparkles
        for i in range(3):
            angle = now * 0.002 + i * 2.1
            sr = 16 + math.sin(now * 0.005 + i) * 4
            sparkx = sx + int(math.cos(angle) * sr)
            sparky = int(sy + bob) + int(math.sin(angle) * sr)
            ss = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(ss, (255, 255, 200, 160), (2, 2), 2)
            surface.blit(ss, (sparkx - 2, sparky - 2))


class ChestRewardScreen:
    """Dramatic chest opening — rolls 1-5 upgrades with scaling fanfare."""

    def __init__(self):
        self.active = False
        self.rewards: list[dict] = []
        self.font_big = pygame.font.SysFont("consolas", 28, bold=True)
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 14)
        self.font_icon = pygame.font.SysFont("consolas", 22, bold=True)
        self.font_huge = pygame.font.SysFont("consolas", 48, bold=True)
        self.open_time = 0
        self.phase = "idle"  # buildup | revealing | revealed
        self._sound_manager = None
        self._tooltip = Tooltip()
        self._reveal_index = 0
        self._reveal_time = 0
        self._buildup_duration = 1500  # ms of anticipation
        self._reveal_interval = 400   # ms between each reward reveal
        self._jackpot = False  # 5 items = jackpot
        self._particles: list[dict] = []
        self._player_class = "knight"

    def open_chest(self, player_class: str, player_passives: list = None, sounds=None):
        """Roll 1-5 random upgrades and start the chest opening sequence."""
        self.active = True
        self.open_time = pygame.time.get_ticks()
        self._sound_manager = sounds
        self._player_class = player_class
        if sounds:
            sounds.play("chest_open")

        owned = set(player_passives or [])
        pool = []
        for u in CHEST_UPGRADES:
            if u["effect"] == "passive" and u["value"] in owned:
                continue
            pool.append(dict(u))

        # Roll 1-5 rewards (weighted: 1=30%, 2=30%, 3=25%, 4=10%, 5=5%)
        roll = random.random()
        if roll < 0.30:
            count = 1
        elif roll < 0.60:
            count = 2
        elif roll < 0.85:
            count = 3
        elif roll < 0.95:
            count = 4
        else:
            count = 5

        self._jackpot = count >= 5
        count = min(count, len(pool))
        self.rewards = random.sample(pool, count)
        self._reveal_index = 0
        self.phase = "buildup"
        self._particles = []

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.active:
            return False
        confirm = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            confirm = True
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            confirm = True
        if confirm:
            if self.phase == "buildup":
                self.phase = "revealing"
                self._reveal_index = 0
                self._reveal_time = pygame.time.get_ticks()
            elif self.phase == "revealing":
                self._reveal_index = len(self.rewards)
                self.phase = "revealed"
                self._reveal_time = pygame.time.get_ticks()
                if self._jackpot:
                    self._spawn_explosion()
                if self._sound_manager:
                    self._sound_manager.play("wheel_stop")
            elif self.phase == "revealed":
                self.active = False
                return True
        return False

    def get_rewards(self) -> list[dict]:
        return list(self.rewards)

    def _spawn_explosion(self):
        """Spawn particles for jackpot (5-item roll)."""
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        for _ in range(80):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 10)
            self._particles.append({
                "x": float(cx), "y": float(cy),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.uniform(0.5, 1.5),
                "age": 0.0,
                "color": random.choice([
                    (255, 220, 50), (255, 180, 30), (255, 255, 150),
                    (255, 100, 50), (255, 255, 255),
                ]),
                "size": random.randint(2, 5),
            })

    def _update_particles(self, dt_s: float):
        alive = []
        for p in self._particles:
            p["age"] += dt_s
            if p["age"] < p["life"]:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 5 * dt_s  # gravity
                alive.append(p)
        self._particles = alive

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return
        now = pygame.time.get_ticks()
        elapsed = now - self.open_time

        # Update phase transitions
        if self.phase == "buildup" and elapsed >= self._buildup_duration:
            self.phase = "revealing"
            self._reveal_index = 0
            self._reveal_time = now

        if self.phase == "revealing":
            reveal_elapsed = now - self._reveal_time
            items_to_show = min(len(self.rewards),
                                reveal_elapsed // self._reveal_interval + 1)
            if items_to_show > self._reveal_index:
                self._reveal_index = items_to_show
                if self._sound_manager:
                    self._sound_manager.play("wheel_tick")
            if self._reveal_index >= len(self.rewards):
                if self.phase != "revealed":
                    self.phase = "revealed"
                    self._reveal_time = now
                    if self._jackpot:
                        self._spawn_explosion()
                    if self._sound_manager:
                        snd = "boss_roar" if self._jackpot else "wheel_stop"
                        self._sound_manager.play(snd)

        # Particle update
        self._update_particles(1 / 60)

        # Darken background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        surface.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        if self.phase == "buildup":
            self._draw_buildup(surface, cx, cy, now, elapsed)
        else:
            self._draw_rewards(surface, cx, cy, now)

        # Draw particles
        for p in self._particles:
            alpha = max(0, int(255 * (1 - p["age"] / p["life"])))
            ps = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p["color"], alpha),
                               (p["size"], p["size"]), p["size"])
            surface.blit(ps, (int(p["x"]) - p["size"], int(p["y"]) - p["size"]))

    def _draw_buildup(self, surface, cx, cy, now, elapsed):
        """Dramatic chest opening anticipation."""
        progress = min(1.0, elapsed / self._buildup_duration)

        # Pulsing glow expanding from center
        glow_r = int(50 + 150 * progress)
        glow_alpha = int(30 + 70 * progress * (0.5 + 0.5 * math.sin(now * 0.01)))
        glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (255, 200, 50, glow_alpha),
                           (glow_r, glow_r), glow_r)
        surface.blit(glow_s, (cx - glow_r, cy - glow_r))

        # Chest icon (growing)
        chest_size = int(30 + 30 * progress)
        half = chest_size // 2
        # Body
        body_r = pygame.Rect(cx - half, cy - half // 2, chest_size, half + 6)
        pygame.draw.rect(surface, (120, 80, 30), body_r, border_radius=3)
        pygame.draw.rect(surface, (200, 160, 60), body_r, 2, border_radius=3)
        # Lid opening
        lid_open = int(12 * progress)
        lid_r = pygame.Rect(cx - half - 2, cy - half // 2 - 6 - lid_open,
                            chest_size + 4, 8)
        pygame.draw.rect(surface, (160, 120, 40), lid_r, border_radius=2)
        pygame.draw.rect(surface, (200, 160, 60), lid_r, 1, border_radius=2)
        # Lock
        pygame.draw.circle(surface, (255, 220, 50),
                           (cx, cy - half // 2 + 2), 4)

        # Light rays from chest
        if progress > 0.3:
            ray_alpha = int(100 * (progress - 0.3) / 0.7)
            for i in range(8):
                angle = now * 0.001 + i * math.pi / 4
                rx = cx + math.cos(angle) * glow_r * 0.8
                ry = cy + math.sin(angle) * glow_r * 0.8 - 20
                ls = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(ls, (255, 255, 200, ray_alpha), (3, 3), 3)
                surface.blit(ls, (int(rx) - 3, int(ry) - 3))

        # Title
        title = self.font_big.render("BOSS CHEST", True, (255, 220, 50))
        surface.blit(title, (cx - title.get_width() // 2, cy - 120))

        # Suspense text
        dots = "." * (1 + (now // 400) % 3)
        hint = self.font.render(f"Opening{dots}", True, (200, 200, 200))
        surface.blit(hint, (cx - hint.get_width() // 2, cy + 80))

    def _draw_rewards(self, surface, cx, cy, now):
        """Draw revealed reward cards."""
        num_rewards = len(self.rewards)
        shown = min(self._reveal_index, num_rewards)

        # Title with reward count
        color_title = (255, 255, 100) if num_rewards >= 4 else (255, 220, 50)
        title_text = "JACKPOT!" if self._jackpot else f"{num_rewards} REWARD{'S' if num_rewards > 1 else ''}!"
        title = self.font_big.render(title_text, True, color_title)
        surface.blit(title, (cx - title.get_width() // 2, 40))

        # Jackpot flash background
        if self._jackpot and self.phase == "revealed":
            flash = int(30 * (0.5 + 0.5 * math.sin(now * 0.008)))
            fs = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 220, 50, flash))
            surface.blit(fs, (0, 0))

        # Layout cards
        card_w, card_h = 360, 70
        total_h = num_rewards * (card_h + 12) - 12
        start_y = cy - total_h // 2

        for i in range(shown):
            reward = self.rewards[i]
            r_col = reward.get("color", (180, 180, 180))
            card_y = start_y + i * (card_h + 12)

            # Card entrance slide-in
            reveal_age = now - (self._reveal_time if self.phase == "revealed"
                                else self._reveal_time + i * self._reveal_interval)
            if self.phase == "revealing":
                reveal_age = now - (self._reveal_time + i * self._reveal_interval)
            slide = min(1.0, max(0.0, reveal_age / 200))
            card_x = int(cx - card_w // 2 - 60 * (1 - slide))
            alpha = int(255 * slide)

            # Card background
            card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            bg_color = (30, 30, 40, min(220, alpha))
            pygame.draw.rect(card, bg_color, (0, 0, card_w, card_h),
                             border_radius=6)
            border_col = (*r_col, min(255, alpha))
            pygame.draw.rect(card, border_col, (0, 0, card_w, card_h),
                             2, border_radius=6)

            # Icon circle
            icon_cx, icon_cy = 35, card_h // 2
            pygame.draw.circle(card, (*r_col, min(200, alpha)),
                               (icon_cx, icon_cy), 18)
            icon_t = self.font_icon.render(reward["icon"], True, (255, 255, 255))
            icon_t.set_alpha(alpha)
            card.blit(icon_t, (icon_cx - icon_t.get_width() // 2,
                               icon_cy - icon_t.get_height() // 2))

            # Name
            name_t = self.font.render(reward["name"], True, r_col)
            name_t.set_alpha(alpha)
            card.blit(name_t, (65, 12))

            # Effect tag
            if reward["effect"] == "weapon":
                tag = "WEAPON"
            elif reward["effect"] == "passive":
                tag = "PASSIVE"
            else:
                tag = "STAT BOOST"
            tag_t = self.font_small.render(tag, True, (150, 150, 160))
            tag_t.set_alpha(alpha)
            card.blit(tag_t, (65, 38))

            surface.blit(card, (card_x, card_y))

        # Instructions
        if self.phase == "revealing":
            hint = self.font_small.render("Press SPACE to skip...",
                                          True, (120, 120, 120))
        elif self.phase == "revealed":
            hint = self.font.render("Press SPACE to continue",
                                    True, (180, 180, 180))
        else:
            hint = self.font_small.render("...", True, (100, 100, 100))
        surface.blit(hint, (cx - hint.get_width() // 2, SCREEN_HEIGHT - 50))
