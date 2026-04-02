# Hack 'n Slash

A 2D top-down hack and slash game built with Python + Pygame.

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| WASD / Arrow Keys | Move |
| Space / J / Left Click | Attack |
| Shift / K | Dash (i-frames) |
| R | Restart (on death) |
| ESC | Quit |

## Project Structure

```
hacknslash/
├── main.py                  # Entry point
├── requirements.txt
├── assets/
│   ├── sprites/
│   ├── sounds/
│   └── fonts/
└── src/
    ├── settings.py          # All tunable constants
    ├── game.py              # Main game loop & state
    ├── entities/
    │   ├── player.py        # Player movement, attacks, leveling
    │   └── enemy.py         # Enemy AI, wandering, aggro
    ├── systems/
    │   ├── combat.py        # Hit detection, damage, XP
    │   ├── spawner.py       # Wave-based enemy spawning
    │   ├── game_map.py      # Tile map rendering
    │   └── camera.py        # Smooth-follow camera
    └── ui/
        └── hud.py           # HP bar, XP bar, wave counter, game over
```

## Features

- Wave-based enemy spawning with increasing difficulty
- Melee attack with knockback and damage numbers
- Dash with invincibility frames
- XP / leveling system with stat scaling
- Smooth camera follow
- Game over / restart flow
