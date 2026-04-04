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

## [Unreleased]

_Planned for future updates:_
- Web build (pending pygame/numpy WebAssembly compatibility)
- macOS / Linux builds via GitHub Actions CI
- Sound settings persist across sessions
- Controller support
- Additional zone themes
