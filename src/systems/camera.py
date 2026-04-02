import pygame
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT, CAMERA_LERP


class Camera:
    """Smoothly follows a target position."""

    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def update(self, target_x: float, target_y: float, world_w: int, world_h: int):
        # Center camera on target with lerp smoothing
        goal_x = target_x - SCREEN_WIDTH / 2
        goal_y = target_y - SCREEN_HEIGHT / 2
        self.x += (goal_x - self.x) * CAMERA_LERP
        self.y += (goal_y - self.y) * CAMERA_LERP

        # Clamp so we don't show outside the world
        self.x = max(0, min(world_w - SCREEN_WIDTH, self.x))
        self.y = max(0, min(world_h - SCREEN_HEIGHT, self.y))
