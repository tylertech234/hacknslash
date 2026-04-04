# Contributing to Hack 'n Slash

Welcome! This guide will take you from zero to making your first contribution — no prior open-source experience needed.

---

## Prerequisites

You'll need these installed on your machine:

| Tool | Version | What it does |
|------|---------|-------------|
| **Python** | 3.10+ | The programming language the game is written in |
| **Git** | Any recent | Version control — tracks changes to the code |
| **A code editor** | VS Code recommended | Where you write and edit code |

### Installing Python

1. Go to [python.org/downloads](https://www.python.org/downloads/) and download the latest 3.x version
2. **Important**: During install, check the box that says **"Add Python to PATH"**
3. Open a terminal and verify: `python --version`

### Installing Git

1. Go to [git-scm.com/downloads](https://git-scm.com/downloads) and install for your OS
2. Verify: `git --version`

---

## Getting the Code

### 1. Fork the repository

Click the **"Fork"** button at the top-right of the GitHub repo page. This creates your own copy.

### 2. Clone your fork

```bash
git clone https://github.com/YOUR-USERNAME/hacknslash.git
cd hacknslash
```

### 3. Set up a virtual environment (recommended)

```bash
python -m venv .venv
```

Activate it:
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **Windows (CMD):** `.venv\Scripts\activate.bat`
- **Mac/Linux:** `source .venv/bin/activate`

You'll see `(.venv)` in your terminal prompt when it's active.

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

This installs **Pygame** and **NumPy** (required for procedural audio generation).

### 5. Run the game

```bash
python main.py
```

If you see the character select screen, you're good to go!

---

## Project Structure

```
hacknslash/
├── main.py                  # Entry point — run this to play
├── requirements.txt         # Python dependencies
├── src/
│   ├── settings.py          # All tunable constants (speeds, HP, sizes, colors)
│   ├── game.py              # Main loop — ties everything together
│   ├── entities/            # Things in the world
│   │   ├── player.py        # Player movement, attacks, leveling, 3 classes (knight/ranger/jester)
│   │   └── enemy.py         # Enemy AI, 21 types across 3 zones
│   ├── systems/             # Game mechanics
│   │   ├── combat.py        # Hit detection, damage numbers, XP
│   │   ├── spawner.py       # Wave spawning, patterns, boss waves, difficulty scaling
│   │   ├── projectiles.py   # Enemy bullets + player daggers, orbiters, grenades
│   │   ├── weapons.py       # 18+ weapons across 3 classes, drawing & stats
│   │   ├── pickups.py       # Item drops (heal, stat boosts, apples)
│   │   ├── boss_chest.py    # Boss chest drops and reward selection screen
│   │   ├── compendium.py    # Enemy unlock tracking — first-kill logic, JSON save
│   │   ├── game_actions.py  # Enemy death processing, coin drops, projectile helpers
│   │   ├── environment.py   # Trees, rocks, bushes, fruit trees
│   │   ├── campfire.py      # Healing campfire between waves
│   │   ├── lighting.py      # Dynamic darkness overlay and light sources
│   │   ├── animations.py    # Particles, death bursts, screen shake
│   │   ├── sounds.py        # Procedurally generated SFX + 2-layer chiptune + boss music
│   │   ├── status_effects.py# Fire, bleed, poison, slow effects
│   │   ├── camera.py        # Smooth-follow camera
│   │   ├── game_map.py      # Tile-based world grid
│   │   ├── zones.py         # Zone definitions (wasteland / city / abyss)
│   │   ├── atmosphere.py    # Atmospheric visual effects per zone
│   │   ├── hazards.py       # Zone-specific hazards (acid, storms, void rifts)
│   │   ├── portal.py        # Zone transition portal entity
│   │   ├── legacy.py        # Roguelite persistence (JSON save)
│   │   └── run_stats.py     # Per-run statistics tracking
│   └── ui/                  # User interface
│       ├── hud.py           # HP/XP bars, wave info, boss HP bar, danger vignette
│       ├── radar.py         # AVP-style motion tracker
│       ├── levelup.py       # Level-up upgrade selection
│       ├── charselect.py    # Character class picker
│       ├── cursor.py        # Animated procedural crosshair — class-themed
│       ├── main_menu.py     # Main menu + settings
│       ├── portal_screen.py # Between-zone portal menu (Continue/Summary/Compendium)
│       ├── run_summary.py   # Post-run statistics summary screen
│       ├── compendium_screen.py # Compendium browser with procedural monster art
│       ├── legacy_screen.py # Post-death permanent upgrade shop
│       ├── passive_swap.py  # Passive swap screen when all slots are full
│       ├── toast.py         # Slide-in achievement-style toast notifications
│       ├── tooltip.py       # Weapon/passive info tooltips
│       ├── weapon_swap.py   # Weapon swap selection screen
│       ├── icons.py         # 35 procedural icon drawings
│       ├── debug_menu.py    # Developer debug menu
│       └── debug_overlay.py # In-game debug overlay (F3)
└── assets/                  # Empty placeholder folders (all art/sound is procedural)
```

### How the code flows

```
main.py
  └─> Game.__init__()        # Set up Pygame window, create all systems
        └─> Game.run()       # Main loop (runs 60 times per second):
              ├─> _handle_events()   # Read keyboard/mouse input
              ├─> _update(dt, now)   # Move everything, check hits, spawn waves
              └─> _draw()           # Render everything to screen
```

**Key concept**: `game.py` is the orchestrator. It doesn't contain game logic itself — it calls methods on the systems. For example, `self.combat.process_player_attack(...)` handles hit detection, `self.spawner.update(...)` manages waves.

---

## How to Make Changes

### Step 1: Create a branch

Always work on a branch, never directly on `main`:

```bash
git checkout -b my-feature-name
```

Use descriptive names like `add-ice-enemy`, `fix-boss-hp-bar`, `buff-jester-weapons`.

### Step 2: Make your changes

Here's where to edit based on what you're doing:

| I want to... | Edit this file |
|---|---|
| Change player/enemy stats, speeds, sizes | `src/settings.py` |
| Add a new weapon | `src/systems/weapons.py` |
| Add a new enemy type | `src/entities/enemy.py` + `src/systems/spawner.py` |
| Change boss wave behavior | `src/systems/spawner.py` |
| Add a new sound effect | `src/systems/sounds.py` |
| Add a new pickup type | `src/systems/pickups.py` |
| Change the HUD | `src/ui/hud.py` |
| Add a new status effect | `src/systems/status_effects.py` |
| Add a new passive ability | `src/systems/boss_chest.py` or `src/ui/levelup.py` (define) + `src/game.py` or `src/systems/game_actions.py` (implement) |
| Add a roguelite upgrade | `src/systems/legacy.py` + `src/ui/legacy_screen.py` |
| Change how damage/combat works | `src/systems/combat.py` |
| Add/edit zone definitions | `src/systems/zones.py` |
| Add zone-specific hazards | `src/systems/hazards.py` |
| Modify the portal/between-zone menu | `src/ui/portal_screen.py` + `src/systems/portal.py` |
| Edit run statistics tracking | `src/systems/run_stats.py` + `src/ui/run_summary.py` |
| Edit the compendium bestiary | `src/systems/compendium.py` + `src/ui/compendium_screen.py` |
| Change the cursor appearance | `src/ui/cursor.py` |

### Step 3: Test your changes

```bash
python main.py
```

Play through a few waves. Check:
- Does the game start without errors?
- Does your change work as expected?
- Did you break anything else? (Try all 3 character classes)

### Step 4: Commit and push

```bash
git add .
git commit -m "Add ice enemy with slow-on-hit mechanic"
git push origin my-feature-name
```

Write clear commit messages that explain **what** you changed and **why**.

### Step 5: Open a Pull Request

Go to the original repo on GitHub and click **"New Pull Request"**. Select your branch and describe your changes.

---

## Common Tasks (With Examples)

### Adding a new weapon

1. Open `src/systems/weapons.py`
2. Add a new entry to the `WEAPONS` dict:

```python
"plasma_lance": {
    "name": "Plasma Lance",
    "damage_mult": 1.3,
    "range": 80,
    "cooldown": 500,
    "duration": 200,
    "sweep_deg": 30,
    "blade_color": (100, 200, 255),
    "trail_color": (50, 150, 200),
    "desc": "Long-range energy thrust",
    "class": "knight",  # which class can use it
},
```

For a **ranged weapon**, add projectile keys:

```python
"laser_pistol": {
    "name": "Laser Pistol",
    "damage_mult": 0.9,
    "range": 40,
    "cooldown": 400,
    "duration": 100,
    "sweep_deg": 30,
    "blade_color": (255, 50, 50),
    "trail_color": (255, 100, 100),
    "desc": "Rapid energy shots",
    "projectile": True,       # marks this as ranged
    "proj_speed": 9.0,        # pixels per frame
    "proj_lifetime": 800,     # ms before it disappears
    "proj_count": 1,          # number of projectiles per shot
    "proj_visual": "bolt",    # visual style: dagger/arrow/bolt/pellet
    "piercing": False,        # True = passes through enemies
    "class": "archer",
},
```

3. The weapon will automatically appear in level-up options for that class.

### Adding a new sound effect

1. Open `src/systems/sounds.py`
2. Add a generator method (look at existing ones like `_make_swing` for the pattern)
3. Register it in `_generate_all()`: `self.sounds["my_sound"] = self._make_my_sound()`
4. Play it anywhere: `self.sounds.play("my_sound")`

### Tweaking game balance

Almost all numbers live in `src/settings.py`. Tweak and test:

```python
WAVE_GROWTH = 5          # Enemies added per wave (higher = harder)
ENEMY_SPEED = 2.4        # Base enemy movement speed
PLAYER_ATTACK_DAMAGE = 20 # Base player damage
DROP_CHANCE = 0.40       # 40% chance enemies drop items
```

Wave scaling (per-wave HP/damage multipliers) is in `src/systems/spawner.py` inside `start_next_wave()`.

---

## Code Conventions

- **No external assets**: All graphics are drawn with Pygame primitives (circles, rects, lines). All sounds are procedurally generated with math. This is intentional — the game runs anywhere Python + Pygame works with zero asset files.
- **Settings are constants**: Tunable values go in `settings.py`, not hardcoded in logic.
- **Systems are modular**: Each system (combat, spawning, lighting, etc.) is its own file with its own class. They communicate through `game.py`.
- **`dt` is in milliseconds**: `dt = clock.tick(60)` returns ms since last frame. `now = pygame.time.get_ticks()` is total ms since start.
- **Coordinates are world-space**: Player, enemies, and projectiles use world coordinates. The camera converts to screen coordinates for drawing.

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'pygame'"
```bash
pip install pygame
```

### "ModuleNotFoundError: No module named 'src'"
Make sure you're running from the project root:
```bash
cd hacknslash
python main.py
```

### Game runs but no sound
Pygame's mixer sometimes fails on certain audio devices. This won't crash the game — sound just won't play. Try restarting or check your audio output device.

### Game feels laggy
The game is locked to 60 FPS. If it drops below that, you may see stuttering. Close other heavy applications. The lighting system (darkness overlay) is the most expensive operation.

---

## What's a Good First Contribution?

Look for things tagged as **"good first issue"** on GitHub, or try one of these:

- **Tune balance numbers** in `settings.py` — make a wave harder/easier and explain why
- **Add a new weapon** with an interesting mechanic
- **Add a new sound effect** for something that's currently silent
- **Improve an enemy drawing** — make the Daleks or Wraiths look cooler
- **Add a new pickup type** like temporary invincibility or double XP
- **Write a new spawn pattern** in `spawner.py` (look at `_spawn_ring` for inspiration)

---

## Questions?

Open an issue on GitHub if you're stuck. No question is too basic.
