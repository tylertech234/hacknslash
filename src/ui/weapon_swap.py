import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE
from src.systems.weapons import WEAPONS
from src.ui.tooltip import Tooltip, calc_weapon_dps


class WeaponSwapScreen:
    """Confirm weapon swap — shows current vs new weapon side by side."""

    def __init__(self):
        self.active = False
        self.new_weapon_key: str = ""
        self.current_weapon_key: str = ""
        self.selected = 0  # 0 = swap, 1 = keep
        self.font_big = pygame.font.SysFont("consolas", 28, bold=True)
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 14)
        self._tooltip = Tooltip()

    def activate(self, current_weapon_key: str, new_weapon_key: str):
        self.current_weapon_key = current_weapon_key
        self.new_weapon_key = new_weapon_key
        self.selected = 0
        self.active = True

    def handle_event(self, event: pygame.event.Event) -> dict | None:
        """Returns {'action': 'swap', 'weapon': key} or {'action': 'keep'} or None."""
        if not self.active:
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            cx = SCREEN_WIDTH // 2
            card_w, card_h, gap = 260, 200, 40
            left_x = cx - card_w - gap // 2
            right_x = cx + gap // 2
            card_y = 170
            if left_x <= mx <= left_x + card_w and card_y <= my <= card_y + card_h:
                self.active = False
                return {"action": "swap", "weapon": self.new_weapon_key}
            if right_x <= mx <= right_x + card_w and card_y <= my <= card_y + card_h:
                self.active = False
                return {"action": "keep"}
            return None
        if event.type != pygame.KEYDOWN:
            return None

        if event.key in (pygame.K_a, pygame.K_LEFT):
            self.selected = 0
        elif event.key in (pygame.K_d, pygame.K_RIGHT):
            self.selected = 1
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            self.active = False
            if self.selected == 0:
                return {"action": "swap", "weapon": self.new_weapon_key}
            return {"action": "keep"}
        elif event.key == pygame.K_ESCAPE:
            self.active = False
            return {"action": "keep"}
        return None

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        surface.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH // 2

        title = self.font_big.render("SWAP WEAPON?", True, (255, 220, 50))
        surface.blit(title, (cx - title.get_width() // 2, 100))

        cur_wpn = WEAPONS.get(self.current_weapon_key, {})
        new_wpn = WEAPONS.get(self.new_weapon_key, {})

        # Two cards side by side
        card_w, card_h = 260, 200
        gap = 40
        left_x = cx - card_w - gap // 2
        right_x = cx + gap // 2
        card_y = 170

        for i, (wpn, key, label) in enumerate([
            (new_wpn, self.new_weapon_key, "NEW"),
            (cur_wpn, self.current_weapon_key, "CURRENT"),
        ]):
            x = left_x if i == 0 else right_x
            selected = (self.selected == i)
            color = wpn.get("blade_color", (180, 180, 180))

            # Card bg
            bg = (50, 45, 25) if selected else (30, 30, 40)
            pygame.draw.rect(surface, bg,
                             (x, card_y, card_w, card_h), border_radius=6)
            border = (255, 220, 50) if selected else (80, 80, 90)
            pygame.draw.rect(surface, border,
                             (x, card_y, card_w, card_h), 2, border_radius=6)

            # Label
            lbl = self.font_small.render(label, True,
                                         (255, 200, 50) if i == 0 else (150, 150, 160))
            surface.blit(lbl, (x + card_w // 2 - lbl.get_width() // 2, card_y + 8))

            # Weapon name
            name = self.font.render(wpn.get("name", key), True, color)
            surface.blit(name, (x + card_w // 2 - name.get_width() // 2, card_y + 30))

            # Stats
            stats_y = card_y + 60
            stat_lines = [
                f"Damage: {wpn.get('damage_mult', 1.0):.1f}x",
                f"Range: {wpn.get('range', 0)}",
                f"Cooldown: {wpn.get('cooldown', 0)}ms",
                f"Type: {wpn.get('type', '?')}",
            ]
            for j, line in enumerate(stat_lines):
                st = self.font_small.render(line, True, (180, 180, 180))
                surface.blit(st, (x + 20, stats_y + j * 22))

            # DPS
            dps = calc_weapon_dps(20, wpn)
            dps_t = self.font_small.render(f"DPS: {dps:.0f}", True, (100, 255, 100))
            surface.blit(dps_t, (x + 20, stats_y + len(stat_lines) * 22 + 4))

        # Arrow indicators
        swap_label = "[ SWAP ]" if self.selected == 0 else "  SWAP  "
        keep_label = "[ KEEP ]" if self.selected == 1 else "  KEEP  "
        btn_y = card_y + card_h + 20
        swap_t = self.font.render(swap_label, True,
                                  (255, 220, 50) if self.selected == 0 else (120, 120, 120))
        keep_t = self.font.render(keep_label, True,
                                  (255, 220, 50) if self.selected == 1 else (120, 120, 120))
        surface.blit(swap_t, (left_x + card_w // 2 - swap_t.get_width() // 2, btn_y))
        surface.blit(keep_t, (right_x + card_w // 2 - keep_t.get_width() // 2, btn_y))

        hint = self.font_small.render("A/D or Arrow keys to choose, SPACE to confirm",
                                      True, (100, 100, 100))
        surface.blit(hint, (cx - hint.get_width() // 2, SCREEN_HEIGHT - 40))
