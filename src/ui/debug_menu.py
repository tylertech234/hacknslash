"""Debug / developer menu — accessible from the bug icon on main menu."""

import pygame
import math
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW, BLACK


class DebugMenu:
    """Dev menu with cheats and debug toggles. Opened from main menu bug icon."""

    def __init__(self):
        self.active = False
        self.selected = 0
        self.font_big = pygame.font.SysFont("consolas", 28, bold=True)
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 14)

        # Cheat options
        self.cheats = {
            "god_mode": False,
            "double_speed": False,
            "double_damage": False,
            "one_hit_kills": False,
            "no_cooldown": False,
            "infinite_dash": False,
            "max_level": False,
            "show_hitboxes": False,
            "show_log": False,
            "show_fps": False,
            "show_positions": False,
            "skip_to_boss": False,
        }
        self.cheat_labels = {
            "god_mode": "God Mode (Infinite HP)",
            "double_speed": "2x Player Speed",
            "double_damage": "2x Damage",
            "one_hit_kills": "One-Hit Kills",
            "no_cooldown": "No Attack Cooldown",
            "infinite_dash": "Infinite Dash (No Cooldown)",
            "max_level": "Start at Level 10",
            "show_hitboxes": "Show Hitboxes",
            "show_log": "On-Screen Log",
            "show_fps": "Show FPS Counter",
            "show_positions": "Show Entity Positions",
            "skip_to_boss": "Skip to Boss Wave",
        }
        self.cheat_keys = list(self.cheats.keys())
        self.start_zone = 0  # 0=wasteland, 1=city, 2=abyss
        self.zone_names = ["wasteland", "city", "abyss"]
        self.start_wave = 1

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Returns 'back' or None."""
        if not self.active:
            return None
        if event.type != pygame.KEYDOWN:
            return None

        total_items = len(self.cheat_keys) + 2  # +2 for zone picker and wave picker

        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.active = False
            return "back"
        elif event.key in (pygame.K_w, pygame.K_UP):
            self.selected = (self.selected - 1) % total_items
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            self.selected = (self.selected + 1) % total_items
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            if self.selected < len(self.cheat_keys):
                key = self.cheat_keys[self.selected]
                self.cheats[key] = not self.cheats[key]
        elif event.key in (pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT):
            direction = 1 if event.key in (pygame.K_d, pygame.K_RIGHT) else -1
            idx = self.selected - len(self.cheat_keys)
            if idx == 0:  # zone picker
                self.start_zone = (self.start_zone + direction) % len(self.zone_names)
            elif idx == 1:  # wave picker
                self.start_wave = max(1, min(30, self.start_wave + direction))
        return None

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return

        now = pygame.time.get_ticks()
        surface.fill((10, 5, 15))

        # Title with bug icon
        title = self.font_big.render("DEV / DEBUG MENU", True, (255, 80, 80))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

        # Bug icon next to title
        bug_x = SCREEN_WIDTH // 2 - title.get_width() // 2 - 40
        self._draw_bug_icon(surface, bug_x, 48, 20, (255, 80, 80))

        start_y = 100
        row_h = 32
        box_w = 500
        box_x = SCREEN_WIDTH // 2 - box_w // 2

        # Cheat toggles
        for i, key in enumerate(self.cheat_keys):
            y = start_y + i * row_h
            is_sel = i == self.selected
            val = self.cheats[key]
            label = self.cheat_labels[key]

            if is_sel:
                bg = pygame.Surface((box_w, row_h - 2), pygame.SRCALPHA)
                bg.fill((255, 80, 80, 20))
                surface.blit(bg, (box_x, y))

            name_color = WHITE if is_sel else (140, 140, 160)
            name_surf = self.font_small.render(label, True, name_color)
            surface.blit(name_surf, (box_x + 10, y + 6))

            state = "ON" if val else "OFF"
            state_color = (100, 255, 100) if val else (255, 80, 80)
            state_surf = self.font_small.render(state, True, state_color)
            surface.blit(state_surf, (box_x + box_w - state_surf.get_width() - 10, y + 6))

        # Zone picker
        zone_idx = len(self.cheat_keys)
        zy = start_y + zone_idx * row_h
        is_sel = self.selected == zone_idx
        if is_sel:
            bg = pygame.Surface((box_w, row_h - 2), pygame.SRCALPHA)
            bg.fill((255, 80, 80, 20))
            surface.blit(bg, (box_x, zy))
        name_color = WHITE if is_sel else (140, 140, 160)
        name_surf = self.font_small.render("Start Zone", True, name_color)
        surface.blit(name_surf, (box_x + 10, zy + 6))
        zone_name = self.zone_names[self.start_zone].title()
        val_surf = self.font_small.render(f"< {zone_name} >", True, name_color)
        surface.blit(val_surf, (box_x + box_w - val_surf.get_width() - 10, zy + 6))

        # Wave picker
        wave_idx = zone_idx + 1
        wy = start_y + wave_idx * row_h
        is_sel = self.selected == wave_idx
        if is_sel:
            bg = pygame.Surface((box_w, row_h - 2), pygame.SRCALPHA)
            bg.fill((255, 80, 80, 20))
            surface.blit(bg, (box_x, wy))
        name_color = WHITE if is_sel else (140, 140, 160)
        name_surf = self.font_small.render("Start Wave", True, name_color)
        surface.blit(name_surf, (box_x + 10, wy + 6))
        val_surf = self.font_small.render(f"< {self.start_wave} >", True, name_color)
        surface.blit(val_surf, (box_x + box_w - val_surf.get_width() - 10, wy + 6))

        # Separator
        sep_y = start_y + (wave_idx + 1) * row_h + 5
        pygame.draw.line(surface, (60, 40, 40), (box_x, sep_y), (box_x + box_w, sep_y), 1)

        # Hint
        hint = self.font_small.render(
            "W/S navigate | Enter/Space toggle | A/D adjust | ESC back", True, (70, 70, 90))
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, sep_y + 15))

        # Warning
        warn = self.font_small.render("Debug features disable achievements.", True, (180, 80, 80))
        surface.blit(warn, (SCREEN_WIDTH // 2 - warn.get_width() // 2, sep_y + 40))

    @staticmethod
    def _draw_bug_icon(surface, x, y, size, color):
        """Draw a simple bug/beetle icon."""
        cx, cy = x, y
        r = size // 2
        # Body (oval)
        body_r = pygame.Rect(cx - r, cy - r // 2, r * 2, r + 2)
        pygame.draw.ellipse(surface, color, body_r)
        # Head
        pygame.draw.circle(surface, color, (cx, cy - r // 2 - 3), r // 3 + 1)
        # Legs (3 on each side)
        for i in range(3):
            offset = -r // 3 + i * (r // 2)
            # Left leg
            pygame.draw.line(surface, color, (cx - r + 1, cy + offset),
                           (cx - r - 5, cy + offset - 3), 2)
            # Right leg
            pygame.draw.line(surface, color, (cx + r - 1, cy + offset),
                           (cx + r + 5, cy + offset - 3), 2)
        # Antennae
        pygame.draw.line(surface, color, (cx - 2, cy - r // 2 - 5),
                       (cx - 6, cy - r // 2 - 10), 1)
        pygame.draw.line(surface, color, (cx + 2, cy - r // 2 - 5),
                       (cx + 6, cy - r // 2 - 10), 1)
