"""Zone definitions — each zone has unique enemies, atmosphere, hazards, and a boss."""


# Zone progression order
ZONE_ORDER = ["wasteland", "city", "abyss"]

ZONES = {
    "wasteland": {
        "name": "The Forest",
        "desc": "Ancient woods. Something lurks in the shadows.",
        "enemy_pool": ["cyber_rat", "cyber_raccoon", "d_lek", "charger", "shielder", "spitter"],
        "mini_boss": "iron_sentinel",
        "sub_boss": "mega_cyber_deer",
        "sub_boss_wave": 5,
        "boss": "supreme_d_lek",
        "boss_wave": 10,
        "tile_colors": {
            "floor": (34, 60, 28),
            "floor_alt": (30, 55, 25),
            "wall": (20, 35, 18),
        },
        "ambient_color": (8, 18, 10),
        "particle_color": (80, 140, 60),   # leaves
        "particle_dir": (0.8, 0.5),           # gentle wind
        "music_key": "minor",
        # Hazards unlocked at these waves
        "hazards": {
            3: "acid_puddle",
            5: "dust_storm",
            7: "solar_flare",
        },
    },
    "city": {
        "name": "Ruined Metropolis",
        "desc": "Shattered skyscrapers. Something stirs below.",
        "enemy_pool": ["cyber_zombie", "cyber_dog", "drone", "cultist", "shambler"],
        "mini_boss": "street_preacher",
        "boss": "eldritch_horror",
        "boss_wave": 10,
        "tile_colors": {
            "floor": (40, 38, 45),
            "floor_alt": (35, 33, 40),
            "wall": (70, 65, 75),
        },
        "ambient_color": (15, 10, 18),
        "particle_color": (200, 100, 50),    # falling ash/embers
        "particle_dir": (0.2, 1.0),           # downward
        "music_key": "chromatic",
        "hazards": {
            3: "falling_debris",
            5: "toxic_gas",
            7: "electrical_surge",
        },
    },
    "abyss": {
        "name": "The Abyss",
        "desc": "Reality fractures. The source of corruption.",
        "enemy_pool": ["specter", "void_wisp", "rift_walker", "mirror_shade", "gravity_warden", "null_serpent"],
        "mini_boss": "architect",
        "boss": "nexus",
        "boss_wave": 10,
        "tile_colors": {
            "floor": (20, 15, 30),
            "floor_alt": (25, 18, 35),
            "wall": (50, 40, 70),
        },
        "ambient_color": (8, 5, 15),
        "particle_color": (140, 80, 220),    # void particles (float upward)
        "particle_dir": (0.0, -1.0),          # upward
        "music_key": "dissonant",
        "hazards": {
            3: "void_rift",
            5: "reality_fracture",
            7: "entropic_decay",
        },
    },
}


def get_zone(name: str) -> dict:
    return ZONES.get(name, ZONES["wasteland"])


def get_next_zone(current: str) -> str | None:
    """Return the next zone name, or None if this was the final zone."""
    try:
        idx = ZONE_ORDER.index(current)
        if idx + 1 < len(ZONE_ORDER):
            return ZONE_ORDER[idx + 1]
    except ValueError:
        pass
    return None
