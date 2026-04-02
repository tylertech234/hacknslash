import pygame
import math
import random
from src.settings import (
    PICKUP_SIZE, PICKUP_LIFETIME, PICKUP_BOB_SPEED,
    GREEN, YELLOW, BLUE, RED, WHITE,
)


# Upgrade types and their stat effects
UPGRADE_TYPES = [
    {"name": "Heal",        "color": (50, 220, 50),   "icon": "+",  "effect": "heal"},
    {"name": "Damage Up",   "color": (255, 80, 60),   "icon": "D",  "effect": "damage"},
    {"name": "Speed Up",    "color": (80, 180, 255),   "icon": "S",  "effect": "speed"},
    {"name": "Range Up",    "color": (255, 200, 50),   "icon": "R",  "effect": "range"},
    {"name": "Max HP Up",   "color": (220, 50, 220),   "icon": "H",  "effect": "max_hp"},
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

        # Outer glow
        glow_surf = pygame.Surface((self.size * 3, self.size * 3), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color, 40), (self.size * 3 // 2, self.size * 3 // 2), self.size)
        surface.blit(glow_surf, (sx - self.size * 3 // 2, sy - self.size * 3 // 2))

        # Diamond shape
        half = self.size // 2
        points = [(sx, sy - half), (sx + half, sy), (sx, sy + half), (sx - half, sy)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, WHITE, points, 2)

        # Icon letter
        label = font.render(self.upgrade["icon"], True, WHITE)
        surface.blit(label, (sx - label.get_width() // 2, sy - label.get_height() // 2))


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

    def update(self, now: int, player):
        for p in self.pickups:
            p.update(now)
            if p.alive and p.rect.colliderect(player.rect):
                self._apply_upgrade(player, p.upgrade, now)
                p.alive = False
        self.pickups = [p for p in self.pickups if p.alive]
        # Notification cleanup
        self.notifications = [n for n in self.notifications if now - n["time"] < 1500]

    def _apply_upgrade(self, player, upgrade: dict, now: int):
        effect = upgrade["effect"]
        if effect == "heal":
            player.hp = min(player.max_hp, player.hp + 30)
        elif effect == "damage":
            player.damage += 5
        elif effect == "speed":
            player.speed += 0.3
        elif effect == "range":
            player.attack_range += 8
        elif effect == "max_hp":
            player.max_hp += 15
            player.hp = min(player.max_hp, player.hp + 15)
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
