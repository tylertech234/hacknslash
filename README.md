# Cyber Survivor

A 2D top-down hack-and-slash survival game built with Python + Pygame. No external assets — all graphics are drawn with code, all sounds are procedurally generated.

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| WASD / Arrow Keys | Move |
| Space / J / E / Left Click | Attack / Confirm |
| Shift / K | Dash (i-frames) |
| Right Mouse (hold → release) | Super Skill (when Energy full) |
| Mouse | Aim direction |
| Esc / P | Pause menu |
| 1–5 | Select upgrades |
| R | Restart (on death) |

## Features

- **3 Zones** — Wasteland (The Forest), City (Ruined Metropolis), Abyss — each with unique enemies, hazards, and boss music
- **21 Enemy Types** — 7 per zone including mini-bosses and a big boss with phase-2 enrage
- **3 Character Classes** — Knight (heavy melee), Ranger (fast ranged), Jester (chaotic fun)
- **Super Skills** — right-click to unleash a class-unique ability when your Energy bar is full (Knight: Blade Storm Nova, Ranger: EMP Arrow, Jester: Chaos Eruption)
- **Energy Bar** — fills +10 per kill, +40 per boss kill; resets on super use
- **18+ Weapons** — swords, axes, throwing daggers, banana boomerangs, confetti grenades, burst crossbow, explosive crossbow, orbiters, and more
- **Boss Phase 2** — at 40% HP bosses enrage: +40% speed, −45% cooldowns, enhanced spread shots, and unique secondary specials
- **Unique boss music per zone** — procedurally generated and cached on first play
- **Wave-based combat** with escalating difficulty (+12% HP, +8% damage, +3% speed per wave)
- **Parry system** — melee attacks deflect enemy projectiles mid-swing
- **Coin drops** — 25% chance from enemies, 100% from bosses; shown in HUD
- **XP pickup orbs** — XP drops as collectible green orbs with a 12-second lifetime
- **Zone hazards** — acid puddles, dust storms, toxic gas, void rifts, and more
- **Passive abilities** — lifesteal, chain lightning, vampiric strike, thorns, shield matrix, second wind, explosive kills, and more
- **Compendium** — in-game bestiary; enemy entries unlock on first kill, with procedural art and inspect view
- **Portal menu** — between-zone screen to review stats, browse the Compendium, or continue
- **Animated custom cursor** — class-themed procedural crosshair that rotates and contracts on click
- **Roguelite persistence** — Legacy Points and 6 permanent upgrades that carry between runs
- **Dynamic lighting** — darkness scales enemy stats and XP rewards
- **Procedural audio** — two-layer 8-bit chiptune with calm/combat crossfade and generated SFX
- **Pause menu** — Esc/P during play: Resume, Settings, Quit to Menu
- **Settable resolution** — defaults to native desktop, changeable in settings
- **Player death animation** — 2.2-second zoom + vignette → YOU DIED screen
- **Unique enemy death animations** — 8 styles by enemy type
- **Minimap** — lightweight full-map overlay in the HUD corner; shows all enemy positions as colored dots
- **Status effects** — fire, bleed, poison, slow with visual particles
- **Boss chests** — powerful upgrades from defeated bosses
- **Campfire healing** between waves
- **Floating damage numbers** with scale-pop and outlines
- **Download-only desktop game** — Windows, Linux, and macOS builds; no browser required
- **Save data in user profile** — all saves written to `%APPDATA%/CyberSurvivor` (Windows) or `~/.cyber_survivor` (Linux/macOS); safe to move or reinstall

## Project Structure

```
hacknslash/
├── main.py                    # Entry point
├── requirements.txt
└── src/
    ├── settings.py            # All tunable constants
    ├── game.py                # Main game loop & state orchestrator
    ├── entities/
    │   ├── player.py          # Player: 3 classes, movement, attacks, coin tracking
    │   └── enemy.py           # 21 enemy types across 3 zones with boss enrage
    ├── systems/
    │   ├── combat.py          # Hit detection, damage, XP rewards
    │   ├── spawner.py         # Wave spawning, patterns, boss waves, scaling
    │   ├── projectiles.py     # Bullets, daggers, orbiters, grenades
    │   ├── weapons.py         # Weapon definitions and drawing
    │   ├── pickups.py         # Item drops: coins, XP orbs, heals
    │   ├── boss_chest.py      # Boss chest rewards
    │   ├── compendium.py      # Enemy unlock tracking — first-kill logic, JSON save
    │   ├── game_actions.py    # Death processing & projectile firing helpers
    │   ├── legacy.py          # Roguelite persistence (JSON save)
    │   ├── environment.py     # Trees, rocks, fruit trees
    │   ├── campfire.py        # Between-wave healing
    │   ├── lighting.py        # Dynamic darkness system
    │   ├── animations.py      # Particles, screen shake, death effects
    │   ├── sounds.py          # Procedural SFX + chiptune + zone boss music
    │   ├── status_effects.py  # DOT effects and debuffs
    │   ├── camera.py          # Smooth-follow camera
    │   ├── game_map.py        # Tile-based world
    │   ├── zones.py           # Zone definitions (wasteland / city / abyss)
    │   ├── atmosphere.py      # Atmospheric visual effects per zone
    │   ├── hazards.py         # Zone-specific hazards
    │   ├── portal.py          # Zone transition portal
    │   └── run_stats.py       # Per-run statistics tracking
    └── ui/
        ├── hud.py             # HP/XP bars, boss HP, coins, wave info, vignette
        ├── minimap.py         # Lightweight full-map enemy tracker — colored dots overlay
        ├── levelup.py         # Level-up upgrade selection
        ├── charselect.py      # Character class picker
        ├── cursor.py          # Animated procedural crosshair — class-themed
        ├── legacy_screen.py   # Post-death permanent upgrade shop
        ├── main_menu.py       # Main menu + settings (resolution, fullscreen, music)
        ├── portal_screen.py   # Between-zone portal menu (Continue / Summary / Compendium)
        ├── run_summary.py     # Post-run statistics summary screen
        ├── compendium_screen.py # Compendium browser with procedural monster art
        ├── passive_swap.py    # Passive swap screen when all slots are full
        ├── toast.py           # Slide-in achievement-style toast notifications
        ├── tooltip.py         # Weapon/passive info tooltips
        ├── weapon_swap.py     # Weapon swap selection screen
        ├── icons.py           # 35 procedural icon drawings
        ├── debug_menu.py      # Developer debug menu
        ├── debug_overlay.py   # In-game debug overlay (F3)
        └── arsenal_screen.py  # Persistent weapon unlock browser per class
```

## Gameplay Guide

See [GAMEPLAY.md](GAMEPLAY.md) for a full guide covering classes, weapons, parry, enemies, zones, boss mechanics, and tips.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and how to make your first contribution.
