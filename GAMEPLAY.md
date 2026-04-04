# Gameplay Guide

A complete guide to everything in the game — classes, weapons, enemies, mechanics, and tips.

---

## Controls

| Action | Keys |
|--------|------|
| Move | W / A / S / D or Arrow Keys |
| Attack / Confirm | Space, J, E, or Left Mouse Click |
| Dash | Shift or K |
| Super Skill | Right Mouse (hold → release, when Energy is full) |
| Pause | Esc or P |
| Aim | Move the mouse — your character always faces the cursor |
| Select chest reward | Number keys 1–5 |

---

## Choosing a Class

You pick one of three classes at the start. Each has different stats, starting weapons, and built-in passive abilities.

### Knight

Heavy armor, devastating melee. Born to fight up close.

- **+30 HP**, **+5 Damage**
- **Starting Weapon:** Sword
- **Passives:**
  - *Melee Lifesteal* — Recover 5 HP every time you kill an enemy with a melee weapon
  - *Armor Plating* — Take 20% less damage from all sources

### Ranger

Fast and deadly at range. Keep your distance.

- **+1.0 Speed**, **-10 HP**
- **Starting Weapon:** Throwing Dagger
- **Passives:**
  - *Crit Shots* — 20% chance to deal double damage with projectiles
  - *Evasion* — 15% chance to completely dodge any incoming attack

### Jester

Chaos incarnate. Funny weapons, unpredictable power.

- **+0.5 Speed**
- **Starting Weapon:** Rubber Chicken
- **Passives:**
  - *Lucky Crits* — 15% chance to deal triple damage
  - *Confetti Burst* — Enemies explode in a colorful AOE burst when they die

---

## Weapons

### Melee Weapons

Melee weapons swing in an arc in front of you. Wider sweep angles hit more enemies per swing.

| Weapon | Damage | Range | Cooldown | Sweep Arc | Notes |
|--------|--------|-------|----------|-----------|-------|
| Sword | 1.0x | 60 | 400ms | 120° | Balanced starter |
| Battle Axe | 1.6x | 50 | 650ms | 90° | Hard-hitting, narrow |
| Spear | 1.3x | 90 | 500ms | 40° | Long reach, precise |
| War Hammer | 2.2x | 55 | 900ms | 160° | Slow, devastating |
| Plasma Blade | 1.4x | 65 | 350ms | 130° | Fast and strong |
| Gravity Maul | 3.5x | 60 | 1000ms | 180° | Highest damage, very slow |
| Rubber Chicken | 0.8x | 55 | 350ms | 140° | Jester starter, fast |
| Joy Buzzer | 1.3x | 35 | 500ms | 360° | Short range, hits all around you |

Damage shown is a multiplier on your base damage stat.

### Ranged Weapons (Ranger)

| Weapon | Damage | Cooldown | Projectiles | Speed | Lifetime | Notes |
|--------|--------|----------|-------------|-------|----------|-------|
| Throwing Dagger | 1.0x | 350ms | 1 | 8.0 | 900ms | Precision single throw |
| Cyber Bow | 1.8x | 550ms | 1 | 11.0 | 1500ms | **Pierces through enemies** |
| Pulse Rifle | 0.7x | 220ms | 1 | 10.0 | 700ms | Rapid fire energy bolts |
| Scatter Shot | 0.9x | 600ms | 5 | 7.0 | 600ms | Wide 5-bolt spread |
| Tri-Burst Crossbow | 1.1x | 480ms | 3 | 10.5 | 800ms | 3-bolt burst, tight spread |
| Explosive Crossbow | 2.2x | 900ms | 1 | 7.0 | 700ms | Explodes on impact, 60px splash |

### Ranged Weapons (Jester)

| Weapon | Damage | Cooldown | Type | Notes |
|--------|--------|----------|------|-------|
| Banana-Rang | 0.9x | 450ms | Orbiter | Launches out, returns, orbits you (max 3) |
| Pie Launcher | 2.2x | 700ms | Projectile | Thrown cream pie — no AoE |
| Confetti Grenade | 2.8x | 600ms | Grenade | 60px splash radius, 600ms fuse |

### Orbiting Weapons (Knight: Blade Barrier / Jester: Banana-Rang)

These unique weapons launch outward, then come back and orbit around you dealing continuous damage.

- **Max orbiters:** 3 at a time (throwing a 4th removes the oldest)
- **Launch phase:** Flies out for 350ms or until 140px away, speed decays over time
- **Return phase:** Homes back toward you
- **Orbit phase:** Circles at 55px radius, hitting nearby enemies
- **Hit cooldown:** Can hit the same enemy every 500ms

### Grenade Mechanics

Grenades (Confetti Grenade, Explosive Crossbow) explode on enemy contact or after their fuse expires.

- **Splash radius:** 60px
- **Damage falloff:** 100% at center, down to 30% at the edge

---

## Parry

**You can deflect enemy bullets by swinging a melee weapon into them.**

How it works:
1. You must be using a **melee weapon** (any non-projectile weapon)
2. An enemy fires a bullet at you
3. **Attack toward the bullet** — if your swing arc overlaps the bullet, it's destroyed
4. You'll see a burst of cyan sparks and hear a parry sound

Key details:
- The parry window lasts the **entire duration of your attack swing** (200–450ms depending on weapon)
- You can parry **multiple bullets in a single swing**
- There is **no separate parry button** — just attack into the bullets
- Faster weapons (Rubber Chicken at 200ms, Plasma Blade at 180ms) have shorter parry windows but can swing again sooner
- Slower weapons (Gravity Maul at 450ms, War Hammer at 400ms) give you a larger parry window per swing

**Tip:** Weapons with wide sweep arcs like the Joy Buzzer (360°) or Gravity Maul (180°) are the easiest to parry with because they cover more area.

---

## Super Skills

Every class has a powerful Super Skill triggered with **Right Mouse** (hold to charge, release to fire) when your **Energy bar** is full.

### Energy Bar
- Displayed horizontally in the HUD (gold/amber bar, above the wave counter)
- Fills **+10 Energy per kill**, **+40 Energy per boss kill**
- Resets to 0 after firing your super
- Maximum energy is 100

### Class Super Skills

| Class | Super Skill | Description |
|-------|-------------|-------------|
| Knight | **Blade Storm Nova** | Fires 12 Thrown Daggers simultaneously in a full 360° ring |
| Ranger | **EMP Arrow** | Launches a high-damage grenade (damage ×15) with a 150px splash radius |
| Jester | **Chaos Eruption** | Launches 6 Confetti Grenades spread evenly in a 360° ring |

**Tip:** Save your super for boss phase 2 (40% HP threshold) — the extra burst can cut through the enrage window.

---

## Zones

The game progresses through three distinct zones. You reach the next zone by defeating the zone's big boss and stepping through the portal that appears.

### Zone 1 — The Forest (Wasteland)
Ancient woods filled with shadow. Hazards: **acid puddles** (wave 3), **dust storms** (wave 5), **solar flares** (wave 7).
- Boss music: military march, D-minor, BPM 168

### Zone 2 — Ruined Metropolis (City)
Shattered skyscrapers. Hazards: **falling debris** (wave 3), **toxic gas** (wave 5), **electrical surges** (wave 7).
- Boss music: glitch industrial, C#-minor, BPM 180

### Zone 3 — The Abyss
Reality fractures. The source of corruption. Hazards: **void rifts** (wave 3), **reality fractures** (wave 5), **entropic decay** (wave 7).
- Boss music: cosmic horror tritone, BPM 85

Zone hazards activate at the listed wave and persist for the rest of that zone.

---

## Portal Menu

After defeating a zone's big boss, a glowing **portal** appears in the arena. Walk into it to open the between-zone Portal Menu:

- **Continue** — step through the portal and travel to the next zone
- **Run Summary** — review your current run stats (kills, damage dealt, bosses killed, etc.)
- **Compendium** — browse the enemy bestiary before pressing on

The portal menu uses a frozen screenshot of the game as its background — no performance cost.

---

## Enemies

Each zone has regular enemies and 2 bosses (mini-boss and big boss). Regular enemy counts vary by zone: 6 in wasteland, 5 in city, 6 in abyss. Bosses enter **Phase 2** when reduced to 40% HP — see the [Boss Phase 2](#boss-phase-2) section below.

### Zone 1 — The Forest

| Enemy | Notes |
|-------|-------|
| **Cyber Rat** | Tiny, fast melee — erratic jitter movement |
| **Cyber Raccoon** | Medium melee — sidestep-dodges when hit |
| **Mega Cyber Deer** *(sub-boss, wave 5)* | Large charging sub-boss — antler slam special |
| **D-Lek** | Ranged — shoots cyan bullets; parallel beam burst attack |
| **Charger** | Charges in a straight line toward the player |
| **Shielder** | Has a damage-absorbing shield; break the shield first |
| **Spitter** | Longer-range acid ranged attacker, kites away from player |
| **Emperor's Elite Guard** | Elite ranged flanking unit |
| **Iron Sentinel** *(mini-boss)* | 3-way spread shots, **missile_barrage** special |
| **Supreme D-Lek** *(big boss)* | 5-way spread shots, **bleed_storm** special; D-Lek Emperor visual |

### Zone 2 — Ruined Metropolis

| Enemy | Notes |
|-------|-------|
| **Cyber Zombie** | Slow, high HP melee |
| **Cyber Dog** | Fast melee, low HP |
| **Drone** | Ranged flyer |
| **Cultist** | Ranged — applies **Fire** on hit |
| **Shambler** | Slow, large AOE melee swing |
| **Street Preacher** *(mini-boss)* | 3-way fire spread shots, **fire_ring** special |
| **Eldritch Horror** *(big boss)* | 7-shot fan spread, **eldritch_pull** special |

### Zone 3 — The Abyss

| Enemy | Notes |
|-------|-------|
| **Specter** | Void-touched wraith melee — applies **Bleed** on hit |
| **Void Wisp** | Ranged, fast, low HP |
| **Rift Walker** | Teleports near the player |
| **Mirror Shade** | Copies your movement direction |
| **Gravity Warden** | Gravity-pull AOE that drags you in |
| **Null Serpent** | Long-range, high HP |
| **Architect** *(mini-boss)* | 3-way void bolts, **void_cage** special |
| **Nexus** *(big boss)* | 9-shot ring spread, **reality_collapse** special |

Bosses take reduced knockback compared to normal enemies.

---

## Boss Phase 2

When any boss reaches **40% HP** it enters an enraged Phase 2:

- **+40% movement speed**
- **−45% attack cooldowns** (fires much faster)
- Spread shot count increases
- Activates a **secondary special ability** unique to each boss

| Boss | Phase 2 Special |
|------|-----------------|
| Iron Sentinel | missile_barrage — carpet of homing missiles |
| Supreme D-Lek | bleed_storm — spreading bleed field |
| Street Preacher | fire_ring — expanding ring of fire |
| Eldritch Horror | eldritch_pull — pulls player and enemies together |
| Architect | void_cage — rings of void bolts |
| Nexus | reality_collapse — screen-wide reality distortion |

Boss music starts when the boss spawns and stops on death. Boss music is unique per zone and cached so it only generates once.

---

## Status Effects

Enemies (and you) can inflict status effects. A small icon appears on the affected character.

| Effect | Duration | Tick Rate | Damage/Tick | Source |
|--------|----------|-----------|-------------|--------|
| Fire (F) | 3 sec | Every 500ms | 4 | Mini Boss hits |
| Bleed (B) | 4 sec | Every 600ms | 3 | Big Boss hits |
| Poison (P) | 5 sec | Every 800ms | 2 | Wraith hits |
| Slow (S) | 3 sec | — | 0 | Cuts move speed to 50% |

---

## Waves & Difficulty

The game is an endless wave survival. Each wave spawns a group of enemies you must defeat before the next wave begins.

- **Enemy count** increases each wave
- **Boss waves** occur periodically — a short roar + screen shake signals the start
  - Boss waves clear all remaining normal enemies, then spawn bosses
  - Boss kills drop a **Boss Chest** with upgrade choices
- **Per-wave scaling:** Each wave, enemies get **+12% HP**, **+8% Damage**, and **+3% Speed**
- **Wraith ratio** increases over the first several waves, capping at ~45% of spawns

### Darkness

A separate difficulty system that scales over time:

- Enemies deal and take scaled damage based on darkness
- You earn **more XP** as darkness increases (up to +200% at max darkness)
- The screen gets progressively darker

---

## Pause Menu

Press **Esc** or **P** at any time during gameplay to open the pause menu:

- **Resume** — return to the game
- **Settings** — adjust resolution, fullscreen, and music volume
- **Quit to Menu** — return to the main menu (progress for the current run is lost)

---

## Between Waves

When all enemies in a wave are dead, you get a short rest period.

### Campfire
A campfire sits at the center of the map. Stand near it between waves to heal.

- **Heal radius:** 80 pixels from center
- **Heal rate:** 2 HP every 200ms (10 HP/sec)
- Only works when no enemies are alive

### Fruit Trees
Some trees on the map bear fruit (roughly 10% of all trees). Hit them with a melee attack to knock an apple loose.

- **Apple heal:** +20 HP
- **Respawn:** 30 seconds after being picked

---

## Dash / Dodge

Press **Shift** or **K** to dash in your current movement direction.

- **Duration:** 150ms of fast movement
- **Cooldown:** 800ms between dashes
- **Invincibility:** You are invincible for 300ms during and after the dash
- Great for escaping boss attacks or dodging into melee range

You also get 300ms of invincibility after taking any damage, preventing rapid multi-hits.

---

## Pickups

Enemies drop items on death. Walk over them to collect.

| Pickup | Effect |
|--------|--------|
| XP Orb | Grants XP — glowing green orb, disappears after 12 seconds |
| Coin | Adds to your coin total — 25% chance from enemies, 100% from bosses |
| Heal | +30 HP |
| Damage Up | +5 base damage |
| Speed Up | +0.3 movement speed |
| Range Up | +8 attack range |
| Max HP Up | +15 max HP (and instant +15 heal) |

XP orbs must be collected before they expire — the **Magnetic Field** passive pulls them to you automatically from 150px away.

Your coin count is displayed in the HUD.

---

## Boss Chests

Killing a boss spawns a glowing chest. Walk into it to open a reward screen with up to 5 random choices. Press the **number key (1–5)** to pick one.

### Stat Upgrades

| Upgrade | Effect |
|---------|--------|
| Overclocked Blade | +15 Damage |
| Extended Reach | +20 Range |
| Turbo Hands | -100ms Attack Cooldown |
| Reinforced Chassis | +60 Max HP (+ instant heal) |
| Emergency Repair | Fully heals you |
| Overdrive | +1.0 Speed |

### Passive Abilities
- **Nano Regen** — Regenerate 1 HP every 2 seconds
- **Berserker Mode** — +50% damage when below 30% HP
- **Shield Matrix** — Absorb one hit every 10 seconds
- **Vampiric Strike** — Heal 3 HP per hit (melee or ranged)
- **Chain Lightning** — Hits arc to 2 nearby enemies for 50% damage
- **Second Wind** — Revive once per run at 30% HP when killed
- **Explosive Kills** — 25% chance enemies explode on death (40 damage, 60px radius)

### Weapon Upgrades
A new weapon appropriate to your class may appear as one of the choices.

## Leveling Up

You gain XP from killing enemies. When you level up, you're offered a choice of 3 upgrades filtered to your class. XP requirements increase with each level.

### Stat Upgrades
- **Power Surge** — +8 Damage
- **Iron Skin** — +25 Max HP (+ instant heal)
- **Leg Servos** — +0.5 Speed
- **Quick Trigger** — -60ms Attack Cooldown
- **Full Repair** — Fully heals you
- **Glass Cannon** — +30% Damage but lose 20 Max HP (risky!)

### Passive Abilities (from level-ups)
- **Vampiric Strike** — Heal 3 HP per hit
- **Thorns** — Reflect 30% of melee damage back to attackers
- **Magnetic Field** — Pickups fly toward you from 150px away
- **Adrenaline Rush** — +30% speed for 3 seconds after each kill
- Plus class-specific passives you don't already have

### Weapon Upgrades
A new weapon for your class may appear as one of the level-up options.

Darkness increases XP gains, so harder waves reward faster leveling.

---

## HUD

The heads-up display shows:

- **HP bar** (top left) — turns red and pulses at low HP with a screen vignette
- **XP bar** — fills toward your next level
- **Wave counter** — current wave number
- **Boss HP bar** — appears when a boss is alive
- **Coin count** — your current coin total
- **Radar** (corner) — shows dots for nearby enemies and the campfire
- **Status effect icons** — appear on your character when affected
- **Floating damage numbers** — pop up when you or enemies take hits

---

## Compendium

The **Compendium** is an in-game bestiary that tracks every enemy type you encounter.

- A new entry **unlocks on first kill** — you'll see a toast notification appear
- Access it from the **Portal Menu** between zones, or from the **Main Menu**
- Each entry shows:
  - The enemy's procedurally drawn art
  - Zone it appears in
  - Enemy type (melee / ranged / boss)
  - A brief description
  - **Inspect view** — larger art and any special abilities
- There are **21 entries** total, one per enemy type across all three zones

---

## Tips

- **Parry is free damage prevention.** Every bullet you deflect is HP you keep. Practice the timing.
- **Don't ignore the campfire.** Between waves, stand at center to top off. Walk away to start the next wave when ready.
- **Fruit trees are hidden heals.** Smack trees while fighting — some drop apples. Look for the ones with colored fruit.
- **The Joy Buzzer hits 360°.** If you're surrounded, it's the only weapon that damages in every direction.
- **Dash through danger.** You're invincible during a dash. Use it to escape boss swings or close the gap on ranged enemies.
- **Orbiters are passive damage.** Blade Barrier / Banana-Rang orbit you and keep hitting nearby enemies while you focus on other threats.
- **Bosses enrage at 40% HP.** When the enrage animation plays, they get faster, shoot more, and unlock a second special. Burst them down fast or increase your distance.
- **Collect XP orbs quickly.** They disappear after 12 seconds. The Magnetic Field passive pulls them toward you automatically.
- **Coins drop from bosses every time.** Use them as a rough measure of boss kills and for legacy shop decisions.
- **Pick Turbo Hands from chests if offered.** Reducing attack cooldown makes every weapon better and gives you more parry opportunities.
- **The Cyber Bow pierces.** Arrows go through enemies, so line them up for multi-kills.
- **Chain Lightning is amazing for crowds.** Each hit arcs to 2 nearby enemies — combine with fast weapons for constant chain procs.
- **Second Wind is your insurance policy.** It revives you once per run. Take it early if you're pushing deep.
- **Legacy upgrades persist forever.** Even a bad run earns Legacy Points. Spend them on permanent stat boosts between runs.

---

## Legacy System (Roguelite)

When you die, you earn **Legacy Points** based on your performance:

```
Legacy Points = (Wave Reached × 10) + Total Kills + (Boss Kills × 20)
```

Press **R** on the death screen to enter the **Legacy Shop**. Spend points on permanent upgrades that carry over to every future run:

| Upgrade | Effect per Rank | Max Rank |
|---------|----------------|----------|
| Vitality | +10 Max HP | 5 |
| Might | +3 Damage | 5 |
| Swiftness | +0.2 Speed | 5 |
| Resilience | +5% Damage Reduction | 5 |
| Fortune | +5% Item Drop Chance | 5 |
| Headstart | +1 Starting Level | 5 |

Costs increase with each rank. Press **1–6** to buy, **Enter** to continue to character select.

Your progress is saved to `legacy_save.json` automatically.
