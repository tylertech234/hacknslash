"""In-game debug overlay — hitboxes, FPS, entity positions, on-screen log."""

import pygame
import math
import collections
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT


class DebugOverlay:
    """Renders debug information over the game when debug mode is active."""

    def __init__(self):
        self.active = False
        self.cheats = {}  # reference to DebugMenu.cheats
        self.font = pygame.font.SysFont("consolas", 12)
        self.font_log = pygame.font.SysFont("consolas", 11)
        self._log_lines = collections.deque(maxlen=20)
        self._fps_history = collections.deque(maxlen=60)

    def set_cheats(self, cheats: dict):
        self.cheats = cheats

    def log(self, msg: str):
        """Add a message to the on-screen log."""
        timestamp = pygame.time.get_ticks() // 1000
        self._log_lines.append(f"[{timestamp}s] {msg}")

    def draw(self, surface: pygame.Surface, cx: int, cy: int,
             player, enemies: list, projectiles_enemy, projectiles_player,
             fps: float, wave: int, boss_chests: list = None):
        """Draw all active debug overlays."""
        if not self.active:
            return

        self._fps_history.append(fps)

        if self.cheats.get("show_hitboxes"):
            self._draw_hitboxes(surface, cx, cy, player, enemies,
                               projectiles_enemy, projectiles_player, boss_chests)

        if self.cheats.get("show_fps"):
            self._draw_fps(surface, fps)

        if self.cheats.get("show_positions"):
            self._draw_positions(surface, cx, cy, player, enemies)

        if self.cheats.get("show_log"):
            self._draw_log(surface)

    def _draw_hitboxes(self, surface, cx, cy, player, enemies,
                       proj_enemy, proj_player, chests):
        """Draw hitbox rectangles for all entities."""
        # Player hitbox (green)
        pr = player.rect.move(-cx, -cy)
        pygame.draw.rect(surface, (0, 255, 0), pr, 1)

        # Player attack rect (yellow) when attacking
        if player.is_attacking:
            ar = player.get_attack_rect().move(-cx, -cy)
            pygame.draw.rect(surface, (255, 255, 0), ar, 1)

        # Enemy hitboxes (red)
        for e in enemies:
            if not e.alive:
                continue
            er = e.rect.move(-cx, -cy)
            pygame.draw.rect(surface, (255, 0, 0), er, 1)
            # Show HP above
            hp_text = self.font.render(f"{e.hp}/{e.max_hp}", True, (255, 100, 100))
            surface.blit(hp_text, (er.centerx - hp_text.get_width() // 2, er.top - 14))

        # Enemy projectiles (orange)
        if hasattr(proj_enemy, 'bullets'):
            for b in proj_enemy.bullets:
                if b.alive:
                    br = b.rect.move(-cx, -cy)
                    pygame.draw.rect(surface, (255, 140, 0), br, 1)

        # Player projectiles (cyan)
        if hasattr(proj_player, 'projectiles'):
            for p in proj_player.projectiles:
                pr2 = pygame.Rect(p.x - 4 - cx, p.y - 4 - cy, 8, 8)
                pygame.draw.rect(surface, (0, 255, 255), pr2, 1)

        # Chests (gold)
        if chests:
            for c in chests:
                if c.alive:
                    cr = c.rect.move(-cx, -cy)
                    pygame.draw.rect(surface, (255, 215, 0), cr, 1)

    def _draw_fps(self, surface, fps):
        """Draw FPS counter and graph in top-right."""
        avg_fps = sum(self._fps_history) / max(1, len(self._fps_history))
        color = (0, 255, 0) if avg_fps >= 55 else (255, 255, 0) if avg_fps >= 30 else (255, 0, 0)
        text = self.font.render(f"FPS: {fps:.0f} (avg: {avg_fps:.0f})", True, color)
        surface.blit(text, (SCREEN_WIDTH - text.get_width() - 10, 10))

        # Mini FPS graph
        graph_x = SCREEN_WIDTH - 130
        graph_y = 28
        graph_w = 120
        graph_h = 30
        bg = pygame.Surface((graph_w, graph_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 120))
        surface.blit(bg, (graph_x, graph_y))

        if len(self._fps_history) > 1:
            points = []
            for i, f in enumerate(self._fps_history):
                px = graph_x + int(i * graph_w / 60)
                py = graph_y + graph_h - int(min(f, 60) * graph_h / 60)
                points.append((px, py))
            if len(points) >= 2:
                pygame.draw.lines(surface, color, False, points, 1)

    def _draw_positions(self, surface, cx, cy, player, enemies):
        """Show coordinates next to entities."""
        # Player
        px = int(player.x - cx)
        py = int(player.y - cy)
        pos_text = self.font.render(f"({player.x:.0f},{player.y:.0f})", True, (0, 255, 0))
        surface.blit(pos_text, (px - pos_text.get_width() // 2, py + player.size // 2 + 4))

        # Enemies (only nearby to avoid clutter)
        for e in enemies[:20]:  # limit to prevent lag
            if not e.alive:
                continue
            ex = int(e.x - cx)
            ey = int(e.y - cy)
            if 0 <= ex < SCREEN_WIDTH and 0 <= ey < SCREEN_HEIGHT:
                et = self.font.render(f"{e.enemy_type}", True, (255, 100, 100))
                surface.blit(et, (ex - et.get_width() // 2, ey + e.size // 2 + 4))

    def _draw_log(self, surface):
        """Draw on-screen log window in bottom-left."""
        log_x = 10
        log_y = SCREEN_HEIGHT - 20 * min(len(self._log_lines), 15) - 30
        log_w = 400
        log_h = 20 * min(len(self._log_lines), 15) + 25

        # Background
        bg = pygame.Surface((log_w, log_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        pygame.draw.rect(bg, (100, 60, 60), (0, 0, log_w, log_h), 1)
        surface.blit(bg, (log_x, log_y))

        # Title
        title = self.font.render("DEBUG LOG", True, (255, 100, 100))
        surface.blit(title, (log_x + 5, log_y + 3))

        # Log lines (most recent at bottom)
        visible = list(self._log_lines)[-15:]
        for i, line in enumerate(visible):
            color = (180, 180, 180)
            if "ERROR" in line:
                color = (255, 80, 80)
            elif "WARN" in line:
                color = (255, 200, 80)
            text = self.font_log.render(line[:60], True, color)
            surface.blit(text, (log_x + 5, log_y + 18 + i * 14))
