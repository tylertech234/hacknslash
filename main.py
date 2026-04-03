import pygame
import json
import os

# ── Detect native desktop resolution before any game module imports ──
pygame.display.init()
try:
    _info = pygame.display.Info()
    _native_w = _info.current_w
    _native_h = _info.current_h
except Exception:
    _native_w, _native_h = 1920, 1080

import src.settings as _settings
_settings.NATIVE_WIDTH = _native_w
_settings.NATIVE_HEIGHT = _native_h

# Common resolutions + native
_RESOLUTIONS = {
    "native":    (_native_w, _native_h),
    "1920x1080": (1920, 1080),
    "1600x900":  (1600, 900),
    "1280x720":  (1280, 720),
    "1024x576":  (1024, 576),
}
_settings.RESOLUTIONS = _RESOLUTIONS

# Load saved resolution preference
_settings_file = os.path.join(os.path.dirname(__file__), "settings_save.json")
_res_key = "native"
try:
    with open(_settings_file) as _f:
        _saved = json.load(_f)
    _k = _saved.get("resolution", "native")
    if _k in _RESOLUTIONS:
        _res_key = _k
except Exception:
    pass

_w, _h = _RESOLUTIONS[_res_key]
_settings.SCREEN_WIDTH = _w
_settings.SCREEN_HEIGHT = _h

from src.game import Game  # noqa: E402 — must come after settings patch


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
