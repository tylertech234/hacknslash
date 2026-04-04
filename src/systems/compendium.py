"""Compendium — tracks which enemies have been encountered and slain.

Entries are unlocked on the first kill of each enemy type.
Data is persisted to compendium_save.json in the project root.
"""
import os
import logging

from src.systems.profile import StorageBackend, FileStorage

log = logging.getLogger("compendium")

_DEFAULT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Enemy metadata ────────────────────────────────────────────────────────────

DISPLAY_NAMES: dict[str, str] = {
    # Zone 1
    "cyber_rat":       "Cyber Rat",
    "cyber_raccoon":   "Cyber Raccoon",
    "mega_cyber_deer": "Mega Cyber Deer",
    "d_lek":           "D-Lek",
    "charger":         "Charger",
    "shielder":        "Shielder",
    "spitter":         "Spitter",
    "iron_sentinel":   "Iron Sentinel",
    "supreme_d_lek":   "D-Lek Emperor",
    "emperors_elite_guard": "Emperor's Elite Guard",
    # Zone 2
    "cyber_zombie":    "Cyber Zombie",
    "cyber_dog":       "Cyber Dog",
    "drone":           "Drone",
    "cultist":         "Cultist",
    "shambler":        "Shambler",
    "street_preacher": "Street Preacher",
    "eldritch_horror": "Eldritch Horror",
    # Zone 3
    "specter":         "Specter",
    "void_wisp":       "Void Wisp",
    "rift_walker":     "Rift Walker",
    "mirror_shade":    "Mirror Shade",
    "gravity_warden":  "Gravity Warden",
    "null_serpent":    "Null Serpent",
    "architect":       "Architect",
    "nexus":           "Nexus",
}

ENEMY_ZONES: dict[str, str] = {
    "cyber_rat":       "wasteland",
    "cyber_raccoon":   "wasteland",
    "mega_cyber_deer": "wasteland",
    "d_lek":           "wasteland",
    "charger":         "wasteland",
    "shielder":        "wasteland",
    "spitter":         "wasteland",
    "iron_sentinel":   "wasteland",
    "supreme_d_lek":   "wasteland",
    "emperors_elite_guard": "wasteland",
    "cyber_zombie":    "city",
    "cyber_dog":       "city",
    "drone":           "city",
    "cultist":         "city",
    "shambler":        "city",
    "street_preacher": "city",
    "eldritch_horror": "city",
    "specter":         "abyss",
    "void_wisp":       "abyss",
    "rift_walker":     "abyss",
    "mirror_shade":    "abyss",
    "gravity_warden":  "abyss",
    "null_serpent":    "abyss",
    "architect":       "abyss",
    "nexus":           "abyss",
}

# Brief lore entries shown in the compendium card
ENEMY_LORE: dict[str, str] = {
    "cyber_rat":       "Small, wiry, relentless.\nCyber implants make them faster\nthan their feral cousins.",
    "cyber_raccoon":   "Opportunistic scavengers fitted\nwith tactical gear.\nDodge when cornered.",
    "mega_cyber_deer": "A massive beast reforged in steel.\nCharged antlers crackle with\nraw cyber-energy.",
    "d_lek":           "Remnant war machines.\nProgrammed to exterminate.\nNever surrender.",
    "charger":         "Enraged muscle.\nBuilds momentum and\nbarely stops for anything.",
    "shielder":        "Heavy frontal plating deflects\nmost attacks.\nFlank to deal real damage.",
    "spitter":         "Bloated acid-sac creature.\nKeeps distance and\nrains corrosive bile.",
    "iron_sentinel":   "An elite guardian\nfrom a forgotten war.\nStill very much operational.",
    "supreme_d_lek":   "The D-Lek Emperor.\nRuler of all D-Lek-kind.\nIts word is extermination.",
    "emperors_elite_guard": "Black-armoured honour guard.\nFlanks the Emperor in battle.\nExterminate. Exterminate.",
    "cyber_zombie":    "Reanimated corps reinforced\nwith scavenged tech.\nOccasionally lunges.",
    "cyber_dog":       "Fast, mechanical, feral.\nStops dead to crouch\nbefore a lethal leap.",
    "drone":           "Surveillance unit retasked\nfor elimination.\nOrbits before opening fire.",
    "cultist":         "Devoted to the Eldritch Horror.\nChannels dark energy before\nunleashing bursts.",
    "shambler":        "An ambulatory mass of rot.\nSlow but hits like a wall.\nDon't get surrounded.",
    "street_preacher": "Fire-touched zealot.\nPreaches in flames.\nA mini-boss of pure devotion.",
    "eldritch_horror": "Tentacled nightmare from\nbeyond sane geometry.\nBoss of the Ruined City.",
    "specter":         "A wraith refined through void\nexposure. Faster, deadlier,\nand it bleeds you dry.",
    "void_wisp":       "Barely perceptible flicker.\nPhases through bullets.\nDisappears when hit.",
    "rift_walker":     "Tears holes in space.\nAppears beside you without\nwarning — then attacks.",
    "mirror_shade":    "Mirrors your every move.\nSplits in two at half health.\nWhich one is real?",
    "gravity_warden":  "Bends gravity at will.\nPulls you into its\nslam radius.",
    "null_serpent":    "Serpentuine stalker.\nWeaves unpredictably.\nLong-range predator.",
    "architect":       "Designed the Abyss itself.\nNow defends it with\nvoid cages and cold precision.",
    "nexus":           "The source of all corruption.\n9-shot rings. Reality collapses.\nSlay it to end the cycle.",
}

# Order enemies appear in the compendium (by zone, then difficulty)
COMPENDIUM_ORDER: list[str] = [
    # Zone 1
    "cyber_rat", "cyber_raccoon", "d_lek", "charger", "shielder", "spitter",
    "mega_cyber_deer", "iron_sentinel", "supreme_d_lek", "emperors_elite_guard",
    # Zone 2
    "cyber_zombie", "cyber_dog", "drone", "cultist", "shambler",
    "street_preacher", "eldritch_horror",
    # Zone 3
    "specter", "void_wisp", "rift_walker", "mirror_shade",
    "gravity_warden", "null_serpent", "architect", "nexus",
]


# ── Compendium data class ─────────────────────────────────────────────────────

class Compendium:
    SAVE_FILENAME = "compendium_save.json"

    def __init__(self, storage: StorageBackend | None = None):
        self._storage = storage or FileStorage(_DEFAULT_DIR)
        # enemy_type -> {"kills": int, "first_seen_wave": int}
        self.entries: dict[str, dict] = {}
        self.load()

    # ── Public API ────────────────────────────────────────────────────────────

    def on_kill(self, enemy_type: str, wave: int = 0) -> bool:
        """Record a kill.  Returns True if this was the *first* kill (unlock event)."""
        if enemy_type not in DISPLAY_NAMES:
            return False  # unknown / not tracked
        first_kill = enemy_type not in self.entries or self.entries[enemy_type]["kills"] == 0
        if enemy_type not in self.entries:
            self.entries[enemy_type] = {"kills": 0, "first_seen_wave": wave}
        self.entries[enemy_type]["kills"] += 1
        self.save()
        return first_kill

    def is_unlocked(self, enemy_type: str) -> bool:
        return self.entries.get(enemy_type, {}).get("kills", 0) > 0

    def get_kills(self, enemy_type: str) -> int:
        return self.entries.get(enemy_type, {}).get("kills", 0)

    def total_unlocked(self) -> int:
        return sum(1 for t in DISPLAY_NAMES if self.is_unlocked(t))

    def total_entries(self) -> int:
        return len(DISPLAY_NAMES)

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self):
        try:
            self._storage.write(self.SAVE_FILENAME, self.entries)
        except Exception as e:
            log.warning("Could not save compendium: %s", e)

    def load(self):
        try:
            data = self._storage.read(self.SAVE_FILENAME)
            if isinstance(data, dict):
                self.entries = data
        except Exception as e:
            log.warning("Could not load compendium: %s", e)
            self.entries = {}
