import pygame
import math
import random
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW
from src.systems.weapons import WEAPONS


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
    """Spin-the-wheel boss chest reward screen."""

    NUM_SEGMENTS = 8

    def __init__(self):
        self.active = False
        self.rewards: list[dict] = []
        self.selected = 0
        self.font_big = pygame.font.SysFont("consolas", 28, bold=True)
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 14)
        self.font_icon = pygame.font.SysFont("consolas", 22, bold=True)
        self.open_time = 0
        # Wheel state
        self.angle = 0.0        # current rotation in degrees
        self.spin_speed = 0.0   # degrees per tick
        self.phase = "idle"     # spinning | braking | stopped | celebrating
        self.stop_time = 0
        self._tick_sound_angle = 0.0
        self._sound_manager = None
        self._played_stop = False

    def open_chest(self, player_class: str, player_passives: list = None, sounds=None):
        """Generate 8 random upgrades and start spinning."""
        self.active = True
        self.open_time = pygame.time.get_ticks()
        self._sound_manager = sounds
        self._played_stop = False
        if sounds:
            sounds.play("chest_open")

        owned = set(player_passives or [])
        pool = []
        for u in CHEST_UPGRADES:
            if u["effect"] == "passive" and u["value"] in owned:
                continue
            pool.append(dict(u))

        # Also offer class-appropriate weapon upgrades
        class_weapons = [k for k, v in WEAPONS.items()
                        if v.get("class") == player_class]
        for wk in class_weapons:
            w = WEAPONS[wk]
            pool.append({
                "name": w["name"],
                "icon": "W",
                "color": w["blade_color"],
                "effect": "weapon",
                "value": wk,
            })

        count = self.NUM_SEGMENTS
        if len(pool) < count:
            # Duplicate to fill wheel
            while len(pool) < count:
                pool.append(random.choice(CHEST_UPGRADES))
        self.rewards = random.sample(pool, count)
        self.selected = 0
        self.angle = random.uniform(0, 360)
        self.spin_speed = random.uniform(8.0, 12.0)
        self.phase = "spinning"
        self._tick_sound_angle = self.angle

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.active:
            return False
        if event.type == pygame.KEYDOWN:
            if self.phase == "spinning":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.phase = "braking"
            elif self.phase == "celebrating":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.active = False
                    return True
        return False

    def get_rewards(self) -> list[dict]:
        if 0 <= self.selected < len(self.rewards):
            return [self.rewards[self.selected]]
        return self.rewards[:1]

    def _update_wheel(self, now):
        """Called each draw frame to update wheel physics."""
        if self.phase == "spinning":
            old_angle = self.angle
            self.angle = (self.angle + self.spin_speed) % 360
            # Tick sound when crossing segment boundary
            seg = 360 / self.NUM_SEGMENTS
            if int(old_angle / seg) != int(self.angle / seg) and self._sound_manager:
                self._sound_manager.play("wheel_tick")
            # Slow natural friction
            self.spin_speed *= 0.997
            # Auto-brake after 3 seconds
            if now - self.open_time > 3000:
                self.phase = "braking"
        elif self.phase == "braking":
            old_angle = self.angle
            self.angle = (self.angle + self.spin_speed) % 360
            seg = 360 / self.NUM_SEGMENTS
            if int(old_angle / seg) != int(self.angle / seg) and self._sound_manager:
                self._sound_manager.play("wheel_tick")
            self.spin_speed *= 0.97  # stronger friction
            if self.spin_speed < 0.15:
                self.spin_speed = 0
                self.phase = "stopped"
                self.stop_time = now
                # Determine which segment the pointer is on (top = 270 degrees)
                pointer_angle = (270 - self.angle) % 360
                seg_size = 360 / self.NUM_SEGMENTS
                self.selected = int(pointer_angle / seg_size) % self.NUM_SEGMENTS
        elif self.phase == "stopped":
            if not self._played_stop and self._sound_manager:
                self._sound_manager.play("wheel_stop")
                self._played_stop = True
            # Brief pause, then celebrate
            if now - self.stop_time > 300:
                self.phase = "celebrating"

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return
        now = pygame.time.get_ticks()
        self._update_wheel(now)

        # Darken background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        # Title
        title = self.font_big.render("BOSS CHEST OPENED!", True, (255, 220, 50))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 30))

        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2 - 10
        radius = 200
        seg_angle = 360 / self.NUM_SEGMENTS

        # Draw wheel segments
        for i, reward in enumerate(self.rewards):
            start_deg = self.angle + i * seg_angle
            end_deg = start_deg + seg_angle

            # Segment color (alternating dark/light base + reward tint)
            r_col = reward.get("color", (150, 150, 150))
            if i % 2 == 0:
                base = (max(0, r_col[0] // 3), max(0, r_col[1] // 3), max(0, r_col[2] // 3))
            else:
                base = (max(0, r_col[0] // 2), max(0, r_col[1] // 2), max(0, r_col[2] // 2))

            # Draw filled arc as polygon wedge
            points = [(cx, cy)]
            steps = 12
            for s in range(steps + 1):
                a = math.radians(start_deg + s * seg_angle / steps)
                points.append((cx + math.cos(a) * radius, cy + math.sin(a) * radius))
            if len(points) >= 3:
                pygame.draw.polygon(surface, base, points)
                pygame.draw.polygon(surface, r_col, points, 2)

            # Draw icon in the middle of the segment
            mid_angle = math.radians(start_deg + seg_angle / 2)
            icon_r = radius * 0.65
            ix = cx + math.cos(mid_angle) * icon_r
            iy = cy + math.sin(mid_angle) * icon_r
            icon_surf = self.font_icon.render(reward["icon"], True, r_col)
            surface.blit(icon_surf, (ix - icon_surf.get_width() // 2,
                                     iy - icon_surf.get_height() // 2))

        # Draw center circle
        pygame.draw.circle(surface, (30, 30, 40), (cx, cy), 30)
        pygame.draw.circle(surface, (255, 220, 50), (cx, cy), 30, 2)

        # Draw pointer (triangle at top)
        ptr_y = cy - radius - 8
        pygame.draw.polygon(surface, (255, 220, 50), [
            (cx, ptr_y + 22),
            (cx - 12, ptr_y),
            (cx + 12, ptr_y),
        ])
        pygame.draw.polygon(surface, (255, 255, 200), [
            (cx, ptr_y + 22),
            (cx - 12, ptr_y),
            (cx + 12, ptr_y),
        ], 2)

        # Phase-specific UI
        if self.phase == "spinning":
            hint = self.font.render("Press SPACE to stop!", True, (200, 200, 200))
            surface.blit(hint, (cx - hint.get_width() // 2, cy + radius + 30))
        elif self.phase == "braking":
            hint = self.font_small.render("Slowing down...", True, (150, 150, 150))
            surface.blit(hint, (cx - hint.get_width() // 2, cy + radius + 35))
        elif self.phase in ("stopped", "celebrating"):
            # Show selected reward with celebration
            reward = self.rewards[self.selected]
            r_col = reward.get("color", (255, 255, 255))

            # Pulsing glow behind reward name
            if self.phase == "celebrating":
                pulse = int(60 + 40 * math.sin(now * 0.008))
                glow = pygame.Surface((400, 60), pygame.SRCALPHA)
                glow.fill((*r_col, pulse))
                surface.blit(glow, (cx - 200, cy + radius + 20))

            # Show what was won
            won_text = self.font_big.render(f"YOU WON: {reward['name']}", True, r_col)
            surface.blit(won_text, (cx - won_text.get_width() // 2, cy + radius + 30))

            if reward["effect"] == "weapon":
                tag = "WEAPON"
            elif reward["effect"] == "passive":
                tag = "PASSIVE"
            else:
                tag = "STAT BOOST"
            tag_surf = self.font.render(tag, True, (180, 180, 180))
            surface.blit(tag_surf, (cx - tag_surf.get_width() // 2, cy + radius + 65))

            hint = self.font_small.render("Press SPACE to continue", True, (100, 100, 100))
            surface.blit(hint, (cx - hint.get_width() // 2, cy + radius + 95))
