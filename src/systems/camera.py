import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, CAMERA_LERP


class Camera:
    """Smoothly follows a target position.

    When CAMERA_ZOOM > 1 the game renders the world to a smaller *viewport*
    surface (vp_w × vp_h) and scales it up to the full screen.  Pass those
    viewport dimensions to update() so the camera clamps correctly.
    """

    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def update(self, target_x: float, target_y: float,
               world_w: int, world_h: int,
               vp_w: int = 0, vp_h: int = 0):
        vw = vp_w if vp_w > 0 else SCREEN_WIDTH
        vh = vp_h if vp_h > 0 else SCREEN_HEIGHT

        # Center camera on target with lerp smoothing
        goal_x = target_x - vw / 2
        goal_y = target_y - vh / 2
        self.x += (goal_x - self.x) * CAMERA_LERP
        self.y += (goal_y - self.y) * CAMERA_LERP

        # Clamp so we don't show outside the world
        self.x = max(0, min(world_w - vw, self.x))
        self.y = max(0, min(world_h - vh, self.y))
