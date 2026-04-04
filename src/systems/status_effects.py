import pygame
import math

# ── Status effect definitions ──
# Each has: name, color, duration (ms), tick_interval (ms), tick_damage, icon_char
STATUS_DEFS = {
    "fire": {
        "name": "Fire",
        "color": (255, 120, 20),
        "duration": 3000,
        "tick_interval": 500,
        "tick_damage": 4,
        "icon": "F",
    },
    "bleed": {
        "name": "Bleed",
        "color": (200, 30, 30),
        "duration": 4000,
        "tick_interval": 600,
        "tick_damage": 3,
        "icon": "B",
    },
    "poison": {
        "name": "Poison",
        "color": (80, 200, 40),
        "duration": 5000,
        "tick_interval": 800,
        "tick_damage": 2,
        "icon": "P",
    },
    "slow": {
        "name": "Slow",
        "color": (100, 160, 255),
        "duration": 3000,
        "tick_interval": 0,       # no damage, just debuff
        "tick_damage": 0,
        "speed_mult": 0.5,
        "icon": "S",
    },
}


class StatusEffect:
    """A single active status effect instance."""
    __slots__ = ("key", "defn", "start_time", "last_tick")

    def __init__(self, key: str, now: int):
        self.key = key
        self.defn = STATUS_DEFS[key]
        self.start_time = now
        self.last_tick = now


class StatusManager:
    """Tracks active status effects on an entity (player or enemy)."""

    def __init__(self):
        self.effects: list[StatusEffect] = []

    def apply(self, key: str, now: int):
        """Apply (or refresh) a status effect."""
        # Refresh if already present
        for e in self.effects:
            if e.key == key:
                e.start_time = now
                return
        self.effects.append(StatusEffect(key, now))

    def update(self, now: int) -> int:
        """Tick all effects. Returns total tick damage this frame."""
        total_dmg = 0
        alive = []
        for e in self.effects:
            elapsed = now - e.start_time
            if elapsed >= e.defn["duration"]:
                continue  # expired
            alive.append(e)
            if e.defn["tick_interval"] > 0:
                if now - e.last_tick >= e.defn["tick_interval"]:
                    total_dmg += e.defn["tick_damage"]
                    e.last_tick = now
        self.effects = alive
        return total_dmg

    def has(self, key: str) -> bool:
        return any(e.key == key for e in self.effects)

    def get_speed_mult(self) -> float:
        """Return combined speed multiplier from active effects."""
        mult = 1.0
        for e in self.effects:
            sm = e.defn.get("speed_mult")
            if sm is not None:
                mult *= sm
        return mult

    def clear(self):
        self.effects.clear()

    # ── drawing helpers ──

    def draw_icons(self, surface: pygame.Surface, x: int, y: int, font: pygame.font.Font):
        """Draw small status icons above entity."""
        now = pygame.time.get_ticks()
        offset = 0
        for e in self.effects:
            remaining = e.defn["duration"] - (now - e.start_time)
            if remaining <= 0:
                continue
            # Blink when about to expire
            if remaining < 800 and (now // 120) % 2 == 0:
                continue
            txt = font.render(e.defn["icon"], True, e.defn["color"])
            surface.blit(txt, (x + offset, y))
            offset += txt.get_width() + 3

    def draw_particles(self, surface: pygame.Surface, cx: int, cy: int, size: int):
        """Draw particle effects around entity based on active statuses."""
        now = pygame.time.get_ticks()
        for e in self.effects:
            color = e.defn["color"]
            if e.key == "fire":
                # Small flame particles rising — use direct draw (no SRCALPHA alloc)
                for i in range(3):
                    angle = (now * 0.005 + i * 2.1) % math.tau
                    px = cx + int(math.cos(angle) * size * 0.4)
                    py = cy + int(math.sin(angle) * size * 0.3) - int((now * 0.02 + i * 7) % 12)
                    r = max(1, 3 - int((now * 0.01 + i * 5) % 3))
                    pygame.draw.circle(surface, color, (px, py), r)
            elif e.key == "bleed":
                # Dripping red dots
                for i in range(2):
                    drip_y = int((now * 0.03 + i * 30) % 20)
                    px = cx + (i * 10 - 5)
                    py = cy + drip_y
                    pygame.draw.circle(surface, color, (px, py), 2)
            elif e.key == "poison":
                # Green bubbles
                for i in range(2):
                    angle = (now * 0.003 + i * 3.14) % math.tau
                    px = cx + int(math.cos(angle) * size * 0.5)
                    py = cy - int((now * 0.015 + i * 20) % 16)
                    pygame.draw.circle(surface, (*color, 140), (px, py), 2)
            elif e.key == "slow":
                # Blue frost crystals
                for i in range(3):
                    angle = (i * math.tau / 3 + now * 0.002) % math.tau
                    px = cx + int(math.cos(angle) * size * 0.5)
                    py = cy + int(math.sin(angle) * size * 0.5)
                    pygame.draw.line(surface, color, (px - 2, py), (px + 2, py), 1)
                    pygame.draw.line(surface, color, (px, py - 2), (px, py + 2), 1)
