"""Death / Victory summary screen — detailed run stats before legacy shop."""

import pygame
import math
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW
from src.systems.run_stats import RunStats
from src.ui.tooltip import PASSIVE_DETAILS, calc_weapon_dps

_ZONE_DISPLAY = {
    "wasteland": "The Forest",
    "city":      "Ruined Metropolis",
    "abyss":     "The Abyss",
}


class RunSummaryScreen:
    """Displays detailed run statistics on death or victory."""

    def __init__(self):
        self.active = False
        self.stats: RunStats | None = None
        self.victory = False
        self.wave = 0
        self.zone_name = ""
        self.legacy_points = 0
        self.player_level = 0
        self.scroll_y = 0
        self._max_scroll = 0
        self.font_title = pygame.font.SysFont("consolas", 38, bold=True)
        self.font_big   = pygame.font.SysFont("consolas", 24, bold=True)
        self.font       = pygame.font.SysFont("consolas", 16)
        self.font_small = pygame.font.SysFont("consolas", 13)
        self.font_micro = pygame.font.SysFont("consolas", 12)

    def activate(self, stats: RunStats, wave: int, zone_name: str,
                 legacy_points: int, player_level: int, victory: bool = False):
        self.active = True
        self.stats = stats
        self.wave = wave
        self.zone_name = zone_name
        self.legacy_points = legacy_points
        self.player_level = player_level
        self.victory = victory
        self.scroll_y = 0
        self._max_scroll = 0
        if stats:
            stats.finalize()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True when player wants to continue."""
        if not self.active:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.active = False
                return True
            elif event.button == 4:  # scroll up
                self.scroll_y = max(0, self.scroll_y - 30)
            elif event.button == 5:  # scroll down
                self.scroll_y = min(self._max_scroll, self.scroll_y + 30)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self.active = False
                return True
            if event.key in (pygame.K_w, pygame.K_UP):
                self.scroll_y = max(0, self.scroll_y - 30)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.scroll_y = min(self._max_scroll, self.scroll_y + 30)
        return False

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _panel(self, surface, x, y, w, h, fill=(14, 18, 28), border=(50, 60, 90)):
        pygame.draw.rect(surface, fill, (x, y, w, h), border_radius=6)
        pygame.draw.rect(surface, border, (x, y, w, h), 1, border_radius=6)

    def _section_header(self, surface, x, y, w, text, color=(255, 200, 60)):
        pygame.draw.rect(surface, (24, 28, 45), (x, y, w, 26), border_radius=4)
        pygame.draw.line(surface, color, (x + 4, y + 25), (x + w - 4, y + 25), 1)
        surf = self.font.render(text, True, color)
        surface.blit(surf, (x + 8, y + 4))
        return y + 30

    def _stat_row(self, surface, x, y, label, value, label_color=(160, 165, 180), val_color=(220, 230, 255)):
        ls = self.font_small.render(label, True, label_color)
        vs = self.font_small.render(str(value), True, val_color)
        surface.blit(ls, (x, y))
        surface.blit(vs, (x + 200, y))
        return y + 17

    def _bar(self, surface, x, y, w, h, frac, fore_color, bg_color=(25, 30, 45)):
        pygame.draw.rect(surface, bg_color, (x, y, w, h), border_radius=3)
        if frac > 0:
            fw = max(4, int(w * frac))
            pygame.draw.rect(surface, fore_color, (x, y, fw, h), border_radius=3)

    # ── Main draw ─────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        if not self.active or not self.stats:
            return

        now = pygame.time.get_ticks()
        s = self.stats

        # Background gradient
        surface.fill((6, 8, 14))
        grad = pygame.Surface((SCREEN_WIDTH, 120), pygame.SRCALPHA)
        for i in range(120):
            a = int(80 * (1.0 - i / 120))
            color = (100, 60, 200, a) if self.victory else (180, 40, 40, a)
            pygame.draw.line(grad, color, (0, i), (SCREEN_WIDTH, i))
        surface.blit(grad, (0, 0))

        PAD = 24
        y = 18 - self.scroll_y

        # ── Title ─────────────────────────────────────────────────────────────
        if self.victory:
            title_text = "MISSION COMPLETE"
            title_color = (80, 255, 130)
        else:
            title_text = "RUN OVER"
            title_color = (255, 90, 90)
        title_surf = self.font_title.render(title_text, True, title_color)
        surface.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, y))
        y += 46

        # Sub-info bar
        zone_str = _ZONE_DISPLAY.get(self.zone_name, self.zone_name.replace("_", " ").title())
        run_dps = s.total_damage_dealt / max(1, s.get_run_time() / 1000)
        info_parts = [
            f"Zone: {zone_str}",
            f"Wave {self.wave}",
            f"Level {self.player_level}",
            f"Time: {s.get_run_time_str()}",
            f"Run DPS: {run_dps:.1f}",
        ]
        info_text = "   |   ".join(info_parts)
        info_surf = self.font_small.render(info_text, True, (160, 160, 185))
        surface.blit(info_surf, (SCREEN_WIDTH // 2 - info_surf.get_width() // 2, y))
        y += 22

        pygame.draw.line(surface, (40, 44, 70),
                         (PAD, y), (SCREEN_WIDTH - PAD, y), 1)
        y += 14

        # ── Two-column layout ─────────────────────────────────────────────────
        col_w = (SCREEN_WIDTH - PAD * 3) // 2
        left_x = PAD
        right_x = PAD * 2 + col_w

        # LEFT: Combat stats
        col_y = y
        self._panel(surface, left_x, col_y, col_w, 186)
        cy = self._section_header(surface, left_x, col_y, col_w, "  COMBAT STATS", (255, 180, 60))
        cy = self._stat_row(surface, left_x + 10, cy, "Total Kills", f"{s.total_kills:,}")
        cy = self._stat_row(surface, left_x + 10, cy, "Boss Kills", f"{s.boss_kills:,}")
        cy = self._stat_row(surface, left_x + 10, cy, "Damage Dealt", f"{s.total_damage_dealt:,}")
        cy = self._stat_row(surface, left_x + 10, cy, "Damage Taken", f"{s.total_damage_taken:,}", val_color=(255, 160, 160))
        cy = self._stat_row(surface, left_x + 10, cy, "Highest Hit", f"{s.highest_hit:,}", val_color=(255, 220, 80))
        cy = self._stat_row(surface, left_x + 10, cy, "Total Healed", f"{s.total_healed:,}", val_color=(100, 230, 130))
        self._stat_row(surface, left_x + 10, cy, "Run DPS", f"{run_dps:.1f}", val_color=(120, 200, 255))

        # Zone times (if available)
        if s.zone_times:
            zt_y = col_y + 196
            self._panel(surface, left_x, zt_y, col_w, 16 + len(s.zone_times) * 17 + 16)
            zt_y2 = self._section_header(surface, left_x, zt_y, col_w, "  ZONE TIMES", (120, 200, 255))
            for z, ms in s.zone_times.items():
                zn = _ZONE_DISPLAY.get(z, z.replace("_", " ").title())
                secs = ms // 1000
                zt_y2 = self._stat_row(surface, left_x + 10, zt_y2, zn, f"{secs // 60}m {secs % 60:02d}s")

        # RIGHT: Weapon performance
        col_y2 = y
        sorted_weapons = sorted(s.weapon_stats.items(), key=lambda kv: -kv[1]["damage"])
        max_wpn_dmg = max((ws["damage"] for _, ws in sorted_weapons), default=1)
        panel_h = 30 + len(sorted_weapons) * 54 + 10
        self._panel(surface, right_x, col_y2, col_w, max(186, panel_h))
        wy = self._section_header(surface, right_x, col_y2, col_w, "  WEAPON PERFORMANCE", (200, 120, 255))

        for wkey, ws in sorted_weapons:
            name = ws["name"]
            hits = ws["hits"]
            dmg = ws["damage"]
            cooldown_ms = ws.get("cooldown_ms", 500)
            cooldown_s = cooldown_ms / 1000

            # Theoretical DPS: avg damage per hit divided by cooldown seconds
            # (what the weapon can sustain at its max fire rate — standard roguelite metric)
            avg_per_hit = dmg / hits if hits > 0 else 0
            theoretical_dps = avg_per_hit / cooldown_s if avg_per_hit > 0 else 0

            frac = dmg / max(1, max_wpn_dmg)

            # Weapon name + DPS on same line
            name_surf = self.font_small.render(name, True, (200, 220, 255))
            surface.blit(name_surf, (right_x + 8, wy))
            dps_color = (255, 220, 80) if theoretical_dps > 0 else (80, 80, 100)
            dps_surf = self.font_small.render(f"{theoretical_dps:.0f} DPS", True, dps_color)
            surface.blit(dps_surf, (right_x + col_w - dps_surf.get_width() - 8, wy))
            wy += 15
            # Damage bar
            self._bar(surface, right_x + 8, wy, col_w - 16, 7, frac, (160, 90, 255))
            wy += 10
            stats_txt = self.font_micro.render(
                f"Hits: {hits}   Total: {dmg:,}   Avg/hit: {avg_per_hit:.0f}   Rate: {cooldown_s:.2f}s",
                True, (120, 125, 145))
            surface.blit(stats_txt, (right_x + 8, wy))
            wy += 17

        y = max(col_y + 186, col_y2 + panel_h) + 14

        # ── Passives ─────────────────────────────────────────────────────────
        if s.passive_stats:
            pas_panel_h = 30 + len(s.passive_stats) * 17 + 10
            self._panel(surface, left_x, y, col_w, pas_panel_h)
            py = self._section_header(surface, left_x, y, col_w, "  PASSIVES", (80, 220, 180))
            for pkey, ps in sorted(s.passive_stats.items(), key=lambda kv: -(kv[1]["damage"] + kv[1]["healed"])):
                info = PASSIVE_DETAILS.get(pkey, {})
                pname = info.get("name", pkey.replace("_", " ").title())
                parts = []
                if ps["procs"]:   parts.append(f"{ps['procs']}x")
                if ps["damage"]:  parts.append(f"{ps['damage']:,}dmg")
                if ps["healed"]:  parts.append(f"+{ps['healed']:,}hp")
                if ps["kills"]:   parts.append(f"{ps['kills']}k")
                detail = "  ".join(parts) if parts else "active"
                py = self._stat_row(surface, left_x + 10, py, pname, detail,
                                    label_color=(100, 200, 160), val_color=(180, 220, 200))

        # ── Upgrades taken ───────────────────────────────────────────────────
        upgrades = getattr(s, "upgrades_taken", [])
        if upgrades:
            up_panel_h = 30 + math.ceil(len(upgrades) / 2) * 17 + 10
            self._panel(surface, right_x, y, col_w, up_panel_h)
            uy = self._section_header(surface, right_x, y, col_w, "  UPGRADES TAKEN", (255, 200, 80))
            # Display in two sub-columns
            sub_w = (col_w - 20) // 2
            for idx, upg in enumerate(upgrades):
                sub_x = right_x + 10 + (idx % 2) * sub_w
                sub_y = uy + (idx // 2) * 17
                us = self.font_micro.render(f"+ {upg}", True, (200, 195, 140))
                surface.blit(us, (sub_x, sub_y))

        # ── Legacy points ────────────────────────────────────────────────────
        y = max(y + pas_panel_h if s.passive_stats else y,
                y + up_panel_h if upgrades else y) + 16

        if self.legacy_points:
            pts_surf = self.font_big.render(f"Legacy Points Earned: +{self.legacy_points}",
                                            True, YELLOW)
            surface.blit(pts_surf, (SCREEN_WIDTH // 2 - pts_surf.get_width() // 2, y))
            y += 34

        # ── Continue hint ─────────────────────────────────────────────────────
        hint_y = max(y + 10, SCREEN_HEIGHT - 36)
        self._max_scroll = max(0, y + 50 - SCREEN_HEIGHT)
        pygame.draw.rect(surface, (10, 12, 20), (0, hint_y - 6, SCREEN_WIDTH, SCREEN_HEIGHT))
        hint = self.font_small.render("[E / Enter] Continue   [W/S] Scroll", True, (80, 80, 100))
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, hint_y))

