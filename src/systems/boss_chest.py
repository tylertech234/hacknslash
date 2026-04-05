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
    """Boss chest — slot-machine reveal of 2-5 random upgrades. No player choice."""

    # Weighted counts: 2=~23%, 3=~23%, 4=~31%, 5=~23%
    _COUNT_POOL = [2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5]

    def __init__(self):
        self.active = False
        self.rewards: list[dict] = []
        self.font_big = pygame.font.SysFont("consolas", 28, bold=True)
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 14)
        self.font_icon = pygame.font.SysFont("consolas", 22, bold=True)
        self.open_time = 0
        self.phase = "idle"  # buildup | spinning | revealing | done
        self._sound_manager = None
        self._buildup_duration = 1500
        self._particles: list[dict] = []
        self._jackpot = False
        # Spinning state
        self._spin_display: list[dict] = []
        self._spin_speed = 80            # ms per reel tick
        self._last_spin_tick = 0
        self._spin_duration = 1200
        self._spin_start = 0
        # Revealing state
        self._reveal_index = 0
        self._reveal_interval = 650
        self._last_reveal_tick = 0
        self._reveal_start = 0
        self._flash_card: int = -1

    def open_chest(self, player_class: str, player_passives: list = None,
                   sounds=None, **kwargs):
        """Start the chest-opening sequence (kwargs absorbs legacy args)."""
        self.active = True
        self.open_time = pygame.time.get_ticks()
        self._sound_manager = sounds
        self.phase = "buildup"
        self._particles = []
        self._jackpot = False
        self._reveal_index = 0
        self._flash_card = -1
        count = random.choice(self._COUNT_POOL)
        self._jackpot = (count >= 5)
        self.rewards = random.sample(CHEST_UPGRADES, min(count, len(CHEST_UPGRADES)))
        self._spin_display = random.choices(CHEST_UPGRADES, k=7)
        self._last_spin_tick = self.open_time
        if sounds:
            sounds.play("chest_open")

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.active:
            return False

        if self.phase == "buildup":
            if (event.type == pygame.KEYDOWN
                    and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e)):
                self.phase = "spinning"
                self._spin_start = pygame.time.get_ticks()
            return False

        if self.phase in ("spinning", "revealing"):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self._reveal_index = len(self.rewards)
                self.phase = "done"
                if self._jackpot:
                    self._spawn_explosion()
                    if self._sound_manager:
                        try:
                            self._sound_manager.play("confetti_boom")
                        except Exception:
                            pass
            return False

        if self.phase == "done":
            if (event.type == pygame.KEYDOWN
                    or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)):
                self.active = False
                return True
        return False

    def get_rewards(self) -> list[dict]:
        return list(self.rewards)

    def _spawn_explosion(self):
        """300+ firework particles for jackpot."""
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        COLORS = [
            (255, 220, 50), (255, 200, 20), (255, 255, 150),
            (255, 120, 50), (255, 255, 255), (200, 255, 100),
            (255, 160, 220), (120, 220, 255),
        ]
        for _ in range(150):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 14)
            self._particles.append({
                "x": float(cx), "y": float(cy),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.uniform(0.8, 2.2), "age": 0.0,
                "color": random.choice(COLORS), "size": random.randint(3, 7),
            })
        for k in range(6):
            rx = cx + (k - 2.5) * 80
            for _ in range(25):
                angle = random.uniform(-math.pi * 0.7, -math.pi * 0.3)
                speed = random.uniform(8, 18)
                self._particles.append({
                    "x": float(rx), "y": float(cy + 60),
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "life": random.uniform(1.0, 2.5), "age": 0.0,
                    "color": random.choice(COLORS), "size": random.randint(3, 6),
                })
        for _ in range(60):
            bx = random.uniform(0, SCREEN_WIDTH)
            angle = random.uniform(-math.pi * 0.85, -math.pi * 0.15)
            speed = random.uniform(10, 20)
            self._particles.append({
                "x": bx, "y": float(SCREEN_HEIGHT),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.uniform(1.2, 2.8), "age": 0.0,
                "color": random.choice(COLORS), "size": random.randint(2, 5),
            })

    def _update_particles(self, dt_s: float):
        alive = []
        for p in self._particles:
            p["age"] += dt_s
            if p["age"] < p["life"]:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 5 * dt_s
                alive.append(p)
        self._particles = alive

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return
        now = pygame.time.get_ticks()

        # Phase transitions (time-driven)
        if self.phase == "buildup" and now - self.open_time >= self._buildup_duration:
            self.phase = "spinning"
            self._spin_start = now
            self._last_spin_tick = now

        if self.phase == "spinning":
            if now - self._last_spin_tick >= self._spin_speed:
                self._spin_display = (
                    self._spin_display[1:] + [random.choice(CHEST_UPGRADES)]
                )
                self._last_spin_tick = now
                if self._sound_manager and random.random() < 0.35:
                    try:
                        self._sound_manager.play("wheel_tick")
                    except Exception:
                        pass
            if now - self._spin_start >= self._spin_duration:
                self.phase = "revealing"
                self._reveal_start = now
                self._last_reveal_tick = now

        if self.phase == "revealing":
            if (self._reveal_index < len(self.rewards)
                    and now - self._last_reveal_tick >= self._reveal_interval):
                self._flash_card = self._reveal_index
                self._reveal_index += 1
                self._last_reveal_tick = now
                if self._sound_manager:
                    try:
                        self._sound_manager.play("wheel_stop")
                    except Exception:
                        pass
            if self._reveal_index >= len(self.rewards):
                self.phase = "done"
                if self._jackpot:
                    self._spawn_explosion()
                    if self._sound_manager:
                        try:
                            self._sound_manager.play("confetti_boom")
                        except Exception:
                            pass

        self._update_particles(1 / 60)

        # Background overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        surface.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        if self.phase == "buildup":
            self._draw_buildup(surface, cx, cy, now, now - self.open_time)
        elif self.phase == "spinning":
            self._draw_spinning(surface, cx, cy, now)
        else:
            self._draw_rewards(surface, cx, cy, now)

        # Particles
        for p in self._particles:
            alpha = max(0, int(255 * (1 - p["age"] / p["life"])))
            ps = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p["color"], alpha),
                               (p["size"], p["size"]), p["size"])
            surface.blit(ps, (int(p["x"]) - p["size"], int(p["y"]) - p["size"]))

    def _draw_buildup(self, surface, cx, cy, now, elapsed):
        progress = min(1.0, elapsed / self._buildup_duration)
        glow_r = int(50 + 150 * progress)
        glow_alpha = int(30 + 70 * progress * (0.5 + 0.5 * math.sin(now * 0.01)))
        glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (255, 200, 50, glow_alpha), (glow_r, glow_r), glow_r)
        surface.blit(glow_s, (cx - glow_r, cy - glow_r))
        chest_size = int(30 + 30 * progress)
        half = chest_size // 2
        body_r = pygame.Rect(cx - half, cy - half // 2, chest_size, half + 6)
        pygame.draw.rect(surface, (120, 80, 30), body_r, border_radius=3)
        pygame.draw.rect(surface, (200, 160, 60), body_r, 2, border_radius=3)
        lid_open = int(12 * progress)
        lid_r = pygame.Rect(cx - half - 2, cy - half // 2 - 6 - lid_open, chest_size + 4, 8)
        pygame.draw.rect(surface, (160, 120, 40), lid_r, border_radius=2)
        pygame.draw.rect(surface, (200, 160, 60), lid_r, 1, border_radius=2)
        pygame.draw.circle(surface, (255, 220, 50), (cx, cy - half // 2 + 2), 4)
        if progress > 0.3:
            ray_alpha = int(100 * (progress - 0.3) / 0.7)
            for i in range(8):
                angle = now * 0.001 + i * math.pi / 4
                rx = cx + math.cos(angle) * glow_r * 0.8
                ry = cy + math.sin(angle) * glow_r * 0.8 - 20
                ls = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(ls, (255, 255, 200, ray_alpha), (3, 3), 3)
                surface.blit(ls, (int(rx) - 3, int(ry) - 3))
        title = self.font_big.render("BOSS CHEST", True, (255, 220, 50))
        surface.blit(title, (cx - title.get_width() // 2, cy - 120))
        dots = "." * (1 + (now // 400) % 3)
        hint = self.font.render(f"Opening{dots}", True, (200, 200, 200))
        surface.blit(hint, (cx - hint.get_width() // 2, cy + 80))

    def _draw_spinning(self, surface, cx, cy, now):
        """Slot-machine reel cycling display."""
        title = self.font_big.render("BOSS CHEST", True, (255, 220, 50))
        surface.blit(title, (cx - title.get_width() // 2, 60))
        row_h = 46
        reel_w = 380
        n_visible = min(5, len(self._spin_display))
        total_h = n_visible * row_h
        reel_x = cx - reel_w // 2
        reel_y = cy - total_h // 2
        reel_bg = pygame.Surface((reel_w, total_h), pygame.SRCALPHA)
        pygame.draw.rect(reel_bg, (15, 18, 25, 220), (0, 0, reel_w, total_h), border_radius=6)
        pygame.draw.rect(reel_bg, (60, 60, 80, 200), (0, 0, reel_w, total_h), 2, border_radius=6)
        surface.blit(reel_bg, (reel_x, reel_y))
        for i, item in enumerate(self._spin_display[:n_visible]):
            row_y = reel_y + i * row_h
            is_center = (i == n_visible // 2)
            col = tuple(item.get("color", (180, 180, 200)))
            if is_center:
                hl = pygame.Surface((reel_w, row_h), pygame.SRCALPHA)
                hl_a = int(40 + 20 * math.sin(now * 0.01))
                pygame.draw.rect(hl, (*col, hl_a), (0, 0, reel_w, row_h))
                surface.blit(hl, (reel_x, row_y))
            pygame.draw.circle(surface, col, (reel_x + 28, row_y + row_h // 2), 14)
            ic = self.font_icon.render(str(item.get("icon", "?")), True, (255, 255, 255))
            surface.blit(ic, (reel_x + 28 - ic.get_width() // 2,
                              row_y + row_h // 2 - ic.get_height() // 2))
            nm_col = (255, 255, 255) if is_center else (140, 140, 155)
            nm = self.font.render(item["name"], True, nm_col)
            surface.blit(nm, (reel_x + 52, row_y + row_h // 2 - nm.get_height() // 2))
        mid_row_y = reel_y + (n_visible // 2) * row_h
        pygame.draw.rect(surface, (255, 200, 50),
                         (reel_x - 3, mid_row_y, reel_w + 6, row_h), 2, border_radius=3)
        hint = self.font_small.render("Rolling...", True, (160, 160, 160))
        surface.blit(hint, (cx - hint.get_width() // 2, reel_y + total_h + 18))

    def _draw_rewards(self, surface, cx, cy, now):
        """Draw revealed reward cards with optional jackpot flash."""
        shown = min(self._reveal_index, len(self.rewards))
        if self._jackpot and self.phase == "done":
            flash = int(50 + 40 * math.sin(now * 0.007))
            fs = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 220, 50, flash))
            surface.blit(fs, (0, 0))
        count = len(self.rewards)
        title_text = "JACKPOT!" if self._jackpot else f"{count} REWARD{'S' if count > 1 else ''}!"
        title_col = (255, 255, 100) if self._jackpot else (255, 220, 50)
        title = self.font_big.render(title_text, True, title_col)
        surface.blit(title, (cx - title.get_width() // 2, 40))
        card_w, card_h = 360, 70
        total_h = shown * (card_h + 12) - 12
        start_y = cy - total_h // 2
        for i in range(shown):
            reward = self.rewards[i]
            r_col = tuple(reward.get("color", (180, 180, 180)))
            card_y = start_y + i * (card_h + 12)
            reveal_age = now - (self._reveal_start + i * self._reveal_interval)
            slide = min(1.0, max(0.0, reveal_age / 200))
            card_x = int(cx - card_w // 2 - 60 * (1 - slide))
            alpha = int(255 * slide)
            is_flash = (i == self._flash_card and now - self._last_reveal_tick < 300)
            flash_col = (255, 255, 180) if is_flash else r_col
            card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            bg_c = (50, 50, 20, min(220, alpha)) if is_flash else (30, 30, 40, min(220, alpha))
            pygame.draw.rect(card, bg_c, (0, 0, card_w, card_h), border_radius=6)
            pygame.draw.rect(card, (*flash_col, min(255, alpha)), (0, 0, card_w, card_h),
                             3 if is_flash else 1, border_radius=6)
            if is_flash:
                glow_a = int(60 + 40 * math.sin(now * 0.02))
                glow_s = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                glow_s.fill((*r_col, glow_a))
                card.blit(glow_s, (0, 0))
            icon_cx_c, icon_cy_c = 30, card_h // 2
            pygame.draw.circle(card, (*r_col, min(200, alpha)), (icon_cx_c, icon_cy_c), 18)
            icon_t = self.font_icon.render(reward["icon"], True, (255, 255, 255))
            icon_t.set_alpha(alpha)
            card.blit(icon_t, (icon_cx_c - icon_t.get_width() // 2,
                               icon_cy_c - icon_t.get_height() // 2))
            nm = self.font.render(reward["name"], True, flash_col)
            nm.set_alpha(alpha)
            card.blit(nm, (58, 12))
            effect = reward.get("effect", "")
            tag = "PASSIVE" if effect == "passive" else ("WEAPON" if effect == "weapon" else "STAT BOOST")
            tag_t = self.font_small.render(tag, True, (140, 140, 155))
            tag_t.set_alpha(alpha)
            card.blit(tag_t, (58, 38))
            surface.blit(card, (card_x, card_y))
        if self.phase == "revealing":
            hint = self.font_small.render("SPACE to skip...", True, (100, 100, 100))
        elif self.phase == "done":
            hint = self.font.render("Press any key to collect all rewards", True, (180, 180, 180))
        else:
            hint = self.font_small.render("...", True, (100, 100, 100))
        surface.blit(hint, (cx - hint.get_width() // 2, SCREEN_HEIGHT - 50))
