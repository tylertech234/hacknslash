# Changelog

All notable changes to Cyber Survivor are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

---

## [0.9.1] — 2026-04-03 — Early Access Launch

### Added
- **Super Skill system** — right-click when Energy bar is full fires a class-unique ability
  - Ranger: EMP Arrow — explosive charged shot, huge AOE blast on impact
  - Knight: Blade Storm Nova — 12 daggers erupt in a 360° ring
  - Jester: Chaos Eruption — 6 grenades launched at every 60°
- **Energy bar** — horizontal gold/amber bar under HP; fills on kills; fire-ripple effect; "SUPER READY" flash when charged
- **Vertical XP bar** — class-themed bar (bottom-left, 1/3 screen height); cyan=Knight, green=Ranger, purple=Jester; pulse glow near full
- **Compendium system** — enemy bestiary with procedural monster art, unlock-on-first-kill, inspect view
- **Toast notifications** — slide-in achievement-style toasts for first-kill unlocks
- **Zone 3 — The Abyss** — 8 enemy types including Specter, Void Wisp, Rift Walker, Mirror Shade, Gravity Warden, Null Serpent; bosses Architect and Nexus
- **Portal menu** — between-zone menu with frozen background (no flashing); includes Compendium access
- **Run Summary screen** — post-run statistics including per-weapon damage, DPS, kills, and upgrade history
- **Persistent legacy upgrades** — 6 permanent upgrades that survive between runs (JSON save)
- **Boss HP bars** — stacked, color-coded (red=main boss, gold=mini-boss); name+HP inside bar
- **Hazard system** — zone-specific environmental hazards (acid puddles, dust storms, void rifts)
- **Campfire** with proximity lighting in Zone 1
- **3 playable classes** — Knight, Ranger (archer), Jester; each with unique starting weapon, passives, and super skill
- **D-Lek faction** — d_lek, emperors_elite_guard, Supreme D-Lek boss (Zone 1 end boss)
- **Dynamic boss music** — per-zone boss tracks procedurally generated and cached
- **Weapon balance** — 14+ weapons across melee/ranged/orbiter/grenade types; burst_crossbow and explosive_crossbow for Ranger

### Changed
- Portal menu no longer flashes the live game world — uses a frozen screenshot as background
- Boss HP bars no longer overlap when multiple bosses are alive
- Level-up card descriptions word-wrap at 34 characters (2-line max)
- Incoming damage global multiplier set to 1.45× for more intense play
- Knight knockback bonus applied; Jester base speed +50%; Ranger renamed from Archer

### Weapon Tuning (0.9.1)
- Spear: damage 1.1 → 1.3
- Gravity Maul: damage 2.8 → 3.5
- Pie Launcher: damage 1.5 → 2.2
- Pulse Rifle: cooldown 150ms → 220ms

### Technical
- PyInstaller single-folder Windows build (~63 MB)
- Per-run statistics logged to `logs/runs.jsonl`
- Off-screen culling for enemy rendering; lighting steps reduced 8→5
- Surface cache on enemy draw methods for performance

---

## [0.9.2] — 2026-04-03

### Added
- **Weapon Arsenal screen** — persistent weapon unlock browser per class; unlocked weapons survive between runs
- **3 new weapons** for Ranger: Burst Crossbow (3-bolt burst), Explosive Crossbow (splash on impact, 60px radius), added to level-up pools
- **Corpse crumble animation** — enemies leave a fading flattened body with spark bleed-out dots on death
- **GitHub Actions CI** — parallel Windows / Linux / macOS builds using PyInstaller; artifacts uploaded automatically
- **itch.io publishing** via butler — `windows-stable` channel updated on every merge to main and tag push

### Changed
- Enemy HP increased (first pass — larger, more satisfying fights)
- Player base stats tuned: incoming damage multiplier raised to 1.45×
- Magnetic field passive pickup radius adjusted
- Hit feedback improved: more visible flash and impact response
- Level-up and chest upgrade pools expanded with additional weapon entries

### Technical
- `build.yml` reads `VERSION` from `settings.py`; injects Supabase secrets at build time
- `cyber_survivor.spec` PyInstaller spec file committed for reproducible builds

---

## [0.9.3] — 2026-04-04

### Added
- Nothing new — focused on balance, stability, and polish

### Changed
- **+25% HP** across all 25 enemy types for longer, more engaging fights
- Controls hint text in main menu moved below gameplay elements (prevents overlap at 1280×720)
- Game is now **download-only** — web/HTML5 build removed after extensive testing; desktop builds are the sole targets

### Fixed
- **Exe crash** `ModuleNotFoundError: No module named 'urllib'` — removed urllib/http/email from PyInstaller excludes
- **Exe crash** `ModuleNotFoundError: No module named 'xml'` — removed xml and setuptools from PyInstaller excludes
- **`AttributeError: 'SoundManager' object has no attribute '_boss_channel'`** on character select — added `hasattr` guard in `stop_boss_music()`
- **Dev mode persisting across runs** — `dev_options` is now explicitly reset to `False` on profile load
- **Leaderboard showing "not configured"** in release builds — CI now injects `SUPABASE_URL` / `SUPABASE_ANON_KEY` secrets before PyInstaller build
- **CI secrets injection condition** — removed `if: env.SUPABASE_URL` guard which always evaluated false (env var only accessible inside the step)

### Technical
- CI: `publish-itch` job now runs on merge to main, manual dispatch, and tag push (previously missed merges)

---

## [Unreleased]

### Added
- **Save data in user profile directory** — all saves, caches, screenshots, and logs now write to `%APPDATA%/CyberSurvivor` (Windows) or `~/.cyber_survivor` (Linux/macOS); no more files written to the install folder

---

## [0.9.11] — 2026-04-06

### Added
- **Procedural backgrounds** for itch.io and trailer
- **Automated trailer generator** (`make_trailer.py`) and gameplay assembler (`assemble_trailer.py`)
- **OBS/ffmpeg workflow** for easy gameplay capture and trailer creation
- **Numerous polish and bugfixes** since 0.9.3

### Changed
- Updated main menu and itch.io banners
- Improved trailer and gameplay video workflow

### Fixed
- Various minor bugs and stability improvements
  - Affected: display settings, player profiles, compendium, legacy saves, run logs, screenshots, procedural music cache

### Performance (zero visual quality change)
- Low-HP vignette surface cached by intensity bucket — rebuilt only ~10 times total (was rebuilding 100+ lines every frame)
- Damage vignette surface cached by alpha bucket — ~20 rebuilds per hit instead of one full-screen surface per frame
- Energy bar flame: single `SRCALPHA` surface instead of ~44 tiny 5×1 surfaces per frame
- Passive slot glow: `set_alpha()` on plain surface instead of per-slot `SRCALPHA` allocation
- Dash trail: single surface reused across 4 ghost positions (was allocating 4 new surfaces per frame while dashing)
- Enemy corpse: surface built once at death, faded with `set_alpha()` over 1.8 seconds

_Planned for future:_
- Sound settings persist across sessions
- Controller support
- Additional zone themes
