"""Run statistics tracking — accumulates combat data for death/victory screens."""

import pygame


class RunStats:
    """Tracks per-run statistics for the death/victory summary screen."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.time_started = pygame.time.get_ticks()
        self.total_damage_dealt = 0
        self.total_damage_taken = 0
        self.highest_hit = 0
        self.total_kills = 0
        self.boss_kills = 0
        self.total_healed = 0

        # Weapon performance: {weapon_key: {name, hits, damage, time_equipped}}
        self.weapon_stats: dict[str, dict] = {}
        self._current_weapon: str = ""
        self._weapon_equip_time: int = 0

        # Passive performance: {key: {procs, damage, healed, kills}}
        self.passive_stats: dict[str, dict] = {}

        # Zone tracking
        self.zones_completed: list[str] = []
        self.current_zone: str = "wasteland"
        self.zone_times: dict[str, int] = {}
        self._zone_start_time: int = pygame.time.get_ticks()

    def set_weapon(self, weapon_key: str, weapon_name: str):
        """Track weapon equip/switch."""
        now = pygame.time.get_ticks()
        # Close out previous weapon time
        if self._current_weapon and self._current_weapon in self.weapon_stats:
            self.weapon_stats[self._current_weapon]["time_equipped"] += now - self._weapon_equip_time

        # Init new weapon entry
        if weapon_key not in self.weapon_stats:
            self.weapon_stats[weapon_key] = {
                "name": weapon_name, "hits": 0, "damage": 0, "time_equipped": 0
            }
        self._current_weapon = weapon_key
        self._weapon_equip_time = now

    def record_hit(self, weapon_key: str, damage: int):
        """Record a weapon hit."""
        if weapon_key not in self.weapon_stats:
            self.weapon_stats[weapon_key] = {
                "name": weapon_key, "hits": 0, "damage": 0, "time_equipped": 0
            }
        self.weapon_stats[weapon_key]["hits"] += 1
        self.weapon_stats[weapon_key]["damage"] += damage
        self.total_damage_dealt += damage
        if damage > self.highest_hit:
            self.highest_hit = damage

    def record_passive_proc(self, passive_key: str, damage: int = 0, healed: int = 0, kills: int = 0):
        """Record a passive ability activation."""
        if passive_key not in self.passive_stats:
            self.passive_stats[passive_key] = {"procs": 0, "damage": 0, "healed": 0, "kills": 0}
        self.passive_stats[passive_key]["procs"] += 1
        self.passive_stats[passive_key]["damage"] += damage
        self.passive_stats[passive_key]["healed"] += healed
        self.passive_stats[passive_key]["kills"] += kills

    def record_damage_taken(self, amount: int):
        """Record damage the player received."""
        self.total_damage_taken += amount

    def record_heal(self, amount: int):
        """Record HP healed."""
        self.total_healed += amount

    def record_kill(self, is_boss: bool = False):
        self.total_kills += 1
        if is_boss:
            self.boss_kills += 1

    def complete_zone(self, zone_name: str):
        """Mark a zone as complete and record time."""
        now = pygame.time.get_ticks()
        elapsed = now - self._zone_start_time
        self.zone_times[zone_name] = elapsed
        self.zones_completed.append(zone_name)
        self._zone_start_time = now

    def set_zone(self, zone_name: str):
        self.current_zone = zone_name
        self._zone_start_time = pygame.time.get_ticks()

    def get_run_time(self) -> int:
        """Total run time in ms."""
        return pygame.time.get_ticks() - self.time_started

    def get_run_time_str(self) -> str:
        """Format total run time as M:SS."""
        ms = self.get_run_time()
        secs = ms // 1000
        mins = secs // 60
        secs = secs % 60
        return f"{mins}m {secs:02d}s"

    def finalize(self):
        """Close out the current weapon timer."""
        now = pygame.time.get_ticks()
        if self._current_weapon and self._current_weapon in self.weapon_stats:
            self.weapon_stats[self._current_weapon]["time_equipped"] += now - self._weapon_equip_time
