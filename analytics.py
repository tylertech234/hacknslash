#!/usr/bin/env python3
"""Cyber Survivor — Game Analytics Dashboard

Pulls run_analytics from Supabase and prints game balance insights.
Run:  python analytics.py
"""

import json
import sys
from collections import Counter, defaultdict
from src.systems.telemetry import TelemetryClient

try:
    from src.secrets import SUPABASE_URL, SUPABASE_ANON_KEY
except ImportError:
    print("ERROR: src/secrets.py not found — cannot connect to Supabase.")
    sys.exit(1)

_ALL_ZONES = {"wasteland", "city", "abyss"}
_CLASS_LABELS = {"knight": "Knight", "archer": "Ranger", "jester": "Jester"}


def _fmt_time(seconds: float) -> str:
    s = int(seconds)
    if s >= 3600:
        return f"{s // 3600}:{(s % 3600) // 60:02d}:{s % 60:02d}"
    return f"{s // 60}:{s % 60:02d}"


def _fmt_num(n: float) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:,.0f}"


def _parse_json_field(val) -> list | dict:
    if val is None:
        return []
    if isinstance(val, (list, dict)):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return []


def _completed_all_zones(row: dict) -> bool:
    zc = _parse_json_field(row.get("zones_completed"))
    if isinstance(zc, list):
        return _ALL_ZONES.issubset(set(zc))
    return False


def _hr(title: str = "", width: int = 72) -> None:
    if title:
        pad = width - len(title) - 4
        print(f"\n{'─' * 2} {title} {'─' * max(1, pad)}")
    else:
        print("─" * width)


def analyze(rows: list[dict]) -> None:
    n = len(rows)
    if n == 0:
        print("No run data found.")
        return

    print(f"\n{'═' * 72}")
    print(f"  CYBER SURVIVOR — ANALYTICS DASHBOARD  ({n} runs)")
    print(f"{'═' * 72}")

    # ── Overall summary ────────────────────────────────────────────────
    _hr("OVERVIEW")
    victories = sum(1 for r in rows if r.get("victory"))
    completions = sum(1 for r in rows if _completed_all_zones(r))
    times = [r["run_time_s"] for r in rows if r.get("run_time_s")]
    avg_time = sum(times) / len(times) if times else 0
    median_time = sorted(times)[len(times) // 2] if times else 0
    waves = [r.get("wave", 0) for r in rows]
    avg_wave = sum(waves) / len(waves) if waves else 0
    levels = [r.get("level", 0) for r in rows]
    avg_level = sum(levels) / len(levels) if levels else 0

    print(f"  Total runs:          {n}")
    print(f"  Victory rate:        {victories}/{n} ({100 * victories / n:.1f}%)")
    print(f"  All-zone completions:{completions}")
    print(f"  Avg wave reached:    {avg_wave:.1f}")
    print(f"  Avg level reached:   {avg_level:.1f}")
    print(f"  Avg run time:        {_fmt_time(avg_time)}")
    print(f"  Median run time:     {_fmt_time(median_time)}")
    if times:
        print(f"  Shortest run:        {_fmt_time(min(times))}")
        print(f"  Longest run:         {_fmt_time(max(times))}")

    # ── Character class usage ──────────────────────────────────────────
    _hr("CHARACTER USAGE")
    class_counts = Counter(r.get("char_class", "unknown") for r in rows)
    class_wins = Counter(r.get("char_class") for r in rows if r.get("victory"))
    for cls, count in class_counts.most_common():
        label = _CLASS_LABELS.get(cls, cls)
        wins = class_wins.get(cls, 0)
        wr = f"{100 * wins / count:.0f}%" if count > 0 else "N/A"
        pct = 100 * count / n
        bar = "█" * int(pct / 2.5) + "░" * (40 - int(pct / 2.5))
        print(f"  {label:8s}  {count:4d} runs ({pct:5.1f}%)  W/R: {wr:>4s}  {bar}")

    # ── Weapon usage & DPS ─────────────────────────────────────────────
    _hr("WEAPON STATS  (from per-run weapon breakdowns)")
    wpn_picks = Counter()       # how many runs featured this weapon
    wpn_total_dmg = defaultdict(int)
    wpn_total_hits = defaultdict(int)
    wpn_total_time = defaultdict(float)  # seconds equipped
    wpn_names = {}

    for r in rows:
        weapons = _parse_json_field(r.get("weapons"))
        if isinstance(weapons, dict):
            for wkey, wdata in weapons.items():
                if not isinstance(wdata, dict):
                    continue
                wpn_picks[wkey] += 1
                wpn_names[wkey] = wdata.get("name", wkey)
                wpn_total_dmg[wkey] += wdata.get("total_damage", wdata.get("damage", 0))
                wpn_total_hits[wkey] += wdata.get("hits", 0)
                equip_s = wdata.get("time_equipped_s", 0)
                if not equip_s:
                    # Fall back to legacy key (ms) and convert
                    equip_ms = wdata.get("time_equipped", 0)
                    equip_s = equip_ms / 1000 if isinstance(equip_ms, (int, float)) else 0
                wpn_total_time[wkey] += equip_s

    if wpn_picks:
        print(f"\n  {'Weapon':<20s} {'Runs':>5s} {'Tot Dmg':>10s} {'Avg/Hit':>8s} {'DPS':>8s}")
        print(f"  {'─' * 55}")
        for wkey, count in wpn_picks.most_common():
            name = wpn_names.get(wkey, wkey)[:20]
            dmg = wpn_total_dmg[wkey]
            hits = wpn_total_hits[wkey]
            time_s = wpn_total_time[wkey]
            avg_hit = dmg / hits if hits > 0 else 0
            dps = dmg / time_s if time_s > 0 else 0
            print(f"  {name:<20s} {count:5d}  {_fmt_num(dmg):>9s} {avg_hit:8.1f} {dps:8.1f}")

        # Best & worst DPS weapons (minimum 3 runs with data)
        dps_data = {}
        for wkey in wpn_picks:
            if wpn_picks[wkey] >= 3 and wpn_total_time[wkey] > 0:
                dps_data[wkey] = wpn_total_dmg[wkey] / wpn_total_time[wkey]
        if dps_data:
            best = max(dps_data, key=dps_data.get)
            worst = min(dps_data, key=dps_data.get)
            print(f"\n  Highest DPS weapon:  {wpn_names.get(best, best)} ({dps_data[best]:.1f} DPS, {wpn_picks[best]} runs)")
            print(f"  Lowest DPS weapon:   {wpn_names.get(worst, worst)} ({dps_data[worst]:.1f} DPS, {wpn_picks[worst]} runs)")
    else:
        print("  No weapon data found in runs.")

    # ── Upgrade / passive usage ────────────────────────────────────────
    _hr("UPGRADE & PASSIVE USAGE")
    upgrade_picks = Counter()
    upgrade_wins = Counter()

    for r in rows:
        upgrades = _parse_json_field(r.get("upgrades"))
        if isinstance(upgrades, list):
            unique = set(upgrades)
            for u in unique:
                upgrade_picks[u] += 1
                if r.get("victory"):
                    upgrade_wins[u] += 1

    if upgrade_picks:
        print(f"\n  {'Upgrade/Passive':<24s} {'Picked':>6s} {'In Wins':>7s} {'Win %':>6s}")
        print(f"  {'─' * 47}")
        for name, count in upgrade_picks.most_common():
            wins = upgrade_wins.get(name, 0)
            wr = f"{100 * wins / count:.0f}%" if count > 0 else "--"
            print(f"  {name:<24s} {count:6d} {wins:7d} {wr:>6s}")

        # Least picked
        print(f"\n  Least picked (bottom 5):")
        for name, count in upgrade_picks.most_common()[-5:]:
            print(f"    {name}: {count} picks")
    else:
        print("  No upgrade data found.")

    # ── Passive proc stats ─────────────────────────────────────────────
    _hr("PASSIVE PROC STATS")
    passive_procs = defaultdict(int)
    passive_runs = Counter()

    for r in rows:
        passives = _parse_json_field(r.get("passives"))
        if isinstance(passives, dict):
            for pkey, count in passives.items():
                if isinstance(count, (int, float)):
                    passive_procs[pkey] += int(count)
                    passive_runs[pkey] += 1

    if passive_procs:
        print(f"\n  {'Passive':<24s} {'Runs':>5s} {'Tot Procs':>10s} {'Avg/Run':>8s}")
        print(f"  {'─' * 51}")
        for pkey in sorted(passive_procs, key=passive_procs.get, reverse=True):
            runs_with = passive_runs[pkey]
            procs = passive_procs[pkey]
            avg = procs / runs_with if runs_with > 0 else 0
            print(f"  {pkey:<24s} {runs_with:5d} {procs:10d} {avg:8.1f}")

    # ── Killed-by analysis ─────────────────────────────────────────────
    _hr("DEADLIEST ENEMIES  (most player kills)")
    deaths = [r for r in rows if not r.get("victory") and r.get("killed_by")]
    if deaths:
        killer_counts = Counter(r["killed_by"] for r in deaths)
        total_deaths = len(deaths)
        print(f"\n  {'Enemy Type':<24s} {'Kills':>6s} {'% of Deaths':>11s}")
        print(f"  {'─' * 45}")
        for enemy, count in killer_counts.most_common():
            pct = 100 * count / total_deaths
            print(f"  {enemy:<24s} {count:6d} {pct:10.1f}%")

        safest = killer_counts.most_common()[-1]
        print(f"\n  Deadliest enemy:  {killer_counts.most_common(1)[0][0]} ({killer_counts.most_common(1)[0][1]} kills)")
        print(f"  Safest enemy:     {safest[0]} ({safest[1]} kills)")
    else:
        print("  No killed_by data yet (added in this update — needs new runs).")

    # ── Damage stats ───────────────────────────────────────────────────
    _hr("DAMAGE STATS")
    dmg_dealt = [r.get("damage_dealt", 0) for r in rows if r.get("damage_dealt")]
    dmg_taken = [r.get("damage_taken", 0) for r in rows if r.get("damage_taken")]
    highest_hits = [r.get("highest_hit", 0) for r in rows if r.get("highest_hit")]

    if dmg_dealt:
        print(f"  Avg damage dealt:    {_fmt_num(sum(dmg_dealt) / len(dmg_dealt))}")
        print(f"  Max damage in a run: {_fmt_num(max(dmg_dealt))}")
    if dmg_taken:
        print(f"  Avg damage taken:    {_fmt_num(sum(dmg_taken) / len(dmg_taken))}")
    if highest_hits:
        print(f"  Biggest single hit:  {_fmt_num(max(highest_hits))}")
    kills = [r.get("kills", 0) for r in rows if r.get("kills")]
    if kills:
        print(f"  Avg kills per run:   {sum(kills) / len(kills):.1f}")
        print(f"  Max kills in a run:  {max(kills)}")

    # ── Zone progression ───────────────────────────────────────────────
    _hr("ZONE PROGRESSION")
    zone_reached = Counter()
    for r in rows:
        zone_reached[r.get("zone", "unknown")] += 1
    print(f"\n  Zone died/won in:")
    for zone, count in zone_reached.most_common():
        pct = 100 * count / n
        print(f"    {zone:<16s}  {count:5d} runs  ({pct:.1f}%)")

    zones_cleared = Counter()
    for r in rows:
        zc = _parse_json_field(r.get("zones_completed"))
        if isinstance(zc, list):
            for z in zc:
                zones_cleared[z] += 1
    if zones_cleared:
        print(f"\n  Zone clear counts:")
        for zone in ["wasteland", "city", "abyss"]:
            count = zones_cleared.get(zone, 0)
            print(f"    {zone:<16s}  {count:5d} clears")

    # ── Platform breakdown ─────────────────────────────────────────────
    _hr("PLATFORMS")
    plat_counts = Counter(r.get("platform", "unknown") for r in rows)
    for plat, count in plat_counts.most_common():
        print(f"  {plat:<12s}  {count:5d} runs ({100 * count / n:.1f}%)")

    print(f"\n{'═' * 72}")
    print("  End of report.")
    print(f"{'═' * 72}\n")


def main():
    print("Connecting to Supabase...")
    client = TelemetryClient(SUPABASE_URL, SUPABASE_ANON_KEY)

    if not client._enabled:
        print("ERROR: Supabase not configured.")
        sys.exit(1)

    print("Fetching run analytics (up to 1000 rows)...")
    rows = client.fetch_all_analytics(limit=1000)

    if not rows:
        print("No data returned. Check your Supabase config or RLS policies.")
        print("\nMake sure you've run the SELECT policy migration:")
        print("  CREATE POLICY \"analytics_select_all\"")
        print("    ON public.run_analytics FOR SELECT USING (true);")
        sys.exit(1)

    print(f"Got {len(rows)} runs.")
    analyze(rows)


if __name__ == "__main__":
    main()
