import random
import math
import pygame
from src.settings import (
    WAVE_BASE_COUNT, WAVE_GROWTH, SPAWN_MARGIN,
    TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
)
from src.entities.enemy import Enemy


class WaveSpawner:
    """Spawns enemies in waves with patterns, bosses, and progressive types."""

    def __init__(self):
        self.wave = 0
        self.enemies: list[Enemy] = []
        self.wave_active = False
        self.wave_delay = 5000  # ms between waves (5s countdown shown to player)
        self.last_wave_end = 0
        self.boss_wave = False
        self.just_started_wave = False
        # Zone-aware enemy pool
        self.zone_enemy_pool = None
        self.zone_mini_boss = "iron_sentinel"
        self.zone_boss = "supreme_d_lek"
        self.zone_boss_wave = 10
        self.zone_sub_boss: str | None = None
        self.zone_sub_boss_wave: int | None = None

    def set_zone(self, zone_data: dict):
        """Configure spawner for a specific zone."""
        self.zone_enemy_pool = zone_data.get("enemy_pool")
        self.zone_mini_boss = zone_data.get("mini_boss", "iron_sentinel")
        self.zone_boss = zone_data.get("boss", "supreme_d_lek")
        self.zone_boss_wave = zone_data.get("boss_wave", 10)
        self.zone_sub_boss = zone_data.get("sub_boss")
        self.zone_sub_boss_wave = zone_data.get("sub_boss_wave")

    @property
    def world_w(self) -> int:
        return MAP_WIDTH * TILE_SIZE

    @property
    def world_h(self) -> int:
        return MAP_HEIGHT * TILE_SIZE

    def _rand_spawn_pos(self, player_x: float = -1, player_y: float = -1) -> tuple[float, float]:
        """Pick a random position, ensuring it's far from the player (off-screen)."""
        min_dist = 500  # must be at least this far from player
        for _ in range(30):
            x = random.randint(SPAWN_MARGIN, self.world_w - SPAWN_MARGIN)
            y = random.randint(SPAWN_MARGIN, self.world_h - SPAWN_MARGIN)
            if player_x < 0 or math.hypot(x - player_x, y - player_y) >= min_dist:
                return (x, y)
        # Fallback: spawn at edge of map away from player
        if player_x >= 0:
            angle = random.uniform(0, math.tau)
            x = player_x + math.cos(angle) * min_dist
            y = player_y + math.sin(angle) * min_dist
            x = max(SPAWN_MARGIN, min(self.world_w - SPAWN_MARGIN, x))
            y = max(SPAWN_MARGIN, min(self.world_h - SPAWN_MARGIN, y))
            return (x, y)
        return (
            random.randint(SPAWN_MARGIN, self.world_w - SPAWN_MARGIN),
            random.randint(SPAWN_MARGIN, self.world_h - SPAWN_MARGIN),
        )

    def _pick_enemy_type(self) -> str:
        """Pick an enemy type based on current wave and zone pool."""
        w = self.wave
        if self.zone_enemy_pool:
            # Unlock more enemy types as waves progress
            pool = self.zone_enemy_pool
            max_idx = min(len(pool), 1 + (w - 1) // 2)
            return random.choice(pool[:max(1, max_idx)])
        # Fallback: original wasteland progression (now using new zone 1 enemies)
        r = random.random()
        if w <= 2:
            return "cyber_rat"
        elif w <= 4:
            if r < 0.30:
                return "cyber_raccoon"
            return "cyber_rat"
        elif w <= 5:
            if r < 0.25:
                return "cyber_raccoon"
            if r < 0.35:
                return "d_lek"
            return "cyber_rat"
        elif w <= 7:
            if r < 0.25:
                return "cyber_raccoon"
            if r < 0.40:
                return "d_lek"
            if r < 0.50:
                return "charger"
            return "cyber_rat"
        else:
            if r < 0.20:
                return "cyber_raccoon"
            if r < 0.35:
                return "d_lek"
            if r < 0.50:
                return "charger"
            if r < 0.60:
                return "spitter"
            if r < 0.70:
                return "shielder"
            return "cyber_rat"

    # ---- Spawn Patterns ----

    def _spawn_random(self, count: int, px: float = -1, py: float = -1):
        """Scatter enemies randomly."""
        for _ in range(count):
            x, y = self._rand_spawn_pos(px, py)
            self.enemies.append(Enemy(x, y, self._pick_enemy_type()))

    def _spawn_ring(self, count: int, cx: float, cy: float, radius: float, px: float = -1, py: float = -1):
        """Spawn enemies in a ring formation around a point."""
        # Ensure ring center is away from player
        if px >= 0 and math.hypot(cx - px, cy - py) < 400:
            angle_away = math.atan2(cy - py, cx - px) if math.hypot(cx - px, cy - py) > 1 else random.uniform(0, math.tau)
            cx = px + math.cos(angle_away) * 500
            cy = py + math.sin(angle_away) * 500
            cx = max(SPAWN_MARGIN, min(self.world_w - SPAWN_MARGIN, cx))
            cy = max(SPAWN_MARGIN, min(self.world_h - SPAWN_MARGIN, cy))
        for i in range(count):
            angle = (math.tau / count) * i + random.uniform(-0.1, 0.1)
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            x = max(SPAWN_MARGIN, min(self.world_w - SPAWN_MARGIN, x))
            y = max(SPAWN_MARGIN, min(self.world_h - SPAWN_MARGIN, y))
            self.enemies.append(Enemy(x, y, self._pick_enemy_type()))

    def _spawn_v_formation(self, count: int, origin_x: float, origin_y: float,
                           angle: float):
        """Spawn enemies in a V/arrow pattern."""
        spacing = 40
        for i in range(count):
            side = 1 if i % 2 == 0 else -1
            rank = (i + 1) // 2
            dx = -math.cos(angle) * rank * spacing
            dy = -math.sin(angle) * rank * spacing
            perp_x = -math.sin(angle) * side * rank * spacing * 0.6
            perp_y = math.cos(angle) * side * rank * spacing * 0.6
            x = max(SPAWN_MARGIN, min(self.world_w - SPAWN_MARGIN, origin_x + dx + perp_x))
            y = max(SPAWN_MARGIN, min(self.world_h - SPAWN_MARGIN, origin_y + dy + perp_y))
            self.enemies.append(Enemy(x, y, self._pick_enemy_type()))

    def _spawn_cluster(self, count: int, cx: float, cy: float, spread: float = 80):
        """Spawn enemies in a tight cluster."""
        for _ in range(count):
            x = cx + random.uniform(-spread, spread)
            y = cy + random.uniform(-spread, spread)
            x = max(SPAWN_MARGIN, min(self.world_w - SPAWN_MARGIN, x))
            y = max(SPAWN_MARGIN, min(self.world_h - SPAWN_MARGIN, y))
            self.enemies.append(Enemy(x, y, self._pick_enemy_type()))

    def _spawn_line(self, count: int, x1: float, y1: float, x2: float, y2: float):
        """Spawn enemies in a line between two points."""
        for i in range(count):
            t = i / max(1, count - 1)
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            self.enemies.append(Enemy(x, y, self._pick_enemy_type()))

    def start_next_wave(self, now: int, player_x: float = -1, player_y: float = -1):
        self.wave += 1
        self.enemies.clear()
        self.boss_wave = False

        count = WAVE_BASE_COUNT + (self.wave - 1) * WAVE_GROWTH

        is_big_boss_wave = self.wave == self.zone_boss_wave
        is_sub_boss_wave = (not is_big_boss_wave
                            and self.zone_sub_boss is not None
                            and self.wave == self.zone_sub_boss_wave)
        is_mini_boss_wave = (not is_big_boss_wave and not is_sub_boss_wave
                             and self.wave % 3 == 0)

        # -- Boss waves: only spawn bosses, no regular enemies --
        if is_big_boss_wave or is_mini_boss_wave or is_sub_boss_wave:
            self.boss_wave = True
            if is_big_boss_wave:
                x, y = self._rand_spawn_pos(player_x, player_y)
                self.enemies.append(Enemy(x, y, self.zone_boss))
                # Escort guards depend on zone boss type
                escort_type = (
                    "emperors_elite_guard"
                    if self.zone_boss == "supreme_d_lek"
                    else self.zone_mini_boss
                )
                for _ in range(2):
                    x, y = self._rand_spawn_pos(player_x, player_y)
                    self.enemies.append(Enemy(x, y, escort_type))
            elif is_sub_boss_wave:
                x, y = self._rand_spawn_pos(player_x, player_y)
                self.enemies.append(Enemy(x, y, self.zone_sub_boss))
                # Add a couple of regulars for flavor
                for _ in range(3):
                    x, y = self._rand_spawn_pos(player_x, player_y)
                    self.enemies.append(Enemy(x, y, self._pick_enemy_type()))
            else:
                x, y = self._rand_spawn_pos(player_x, player_y)
                self.enemies.append(Enemy(x, y, self.zone_mini_boss))

            # Stamp spawn time for scale-in animation + wave scaling
            wave_hp_mult = 1.0 + (self.wave - 1) * 0.12
            wave_dmg_mult = 1.0 + (self.wave - 1) * 0.08
            for e in self.enemies:
                e.spawn_time = now
                e.max_hp = int(e.max_hp * wave_hp_mult)
                e.hp = e.max_hp
                e.damage = int(e.damage * wave_dmg_mult)
            self.wave_active = True
            self.just_started_wave = True
            return

        # -- Spawn normal enemies using patterns --
        # Pick 1-3 patterns and split enemies across them
        center_x = self.world_w // 2
        center_y = self.world_h // 2
        patterns = ["random", "ring", "v_formation", "cluster", "line"]
        num_patterns = min(3, 1 + self.wave // 3)
        chosen = random.sample(patterns, min(num_patterns, len(patterns)))
        per_pattern = count // len(chosen)
        remainder = count - per_pattern * len(chosen)

        for pidx, pattern in enumerate(chosen):
            n = per_pattern + (1 if pidx < remainder else 0)
            if n <= 0:
                continue

            if pattern == "random":
                self._spawn_random(n, player_x, player_y)
            elif pattern == "ring":
                rx = random.randint(center_x - 400, center_x + 400)
                ry = random.randint(center_y - 400, center_y + 400)
                self._spawn_ring(n, rx, ry, 120 + self.wave * 5, player_x, player_y)
            elif pattern == "v_formation":
                ox, oy = self._rand_spawn_pos(player_x, player_y)
                angle = math.atan2(center_y - oy, center_x - ox)
                self._spawn_v_formation(n, ox, oy, angle)
            elif pattern == "cluster":
                cx, cy = self._rand_spawn_pos(player_x, player_y)
                self._spawn_cluster(n, cx, cy, 60 + self.wave * 3)
            elif pattern == "line":
                x1, y1 = self._rand_spawn_pos(player_x, player_y)
                x2, y2 = self._rand_spawn_pos(player_x, player_y)
                self._spawn_line(n, x1, y1, x2, y2)

        # Stamp spawn time for scale-in animation, and scale stats per wave
        wave_hp_mult = 1.0 + (self.wave - 1) * 0.15   # +15% HP per wave
        wave_dmg_mult = 1.0 + (self.wave - 1) * 0.12  # +12% damage per wave
        wave_speed_mult = 1.0 + (self.wave - 1) * 0.04  # +4% speed per wave
        for e in self.enemies:
            e.spawn_time = now
            e.max_hp = int(e.max_hp * wave_hp_mult)
            e.hp = e.max_hp
            e.damage = int(e.damage * wave_dmg_mult)
            e.speed = e.speed * min(wave_speed_mult, 2.0)  # cap at 2x

        self.wave_active = True
        self.just_started_wave = True

    def update(self, now: int, player_x: float = -1, player_y: float = -1):
        self.just_started_wave = False
        if self.wave_active:
            alive = [e for e in self.enemies if e.alive]
            if len(alive) == 0:
                self.wave_active = False
                self.last_wave_end = now
        else:
            # Stop auto-advancing after the zone's boss wave — portal handles progression
            if self.wave >= self.zone_boss_wave:
                return
            if now - self.last_wave_end >= self.wave_delay:
                self.start_next_wave(now, player_x, player_y)

    def get_alive_enemies(self) -> list[Enemy]:
        return [e for e in self.enemies if e.alive]
