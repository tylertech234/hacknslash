import pygame
import math
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, YELLOW, BLACK
from src.systems.weapons import CHARACTER_CLASSES, WEAPONS


class CharacterSelectScreen:
    """Full-screen character selection before the game starts."""

    def __init__(self):
        self.active = True
        self.selected = 0
        self.classes = list(CHARACTER_CLASSES.keys())  # knight, archer, jester
        self.font_big = pygame.font.SysFont("consolas", 36, bold=True)
        self.font = pygame.font.SysFont("consolas", 20)
        self.font_small = pygame.font.SysFont("consolas", 14)
        self.chosen_class = None  # set when player picks

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Returns class key ('knight', 'archer', 'jester') or None."""
        if not self.active:
            return None
        # Click on a class card
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            card_w, card_h, gap = 220, 340, 30
            total_w = len(self.classes) * card_w + (len(self.classes) - 1) * gap
            start_x = SCREEN_WIDTH // 2 - total_w // 2
            card_y = 120
            for i in range(len(self.classes)):
                cx_c = start_x + i * (card_w + gap)
                if cx_c <= mx <= cx_c + card_w and card_y <= my <= card_y + card_h:
                    self.chosen_class = self.classes[i]
                    self.active = False
                    return self.chosen_class
            return None

        if event.type != pygame.KEYDOWN:
            return None

        if event.key in (pygame.K_a, pygame.K_LEFT):
            self.selected = (self.selected - 1) % len(self.classes)
        elif event.key in (pygame.K_d, pygame.K_RIGHT):
            self.selected = (self.selected + 1) % len(self.classes)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            self.chosen_class = self.classes[self.selected]
            self.active = False
            return self.chosen_class
        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
            idx = event.key - pygame.K_1
            if 0 <= idx < len(self.classes):
                self.chosen_class = self.classes[idx]
                self.active = False
                return self.chosen_class
        return None

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return

        surface.fill((10, 10, 20))
        now = pygame.time.get_ticks()

        # Title
        title = self.font_big.render("CHOOSE YOUR CLASS", True, YELLOW)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        card_w = 220
        card_h = 340
        gap = 30
        total_w = len(self.classes) * card_w + (len(self.classes) - 1) * gap
        start_x = SCREEN_WIDTH // 2 - total_w // 2
        card_y = 120

        for i, cls_key in enumerate(self.classes):
            cls = CHARACTER_CLASSES[cls_key]
            cx = start_x + i * (card_w + gap)
            is_sel = i == self.selected

            # Card background
            bg_color = (30, 30, 50) if not is_sel else (40, 40, 70)
            pygame.draw.rect(surface, bg_color, (cx, card_y, card_w, card_h), border_radius=10)

            # Border
            border_color = cls["color"] if is_sel else (60, 60, 80)
            width = 3 if is_sel else 1
            pygame.draw.rect(surface, border_color, (cx, card_y, card_w, card_h), width, border_radius=10)

            # Glow pulse when selected
            if is_sel:
                pulse = int(20 + 15 * math.sin(now * 0.004))
                glow = pygame.Surface((card_w + 20, card_h + 20), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*cls["color"], pulse), (0, 0, card_w + 20, card_h + 20), border_radius=14)
                surface.blit(glow, (cx - 10, card_y - 10))

            # Number
            num = self.font_small.render(f"[{i + 1}]", True, (100, 100, 100))
            surface.blit(num, (cx + 10, card_y + 10))

            # Character preview
            preview_x = cx + card_w // 2
            preview_y = card_y + 90
            self._draw_preview(surface, preview_x, preview_y, cls_key, cls["color"], now)

            # Name
            name = self.font.render(cls["name"], True, cls["color"])
            surface.blit(name, (cx + card_w // 2 - name.get_width() // 2, card_y + 160))

            # Description
            desc_lines = self._wrap_text(cls["desc"], 28)
            for j, line in enumerate(desc_lines):
                d = self.font_small.render(line, True, (180, 180, 180))
                surface.blit(d, (cx + card_w // 2 - d.get_width() // 2, card_y + 190 + j * 18))

            # Starting weapon
            wpn = WEAPONS[cls["start_weapon"]]
            wpn_text = self.font_small.render(f"Weapon: {wpn['name']}", True, wpn["blade_color"])
            surface.blit(wpn_text, (cx + card_w // 2 - wpn_text.get_width() // 2, card_y + 240))

            # Passives
            py_off = card_y + 265
            for p in cls["passives"]:
                pname = p.replace("_", " ").title()
                pt = self.font_small.render(f"• {pname}", True, (150, 200, 150))
                surface.blit(pt, (cx + 20, py_off))
                py_off += 18

            # Stats
            stats_y = card_y + card_h - 30
            hp_text = f"HP{cls['hp_bonus']:+d}" if cls['hp_bonus'] else "HP+0"
            dmg_text = f"DMG{cls['damage_bonus']:+d}" if cls['damage_bonus'] else "DMG+0"
            spd_text = f"SPD{cls['speed_bonus']:+.1f}" if cls['speed_bonus'] else "SPD+0"
            stats = self.font_small.render(f"{hp_text}  {dmg_text}  {spd_text}", True, (140, 140, 160))
            surface.blit(stats, (cx + card_w // 2 - stats.get_width() // 2, stats_y))

        # Hint
        hint = self.font_small.render("A/D or Left/Right to browse  |  E/Enter/Space or 1-3 to select", True, (80, 80, 100))
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 40))

    def _draw_preview(self, surface, cx, cy, cls_key, color, now):
        """Draw a mini character preview."""
        if cls_key == "knight":
            # Armored cyberknight
            pygame.draw.rect(surface, (30, 40, 60), (cx - 5, cy + 10, 4, 10))
            pygame.draw.rect(surface, (30, 40, 60), (cx + 2, cy + 10, 4, 10))
            pygame.draw.polygon(surface, (40, 55, 90), [
                (cx - 10, cy + 10), (cx + 10, cy + 10),
                (cx + 12, cy - 8), (cx - 12, cy - 8)])
            pulse = int(4 + 2 * math.sin(now * 0.006))
            core_s = pygame.Surface((pulse * 2, pulse * 2), pygame.SRCALPHA)
            pygame.draw.circle(core_s, (0, 220, 255, 140), (pulse, pulse), pulse)
            surface.blit(core_s, (cx - pulse, cy - 4 - pulse))
            pygame.draw.circle(surface, (40, 55, 90), (cx, cy - 16), 8)
            pygame.draw.line(surface, color, (cx - 5, cy - 17), (cx + 5, cy - 17), 2)
            pygame.draw.line(surface, color, (cx, cy - 17), (cx, cy - 13), 2)
            pygame.draw.line(surface, color, (cx, cy - 24), (cx, cy - 20), 2)
        elif cls_key == "archer":
            # Sleek ranger
            pygame.draw.rect(surface, (20, 50, 40), (cx - 4, cy + 10, 3, 10))
            pygame.draw.rect(surface, (20, 50, 40), (cx + 2, cy + 10, 3, 10))
            pygame.draw.polygon(surface, (30, 60, 50), [
                (cx - 8, cy + 10), (cx + 8, cy + 10),
                (cx + 6, cy - 8), (cx - 6, cy - 8)])
            # Targeting reticle
            r = int(4 + 2 * math.sin(now * 0.005))
            pygame.draw.circle(surface, color, (cx, cy - 2), r, 1)
            pygame.draw.circle(surface, (30, 60, 50), (cx, cy - 16), 7)
            pygame.draw.line(surface, color, (cx - 5, cy - 16), (cx + 5, cy - 16), 1)
            # Hood point
            pygame.draw.polygon(surface, (25, 55, 45), [
                (cx - 7, cy - 14), (cx + 7, cy - 14), (cx, cy - 25)])
        elif cls_key == "jester":
            # Colorful chaotic jester
            pygame.draw.rect(surface, (60, 20, 60), (cx - 5, cy + 10, 4, 10))
            pygame.draw.rect(surface, (60, 20, 60), (cx + 2, cy + 10, 4, 10))
            # Two-tone torso
            pygame.draw.polygon(surface, (80, 30, 80), [
                (cx, cy + 10), (cx + 10, cy + 10),
                (cx + 8, cy - 8), (cx, cy - 8)])
            pygame.draw.polygon(surface, (200, 50, 200), [
                (cx, cy + 10), (cx - 10, cy + 10),
                (cx - 8, cy - 8), (cx, cy - 8)])
            pygame.draw.circle(surface, (70, 25, 70), (cx, cy - 16), 8)
            # Jester hat bells
            for side in (-1, 1):
                bx = cx + side * 10
                by = cy - 22 + int(math.sin(now * 0.006 + side) * 2)
                pygame.draw.line(surface, (255, 220, 0), (cx + side * 4, cy - 20), (bx, by), 2)
                pygame.draw.circle(surface, (255, 255, 0), (bx, by), 3)
            # Grin
            pygame.draw.arc(surface, (255, 255, 0),
                           (cx - 4, cy - 18, 8, 6), 3.14, 6.28, 1)

    def _wrap_text(self, text, max_chars):
        words = text.split()
        lines = []
        current = ""
        for w in words:
            if len(current) + len(w) + 1 <= max_chars:
                current = f"{current} {w}" if current else w
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)
        return lines
