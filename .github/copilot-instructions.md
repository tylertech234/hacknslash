# Copilot Instructions for Cyber Survivor

## Project Overview
Python + Pygame top-down hack-and-slash survival game. ~12,742 LOC across 43 Python files. Procedural graphics and audio (zero external assets). Title: **"Cyber Survivor"**.

## Architecture
- Entry: `main.py` → `src/game.py` Game class
- Game loop: `_handle_events()` → `_update(dt, now)` → `_draw()`
- `dt` = milliseconds from `clock.tick(60)`, `now` = `pygame.time.get_ticks()`
- Zone progression: wasteland → city → abyss (each with unique enemies, hazards, and boss music)

## Key File Roles
| File | What it does |
|------|-------------|
| `src/game.py` | Main orchestrator — wires all systems, processes kills, applies passives |
| `src/settings.py` | All game constants (display, player, enemy, spawning, XP, lighting, zones) |
| `src/entities/player.py` | Player state, 3 class draw methods, damage/evasion/shield logic, coin tracking |
| `src/entities/enemy.py` | 21 enemy types across 3 zones, AI, draw, boss phase-2 enrage |
| `src/systems/weapons.py` | Weapon stat dicts + procedural draw functions per weapon |
| `src/systems/combat.py` | Melee hit resolution, passives (vampiric/chain/thorns) |
| `src/systems/game_actions.py` | Enemy death processing, coin drops, boss music, projectile firing helpers |
| `src/systems/projectiles.py` | ThrownDagger, OrbitingProjectile, ConfettiGrenade + collision |
| `src/systems/spawner.py` | Wave patterns, boss wave triggers, difficulty scaling |
| `src/systems/boss_chest.py` | Chest upgrade pool + reward selection screen |
| `src/systems/pickups.py` | Item drops (coins, XP orbs, heals) + magnetic field passive |
| `src/systems/status_effects.py` | Fire/bleed/poison/slow with tick damage |
| `src/systems/legacy.py` | Roguelite persistence (JSON save, 6 permanent upgrades) |
| `src/systems/sounds.py` | All procedural SFX + 2-layer chiptune + zone boss music (cached to `.cache/`) |
| `src/systems/zones.py` | Zone definitions — ZONE_ORDER, ZONES dict, get_zone(), get_next_zone() |
| `src/systems/atmosphere.py` | Atmospheric visual effects per zone |
| `src/systems/hazards.py` | Zone-specific hazards (acid puddle, dust storm, void rift, etc.) |
| `src/systems/portal.py` | Zone transition portal |
| `src/systems/run_stats.py` | Per-run statistics tracking |
| `src/systems/compendium.py` | Enemy unlock tracking — first-kill logic, JSON save, display names |
| `src/ui/toast.py` | Slide-in achievement-style toast notifications |
| `src/ui/compendium_screen.py` | Compendium browser with procedural monster art + inspect view |
| `src/ui/hud.py` | In-game HUD (HP/XP bars, boss HP, wave info, coin count, vignette) |
| `src/ui/charselect.py` | 3-class picker (knight / archer / jester) |
| `src/ui/levelup.py` | Level-up upgrade choices |
| `src/ui/radar.py` | Motion tracker |
| `src/ui/legacy_screen.py` | Post-death permanent upgrade shop |
| `src/ui/main_menu.py` | Main menu + settings (resolution, fullscreen, music volume) |
| `src/ui/run_summary.py` | Post-run statistics summary screen |
| `src/ui/passive_swap.py` | Passive swap screen when all passive slots are full |
| `src/ui/tooltip.py` | Weapon/passive info tooltips |
| `src/ui/weapon_swap.py` | Weapon swap selection screen |
| `src/ui/icons.py` | 35 procedural icon drawings for UI elements |
| `src/ui/debug_menu.py` | Developer debug menu |
| `src/ui/debug_overlay.py` | In-game debug overlay (F3) |

## Enemy Types (by Zone)

### Zone 1 — Wasteland ("The Forest")
- **cyber_rat** — tiny, fast melee, erratic jitter movement
- **cyber_raccoon** — medium melee, sidestep-dodges when hit
- **mega_cyber_deer** *(sub-boss, wave 5)* — large charging boss, antler slam special
- **d_lack** — ranged, shoots cyan bullets (renamed from dalek)
- **charger** — charges in a straight line
- **shielder** — has a damage-absorbing shield
- **spitter** — longer-range acid ranged attacker, kites away from player
- **iron_sentinel** *(mini-boss)* — 3-way spread shots, missile_barrage special
- **warlord_kron** *(big boss)* — 5-way spread shots, bleed_storm special

### Zone 2 — City ("Ruined Metropolis")
- **cyber_zombie** — slow, high HP melee
- **cyber_dog** — fast melee, low HP
- **drone** — ranged flyer
- **cultist** — ranged, applies fire on hit
- **shambler** — slow, large AOE melee
- **preacher** *(mini-boss)* — 3-way fire spread shots, fire_ring special
- **eldritch_horror** *(big boss)* — 7-shot fan, eldritch_pull special

### Zone 3 — Abyss ("The Abyss")
- **specter** — void-touched wraith, melee, applies bleed (moved from zone 1)
- **void_wisp** — ranged, fast, low HP
- **rift_walker** — teleports near player
- **mirror_shade** — copies player movement
- **gravity_warden** — gravity-pull AOE
- **null_serpent** — long-range, high HP
- **architect** *(mini-boss)* — 3-way void bolts, void_cage special
- **nexus** *(big boss)* — 9-shot ring, reality_collapse special

## Boss Phase 2 (Enrage at 40% HP)
- Speed +40%, all attack cooldowns −45%
- Spread shot count increases per phase
- Secondary special ability activates (unique per boss type)
- Call `sounds.start_boss_music(zone)` on boss spawn, `sounds.stop_boss_music()` on boss death
- Boss music is cached to `.cache/boss_music_v1.pkl`, keyed by zone name

## Conventions
- All graphics are drawn with `pygame.draw.*` — no image files
- All audio is generated with `pygame.sndarray` — no sound files
- Weapon definitions are dicts in `weapons.py` with keys: `name`, `damage_mult`, `range`, `cooldown`, `duration`, `sweep_deg`, `projectile` (bool), `type` (melee/ranged/orbiter/grenade)
- Passives are tracked in `player.passives` list of strings. Check with `"name" in self.player.passives`
- Enemy types are defined in `enemy.py` ENEMY_TYPES dict at the top
- Coins: `player.coins` int, incremented in `game_actions.py` on enemy death (25% chance, 100% from bosses)
- XP drops as collectible pickup orbs (green, 12s lifetime) — handled by `pickups.py`
- Zone constants live in `zones.py`: `ZONE_ORDER = ["wasteland", "city", "abyss"]`
- When adding a passive: define in upgrade pool (boss_chest.py or levelup.py), then implement the check in game.py `_update()`, player.py, or combat.py

## Testing
- Quick compile check: `python -c "from src.game import Game; print('OK')"`
- Run game: `python main.py`
- No test framework — verify by running the game
