"""Between-run legacy screen — spend legacy points on permanent upgrades."""

import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW
from src.systems.legacy import LEGACY_UPGRADES, LegacyData


class LegacyScreen:
    """Shows after a run ends. Spend legacy points on permanent upgrades."""

    def __init__(self, legacy: LegacyData):
        self.legacy = legacy
        self.active = False
        self.points_earned = 0
        self.run_wave = 0
        self.run_kills = 0
        self.font_big = pygame.font.SysFont("consolas", 32, bold=True)
        self.font = pygame.font.SysFont("consolas", 20)
        self.font_small = pygame.font.SysFont("consolas", 14)

    def activate(self, wave: int, kills: int, points_earned: int):
        self.active = True
        self.run_wave = wave
        self.run_kills = kills
        self.points_earned = points_earned

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True when player is done and wants to continue."""
        if not self.active:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            card_w, card_h = 500, 55
            start_y = 185
            cx_c = SCREEN_WIDTH // 2 - card_w // 2
            for i, u in enumerate(LEGACY_UPGRADES):
                cy = start_y + i * (card_h + 6)
                if cx_c <= mx <= cx_c + card_w and cy <= my <= cy + card_h:
                    self.legacy.try_purchase(u["key"])
                    return False
            # Click the continue hint area at bottom
            hint_y = start_y + len(LEGACY_UPGRADES) * (card_h + 6) + 10
            if my >= hint_y:
                self.active = False
                return True
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self.active = False
                return True
            # Number keys 1-6 to buy upgrades
            num_keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]
            for i, k in enumerate(num_keys):
                if event.key == k and i < len(LEGACY_UPGRADES):
                    self.legacy.try_purchase(LEGACY_UPGRADES[i]["key"])
        return False

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return
        surface.fill((10, 10, 15))

        # Title
        title = self.font_big.render("LEGACY", True, YELLOW)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 30))

        # Run summary
        summary = self.font.render(
            f"Wave {self.run_wave}  |  {self.run_kills} Kills  |  +{self.points_earned} Points",
            True, (180, 180, 180))
        surface.blit(summary, (SCREEN_WIDTH // 2 - summary.get_width() // 2, 75))

        # Stats
        stats = self.font_small.render(
            f"Total Runs: {self.legacy.total_runs}  |  Best Wave: {self.legacy.best_wave}  |  Total Kills: {self.legacy.total_kills}",
            True, (120, 120, 120))
        surface.blit(stats, (SCREEN_WIDTH // 2 - stats.get_width() // 2, 105))

        # Points available
        pts = self.font.render(f"Legacy Points: {self.legacy.legacy_points}", True, YELLOW)
        surface.blit(pts, (SCREEN_WIDTH // 2 - pts.get_width() // 2, 140))

        # Upgrades
        card_w = 500
        card_h = 55
        start_y = 185
        for i, u in enumerate(LEGACY_UPGRADES):
            rank = self.legacy.get_rank(u["key"])
            max_rank = u["max_rank"]
            cost = self.legacy.get_cost(u["key"])
            maxed = rank >= max_rank
            can_afford = self.legacy.legacy_points >= cost and not maxed

            cy = start_y + i * (card_h + 6)
            cx = SCREEN_WIDTH // 2 - card_w // 2

            # Card bg
            bg_color = (30, 35, 45) if can_afford else (20, 20, 25)
            pygame.draw.rect(surface, bg_color, (cx, cy, card_w, card_h), border_radius=6)

            # Border
            border_color = YELLOW if can_afford else (60, 60, 60)
            if maxed:
                border_color = (100, 255, 100)
            pygame.draw.rect(surface, border_color, (cx, cy, card_w, card_h), 2, border_radius=6)

            # Number key
            num = self.font_small.render(f"[{i + 1}]", True, (120, 120, 120))
            surface.blit(num, (cx + 10, cy + 16))

            # Name + rank pips
            name_color = WHITE if can_afford else (100, 100, 100)
            pips = chr(9632) * rank + chr(9633) * (max_rank - rank)  # filled/empty squares
            rank_str = f"{u['name']}  {pips}"
            name_surf = self.font.render(rank_str, True, name_color)
            surface.blit(name_surf, (cx + 50, cy + 8))

            # Description
            desc_surf = self.font_small.render(u["desc"], True, (140, 140, 140))
            surface.blit(desc_surf, (cx + 50, cy + 34))

            # Cost / maxed
            if maxed:
                cost_surf = self.font_small.render("MAXED", True, (100, 255, 100))
            else:
                cost_color = YELLOW if can_afford else (80, 80, 80)
                cost_surf = self.font_small.render(f"Cost: {cost}", True, cost_color)
            surface.blit(cost_surf, (cx + card_w - cost_surf.get_width() - 15, cy + 18))

        # Hint
        hint = self.font_small.render(
            "Press 1-6 to buy upgrades  |  Enter to continue",
            True, (100, 100, 100))
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                           start_y + len(LEGACY_UPGRADES) * (card_h + 6) + 20))
