"""Compendium screen — browse all discovered (and undiscovered) enemy entries."""
import pygame
import math
from src.font_cache import get_font
from src.entities.enemy import Enemy, ENEMY_TYPES
from src.systems.compendium import (
    Compendium, COMPENDIUM_ORDER, DISPLAY_NAMES, ENEMY_ZONES, ENEMY_LORE
)
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT

# ── Palette ──────────────────────────────────────────────────────────────────
_BG_COLOR     = (8, 8, 18)
_PANEL_COLOR  = (16, 14, 28)
_BORDER_DIM   = (40, 38, 55)
_TEXT_DIM     = (120, 118, 140)
_WHITE        = (230, 230, 240)
_YELLOW       = (220, 180, 60)

_ZONE_COLORS = {
    "wasteland": (80, 180, 80),
    "city":      (100, 140, 220),
    "abyss":     (160, 80, 240),
}
_ZONE_NAMES = {
    "wasteland": "Zone 1  —  The Forest",
    "city":      "Zone 2  —  Ruined Metropolis",
    "abyss":     "Zone 3  —  The Abyss",
}

# ── Card layout ───────────────────────────────────────────────────────────────
_COLS      = 3
_CARD_W    = 360
_CARD_H    = 100
_CARD_GAP  = 12
_SECTION_H = 36    # zone header height
_CONTENT_X = (SCREEN_WIDTH - (_COLS * _CARD_W + (_COLS - 1) * _CARD_GAP)) // 2
_CONTENT_W = _COLS * _CARD_W + (_COLS - 1) * _CARD_GAP
_TOP_BAR_H = 56
_BOT_BAR_H = 36
_SCROLL_VIEW_H = SCREEN_HEIGHT - _TOP_BAR_H - _BOT_BAR_H


class CompendiumScreen:
    """Full-screen compendium browser."""

    def __init__(self, compendium: Compendium):
        self.compendium = compendium
        self.active = False
        self._scroll_y = 0
        self._selected = 0               # index into COMPENDIUM_ORDER
        self._max_scroll = 0
        self._inspect = False            # detail view active
        # Pre-build layout items = list of (kind, data) tuples
        # kind: "section_header" | "card_row"
        self._layout: list = []
        self._flat_cards: list[str] = []   # flat list of enemy types in display order
        self._build_layout()
        # Preview enemy cache (enemy_type -> dummy Enemy)
        self._preview_cache: dict[str, Enemy] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    def activate(self) -> None:
        self.active = True
        self._scroll_y = 0
        self._selected = 0
        self._inspect = False

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Returns 'back' when the user exits, None otherwise."""
        if not self.active:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Clicking anywhere in the bottom hint bar goes back
            bot_y = SCREEN_HEIGHT - _BOT_BAR_H
            if my >= bot_y:
                self.active = False
                return "back"
            # Inspect view: click anywhere outside the card panel to go back
            if self._inspect and mx < 20:
                self._inspect = False
            return None

        if event.type != pygame.KEYDOWN:
            return None

        if self._inspect:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_e,
                             pygame.K_RETURN):
                self._inspect = False
            return None

        key = event.key
        if key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.active = False
            return "back"
        elif key in (pygame.K_a, pygame.K_LEFT):
            self._move_selection(-1)
        elif key in (pygame.K_d, pygame.K_RIGHT):
            self._move_selection(1)
        elif key in (pygame.K_w, pygame.K_UP):
            self._move_selection(-_COLS)
        elif key in (pygame.K_s, pygame.K_DOWN):
            self._move_selection(_COLS)
        elif key in (pygame.K_e, pygame.K_RETURN):
            etype = self._flat_cards[self._selected]
            if self.compendium.is_unlocked(etype):
                self._inspect = True
        return None

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return
        now = pygame.time.get_ticks()
        surface.fill(_BG_COLOR)

        if self._inspect:
            self._draw_inspect(surface, now)
        else:
            self._draw_grid(surface, now)

    # ── Layout building ───────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """Build a list of layout rows: section headers and card rows."""
        zones_seen = []
        zones_ordered = ["wasteland", "city", "abyss"]
        by_zone: dict[str, list[str]] = {z: [] for z in zones_ordered}
        for etype in COMPENDIUM_ORDER:
            z = ENEMY_ZONES.get(etype, "wasteland")
            by_zone[z].append(etype)

        self._flat_cards = []
        for z in zones_ordered:
            cards = by_zone[z]
            if not cards:
                continue
            self._layout.append(("section", z))
            for i in range(0, len(cards), _COLS):
                row = cards[i: i + _COLS]
                self._layout.append(("row", row))
                self._flat_cards.extend(row)

        # Compute total content height
        total_h = 8
        for kind, _ in self._layout:
            total_h += (_SECTION_H + 6) if kind == "section" else (_CARD_H + _CARD_GAP)
        self._max_scroll = max(0, total_h - _SCROLL_VIEW_H)

    def _get_preview_enemy(self, etype: str) -> Enemy:
        if etype not in self._preview_cache:
            self._preview_cache[etype] = Enemy(0, 0, etype)
        return self._preview_cache[etype]

    # ── Selection / scroll ────────────────────────────────────────────────────

    def _move_selection(self, delta: int) -> None:
        new_sel = max(0, min(len(self._flat_cards) - 1, self._selected + delta))
        self._selected = new_sel
        self._ensure_selected_visible()

    def _ensure_selected_visible(self) -> None:
        """Scroll so the selected card is visible."""
        sel_y = self._card_content_y(self._selected)
        if sel_y < self._scroll_y + 4:
            self._scroll_y = max(0, sel_y - 4)
        elif sel_y + _CARD_H > self._scroll_y + _SCROLL_VIEW_H - 4:
            self._scroll_y = min(self._max_scroll,
                                 sel_y + _CARD_H - _SCROLL_VIEW_H + 4)

    def _card_content_y(self, flat_index: int) -> int:
        """Return the content-space Y of the card at flat_cards[flat_index]."""
        etype = self._flat_cards[flat_index]
        y = 8
        flat_pos = 0
        for kind, data in self._layout:
            if kind == "section":
                y += _SECTION_H + 6
            else:
                row: list[str] = data
                if etype in row:
                    return y
                y += _CARD_H + _CARD_GAP
                flat_pos += len(row)
        return y

    # ── Grid drawing ─────────────────────────────────────────────────────────

    def _draw_grid(self, surface: pygame.Surface, now: int) -> None:
        # ── Top bar ──
        pygame.draw.rect(surface, (14, 12, 24), (0, 0, SCREEN_WIDTH, _TOP_BAR_H))
        pygame.draw.line(surface, (60, 55, 80), (0, _TOP_BAR_H), (SCREEN_WIDTH, _TOP_BAR_H), 1)

        title_font = get_font("consolas", 26, True)
        sub_font   = get_font("consolas", 14, False)
        title_surf = title_font.render("COMPENDIUM", True, _YELLOW)
        surface.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 12))

        unlocked = self.compendium.total_unlocked()
        total    = self.compendium.total_entries()
        progress_str = f"{unlocked}/{total} discovered"
        prog_surf = sub_font.render(progress_str, True, _TEXT_DIM)
        surface.blit(prog_surf, (SCREEN_WIDTH - prog_surf.get_width() - 16, 20))

        # ── Scrollable content area ──
        content_surf = pygame.Surface((_CONTENT_W, max(1, self._max_scroll + _SCROLL_VIEW_H)),
                                      pygame.SRCALPHA)
        content_surf.fill((0, 0, 0, 0))

        y = 8
        flat_idx = 0
        for kind, data in self._layout:
            if kind == "section":
                zone_name = _ZONE_NAMES.get(data, data)
                zone_color = _ZONE_COLORS.get(data, (180, 180, 180))
                sec_font = get_font("consolas", 16, True)
                sec_surf = sec_font.render(zone_name, True, zone_color)
                content_surf.blit(sec_surf, (6, y + 8))
                pygame.draw.line(content_surf, zone_color,
                                 (0, y + _SECTION_H - 2),
                                 (_CONTENT_W, y + _SECTION_H - 2), 1)
                y += _SECTION_H + 6
            else:
                row: list[str] = data
                for col, etype in enumerate(row):
                    cx = col * (_CARD_W + _CARD_GAP)
                    cy = y
                    is_selected = (self._flat_cards[flat_idx] == etype
                                   and flat_idx == self._selected)
                    self._draw_card(content_surf, cx, cy, etype, is_selected, now)
                    flat_idx += 1
                y += _CARD_H + _CARD_GAP

        # Blit scrolled region to screen
        src_rect = pygame.Rect(0, self._scroll_y, _CONTENT_W, _SCROLL_VIEW_H)
        surface.blit(content_surf, (_CONTENT_X, _TOP_BAR_H), src_rect)

        # ── Bottom hint bar ──
        bot_y = SCREEN_HEIGHT - _BOT_BAR_H
        pygame.draw.rect(surface, (14, 12, 24), (0, bot_y, SCREEN_WIDTH, _BOT_BAR_H))
        pygame.draw.line(surface, (60, 55, 80), (0, bot_y), (SCREEN_WIDTH, bot_y), 1)
        hint = "W/A/S/D navigate  |  E/Enter inspect  |  Esc or click here to go back"
        hint_surf = get_font("consolas", 13, False).render(hint, True, _TEXT_DIM)
        surface.blit(hint_surf, (SCREEN_WIDTH // 2 - hint_surf.get_width() // 2, bot_y + 10))

    def _draw_card(self, surface: pygame.Surface, cx: int, cy: int,
                   etype: str, selected: bool, now: int) -> None:
        unlocked = self.compendium.is_unlocked(etype)
        zone = ENEMY_ZONES.get(etype, "wasteland")
        zone_color = _ZONE_COLORS.get(zone, (180, 180, 180))

        # Card background
        bg_color = (20, 18, 32) if unlocked else (14, 12, 22)
        pygame.draw.rect(surface, bg_color, (cx, cy, _CARD_W, _CARD_H))
        border_color = zone_color if selected else (_BORDER_DIM if unlocked else (30, 28, 40))
        pygame.draw.rect(surface, border_color, (cx, cy, _CARD_W, _CARD_H), 2)

        # Zone accent stripe on left
        pygame.draw.rect(surface, zone_color if unlocked else (30, 28, 40),
                         (cx, cy, 4, _CARD_H))

        name_font = get_font("consolas", 14, True)
        info_font = get_font("consolas", 11, False)

        if unlocked:
            # Preview sprite in a 70x70 box on the left
            preview_size = 70
            preview_x = cx + 12
            preview_y = cy + (_CARD_H - preview_size) // 2

            # Draw to temp surface
            preview_surf = pygame.Surface((preview_size, preview_size), pygame.SRCALPHA)
            enemy = self._get_preview_enemy(etype)
            # Set facing direction for a nice preview angle
            enemy.face_x = 0.4
            enemy.face_y = 0.9
            half = preview_size // 2
            # Temporarily move enemy to preview center, draw, restore
            orig_x, orig_y = enemy.x, enemy.y
            enemy.x = half
            enemy.y = half
            try:
                enemy._draw_dispatch(preview_surf, half, half, now)
            except Exception:
                pass
            enemy.x, enemy.y = orig_x, orig_y
            surface.blit(preview_surf, (preview_x, preview_y))

            # Name
            display = DISPLAY_NAMES.get(etype, etype)
            name_surf = name_font.render(display, True, _WHITE)
            surface.blit(name_surf, (cx + 90, cy + 14))

            # Stats line
            preset = ENEMY_TYPES.get(etype, {})
            hp_str = f"HP: {preset.get('hp', '?')}"
            spd_str = f"SPD: {preset.get('speed', '?'):.1f}"
            stats_surf = info_font.render(f"{hp_str}   {spd_str}", True, _TEXT_DIM)
            surface.blit(stats_surf, (cx + 90, cy + 38))

            # Kill count
            kills = self.compendium.get_kills(etype)
            kill_surf = info_font.render(f"Kills: {kills}", True, zone_color)
            surface.blit(kill_surf, (cx + 90, cy + 58))

            # Boss badge
            preset_data = ENEMY_TYPES.get(etype, {})
            if etype in ("iron_sentinel", "mega_cyber_deer", "street_preacher", "architect", "supreme_d_lek", "eldritch_horror", "nexus"):
                badge = info_font.render("ELITE", True, (200, 160, 40))
                surface.blit(badge, (cx + _CARD_W - badge.get_width() - 8, cy + 8))
            elif etype in ("warlord_kron", "eldritch_horror", "nexus"):
                badge = info_font.render("BOSS", True, (220, 60, 60))
                surface.blit(badge, (cx + _CARD_W - badge.get_width() - 8, cy + 8))

            # Selection glow
            if selected:
                glow_s = pygame.Surface((_CARD_W, _CARD_H), pygame.SRCALPHA)
                pygame.draw.rect(glow_s, (*zone_color, 18), (0, 0, _CARD_W, _CARD_H))
                surface.blit(glow_s, (cx, cy))

        else:
            # Locked card
            lock_font = get_font("consolas", 20, True)
            unk_surf  = lock_font.render("???", True, (55, 52, 70))
            surface.blit(unk_surf, (cx + _CARD_W // 2 - unk_surf.get_width() // 2,
                                    cy + _CARD_H // 2 - unk_surf.get_height() // 2))
            if selected:
                hint_s = info_font.render("Kill to unlock", True, (80, 75, 100))
                surface.blit(hint_s, (cx + _CARD_W // 2 - hint_s.get_width() // 2,
                                      cy + _CARD_H - 20))

    # ── Inspect / detail view ─────────────────────────────────────────────────

    def _draw_inspect(self, surface: pygame.Surface, now: int) -> None:
        etype = self._flat_cards[self._selected]
        if not self.compendium.is_unlocked(etype):
            self._inspect = False
            return

        zone  = ENEMY_ZONES.get(etype, "wasteland")
        zcolor = _ZONE_COLORS.get(zone, (180, 180, 180))
        preset = ENEMY_TYPES.get(etype, {})
        display = DISPLAY_NAMES.get(etype, etype)
        lore = ENEMY_LORE.get(etype, "No data available.")

        surface.fill(_BG_COLOR)

        # ── Large sprite preview ──
        prev_sz = 140
        prev_x  = SCREEN_WIDTH // 2 - 200
        prev_y  = SCREEN_HEIGHT // 2 - prev_sz // 2
        prev_surf = pygame.Surface((prev_sz, prev_sz), pygame.SRCALPHA)
        enemy = self._get_preview_enemy(etype)
        enemy.face_x = 0.3
        enemy.face_y = 0.95
        half = prev_sz // 2
        enemy.x = half
        enemy.y = half
        try:
            enemy._draw_dispatch(prev_surf, half, half, now)
        except Exception:
            pass
        # Box around sprite
        pygame.draw.rect(surface, (24, 22, 36), (prev_x - 2, prev_y - 2, prev_sz + 4, prev_sz + 4))
        pygame.draw.rect(surface, zcolor,       (prev_x - 2, prev_y - 2, prev_sz + 4, prev_sz + 4), 2)
        surface.blit(prev_surf, (prev_x, prev_y))

        # ── Info panel on the right ──
        info_x = SCREEN_WIDTH // 2 - 20
        info_y = SCREEN_HEIGHT // 2 - 120
        title_font = get_font("consolas", 28, True)
        head_font  = get_font("consolas", 15, True)
        body_font  = get_font("consolas", 13, False)
        lore_font  = get_font("consolas", 12, False)

        # Name
        name_surf = title_font.render(display, True, zcolor)
        surface.blit(name_surf, (info_x, info_y))

        # Zone badge
        zone_name = _ZONE_NAMES.get(zone, zone)
        zone_surf = head_font.render(zone_name, True, _TEXT_DIM)
        surface.blit(zone_surf, (info_x, info_y + 42))

        # Stats
        def stat_line(label: str, val: str, y_off: int):
            surface.blit(head_font.render(label, True, (180, 175, 200)), (info_x, info_y + y_off))
            surface.blit(body_font.render(val,   True, _WHITE),           (info_x + 120, info_y + y_off))

        stat_line("HP",      str(preset.get("hp", "?")),               80)
        stat_line("SPEED",   f"{preset.get('speed', '?'):.1f}",         100)
        stat_line("DAMAGE",  str(preset.get("damage", "?")),             120)
        on_hit = preset.get("status_on_hit") or "—"
        stat_line("ON HIT",  on_hit.upper(),                             140)
        stat_line("XP",      str(preset.get("xp_value", "?")),          160)
        stat_line("KILLS",   str(self.compendium.get_kills(etype)),      180)

        # Lore
        lore_y = info_y + 215
        surface.blit(head_font.render("INTEL", True, _YELLOW), (info_x, lore_y))
        for i, line in enumerate(lore.split("\n")):
            lore_surf = lore_font.render(line, True, _TEXT_DIM)
            surface.blit(lore_surf, (info_x, lore_y + 22 + i * 18))

        # Hint
        hint = "Esc / E / Enter — return to compendium"
        hint_surf = get_font("consolas", 13, False).render(hint, True, _TEXT_DIM)
        surface.blit(hint_surf, (SCREEN_WIDTH // 2 - hint_surf.get_width() // 2,
                                 SCREEN_HEIGHT - 30))
