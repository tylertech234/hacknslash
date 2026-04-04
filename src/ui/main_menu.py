"""Main menu screen — New Run, Settings, Legacy Stats, Quit."""

import pygame
import math
import json
import os
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW, BLACK, VERSION


SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "settings_save.json")

DEFAULT_SETTINGS = {
    "master_volume": 1.0,
    "sfx_volume": 1.0,
    "music_volume": 0.6,
    "particles": "high",       # low / medium / high
    "vignette": True,
    "screen_shake": True,
    "fullscreen": False,
    "resolution": "native",
    "dev_options": False,
}


def load_settings() -> dict:
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
        # Merge with defaults for any missing keys
        merged = {**DEFAULT_SETTINGS, **data}
        return merged
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


class MainMenuScreen:
    """Title screen with menu options."""

    def __init__(self):
        self.active = True
        self.selected = 0
        self.options = ["New Run", "Compendium", "Settings", "Quit"]
        self.settings_open = False
        self.settings_selected = 0
        self.settings = load_settings()
        self.font_title = pygame.font.SysFont("consolas", 48, bold=True)
        self.font_sub = pygame.font.SysFont("consolas", 20)
        self.font = pygame.font.SysFont("consolas", 22)
        self.font_small = pygame.font.SysFont("consolas", 16)
        self._anim_time = 0

        # Secret: 10 rapid clicks anywhere in settings to reveal dev options
        self._dev_click_times: list[int] = []
        self._dev_revealed = False

        # Build resolution choices from what main.py populated
        import src.settings as _s
        _res_keys = list(_s.RESOLUTIONS.keys()) if _s.RESOLUTIONS else ["native", "1920x1080", "1280x720"]

        self.settings_items = [
            {"key": "master_volume", "name": "Master Volume", "type": "slider", "min": 0.0, "max": 1.0, "step": 0.1},
            {"key": "sfx_volume",    "name": "SFX Volume",    "type": "slider", "min": 0.0, "max": 1.0, "step": 0.1},
            {"key": "music_volume",  "name": "Music Volume",  "type": "slider", "min": 0.0, "max": 1.0, "step": 0.1},
            {"key": "particles",     "name": "Particles",     "type": "choice", "choices": ["low", "medium", "high"]},
            {"key": "vignette",      "name": "Vignette",      "type": "toggle"},
            {"key": "screen_shake",  "name": "Screen Shake",  "type": "toggle"},
            {"key": "fullscreen",    "name": "Fullscreen",    "type": "toggle"},
            {"key": "resolution",    "name": "Resolution",    "type": "choice", "choices": _res_keys},
        ]
        self._res_changed = False  # track if restart is needed
        self._dev_item = {"key": "dev_options", "name": "Dev Options", "type": "toggle"}

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Returns 'new_run', 'quit', 'debug_menu', or None."""
        if not self.active:
            return None

        # Mouse click on bug icon
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Secret dev click counter in settings screen
            if self.settings_open and not self._dev_revealed:
                now = pygame.time.get_ticks()
                self._dev_click_times.append(now)
                # Keep only clicks within last 2 seconds
                self._dev_click_times = [t for t in self._dev_click_times if now - t <= 2000]
                if len(self._dev_click_times) >= 10:
                    self._dev_revealed = True
                    if self._dev_item not in self.settings_items:
                        self.settings_items.append(self._dev_item)
                    self._dev_click_times.clear()

            if self.settings.get("dev_options") and not self.settings_open:
                mx, my = event.pos
                bug_x, bug_y, bug_r = SCREEN_WIDTH - 60, 150, 18
                if (mx - bug_x) ** 2 + (my - bug_y) ** 2 <= (bug_r + 5) ** 2:
                    return "debug_menu"

        if event.type != pygame.KEYDOWN:
            return None

        if self.settings_open:
            return self._handle_settings_event(event)

        if event.key in (pygame.K_w, pygame.K_UP):
            self.selected = (self.selected - 1) % len(self.options)
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            self.selected = (self.selected + 1) % len(self.options)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            opt = self.options[self.selected]
            if opt == "New Run":
                self.active = False
                return "new_run"
            elif opt == "Compendium":
                return "compendium"
            elif opt == "Settings":
                self.settings_open = True
                self.settings_selected = 0
                # If dev_options already enabled, show the toggle
                if self.settings.get("dev_options") and self._dev_item not in self.settings_items:
                    self._dev_revealed = True
                    self.settings_items.append(self._dev_item)
            elif opt == "Quit":
                return "quit"
        elif event.key == pygame.K_ESCAPE:
            return "quit"
        return None

    def _handle_settings_event(self, event: pygame.event.Event) -> str | None:
        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.settings_open = False
            save_settings(self.settings)
            return None

        if event.key in (pygame.K_w, pygame.K_UP):
            self.settings_selected = (self.settings_selected - 1) % len(self.settings_items)
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            self.settings_selected = (self.settings_selected + 1) % len(self.settings_items)
        elif event.key in (pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT):
            item = self.settings_items[self.settings_selected]
            direction = 1 if event.key in (pygame.K_d, pygame.K_RIGHT) else -1
            key = item["key"]

            if item["type"] == "slider":
                val = self.settings[key] + direction * item["step"]
                self.settings[key] = round(max(item["min"], min(item["max"], val)), 2)
            elif item["type"] == "toggle":
                self.settings[key] = not self.settings[key]
            elif item["type"] == "choice":
                choices = item["choices"]
                idx = choices.index(self.settings[key]) if self.settings[key] in choices else 0
                self.settings[key] = choices[(idx + direction) % len(choices)]
                if key == "resolution":
                    self._res_changed = True
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            item = self.settings_items[self.settings_selected]
            if item["type"] == "toggle":
                self.settings[item["key"]] = not self.settings[item["key"]]
        return None

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return

        now = pygame.time.get_ticks()
        surface.fill((8, 8, 14))

        # Animated background particles
        for i in range(30):
            px = (i * 97 + now // 40) % SCREEN_WIDTH
            py = (i * 53 + now // 60) % SCREEN_HEIGHT
            alpha = int(30 + 20 * math.sin(now * 0.001 + i))
            ps = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(ps, (80, 120, 180, alpha), (2, 2), 2)
            surface.blit(ps, (px, py))

        # Title
        glow = int(200 + 55 * math.sin(now * 0.002))
        title = self.font_title.render("CYBER SURVIVOR", True, (glow, glow, 255))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))

        # Subtitle
        sub = self.font_sub.render("cyber. survive. repeat.", True, (100, 120, 160))
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 210))

        if self.settings_open:
            self._draw_settings(surface, now)
        else:
            self._draw_menu(surface, now)

        # Version watermark — bottom-right corner
        ver_surf = self.font_small.render(f"v{VERSION}  Early Access", True, (55, 55, 75))
        surface.blit(ver_surf, (SCREEN_WIDTH - ver_surf.get_width() - 12, SCREEN_HEIGHT - ver_surf.get_height() - 8))

    def _draw_menu(self, surface: pygame.Surface, now: int):
        start_y = 320
        for i, opt in enumerate(self.options):
            is_sel = i == self.selected
            color = YELLOW if is_sel else (140, 140, 160)
            prefix = "> " if is_sel else "  "

            text = self.font.render(f"{prefix}{opt}", True, color)
            x = SCREEN_WIDTH // 2 - text.get_width() // 2
            y = start_y + i * 50

            if is_sel:
                # Selection highlight bar
                bar_w = text.get_width() + 40
                bar = pygame.Surface((bar_w, 36), pygame.SRCALPHA)
                bar.fill((255, 215, 0, 25))
                surface.blit(bar, (x - 20, y - 4))

            surface.blit(text, (x, y))

        # Controls hint
        hint = self.font_small.render("W/S to navigate  |  E/Enter to select", True, (70, 70, 90))
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 520))

        # Bug icon when dev_options enabled
        if self.settings.get("dev_options"):
            self._draw_bug_icon(surface, SCREEN_WIDTH - 60, 150, now)

    def _draw_settings(self, surface: pygame.Surface, now: int):
        # Title
        title = self.font.render("SETTINGS", True, YELLOW)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 280))

        start_y = 330
        row_h = 40
        box_w = 400
        box_x = SCREEN_WIDTH // 2 - box_w // 2

        for i, item in enumerate(self.settings_items):
            y = start_y + i * row_h
            is_sel = i == self.settings_selected
            val = self.settings[item["key"]]

            # Background
            if is_sel:
                bg = pygame.Surface((box_w, row_h - 4), pygame.SRCALPHA)
                bg.fill((255, 215, 0, 20))
                surface.blit(bg, (box_x, y))

            # Name
            name_color = WHITE if is_sel else (140, 140, 160)
            name_surf = self.font_small.render(item["name"], True, name_color)
            surface.blit(name_surf, (box_x + 10, y + 8))

            # Value
            if item["type"] == "slider":
                val_str = f"{'<' if is_sel else ' '} {val:.0%} {'>' if is_sel else ' '}"
                # Draw slider bar
                bar_x = box_x + 220
                bar_w = 120
                bar_y = y + 14
                pygame.draw.rect(surface, (50, 50, 60), (bar_x, bar_y, bar_w, 6), border_radius=3)
                fill_w = int(bar_w * val)
                if fill_w > 0:
                    pygame.draw.rect(surface, YELLOW if is_sel else (100, 100, 120),
                                   (bar_x, bar_y, fill_w, 6), border_radius=3)
                pct = self.font_small.render(f"{val:.0%}", True, name_color)
                surface.blit(pct, (bar_x + bar_w + 10, y + 8))
            elif item["type"] == "toggle":
                state = "ON" if val else "OFF"
                state_color = (100, 255, 100) if val else (255, 80, 80)
                state_surf = self.font_small.render(state, True, state_color)
                surface.blit(state_surf, (box_x + box_w - state_surf.get_width() - 10, y + 8))
            elif item["type"] == "choice":
                val_surf = self.font_small.render(f"< {val} >", True, name_color)
                surface.blit(val_surf, (box_x + box_w - val_surf.get_width() - 10, y + 8))

        # Hint
        hint_text = "W/S navigate  |  A/D adjust  |  ESC back"
        hint = self.font_small.render(hint_text, True, (70, 70, 90))
        hy = start_y + len(self.settings_items) * row_h + 20
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, hy))

        if self._res_changed:
            restart_hint = self.font_small.render("Resolution change takes effect on restart", True, (255, 180, 60))
            surface.blit(restart_hint, (SCREEN_WIDTH // 2 - restart_hint.get_width() // 2, hy + 22))

        # Flash effect when dev options just revealed
        if self._dev_revealed and self._dev_item in self.settings_items:
            dev_idx = self.settings_items.index(self._dev_item)
            dy = start_y + dev_idx * row_h
            elapsed = now - (self._dev_click_times[0] if self._dev_click_times else now)
            # Brief golden flash for 600ms on first reveal
            flash_age = (now % 1200)
            if flash_age < 600:
                alpha = int(40 * (1.0 - flash_age / 600))
                flash = pygame.Surface((box_w, row_h - 4), pygame.SRCALPHA)
                flash.fill((255, 215, 0, alpha))
                surface.blit(flash, (box_x, dy))

    def _draw_bug_icon(self, surface, x, y, now):
        """Draw an animated bug icon that pulses."""
        pulse = 1.0 + 0.1 * math.sin(now * 0.004)
        r = int(14 * pulse)
        color = (255, 80, 80)
        # Body
        pygame.draw.ellipse(surface, color, (x - r, y - r // 2, r * 2, r + 2))
        # Head
        pygame.draw.circle(surface, color, (x, y - r // 2 - 3), r // 3 + 1)
        # Legs
        for i in range(3):
            off = -r // 3 + i * (r // 2)
            pygame.draw.line(surface, color, (x - r + 1, y + off), (x - r - 5, y + off - 3), 2)
            pygame.draw.line(surface, color, (x + r - 1, y + off), (x + r + 5, y + off - 3), 2)
        # Antennae
        pygame.draw.line(surface, color, (x - 3, y - r // 2 - 4), (x - 7, y - r // 2 - 10), 1)
        pygame.draw.line(surface, color, (x + 3, y - r // 2 - 4), (x + 7, y - r // 2 - 10), 1)
        # Label
        label = self.font_small.render("DEV", True, color)
        surface.blit(label, (x - label.get_width() // 2, y + r + 6))
