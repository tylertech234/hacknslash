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
    "freeze": {
        "name": "Freeze",
        "color": (140, 210, 255),
        "duration": 1800,
        "tick_interval": 0,       # no DoT — pure movement lock
        "tick_damage": 0,
        "speed_mult": 0.0,        # completely rooted
        "icon": "Z",
    },
    "shock": {
        "name": "Shock",
        "color": (255, 240, 60),
        "duration": 2500,
        "tick_interval": 280,     # rapid zap ticks
        "tick_damage": 6,
        "icon": "!",
    },
    "insanity": {
        "name": "Insanity",
        "color": (220, 40, 180),
        "duration": 2000,         # up to 2 s of lost control
        "tick_interval": 0,
        "tick_damage": 0,
        "icon": "?",
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

    def is_frozen(self) -> bool:
        return self.has("freeze")

    def is_insane(self) -> bool:
        return self.has("insanity")

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
            elif e.key == "freeze":
                # Spiked ice shards radiating outward
                for i in range(6):
                    angle = (i * math.tau / 6) + now * 0.0005
                    dist = size * 0.55 + math.sin(now * 0.008 + i) * 3
                    px = cx + int(math.cos(angle) * dist)
                    py = cy + int(math.sin(angle) * dist)
                    px2 = cx + int(math.cos(angle) * (dist - 6))
                    py2 = cy + int(math.sin(angle) * (dist - 6))
                    pygame.draw.line(surface, color, (px2, py2), (px, py), 2)
                    pygame.draw.circle(surface, (200, 240, 255), (px, py), 2)
            elif e.key == "shock":
                # Jagged lightning arcs
                for i in range(3):
                    base_angle = (i * math.tau / 3 + now * 0.025) % math.tau
                    sx2 = cx + int(math.cos(base_angle) * size * 0.3)
                    sy2 = cy + int(math.sin(base_angle) * size * 0.3)
                    ex2 = cx + int(math.cos(base_angle) * size * 0.65)
                    ey2 = cy + int(math.sin(base_angle) * size * 0.65)
                    # Jag mid-point
                    jag_x = (sx2 + ex2) // 2 + int(math.sin(now * 0.04 + i * 2) * 5)
                    jag_y = (sy2 + ey2) // 2 + int(math.cos(now * 0.04 + i * 2) * 5)
                    pygame.draw.line(surface, color, (sx2, sy2), (jag_x, jag_y), 2)
                    pygame.draw.line(surface, color, (jag_x, jag_y), (ex2, ey2), 2)
            elif e.key == "insanity":
                # Swirling crimson-purple wisps orbiting faster each frame
                for i in range(5):
                    angle = (i * math.tau / 5 + now * 0.018) % math.tau
                    r = size * 0.55 + math.sin(now * 0.01 + i * 1.3) * 5
                    px = cx + int(math.cos(angle) * r)
                    py = cy + int(math.sin(angle) * r)
                    pygame.draw.circle(surface, color, (px, py), 3)
                    # Inner dark pupil effect
                    pygame.draw.circle(surface, (40, 0, 30), (px, py), 1)
