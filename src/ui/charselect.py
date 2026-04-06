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
            card_w, card_h, gap = 240, 380, 30
            total_w = len(self.classes) * card_w + (len(self.classes) - 1) * gap
            start_x = SCREEN_WIDTH // 2 - total_w // 2
            card_y = 100
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

        card_w = 240
        card_h = 380
        gap = 30
        total_w = len(self.classes) * card_w + (len(self.classes) - 1) * gap
        start_x = SCREEN_WIDTH // 2 - total_w // 2
        card_y = 100

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
            preview_y = card_y + 100
            self._draw_preview(surface, preview_x, preview_y, cls_key, cls["color"], now)

            # Name
            name = self.font.render(cls["name"], True, cls["color"])
            surface.blit(name, (cx + card_w // 2 - name.get_width() // 2, card_y + 180))

            # Description — wrap within card padding
            desc_lines = self._wrap_text(cls["desc"], 32)
            for j, line in enumerate(desc_lines):
                d = self.font_small.render(line, True, (180, 180, 180))
                surface.blit(d, (cx + card_w // 2 - d.get_width() // 2, card_y + 210 + j * 18))

            # Starting weapon
            wpn = WEAPONS[cls["start_weapon"]]
            wpn_text = self.font_small.render(f"Weapon: {wpn['name']}", True, wpn["blade_color"])
            surface.blit(wpn_text, (cx + card_w // 2 - wpn_text.get_width() // 2, card_y + 262))

            # Passives
            py_off = card_y + 288
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
        """Draw a mini character preview with class-specific props."""
        if cls_key == "knight":
            # ---- Armored cyberknight with shield ----
            # Armored legs
            pygame.draw.rect(surface, (30, 40, 60), (cx - 7, cy + 12, 6, 14))
            pygame.draw.rect(surface, (30, 40, 60), (cx + 2, cy + 12, 6, 14))
            pygame.draw.line(surface, color, (cx - 6, cy + 18), (cx - 2, cy + 18), 1)
            pygame.draw.line(surface, color, (cx + 3, cy + 18), (cx + 7, cy + 18), 1)
            # Torso
            pygame.draw.polygon(surface, (40, 55, 90), [
                (cx - 14, cy + 12), (cx + 14, cy + 12),
                (cx + 16, cy - 10), (cx - 16, cy - 10)])
            pygame.draw.polygon(surface, (55, 70, 110), [
                (cx - 14, cy + 12), (cx + 14, cy + 12),
                (cx + 16, cy - 10), (cx - 16, cy - 10)], 2)
            # Energy core
            pulse = int(5 + 3 * math.sin(now * 0.006))
            core_s = pygame.Surface((pulse * 2, pulse * 2), pygame.SRCALPHA)
            pygame.draw.circle(core_s, (0, 220, 255, 140), (pulse, pulse), pulse)
            surface.blit(core_s, (cx - pulse, cy - 2 - pulse))
            pygame.draw.circle(surface, (200, 255, 255), (cx, cy - 2), 3)
            # Trim lines
            pygame.draw.line(surface, color, (cx - 14, cy + 4), (cx + 14, cy + 4), 1)
            # Shoulder pauldrons
            pygame.draw.ellipse(surface, (50, 65, 100), (cx - 20, cy - 12, 14, 10))
            pygame.draw.ellipse(surface, color, (cx - 20, cy - 12, 14, 10), 1)
            pygame.draw.ellipse(surface, (50, 65, 100), (cx + 7, cy - 12, 14, 10))
            pygame.draw.ellipse(surface, color, (cx + 7, cy - 12, 14, 10), 1)
            # Helmet
            head_y = cy - 20
            pygame.draw.circle(surface, (40, 55, 90), (cx, head_y), 12)
            pygame.draw.circle(surface, (55, 70, 110), (cx, head_y), 12, 2)
            visor_glow = int(180 + 60 * math.sin(now * 0.005))
            pygame.draw.line(surface, (0, min(255, visor_glow), 255), (cx - 7, head_y), (cx + 7, head_y), 2)
            pygame.draw.line(surface, (0, min(255, visor_glow), 255), (cx, head_y), (cx, head_y + 5), 2)
            pygame.draw.line(surface, color, (cx, head_y - 12), (cx, head_y - 7), 2)
            # Shield on left arm
            sh_x = cx - 22
            sh_top = cy - 8
            sh_bot = cy + 8
            shield_pts = [
                (sh_x, sh_top), (sh_x + 10, sh_top - 2),
                (sh_x + 10, sh_bot), (sh_x + 5, sh_bot + 8), (sh_x, sh_bot)]
            pygame.draw.polygon(surface, (55, 80, 130), shield_pts)
            pygame.draw.polygon(surface, color, shield_pts, 1)
            pygame.draw.line(surface, color, (sh_x + 5, sh_top), (sh_x + 5, sh_bot), 1)

        elif cls_key == "archer":
            # ---- Sleek ranger with throwing dagger ----
            # Slim legs
            pygame.draw.rect(surface, (20, 50, 40), (cx - 6, cy + 12, 4, 14))
            pygame.draw.rect(surface, (20, 50, 40), (cx + 3, cy + 12, 4, 14))
            # Torso
            pygame.draw.polygon(surface, (30, 60, 50), [
                (cx - 12, cy + 12), (cx + 12, cy + 12),
                (cx + 10, cy - 10), (cx - 10, cy - 10)])
            # Targeting reticle
            r = int(5 + 2 * math.sin(now * 0.005))
            pygame.draw.circle(surface, color, (cx, cy), r, 1)
            pygame.draw.circle(surface, color, (cx, cy), 1)
            # Shoulder guards
            pygame.draw.ellipse(surface, (40, 70, 55), (cx - 16, cy - 12, 10, 8))
            pygame.draw.ellipse(surface, (40, 70, 55), (cx + 7, cy - 12, 10, 8))
            # Hooded head
            head_y = cy - 20
            pygame.draw.circle(surface, (30, 60, 50), (cx, head_y), 10)
            pygame.draw.polygon(surface, (25, 55, 45), [
                (cx - 10, head_y + 2), (cx + 10, head_y + 2), (cx, head_y - 16)])
            eye_glow = int(200 + 55 * math.sin(now * 0.006))
            pygame.draw.circle(surface, (0, min(255, eye_glow), 100), (cx - 4, head_y), 2)
            pygame.draw.circle(surface, (0, min(255, eye_glow), 100), (cx + 4, head_y), 2)
            # Throwing dagger in right hand
            dagger_x = cx + 18
            dagger_y = cy - 2
            bob = math.sin(now * 0.004) * 2
            d_tip_x = dagger_x + 10
            d_tip_y = dagger_y - 6 + int(bob)
            pygame.draw.line(surface, color, (dagger_x, dagger_y + int(bob)), (d_tip_x, d_tip_y), 2)
            # Dagger cross-guard
            pygame.draw.line(surface, (180, 180, 180), (dagger_x - 2, dagger_y - 1 + int(bob)),
                             (dagger_x + 2, dagger_y + 3 + int(bob)), 2)
            # Dagger glint
            glint = int(200 + 55 * math.sin(now * 0.008))
            pygame.draw.circle(surface, (glint, 255, glint), (d_tip_x, d_tip_y), 1)

        elif cls_key == "jester":
            # ---- Chaotic jester on ball with chicken ----
            # Rolling ball under jester
            ball_r = 12
            ball_cx = cx
            ball_cy = cy + 22
            ball_spin = now * 0.008
            pygame.draw.circle(surface, (60, 20, 100), (ball_cx, ball_cy), ball_r)
            pygame.draw.circle(surface, (100, 40, 160), (ball_cx, ball_cy), ball_r, 2)
            for i in range(3):
                angle = ball_spin + i * (math.tau / 3)
                lx = ball_cx + int(math.cos(angle) * ball_r * 0.7)
                ly = ball_cy + int(math.sin(angle) * ball_r * 0.5)
                pygame.draw.circle(surface, (255, 220, 0), (lx, ly), 2)
            pygame.draw.circle(surface, (180, 120, 255), (ball_cx - 3, ball_cy - 3), 3)
            # Legs balanced on ball
            leg_cycle = math.sin(now * 0.01) * 4
            pygame.draw.line(surface, (200, 50, 200), (cx - 3, cy + 6),
                             (cx - 5 + int(leg_cycle), cy + 22 - ball_r + 2), 3)
            pygame.draw.line(surface, (80, 30, 80), (cx + 3, cy + 6),
                             (cx + 5 - int(leg_cycle), cy + 22 - ball_r + 2), 3)
            # Two-tone torso
            pygame.draw.polygon(surface, (80, 30, 80), [
                (cx, cy + 6), (cx + 12, cy + 6),
                (cx + 10, cy - 10), (cx, cy - 10)])
            pygame.draw.polygon(surface, (200, 50, 200), [
                (cx, cy + 6), (cx - 12, cy + 6),
                (cx - 10, cy - 10), (cx, cy - 10)])
            # Diamond pattern
            for dy_off in range(-4, 6, 8):
                pygame.draw.polygon(surface, (255, 220, 0), [
                    (cx, cy + dy_off - 3), (cx + 3, cy + dy_off),
                    (cx, cy + dy_off + 3), (cx - 3, cy + dy_off)], 1)
            # Collar ruffle
            for a in range(0, 360, 30):
                rx = cx + int(math.cos(math.radians(a)) * 10)
                ry = (cy - 10) + int(math.sin(math.radians(a)) * 3)
                pygame.draw.circle(surface, (255, 220, 0), (rx, ry), 2)
            # Head
            head_y = cy - 20
            pygame.draw.circle(surface, (200, 50, 200), (cx, head_y), 10)
            pygame.draw.arc(surface, (255, 220, 0), (cx - 5, head_y - 2, 10, 8), 3.14, 6.28, 2)
            pygame.draw.circle(surface, (255, 255, 255), (cx - 4, head_y - 2), 2)
            pygame.draw.circle(surface, (255, 255, 255), (cx + 4, head_y - 2), 2)
            pygame.draw.circle(surface, (0, 0, 0), (cx - 4, head_y - 2), 1)
            pygame.draw.circle(surface, (0, 0, 0), (cx + 4, head_y - 2), 1)
            # Jester hat
            for side in (-1, 1):
                bx = cx + side * 14
                by = head_y - 16 + int(math.sin(now * 0.006 + side) * 3)
                hat_color = (200, 50, 200) if side == -1 else (80, 30, 80)
                pygame.draw.line(surface, hat_color, (cx + side * 5, head_y - 8), (bx, by), 3)
                pygame.draw.circle(surface, (255, 255, 0), (bx, by), 3)
            # Rubber chicken in right hand
            ch_x = cx + 18
            ch_y = cy - 4
            wobble = math.sin(now * 0.005) * 3
            ch_by = ch_y + int(wobble)
            pygame.draw.line(surface, (255, 200, 50), (cx + 10, cy - 4), (ch_x, ch_by), 3)
            pygame.draw.circle(surface, (255, 220, 80), (ch_x, ch_by), 6)
            # Chicken beak
            pygame.draw.polygon(surface, (255, 150, 0), [
                (ch_x + 4, ch_by), (ch_x + 10, ch_by - 2), (ch_x + 10, ch_by + 2)])
            # Chicken eye
            pygame.draw.circle(surface, (0, 0, 0), (ch_x + 2, ch_by - 3), 2)

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
