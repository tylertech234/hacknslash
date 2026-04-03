import pygame
from src.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, PASSIVE_INFO, MAX_PASSIVES,
)


class PassiveSwapScreen:
    """When the player already has MAX_PASSIVES, let them swap one out."""

    def __init__(self):
        self.active = False
        self.new_passive: str = ""
        self.new_passive_name: str = ""
        self.current_passives: list[str] = []
        self.selected = 0  # 0..MAX_PASSIVES-1 = swap slot, MAX_PASSIVES = skip
        self.font_big = pygame.font.SysFont("consolas", 28, bold=True)
        self.font = pygame.font.SysFont("consolas", 18)
        self.font_small = pygame.font.SysFont("consolas", 14)

    def activate(self, current_passives: list[str], new_key: str, new_name: str):
        # Only show swappable passives (exclude glass_cannon flag)
        self.current_passives = [p for p in current_passives if p != "glass_cannon"]
        self.new_passive = new_key
        self.new_passive_name = new_name
        self.selected = 0
        self.active = True

    def handle_event(self, event: pygame.event.Event) -> dict | None:
        """Returns {'action': 'swap', 'remove': key, 'add': key} or {'action': 'skip'} or None."""
        if not self.active:
            return None
        if event.type != pygame.KEYDOWN:
            return None

        n = len(self.current_passives)
        if event.key in (pygame.K_w, pygame.K_UP):
            self.selected = (self.selected - 1) % (n + 1)
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            self.selected = (self.selected + 1) % (n + 1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.active = False
            if self.selected < n:
                return {"action": "swap", "remove": self.current_passives[self.selected],
                        "add": self.new_passive}
            return {"action": "skip"}
        elif event.key == pygame.K_ESCAPE:
            self.active = False
            return {"action": "skip"}
        # Number keys for quick select
        num_keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]
        for i, k in enumerate(num_keys):
            if event.key == k:
                if i < n:
                    self.active = False
                    return {"action": "swap", "remove": self.current_passives[i],
                            "add": self.new_passive}
                elif i == n:
                    self.active = False
                    return {"action": "skip"}
        return None

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        # Title
        title = self.font_big.render("PASSIVE SLOTS FULL!", True, (255, 200, 50))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        new_icon, new_color = PASSIVE_INFO.get(self.new_passive, ("?", (180, 180, 180)))
        new_txt = self.font.render(
            f"New: [{new_icon}] {self.new_passive_name}", True, new_color)
        surface.blit(new_txt, (SCREEN_WIDTH // 2 - new_txt.get_width() // 2, 145))

        sub = self.font_small.render("Choose a passive to replace, or skip:", True, (180, 180, 180))
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 175))

        # List current passives
        box_w = 360
        start_y = 210
        row_h = 44

        for i, key in enumerate(self.current_passives):
            icon, color = PASSIVE_INFO.get(key, ("?", (180, 180, 180)))
            x = SCREEN_WIDTH // 2 - box_w // 2
            y = start_y + i * row_h

            # Background
            bg_color = (60, 50, 20) if i == self.selected else (30, 30, 40)
            pygame.draw.rect(surface, bg_color, (x, y, box_w, row_h - 4), border_radius=4)

            # Selection indicator
            if i == self.selected:
                pygame.draw.rect(surface, (255, 200, 50), (x, y, box_w, row_h - 4), 2,
                                 border_radius=4)

            # Number + icon + name
            label = self.font.render(f"{i + 1}. [{icon}] {key}", True, color)
            surface.blit(label, (x + 10, y + 8))

        # Skip option
        skip_y = start_y + len(self.current_passives) * row_h
        skip_x = SCREEN_WIDTH // 2 - box_w // 2
        is_skip_selected = self.selected == len(self.current_passives)
        bg = (40, 40, 60) if is_skip_selected else (30, 30, 40)
        pygame.draw.rect(surface, bg, (skip_x, skip_y, box_w, row_h - 4), border_radius=4)
        if is_skip_selected:
            pygame.draw.rect(surface, (150, 150, 180), (skip_x, skip_y, box_w, row_h - 4), 2,
                             border_radius=4)
        skip_label = self.font.render(f"{len(self.current_passives) + 1}. Skip (keep current)", True,
                                       (150, 150, 150))
        surface.blit(skip_label, (skip_x + 10, skip_y + 8))
