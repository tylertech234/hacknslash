import pygame
import math
import random
from src.settings import (
    PICKUP_SIZE, PICKUP_LIFETIME, PICKUP_BOB_SPEED,
    GREEN, YELLOW, BLUE, RED, WHITE,
)


# Upgrade types that drop on the floor (stat drops removed — only heals drop now)
UPGRADE_TYPES = [
    {"name": "Heal", "color": (50, 220, 50), "icon": "+", "effect": "heal"},
]


class Pickup:
    def __init__(self, x: float, y: float, upgrade: dict):
        self.x = x
        self.y = y
        self.upgrade = upgrade
        self.size = PICKUP_SIZE
        self.alive = True
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = PICKUP_LIFETIME

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.x - self.size // 2,
            self.y - self.size // 2,
            self.size,
            self.size,
        )

    def update(self, now: int):
        if now - self.spawn_time > self.lifetime:
            self.alive = False

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int, font: pygame.font.Font):
        if not self.alive:
            return
        now = pygame.time.get_ticks()
        bob = math.sin(now * PICKUP_BOB_SPEED) * 4
        sx = int(self.x - camera_x)
        sy = int(self.y - camera_y + bob)
        color = self.upgrade["color"]

        # Outer glow — stronger for XP orbs and coins
        effect = self.upgrade.get("effect", "")
        pulse = int(45 + 35 * math.sin(now * 0.008)) if effect in ("xp", "coin") else 30
        glow_r = self.size * 2
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color, pulse), (glow_r, glow_r), glow_r)
        surface.blit(glow_surf, (sx - glow_r, sy - glow_r))
        if effect in ("xp", "coin"):
            # Outer ring pulse
            ring_r = self.size + int(3 + 4 * math.sin(now * 0.006))
            ring_alpha = int(60 + 40 * math.sin(now * 0.006))
            ring_s = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring_s, (*color, ring_alpha), (ring_r + 2, ring_r + 2), ring_r, 2)
            surface.blit(ring_s, (sx - ring_r - 2, sy - ring_r - 2))

        # Diamond shape
        half = self.size // 2
        points = [(sx, sy - half), (sx + half, sy), (sx, sy + half), (sx - half, sy)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, WHITE, points, 2)

        # Icon letter
        label = font.render(self.upgrade["icon"], True, WHITE)
        surface.blit(label, (sx - label.get_width() // 2, sy - label.get_height() // 2))


# XP orb and Coin descriptors (color + icon + effect)
_XP_ORB = {"name": "XP", "color": (100, 255, 150), "icon": "XP", "effect": "xp"}
_COIN   = {"name": "Coin", "color": (255, 200, 50), "icon": "$", "effect": "coin"}


class PickupSystem:
    """Manages item drops and player collection."""

    def __init__(self):
        self.pickups: list[Pickup] = []
        self.font = pygame.font.SysFont("consolas", 14, bold=True)
        self.notifications: list[dict] = []  # on-screen pickup text

    def try_drop(self, x: float, y: float, drop_chance: float):
        if random.random() < drop_chance:
            upgrade = random.choice(UPGRADE_TYPES)
            self.pickups.append(Pickup(x, y, upgrade))

    def spawn_xp_orb(self, x: float, y: float, xp_amount: int):
        """Spawn a collectable XP orb at enemy death position."""
        orb = dict(_XP_ORB)
        orb["xp_amount"] = xp_amount
        p = Pickup(x + random.uniform(-20, 20), y + random.uniform(-20, 20), orb)
        p.lifetime = 12000
        self.pickups.append(p)

    def spawn_coin(self, x: float, y: float):
        """Spawn a coin pickup."""
        p = Pickup(x + random.uniform(-16, 16), y + random.uniform(-16, 16), dict(_COIN))
        p.lifetime = 18000
        self.pickups.append(p)

    def spawn_apple(self, x: float, y: float):
        """Drop a healing apple from a fruit tree."""
        apple = {"name": "Apple", "color": (220, 40, 30), "icon": "a", "effect": "apple"}
        self.pickups.append(Pickup(x, y, apple))

    def spawn_medkit(self, x: float, y: float):
        """Drop a first-aid kit from a city healing box."""
        medkit = {"name": "First Aid", "color": (255, 80, 80), "icon": "+", "effect": "medkit"}
        self.pickups.append(Pickup(x, y, medkit))

    def spawn_void_essence(self, x: float, y: float):
        """Drop void essence from an abyss bloom."""
        ve = {"name": "Void Essence", "color": (180, 100, 255), "icon": "v", "effect": "void_essence"}
        self.pickups.append(Pickup(x, y, ve))

    def update(self, now: int, player):
        magnet = "magnetic_field" in getattr(player, 'passives', [])
        for p in self.pickups:
            p.update(now)
            if p.alive:
                effect = p.upgrade.get("effect", "")
                dx = player.x - p.x
                dy = player.y - p.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    if magnet:
                        # Vacuum cleaner: all pickups in a huge radius snap toward player
                        if dist < 900:
                            pull = min(22.0, 900 / max(dist, 1))
                            p.x += (dx / dist) * pull
                            p.y += (dy / dist) * pull
                    else:
                        # Baseline attraction: ALL pickups drift toward player
                        if dist < 300:
                            pull = min(7.0, 300 / max(dist, 1))
                            p.x += (dx / dist) * pull
                            p.y += (dy / dist) * pull
            if p.alive and p.rect.colliderect(player.rect):
                self._apply_upgrade(player, p.upgrade, now)
                p.alive = False
        self.pickups = [p for p in self.pickups if p.alive]
        # Notification cleanup
        self.notifications = [n for n in self.notifications if now - n["time"] < 1500]

    def _apply_upgrade(self, player, upgrade: dict, now: int):
        effect = upgrade["effect"]
        if effect == "heal":
            player.hp = min(player.max_hp, player.hp + 60)
        elif effect == "apple":
            player.hp = min(player.max_hp, player.hp + 45)
        elif effect == "medkit":
            player.hp = min(player.max_hp, player.hp + 70)
        elif effect == "void_essence":
            player.hp = min(player.max_hp, player.hp + 50)
        elif effect == "damage":
            player.damage += 5
        elif effect == "speed":
            player.speed += 0.3
        elif effect == "range":
            player.attack_range += 8
        elif effect == "max_hp":
            player.max_hp += 15
            player.hp = min(player.max_hp, player.hp + 15)
        elif effect == "xp":
            player.gain_xp(upgrade.get("xp_amount", 5))
        elif effect == "coin":
            player.coins = getattr(player, "coins", 0) + 1
        self.notifications.append({
            "text": upgrade["name"],
            "color": upgrade["color"],
            "time": now,
        })

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        for p in self.pickups:
            p.draw(surface, camera_x, camera_y, self.font)

    def draw_notifications(self, surface: pygame.Surface):
        now = pygame.time.get_ticks()
        y = 100
        for n in self.notifications:
            elapsed = now - n["time"]
            alpha = max(0, 1.0 - elapsed / 1500)
            txt = self.font.render(f">> {n['text']} <<", True, n["color"])
            txt.set_alpha(int(alpha * 255))
            surface.blit(txt, (20, y))
            y += 22
