"""Enemy death processing — extracted from game.py to reduce size and duplication."""
import math
import random as _rng
import logging

from src.systems.boss_chest import BossChest
from src.settings import XP_PER_KILL, XP_DARKNESS_BONUS

log = logging.getLogger("game")


def process_enemy_death(enemy, player, alive, animations, combat, sounds,
                        lighting, boss_chests, kills_tracker, now):
    """Handle a single enemy death: effects, passives, XP, drops, chests.

    Args:
        kills_tracker: dict with 'kills' and 'boss_kills' integer values (mutated)

    Returns nothing — mutates lists/counters in place.
    """
    kills_tracker["kills"] += 1
    if enemy.enemy_type in ("mini_boss", "big_boss"):
        kills_tracker["boss_kills"] += 1

    # -- colour by type
    color = (200, 50, 50)
    if enemy.enemy_type == "wraith":
        color = (100, 200, 255)
    elif enemy.enemy_type in ("mini_boss", "big_boss"):
        color = (255, 160, 0)
    elif enemy.enemy_type == "charger":
        color = (255, 100, 50)
    elif enemy.enemy_type == "shielder":
        color = (100, 150, 255)
    elif enemy.enemy_type == "spitter":
        color = (80, 200, 50)

    # -- visual / audio
    animations.spawn_death_burst(enemy.x, enemy.y, color)
    animations.spawn_death_anim(enemy.x, enemy.y, enemy.enemy_type, color)
    is_boss = enemy.enemy_type in ("mini_boss", "big_boss")
    animations.add_screen_shake(4 if is_boss else 2)
    sounds.play("enemy_death")

    # -- passives
    if "melee_lifesteal" in player.passives and not player.weapon.get("projectile"):
        player.hp = min(player.max_hp, player.hp + 5)

    if "confetti_burst" in player.passives:
        for _ in range(3):
            animations.spawn_death_burst(
                enemy.x + _rng.randint(-20, 20),
                enemy.y + _rng.randint(-20, 20),
                (_rng.randint(100, 255), _rng.randint(100, 255), _rng.randint(100, 255)))

    if "adrenaline" in player.passives:
        player._adrenaline_until = now + 3000

    if "explosive_kills" in player.passives and _rng.random() < 0.25:
        for other in alive:
            if other.alive and other is not enemy:
                d = math.hypot(other.x - enemy.x, other.y - enemy.y)
                if d < 60:
                    exp_dmg = 40
                    other.take_damage(exp_dmg, other.x - enemy.x, other.y - enemy.y, now)
                    combat._add_damage_number(other.x, other.y - other.size, exp_dmg, (255, 150, 0))
        animations.spawn_death_burst(enemy.x, enemy.y, (255, 150, 0), count=16)
        sounds.play("confetti_boom")

    # -- XP + drops
    xp_mult = 1.0 + lighting.darkness * XP_DARKNESS_BONUS
    xp_base = getattr(enemy, "xp_value", XP_PER_KILL)
    player.gain_xp(int(xp_base * xp_mult))
    combat.pending_drops.append((enemy.x, enemy.y))

    # -- boss chest
    if is_boss:
        chest = BossChest(enemy.x, enemy.y)
        boss_chests.append(chest)
        log.info("Boss chest spawned at (%.0f, %.0f)", enemy.x, enemy.y)


def fire_player_projectile(player, player_projectiles, sounds):
    """Spawn projectiles for the player's current weapon. Returns True if fired."""
    w = player.weapon
    if not w.get("projectile"):
        return False

    dmg = int(player.damage * w["damage_mult"] * player.damage_multiplier)
    px, py = player.x, player.y
    fx, fy = player.facing_x, player.facing_y
    cnt = w.get("proj_count", 1)
    spd = w.get("proj_speed", 7.0)
    lt = w.get("proj_lifetime", 800)

    if w.get("orbiter"):
        player_projectiles.spawn_orbiter(px, py, fx, fy, dmg, w.get("orbiter_type", "banana"))
    elif w.get("grenade"):
        player_projectiles.spawn_grenades(px, py, fx, fy, dmg, cnt, spd, lt)
    else:
        vis = w.get("proj_visual", "dagger")
        prc = w.get("piercing", False)
        player_projectiles.spawn_daggers(px, py, fx, fy, dmg, cnt, spd, lt, vis, prc)

    if "Chicken" in w.get("name", ""):
        sounds.play("chicken")
    else:
        sounds.play("throw")
    return True
