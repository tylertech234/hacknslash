-- Cyber Survivor — Supabase schema
-- Run this in your Supabase project SQL editor after creating the project.
-- Dashboard → SQL Editor → New query → paste → Run

-- ── Players ───────────────────────────────────────────────────────────────────
-- Lightweight player registry.  Created / updated automatically by the client.
create table if not exists public.players (
    player_id   uuid        primary key,
    display_name text       not null default 'Survivor',
    platform    text        not null default 'desktop',   -- 'desktop' | 'web' | 'steam'
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

-- ── Leaderboard ────────────────────────────────────────────────────────────────
-- One row per player.  best_wave is guarded by GREATEST so it only ever grows.
create table if not exists public.leaderboard (
    player_id       uuid        primary key,
    display_name    text        not null default 'Survivor',
    platform        text        not null default 'desktop',
    char_class      text        not null default 'knight',  -- last class used for best wave
    best_wave       int         not null default 0,
    best_run_date   date,
    updated_at      timestamptz not null default now()
);

-- Conflict rule: keep the highest wave ever reached
create or replace function public.leaderboard_upsert_guard()
returns trigger language plpgsql as $$
begin
    new.best_wave := greatest(new.best_wave,
        coalesce((select best_wave from public.leaderboard
                  where player_id = new.player_id), 0));
    new.updated_at := now();
    return new;
end;
$$;

drop trigger if exists leaderboard_upsert_guard_trigger on public.leaderboard;
create trigger leaderboard_upsert_guard_trigger
before insert or update on public.leaderboard
for each row execute function public.leaderboard_upsert_guard();

-- ── Run analytics ─────────────────────────────────────────────────────────────
-- One row per completed or failed run.  Stored for balance / design analysis.
create table if not exists public.run_analytics (
    id              bigserial   primary key,
    player_id       uuid        not null,
    display_name    text        not null default 'Survivor',
    platform        text        not null default 'desktop',
    "timestamp"     text,
    char_class      text,
    zone            text,
    wave            int,
    level           int,
    victory         boolean,
    run_time_s      real,
    kills           int,
    boss_kills      int,
    damage_dealt    int,
    damage_taken    int,
    highest_hit     int,
    total_healed    int,
    killed_by       text,           -- enemy type that killed the player (empty on victory)
    zones_completed text,   -- JSON array
    upgrades        text,   -- JSON array of upgrade names
    weapons         text,   -- JSON object: {weapon_key: stats}
    passives        text,   -- JSON object: {passive_key: proc_count}
    created_at      timestamptz not null default now()
);

-- ── Row Level Security ────────────────────────────────────────────────────────
-- Public read on leaderboard (anyone can view scores).
-- Players can only insert their own rows (player_id is validated client-side).
-- No UPDATE or DELETE exposed to the anon key.

alter table public.leaderboard      enable row level security;
alter table public.run_analytics    enable row level security;
alter table public.players          enable row level security;

-- Leaderboard: public SELECT, INSERT only (handled by upsert trigger)
create policy "leaderboard_select_all"
    on public.leaderboard for select using (true);

create policy "leaderboard_insert_anon"
    on public.leaderboard for insert with check (true);

create policy "leaderboard_update_anon"
    on public.leaderboard for update using (true) with check (true);

-- Run analytics: public SELECT + INSERT (leaderboard UI queries runs directly)
create policy "analytics_select_all"
    on public.run_analytics for select using (true);

create policy "analytics_insert_anon"
    on public.run_analytics for insert with check (true);

-- Players: INSERT / UPDATE only
create policy "players_insert_anon"
    on public.players for insert with check (true);

create policy "players_update_anon"
    on public.players for update using (true) with check (true);

-- ── Indexes ───────────────────────────────────────────────────────────────────
create index if not exists leaderboard_best_wave_idx
    on public.leaderboard (best_wave desc);

create index if not exists analytics_player_idx
    on public.run_analytics (player_id);

create index if not exists analytics_wave_idx
    on public.run_analytics (wave desc);

create index if not exists analytics_damage_idx
    on public.run_analytics (damage_dealt desc);
