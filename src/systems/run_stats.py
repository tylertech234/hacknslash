"""Run statistics tracking — accumulates combat data for death/victory screens."""

import json
import os
import time
import pygame
from src.settings import DATA_DIR


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

        # Upgrades taken (ordered list)
        self.upgrades_taken: list[str] = []

        # Zone tracking
        self.zones_completed: list[str] = []
        self.current_zone: str = "wasteland"
        self.zone_times: dict[str, int] = {}
        self._zone_start_time: int = pygame.time.get_ticks()

        # Enemy that killed the player (empty if victory)
        self.killed_by: str = ""

    def set_weapon(self, weapon_key: str, weapon_name: str, cooldown_ms: int = 500):
        """Track weapon equip/switch."""
        now = pygame.time.get_ticks()
        # Close out previous weapon time
        if self._current_weapon and self._current_weapon in self.weapon_stats:
            self.weapon_stats[self._current_weapon]["time_equipped"] += now - self._weapon_equip_time

        # Init new weapon entry
        if weapon_key not in self.weapon_stats:
            self.weapon_stats[weapon_key] = {
                "name": weapon_name, "hits": 0, "damage": 0, "time_equipped": 0,
                "cooldown_ms": cooldown_ms,
            }
        self._current_weapon = weapon_key
        self._weapon_equip_time = now

    def record_hit(self, weapon_key: str, damage: int):
        """Record a weapon hit."""
        if weapon_key not in self.weapon_stats:
            self.weapon_stats[weapon_key] = {
                "name": weapon_key, "hits": 0, "damage": 0, "time_equipped": 0,
                "cooldown_ms": 500,
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

    def record_upgrade(self, name: str):
        """Record an upgrade or passive chosen at level up / chest."""
        self.upgrades_taken.append(name)

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

    def save_to_log(self, wave: int, zone: str, player_level: int,
                    char_class: str, victory: bool):
        """Append a summary of this run to logs/runs.jsonl for balance analysis."""
        # Build weapon DPS summary
        weapon_summary = {}
        for wkey, ws in self.weapon_stats.items():
            hits = ws["hits"]
            dmg = ws["damage"]
            cooldown_s = ws.get("cooldown_ms", 500) / 1000
            avg = dmg / hits if hits > 0 else 0
            theoretical_dps = avg / cooldown_s if avg > 0 else 0
            weapon_summary[wkey] = {
                "name": ws["name"],
                "hits": hits,
                "total_damage": dmg,
                "avg_per_hit": round(avg, 1),
                "theoretical_dps": round(theoretical_dps, 1),
                "time_equipped_s": round(ws.get("time_equipped", 0) / 1000, 1),
            }

        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "char_class": char_class,
            "zone": zone,
            "wave": wave,
            "level": player_level,
            "victory": victory,
            "run_time_s": round(self.get_run_time() / 1000, 1),
            "kills": self.total_kills,
            "boss_kills": self.boss_kills,
            "damage_dealt": self.total_damage_dealt,
            "damage_taken": self.total_damage_taken,
            "highest_hit": self.highest_hit,
            "total_healed": self.total_healed,
            "killed_by": self.killed_by,
            "zones_completed": self.zones_completed,
            "upgrades": self.upgrades_taken,
            "weapons": weapon_summary,
            "passives": {k: v["procs"] for k, v in self.passive_stats.items()},
        }

        log_dir = os.path.join(DATA_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "runs.jsonl")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
