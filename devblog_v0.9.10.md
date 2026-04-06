# Cyber Survivor v0.9.10 — Patch Notes

**Hey everyone!** Big update just dropped. This one touches a lot — UI overhaul, leaderboard rework, boss balance, a new laser attack, and a proper victory credits sequence. Here's the full rundown.

---

## 🎨 Title Screen & Character Select Overhaul

- **Completely redesigned title screen** with animated enemy parade — real enemies now chase a decoy player across the background
- **Character select cards** cleaned up — weapon/passive info is now consistently aligned across all three classes, no more text floating at different heights
- Card text properly wraps with pixel-accurate line breaks (no more clipping)
- Weapon labels are class-colored for easier scanning

## 🏆 Leaderboard Rework

- **Two-tier ranking system** — Champions (fastest victory runs) and Contenders (highest damage dealt) are now fetched and displayed separately
- Leaderboard panel is responsive to screen size instead of hardcoded dimensions
- Players with invalid or missing run times no longer appear in the Champions tier
- Panel sizing: `min(860, screen_width - 40)` × `min(620, screen_height - 40)`

## 💀 Killed By Tracking

- The game now tracks **what killed you** — environmental hazards, status effect DoT, entropic decay, and enemy attacks all record a `killed_by` value
- This feeds into run analytics and will show on your death summary
- New `analytics.py` CLI tool for inspecting run data with proper weapon equip-time detection

## 🤖 Smart Default Names

- New players get a procedurally generated display name instead of a blank field
- Names are fun, game-themed, and unique per profile

## ⚔️ Boss Balance — Iron Sentinel & Supreme D-Lek

These two were nearly impossible for melee classes. That's fixed now.

### Iron Sentinel

- **Mixed approach/retreat AI** — 40% chance to rush toward the player for 800-1500ms instead of always running away. Melee classes can actually hit it now
- **Wind-up vulnerability window** — 900ms freeze with a pulsing yellow flash and red "!" before it fires a volley. This is your cue to rush in and smack it
- **Takes damage from its own toxic pools** — acid puddles and toxic gas now have `hits_enemies = True`, so the sentinel poisons itself
- Flee speed reduced from 1.8× to 1.0× multiplier

### Supreme D-Lek

- Same approach/retreat AI and wind-up vulnerability as Iron Sentinel
- **NEW: Laser Beam Attack** — charges for 1.2 seconds (red aim line + body shake), then fires an 800ms beam that deals continuous fire damage
  - 3-layer visual: orange outer glow → gold core → white-hot center
  - 30px wide beam, 500px range, ticks damage every 100ms
  - Applies fire status on hit
  - 8 second cooldown between beams

## 🎬 Victory Credits Screen

Beat the final boss in The Abyss? You now get a **proper credits roll** with:

- Procedural **fireworks** — colorful bursts with gravity-affected sparks, spawning continuously
- Scrolling credit lines on a dark background
- Click or press Enter to continue to the run summary when you're ready

After credits, you'll still see the full run summary and legacy shop as usual.

## 🔧 Other Fixes

- Parade enemies on the title screen now spawn at proper screen-relative positions instead of hardcoded Y values
- Parade respawns use a fixed timestamp cooldown instead of re-rolling every frame
- `killed_by` column in Supabase schema now has `NOT NULL DEFAULT ''`
- Weapon equip time analytics uses key-name distinction instead of magnitude heuristic

---

## 🖥️ Platform Notes

- **Windows** — Fully tested, this is the primary build
- **Mac & Linux builds are now available!** I haven't been able to test them myself yet, so if you grab one and something doesn't work, **please let me know** — bug reports are super helpful
- **Controller support is in** but hasn't been fully tested yet. If you try it and something feels off or doesn't work, drop me a message

---

*Thanks for playing Cyber Survivor. Go out and make a difference.*
