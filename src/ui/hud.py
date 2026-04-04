import pygame
import math
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, RED, GREEN, WHITE, YELLOW, BLACK, LIGHT_GRAY,
    XP_DARKNESS_BONUS, MAX_PASSIVES, PASSIVE_INFO,
)
from src.ui.icons import get_passive_icon, get_weapon_icon
from src.systems.compendium import DISPLAY_NAMES as _ENEMY_DISPLAY_NAMES


class HUD:
    """Draws the heads-up display: HP bar, XP bar, wave counter, level."""

    def __init__(self):
        self.font = pygame.font.SysFont("consolas", 20)
        self.font_big = pygame.font.SysFont("consolas", 36)
        self.font_small = pygame.font.SysFont("consolas", 14)

    def draw(self, surface: pygame.Surface, player, wave: int, enemy_count: int,
             darkness: float = 0.0, boss_wave: bool = False, boss_enemies: list = None):
        self._draw_hp_bar(surface, player)
        self._draw_vertical_xp_bar(surface, player)
        self._draw_energy_bar(surface, player)
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

    def _draw_vertical_xp_bar(self, surface: pygame.Surface, player):
        """Vertical class-themed XP bar at bottom-left, 1/3 screen height."""
        _cls_colors = {
            "knight": (0, 180, 255),
            "archer": (0, 220, 100),
            "jester": (200, 50, 220),
        }
        cls_color = _cls_colors.get(getattr(player, "char_class", "knight"), (0, 180, 255))
        now = pygame.time.get_ticks()
        ratio = player.xp / player.xp_to_next if player.xp_to_next > 0 else 0

        # Position: bottom-left, 1/3 screen height, above passive slots
        # Passive slots sit at SCREEN_HEIGHT - 36 - 16 = 668
        slot_clearance = 36 + 16 + 10  # slot_size + margin + gap
        bar_h = SCREEN_HEIGHT // 3
        bar_w = 20
        bar_x = 6
        bar_y = SCREEN_HEIGHT - slot_clearance - bar_h

        # Background
        pygame.draw.rect(surface, (10, 15, 25), (bar_x, bar_y, bar_w, bar_h), border_radius=6)

        # Fill (bottom-to-top)
        fill_h = int(bar_h * ratio)
        if fill_h > 0:
            if ratio > 0.8:
                pulse = int(25 * abs(math.sin(now * 0.005)))
                fc = (min(255, cls_color[0] + pulse),
                      min(255, cls_color[1] + pulse),
                      min(255, cls_color[2] + pulse))
            else:
                fc = cls_color
            pygame.draw.rect(surface, fc,
                             (bar_x, bar_y + bar_h - fill_h, bar_w, fill_h),
                             border_radius=6)

        # Tick marks every 25%
        for i in range(1, 4):
            ty = bar_y + bar_h - int(bar_h * i / 4)
            pygame.draw.line(surface, (35, 45, 65), (bar_x + 3, ty), (bar_x + bar_w - 3, ty), 1)

        # Border
        pygame.draw.rect(surface, cls_color, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=6)

        # Level text above bar
        lv_surf = self.font_small.render("LV", True, cls_color)
        surface.blit(lv_surf, (bar_x + bar_w // 2 - lv_surf.get_width() // 2, bar_y - 28))
        num_surf = self.font_small.render(str(player.level), True, WHITE)
        surface.blit(num_surf, (bar_x + bar_w // 2 - num_surf.get_width() // 2, bar_y - 14))

    def _draw_energy_bar(self, surface: pygame.Surface, player):
        """Horizontal energy bar under the HP bar. Gold border, fire when full."""
        bar_x, bar_y = 20, 48
        bar_w, bar_h = 220, 16
        energy = getattr(player, "energy", 0)
        max_energy = getattr(player, "max_energy", 100)
        ratio = min(1.0, energy / max_energy) if max_energy > 0 else 0
        now = pygame.time.get_ticks()
        ready = energy >= max_energy
        flash_on = ready and (now // 120) % 2 == 0

        # Background
        pygame.draw.rect(surface, (25, 18, 0), (bar_x, bar_y, bar_w, bar_h))

        # Fill colour
        fill_w = int(bar_w * ratio)
        if fill_w > 0:
            if ready:
                # Flashing bright gold when full
                if flash_on:
                    fill_c = (255, 255, 160)
                else:
                    fill_c = (230, 180, 20)
            else:
                # Dark amber gradient-ish: brighter as it fills
                r = min(255, 160 + int(95 * ratio))
                g = min(255, 80 + int(100 * ratio))
                fill_c = (r, g, 0)
            pygame.draw.rect(surface, fill_c, (bar_x, bar_y, fill_w, bar_h))

        # Border — plain gold, fire-glow when full
        if ready:
            pulse = int(35 * abs(math.sin(now * 0.008)))
            border_c = (255, min(255, 200 + pulse), 40)
            pygame.draw.rect(surface, border_c, (bar_x, bar_y, bar_w, bar_h), 2)
            # Inner bright line
            pygame.draw.rect(surface, (255, 255, 100), (bar_x + 1, bar_y + 1, bar_w - 2, 2))
        else:
            pygame.draw.rect(surface, (160, 110, 10), (bar_x, bar_y, bar_w, bar_h), 1)

        # Flame ripple along top of bar when full
        if ready:
            for i in range(0, bar_w, 5):
                flicker = math.sin(now * 0.009 + i * 0.4)
                fh = int(3 + 3 * abs(flicker))
                fx = bar_x + i
                g_c = int(80 + 140 * abs(flicker))
                for row in range(fh):
                    alpha = int(240 * (1.0 - row / (fh + 1)))
                    glow_line = pygame.Surface((5, 1), pygame.SRCALPHA)
                    glow_line.fill((255, g_c, 0, alpha))
                    surface.blit(glow_line, (fx, bar_y + row))

        # "SUPER" label with flash
        if ready:
            lbl_color = (255, 255, 100) if flash_on else (200, 160, 20)
            lbl = self.font_small.render("SUPER READY", True, lbl_color)
            surface.blit(lbl, (bar_x + bar_w // 2 - lbl.get_width() // 2, bar_y + 1))
        else:
            e_lbl = self.font_small.render(f"ENERGY  {energy}/{max_energy}", True, (140, 100, 10))
            surface.blit(e_lbl, (bar_x + 4, bar_y + 1))


    def _draw_info(self, surface: pygame.Surface, player, wave: int, enemy_count: int,
                   darkness: float = 0.0, boss_wave: bool = False):
        lvl = self.font.render(f"Lv {player.level}", True, YELLOW)
        surface.blit(lvl, (250, 20))

        # Weapon icon + name
        icon_size = 20
        wpn_icon_key = getattr(player, "weapon_name", "")
        if wpn_icon_key:
            wicon = get_weapon_icon(wpn_icon_key, icon_size)
            surface.blit(wicon, (250, 42))
        wpn = self.font_small.render(player.weapon["name"], True, LIGHT_GRAY)
        surface.blit(wpn, (250 + (icon_size + 4 if wpn_icon_key else 0), 44))

        # Coin counter
        coins = getattr(player, "coins", 0)
        coin_txt = self.font_small.render(f"$ {coins}", True, (255, 200, 50))
        surface.blit(coin_txt, (250, 62))

        # Wave info — show BOSS prefix inline when boss wave is active
        boss_prefix = "\u2605 BOSS  " if boss_wave else ""
        wave_label = f"{boss_prefix}Wave {wave}  |  Enemies: {enemy_count}"
        wave_color = (255, 80, 80) if boss_wave else LIGHT_GRAY
        wave_txt = self.font.render(wave_label, True, wave_color)
        surface.blit(wave_txt, (SCREEN_WIDTH - wave_txt.get_width() - 20, 20))

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
        """Draw a large HP bar at top-center for each boss, name rendered inside."""
        bar_w = 420
        bar_h = 26
        gap = 8
        bar_x = SCREEN_WIDTH // 2 - bar_w // 2
        bar_y = 80
        alive_bosses = [b for b in boss_enemies if b.alive]
        for i, boss in enumerate(alive_bosses):
            y = bar_y + i * (bar_h + gap)
            ratio = max(0, boss.hp / boss.max_hp)
            boss_label = _ENEMY_DISPLAY_NAMES.get(
                boss.enemy_type,
                boss.enemy_type.replace("_", " ").title()
            )
            fill_color = (255, 50, 50) if boss.is_big_boss else (220, 130, 0)
            # Background
            pygame.draw.rect(surface, (40, 0, 0), (bar_x, y, bar_w, bar_h))
            # HP fill
            fill_w = int(bar_w * ratio)
            pygame.draw.rect(surface, fill_color, (bar_x, y, fill_w, bar_h))
            # Border
            border_color = (255, 100, 100) if boss.is_big_boss else (255, 200, 60)
            pygame.draw.rect(surface, border_color, (bar_x, y, bar_w, bar_h), 2)
            # Name + HP inside the bar, vertically centred
            label_text = f"{boss_label}  \u2665 {boss.hp} / {boss.max_hp}"
            name_surf = self.font_small.render(label_text, True, WHITE)
            lx = bar_x + 8
            ly = y + bar_h // 2 - name_surf.get_height() // 2
            surface.blit(name_surf, (lx, ly))

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
                # Procedural icon
                picon = get_passive_icon(key, slot_size - 6, color)
                surface.blit(picon, (x + 3, y + 3))
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
