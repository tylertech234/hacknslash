import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, RED, GREEN, WHITE, YELLOW, BLACK, LIGHT_GRAY,
    XP_DARKNESS_BONUS,
)


class HUD:
    """Draws the heads-up display: HP bar, XP bar, wave counter, level."""

    def __init__(self):
        self.font = pygame.font.SysFont("consolas", 20)
        self.font_big = pygame.font.SysFont("consolas", 36)
        self.font_small = pygame.font.SysFont("consolas", 14)

    def draw(self, surface: pygame.Surface, player, wave: int, enemy_count: int,
             darkness: float = 0.0, boss_wave: bool = False):
        self._draw_hp_bar(surface, player)
        self._draw_xp_bar(surface, player)
        self._draw_info(surface, player, wave, enemy_count, darkness, boss_wave)

    def _draw_hp_bar(self, surface: pygame.Surface, player):
        bar_x, bar_y = 20, 20
        bar_w, bar_h = 220, 22
        ratio = max(0, player.hp / player.max_hp)
        pygame.draw.rect(surface, (60, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, RED, (bar_x, bar_y, int(bar_w * ratio), bar_h))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, bar_h), 2)
        label = self.font_small.render(f"HP {player.hp}/{player.max_hp}", True, WHITE)
        surface.blit(label, (bar_x + 4, bar_y + 3))

    def _draw_xp_bar(self, surface: pygame.Surface, player):
        bar_x, bar_y = 20, 48
        bar_w, bar_h = 220, 14
        ratio = player.xp / player.xp_to_next if player.xp_to_next > 0 else 0
        pygame.draw.rect(surface, (0, 30, 60), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, YELLOW, (bar_x, bar_y, int(bar_w * ratio), bar_h))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, bar_h), 1)
        label = self.font_small.render(f"XP {player.xp}/{player.xp_to_next}", True, WHITE)
        surface.blit(label, (bar_x + 4, bar_y + 0))

    def _draw_info(self, surface: pygame.Surface, player, wave: int, enemy_count: int,
                   darkness: float = 0.0, boss_wave: bool = False):
        lvl = self.font.render(f"Lv {player.level}", True, YELLOW)
        surface.blit(lvl, (250, 20))

        # Weapon name
        wpn = self.font_small.render(player.weapon["name"], True, LIGHT_GRAY)
        surface.blit(wpn, (250, 44))

        # Wave info with boss indicator
        wave_label = f"Wave {wave}  |  Enemies: {enemy_count}"
        wave_txt = self.font.render(wave_label, True, LIGHT_GRAY)
        surface.blit(wave_txt, (SCREEN_WIDTH - wave_txt.get_width() - 20, 20))

        if boss_wave:
            boss_txt = self.font.render("!! BOSS WAVE !!", True, (255, 60, 60))
            bx = SCREEN_WIDTH // 2 - boss_txt.get_width() // 2
            surface.blit(boss_txt, (bx, 50))

        # Darkness / XP multiplier indicator
        if darkness > 0.01:
            xp_mult = 1.0 + darkness * XP_DARKNESS_BONUS
            dark_pct = int(darkness * 100)
            # Color shifts from white to red as darkness increases
            r = min(255, 180 + int(75 * darkness))
            g = max(80, int(180 * (1.0 - darkness)))
            b = max(80, int(180 * (1.0 - darkness)))
            info = self.font_small.render(
                f"Darkness {dark_pct}%  |  XP x{xp_mult:.1f}", True, (r, g, b))
            surface.blit(info, (SCREEN_WIDTH - info.get_width() - 20, 46))

    def draw_game_over(self, surface: pygame.Surface, wave: int, level: int):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        title = self.font_big.render("YOU DIED", True, RED)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 60))

        info = self.font.render(f"Reached Wave {wave}  |  Level {level}", True, WHITE)
        surface.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, SCREEN_HEIGHT // 2))

        hint = self.font.render("Press R to restart  |  ESC to quit", True, LIGHT_GRAY)
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT // 2 + 40))
