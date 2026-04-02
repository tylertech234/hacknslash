"""Roguelite meta-progression — permanent upgrades that carry between runs."""

import json
import os

# Save file lives next to main.py (project root)
_SAVE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAVE_FILE = os.path.join(_SAVE_DIR, "legacy_save.json")

LEGACY_UPGRADES = [
    {
        "key": "vitality",
        "name": "Vitality",
        "desc": "+10 Max HP per rank",
        "max_rank": 5,
        "cost_per_rank": 50,
        "stat": "max_hp",
        "value_per_rank": 10,
    },
    {
        "key": "might",
        "name": "Might",
        "desc": "+3 Damage per rank",
        "max_rank": 5,
        "cost_per_rank": 60,
        "stat": "damage",
        "value_per_rank": 3,
    },
    {
        "key": "swiftness",
        "name": "Swiftness",
        "desc": "+0.2 Speed per rank",
        "max_rank": 5,
        "cost_per_rank": 40,
        "stat": "speed",
        "value_per_rank": 0.2,
    },
    {
        "key": "resilience",
        "name": "Resilience",
        "desc": "+5% damage reduction per rank",
        "max_rank": 5,
        "cost_per_rank": 75,
        "stat": "damage_reduction",
        "value_per_rank": 0.05,
    },
    {
        "key": "fortune",
        "name": "Fortune",
        "desc": "+5% drop chance per rank",
        "max_rank": 5,
        "cost_per_rank": 45,
        "stat": "drop_chance",
        "value_per_rank": 0.05,
    },
    {
        "key": "headstart",
        "name": "Headstart",
        "desc": "Start with bonus levels (+1 per rank)",
        "max_rank": 5,
        "cost_per_rank": 100,
        "stat": "start_level",
        "value_per_rank": 1,
    },
]


class LegacyData:
    """Persistent roguelite progression that carries over between runs."""

    def __init__(self):
        self.total_runs = 0
        self.best_wave = 0
        self.total_kills = 0
        self.legacy_points = 0
        self.upgrades: dict[str, int] = {}
        self.load()

    def load(self):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
            self.total_runs = data.get("total_runs", 0)
            self.best_wave = data.get("best_wave", 0)
            self.total_kills = data.get("total_kills", 0)
            self.legacy_points = data.get("legacy_points", 0)
            self.upgrades = data.get("upgrades", {})
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # Use defaults

    def save(self):
        data = {
            "total_runs": self.total_runs,
            "best_wave": self.best_wave,
            "total_kills": self.total_kills,
            "legacy_points": self.legacy_points,
            "upgrades": self.upgrades,
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def finish_run(self, wave: int, kills: int, boss_kills: int) -> int:
        """Record a completed run and return legacy points earned."""
        self.total_runs += 1
        self.best_wave = max(self.best_wave, wave)
        self.total_kills += kills
        points = wave * 10 + kills + boss_kills * 20
        self.legacy_points += points
        self.save()
        return points

    def get_rank(self, key: str) -> int:
        return self.upgrades.get(key, 0)

    def try_purchase(self, key: str) -> bool:
        """Try to buy the next rank of an upgrade. Returns True on success."""
        upgrade = next((u for u in LEGACY_UPGRADES if u["key"] == key), None)
        if upgrade is None:
            return False
        rank = self.get_rank(key)
        if rank >= upgrade["max_rank"]:
            return False
        cost = upgrade["cost_per_rank"] * (rank + 1)
        if self.legacy_points < cost:
            return False
        self.legacy_points -= cost
        self.upgrades[key] = rank + 1
        self.save()
        return True

    def get_cost(self, key: str) -> int:
        """Get cost for the next rank of an upgrade."""
        upgrade = next((u for u in LEGACY_UPGRADES if u["key"] == key), None)
        if upgrade is None:
            return 0
        rank = self.get_rank(key)
        return upgrade["cost_per_rank"] * (rank + 1)

    def get_bonuses(self) -> dict:
        """Get all active permanent bonuses from purchased upgrades."""
        bonuses = {}
        for u in LEGACY_UPGRADES:
            rank = self.get_rank(u["key"])
            if rank > 0:
                bonuses[u["stat"]] = u["value_per_rank"] * rank
        return bonuses
