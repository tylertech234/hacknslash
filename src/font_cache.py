"""Shared font cache — avoids costly per-frame pygame.font.SysFont() calls."""
import pygame

_cache: dict[tuple, pygame.font.Font] = {}


def get_font(name: str = "consolas", size: int = 14, bold: bool = False) -> pygame.font.Font:
    key = (name, size, bold)
    if key not in _cache:
        _cache[key] = pygame.font.SysFont(name, size, bold=bold)
    return _cache[key]
