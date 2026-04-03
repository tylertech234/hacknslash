"""Death / Victory summary screen — detailed run stats before legacy shop."""

import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW
from src.systems.run_stats import RunStats
from src.ui.tooltip import PASSIVE_DETAILS, calc_weapon_dps


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
        self.font_big = pygame.font.SysFont("consolas", 32, bold=True)
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 14)
        self.font_header = pygame.font.SysFont("consolas", 20, bold=True)

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
        if stats:
            stats.finalize()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True when player wants to continue to legacy screen."""
        if not self.active:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = False
            return True
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self.active = False
                return True
            if event.key in (pygame.K_w, pygame.K_UP):
                self.scroll_y = max(0, self.scroll_y - 30)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.scroll_y += 30
        return False

    def draw(self, surface: pygame.Surface):
        if not self.active or not self.stats:
            return

        surface.fill((8, 8, 14))
        s = self.stats
        y = 30 - self.scroll_y

        # Title
        if self.victory:
            title = self.font_big.render("MISSION COMPLETE", True, (100, 255, 100))
        else:
            title = self.font_big.render("RUN OVER", True, (255, 80, 80))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, y))
        y += 42

        # Zone / wave info
        zone_str = self.zone_name.replace("_", " ").title()
        info = self.font.render(f"Zone: {zone_str}  |  Wave {self.wave}  |  Level {self.player_level}", True, (180, 180, 200))
        surface.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, y))
        y += 30

        # Time
        time_surf = self.font.render(f"Time: {s.get_run_time_str()}", True, (150, 150, 170))
        surface.blit(time_surf, (SCREEN_WIDTH // 2 - time_surf.get_width() // 2, y))
        y += 40

        # ── Combat Stats ──
        y = self._draw_section(surface, y, "COMBAT STATS", [
            f"Total Kills ............ {s.total_kills}",
            f"Boss Kills ............. {s.boss_kills}",
            f"Total Damage Dealt ..... {s.total_damage_dealt:,}",
            f"Total Damage Taken ..... {s.total_damage_taken:,}",
            f"Highest Hit ............ {s.highest_hit}",
            f"Total Healed ........... {s.total_healed:,}",
        ])

        # ── Weapon Performance ──
        wpn_lines = []
        for wkey, ws in sorted(s.weapon_stats.items(), key=lambda kv: -kv[1]["damage"]):
            name = ws["name"]
            hits = ws["hits"]
            dmg = ws["damage"]
            time_s = max(1, ws["time_equipped"]) / 1000
            actual_dps = dmg / time_s if time_s > 1 else 0
            wpn_lines.append(f"  {name}")
            wpn_lines.append(f"    Hits: {hits}  |  Damage: {dmg:,}  |  DPS: {actual_dps:.1f}")

        if wpn_lines:
            y = self._draw_section(surface, y, "WEAPON PERFORMANCE", wpn_lines)

        # ── Passive Performance ──
        pas_lines = []
        for pkey, ps in sorted(s.passive_stats.items(), key=lambda kv: -(kv[1]["damage"] + kv[1]["healed"])):
            info = PASSIVE_DETAILS.get(pkey, {})
            name = info.get("name", pkey.replace("_", " ").title())
            parts = []
            if ps["procs"]:
                parts.append(f"{ps['procs']} procs")
            if ps["damage"]:
                parts.append(f"{ps['damage']:,} dmg")
            if ps["healed"]:
                parts.append(f"{ps['healed']:,} healed")
            if ps["kills"]:
                parts.append(f"{ps['kills']} kills")
            pas_lines.append(f"  {name}: {' | '.join(parts)}")

        if pas_lines:
            y = self._draw_section(surface, y, "PASSIVE ABILITIES", pas_lines)

        # ── Legacy Points ──
        y += 10
        pts = self.font.render(f"Legacy Points Earned: +{self.legacy_points}", True, YELLOW)
        surface.blit(pts, (SCREEN_WIDTH // 2 - pts.get_width() // 2, y))
        y += 40

        # Continue prompt
        hint = self.font_small.render("[Enter] Continue to Legacy Shop", True, (120, 120, 140))
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, max(y, SCREEN_HEIGHT - 40)))

    def _draw_section(self, surface: pygame.Surface, y: int,
                      header: str, lines: list[str]) -> int:
        """Draw a titled section with lines. Returns new y position."""
        box_w = 500
        box_x = SCREEN_WIDTH // 2 - box_w // 2

        # Header
        header_surf = self.font_header.render(header, True, YELLOW)
        surface.blit(header_surf, (box_x, y))
        y += 26

        # Separator
        pygame.draw.line(surface, (60, 60, 80), (box_x, y), (box_x + box_w, y), 1)
        y += 6

        # Lines
        for line in lines:
            line_surf = self.font_small.render(line, True, (180, 180, 200))
            surface.blit(line_surf, (box_x + 10, y))
            y += 18
        y += 14
        return y
