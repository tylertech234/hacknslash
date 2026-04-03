import pygame
import math
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, RED, GREEN, WHITE, YELLOW, BLACK, LIGHT_GRAY,
    XP_DARKNESS_BONUS, MAX_PASSIVES, PASSIVE_INFO,
)


class HUD:
    """Draws the heads-up display: HP bar, XP bar, wave counter, level."""

    def __init__(self):
        self.font = pygame.font.SysFont("consolas", 20)
        self.font_big = pygame.font.SysFont("consolas", 36)
        self.font_small = pygame.font.SysFont("consolas", 14)

    def draw(self, surface: pygame.Surface, player, wave: int, enemy_count: int,
             darkness: float = 0.0, boss_wave: bool = False, boss_enemies: list = None):
        self._draw_hp_bar(surface, player)
        self._draw_xp_bar(surface, player)
        self._draw_info(surface, player, wave, enemy_count, darkness, boss_wave)
        self._draw_passive_slots(surface, player)
        if boss_wave and boss_enemies:
            self._draw_boss_hp_bar(surface, boss_enemies)
        self._draw_low_hp_vignette(surface, player)

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

    def _draw_boss_hp_bar(self, surface: pygame.Surface, boss_enemies: list):
        """Draw a large HP bar at top-center for each boss."""
        bar_w = 400
        bar_h = 20
        bar_x = SCREEN_WIDTH // 2 - bar_w // 2
        bar_y = 80
        for i, boss in enumerate(boss_enemies):
            if not boss.alive:
                continue
            y = bar_y + i * (bar_h + 8)
            ratio = max(0, boss.hp / boss.max_hp)
            # Label
            label = "BOSS" if boss.enemy_type == "big_boss" else "ELITE"
            name_surf = self.font_small.render(f"{label}  {boss.hp}/{boss.max_hp}", True, WHITE)
            surface.blit(name_surf, (bar_x, y - 16))
            # Background
            pygame.draw.rect(surface, (60, 0, 0), (bar_x, y, bar_w, bar_h))
            # HP fill
            color = (255, 50, 50) if boss.enemy_type == "big_boss" else (255, 160, 0)
            pygame.draw.rect(surface, color, (bar_x, y, int(bar_w * ratio), bar_h))
            # Border
            pygame.draw.rect(surface, WHITE, (bar_x, y, bar_w, bar_h), 2)

    def _draw_passive_slots(self, surface: pygame.Surface, player):
        """Draw up to MAX_PASSIVES square slots showing active passives."""
        slot_size = 36
        gap = 6
        # Position: bottom-left, above the screen edge
        base_x = 20
        base_y = SCREEN_HEIGHT - slot_size - 16
        now = pygame.time.get_ticks()

        # Filter out non-slot passives (glass_cannon is a flag, not a slot occupant)
        display_passives = [p for p in player.passives if p != "glass_cannon"]

        for i in range(MAX_PASSIVES):
            x = base_x + i * (slot_size + gap)
            y = base_y
            # Empty slot background
            pygame.draw.rect(surface, (30, 30, 40), (x, y, slot_size, slot_size),
                             border_radius=4)
            pygame.draw.rect(surface, (80, 80, 100), (x, y, slot_size, slot_size), 2,
                             border_radius=4)

            if i < len(display_passives):
                key = display_passives[i]
                icon, color = PASSIVE_INFO.get(key, ("?", (180, 180, 180)))
                # Filled slot glow
                glow = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
                alpha = 40 + int(15 * math.sin(now * 0.003 + i))
                glow.fill((*color, alpha))
                surface.blit(glow, (x, y))
                # Icon letter
                txt = self.font.render(icon, True, color)
                tx = x + (slot_size - txt.get_width()) // 2
                ty = y + (slot_size - txt.get_height()) // 2
                surface.blit(txt, (tx, ty))
                # Border highlight
                pygame.draw.rect(surface, color, (x, y, slot_size, slot_size), 2,
                                 border_radius=4)

    def _draw_low_hp_vignette(self, surface: pygame.Surface, player):
        """Draw red screen edges when player HP is below 20%."""
        if player.hp <= 0 or player.max_hp <= 0:
            return
        ratio = player.hp / player.max_hp
        if ratio >= 0.2:
            return
        # Intensity: 0.0 at 20%, 1.0 at 0%
        intensity = 1.0 - (ratio / 0.2)
        alpha = int(60 + 100 * intensity)
        vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        # Draw red gradient borders
        edge = int(60 + 40 * intensity)
        for i in range(edge):
            a = int(alpha * (1.0 - i / edge))
            # Top
            pygame.draw.line(vignette, (180, 0, 0, a), (0, i), (SCREEN_WIDTH, i))
            # Bottom
            pygame.draw.line(vignette, (180, 0, 0, a), (0, SCREEN_HEIGHT - 1 - i), (SCREEN_WIDTH, SCREEN_HEIGHT - 1 - i))
            # Left
            pygame.draw.line(vignette, (180, 0, 0, a), (i, 0), (i, SCREEN_HEIGHT))
            # Right
            pygame.draw.line(vignette, (180, 0, 0, a), (SCREEN_WIDTH - 1 - i, 0), (SCREEN_WIDTH - 1 - i, SCREEN_HEIGHT))
        surface.blit(vignette, (0, 0))

    def draw_game_over(self, surface: pygame.Surface, wave: int, level: int,
                       kills: int = 0, legacy_points: int = 0):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        title = self.font_big.render("YOU DIED", True, RED)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 80))

        info = self.font.render(f"Reached Wave {wave}  |  Level {level}  |  {kills} Kills", True, WHITE)
        surface.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, SCREEN_HEIGHT // 2 - 20))

        if legacy_points > 0:
            lp = self.font.render(f"+{legacy_points} Legacy Points", True, YELLOW)
            surface.blit(lp, (SCREEN_WIDTH // 2 - lp.get_width() // 2, SCREEN_HEIGHT // 2 + 15))

        hint = self.font.render("Press R for Legacy Shop  |  ESC to quit", True, LIGHT_GRAY)
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT // 2 + 55))
