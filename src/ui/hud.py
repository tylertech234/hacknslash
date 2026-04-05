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
        """Horizontal energy bar under the HP bar. Gold border, fireworks when full."""
        bar_x, bar_y = 20, 48
        bar_w, bar_h = 220, 16
        energy = getattr(player, "energy", 0)
        max_energy = getattr(player, "max_energy", 100)
        ratio = min(1.0, energy / max_energy) if max_energy > 0 else 0
        now = pygame.time.get_ticks()
        ready = energy >= max_energy
        flash_on = ready and (now // 80) % 2 == 0   # faster flash

        # Subtle golden edge vignette when super is ready
        if ready:
            edge_pulse = int(28 + 18 * math.sin(now * 0.006))
            vig = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for t in range(14):
                a = max(0, edge_pulse - t * 3)
                pygame.draw.rect(vig, (255, 200, 0, a),
                                 (t, t, SCREEN_WIDTH - t * 2, SCREEN_HEIGHT - t * 2), 1)
            surface.blit(vig, (0, 0))

        # Background
        pygame.draw.rect(surface, (25, 18, 0), (bar_x, bar_y, bar_w, bar_h))

        # Fill
        fill_w = int(bar_w * ratio)
        if fill_w > 0:
            if ready:
                fill_c = (255, 255, 100) if flash_on else (255, 200, 0)
            else:
                r = min(255, 160 + int(95 * ratio))
                g = min(255, 80 + int(100 * ratio))
                fill_c = (r, g, 0)
            pygame.draw.rect(surface, fill_c, (bar_x, bar_y, fill_w, bar_h))

        # Border
        if ready:
            pulse = int(55 * abs(math.sin(now * 0.010)))
            border_c = (255, min(255, 200 + pulse), 0)
            # Thick glowing border
            pygame.draw.rect(surface, border_c, (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), 3)
            pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 1)
        else:
            pygame.draw.rect(surface, (160, 110, 10), (bar_x, bar_y, bar_w, bar_h), 1)

        # Tall flame ripple above bar when full
        if ready:
            _flame_h = 20
            flame_surf = pygame.Surface((bar_w, _flame_h), pygame.SRCALPHA)
            for i in range(0, bar_w, 4):
                flicker = math.sin(now * 0.011 + i * 0.35)
                fh = int(5 + 9 * abs(flicker))
                g_c = int(60 + 160 * abs(flicker))
                for row in range(fh):
                    alpha = int(255 * (1.0 - row / (fh + 1)))
                    pygame.draw.rect(flame_surf, (255, g_c, 0, alpha), (i, row, 4, 1))
            surface.blit(flame_surf, (bar_x, bar_y - _flame_h + 4))

        # Label — big bold flashing when ready
        if ready:
            lbl_color = (255, 255, 255) if flash_on else (255, 220, 0)
            lbl = self.font.render("⚡ SUPER READY ⚡", True, lbl_color)
            # Shadow
            shadow = self.font.render("⚡ SUPER READY ⚡", True, (80, 40, 0))
            lx = bar_x + bar_w // 2 - lbl.get_width() // 2
            surface.blit(shadow, (lx + 2, bar_y + 2))
            surface.blit(lbl, (lx, bar_y))
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
                # Filled slot glow — use set_alpha instead of SRCALPHA surface
                alpha = 40 + int(15 * math.sin(now * 0.003 + i))
                glow = pygame.Surface((slot_size, slot_size))
                glow.fill(color)
                glow.set_alpha(alpha)
                surface.blit(glow, (x, y))
                # Procedural icon
                picon = get_passive_icon(key, slot_size - 6, color)
                surface.blit(picon, (x + 3, y + 3))
                # Border highlight
                pygame.draw.rect(surface, color, (x, y, slot_size, slot_size), 2,
                                 border_radius=4)

    def _draw_low_hp_vignette(self, surface: pygame.Surface, player):
        """Draw red screen edges when player HP is below 20%.  Cached by intensity bucket."""
        if player.hp <= 0 or player.max_hp <= 0:
            return
        ratio = player.hp / player.max_hp
        if ratio >= 0.2:
            return
        # Quantise to ~10 visual steps so we don't rebuild every frame
        intensity = 1.0 - (ratio / 0.2)
        bucket = int(intensity * 10)
        if bucket != getattr(self, '_vig_bucket', -1):
            self._vig_bucket = bucket
            alpha = int(60 + 100 * intensity)
            vig = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            edge = int(60 + 40 * intensity)
            for i in range(edge):
                a = int(alpha * (1.0 - i / edge))
                pygame.draw.line(vig, (180, 0, 0, a), (0, i), (SCREEN_WIDTH, i))
                pygame.draw.line(vig, (180, 0, 0, a), (0, SCREEN_HEIGHT - 1 - i), (SCREEN_WIDTH, SCREEN_HEIGHT - 1 - i))
                pygame.draw.line(vig, (180, 0, 0, a), (i, 0), (i, SCREEN_HEIGHT))
                pygame.draw.line(vig, (180, 0, 0, a), (SCREEN_WIDTH - 1 - i, 0), (SCREEN_WIDTH - 1 - i, SCREEN_HEIGHT))
            self._vig_cache = vig
        surface.blit(self._vig_cache, (0, 0))

    def draw_game_over(self, surface: pygame.Surface, wave: int, level: int,
                       kills: int = 0, legacy_points: int = 0, game_over_start: int = 0):
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

        elapsed = pygame.time.get_ticks() - game_over_start if game_over_start else 0
        self._gameover_btns = {}

        if elapsed >= 3000:
            # Draw 3 clickable buttons
            btn_labels = [("run_summary", "Run Summary"), ("quit_to_menu", "Quit to Menu"), ("quit", "Quit")]
            btn_w, btn_h = 180, 44
            gap = 20
            total_w = len(btn_labels) * btn_w + (len(btn_labels) - 1) * gap
            start_x = SCREEN_WIDTH // 2 - total_w // 2
            btn_y = SCREEN_HEIGHT // 2 + 70
            mouse_pos = pygame.mouse.get_pos()
            # Fade in over 400ms
            fade_t = min(1.0, (elapsed - 3000) / 400)
            btn_alpha = int(255 * fade_t)
            for i, (key, label) in enumerate(btn_labels):
                bx = start_x + i * (btn_w + gap)
                rect = pygame.Rect(bx, btn_y, btn_w, btn_h)
                self._gameover_btns[key] = rect
                hovered = rect.collidepoint(mouse_pos)
                bg_color = (60, 20, 20) if not hovered else (100, 30, 30)
                border_color = (180, 60, 60) if not hovered else (255, 100, 100)
                btn_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
                pygame.draw.rect(btn_surf, (*bg_color, btn_alpha), (0, 0, btn_w, btn_h), border_radius=8)
                pygame.draw.rect(btn_surf, (*border_color, btn_alpha), (0, 0, btn_w, btn_h), 2, border_radius=8)
                surface.blit(btn_surf, (bx, btn_y))
                lbl_color = (255, 220, 220) if hovered else (200, 160, 160)
                lbl_surf = self.font_small.render(label, True, lbl_color)
                lbl_surf.set_alpha(btn_alpha)
                surface.blit(lbl_surf, (bx + btn_w // 2 - lbl_surf.get_width() // 2,
                                        btn_y + btn_h // 2 - lbl_surf.get_height() // 2))
        else:
            # Show a brief "..." while waiting
            wait_t = elapsed / 3000
            dots = "." * (int(wait_t * 6) % 4)
            hint = self.font_small.render(dots, True, LIGHT_GRAY)
            surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT // 2 + 70))
