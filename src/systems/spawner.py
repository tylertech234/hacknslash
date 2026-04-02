import random
import math
import pygame
from src.settings import (
    WAVE_BASE_COUNT, WAVE_GROWTH, SPAWN_MARGIN,
    TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
)
from src.entities.enemy import Enemy


class WaveSpawner:
    """Spawns enemies in waves with bosses every 3/5 waves."""

    def __init__(self):
        self.wave = 0
        self.enemies: list[Enemy] = []
        self.wave_active = False
        self.wave_delay = 2000  # ms between waves
        self.last_wave_end = 0
        self.boss_wave = False  # set True on boss waves for HUD
        self.just_started_wave = False  # flag for game loop to detect new wave

    @property
    def world_w(self) -> int:
        return MAP_WIDTH * TILE_SIZE

    @property
    def world_h(self) -> int:
        return MAP_HEIGHT * TILE_SIZE

    def _rand_spawn_pos(self) -> tuple[float, float]:
        return (
            random.randint(SPAWN_MARGIN, self.world_w - SPAWN_MARGIN),
            random.randint(SPAWN_MARGIN, self.world_h - SPAWN_MARGIN),
        )

    def start_next_wave(self, now: int):
        self.wave += 1
        self.enemies.clear()
        self.boss_wave = False

        count = WAVE_BASE_COUNT + (self.wave - 1) * WAVE_GROWTH

        is_big_boss_wave = self.wave % 5 == 0
        is_mini_boss_wave = (not is_big_boss_wave) and self.wave % 3 == 0
        use_wraiths = self.wave > 10  # wraith enemy type unlocks after wave 10

        # Spawn normal enemies
        for _ in range(count):
            x, y = self._rand_spawn_pos()
            if use_wraiths and random.random() < 0.4:
                self.enemies.append(Enemy(x, y, "wraith"))
            else:
                self.enemies.append(Enemy(x, y, "dalek"))

        # Spawn bosses
        if is_big_boss_wave:
            self.boss_wave = True
            x, y = self._rand_spawn_pos()
            self.enemies.append(Enemy(x, y, "big_boss"))
            # Also add a couple mini bosses as escorts
            for _ in range(2):
                x, y = self._rand_spawn_pos()
                self.enemies.append(Enemy(x, y, "mini_boss"))
        elif is_mini_boss_wave:
            self.boss_wave = True
            x, y = self._rand_spawn_pos()
            self.enemies.append(Enemy(x, y, "mini_boss"))

        self.wave_active = True
        self.just_started_wave = True

    def update(self, now: int):
        self.just_started_wave = False
        if self.wave_active:
            alive = [e for e in self.enemies if e.alive]
            if len(alive) == 0:
                self.wave_active = False
                self.last_wave_end = now
        else:
            if now - self.last_wave_end >= self.wave_delay:
                self.start_next_wave(now)

    def get_alive_enemies(self) -> list[Enemy]:
        return [e for e in self.enemies if e.alive]
