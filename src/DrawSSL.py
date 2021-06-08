import turtle
import pygame
from multiprocessing import Process, Queue


FIELD_LINE_PEN_SZ = 10
DEFAULT_PEN_SZ = 2


class DrawSSL(object):

    def __init__(self):
        self.field_size = (800, 600)
        self.center_circle_radius = 100
        self.current_callback = None

# =============================================================================

    def __del__(self):
        pass

# =============================================================================

    def set_key_callback(self, callback_fn=None):
        pass

# =============================================================================

    def start_draw(self):
        pass

# =============================================================================

    def finish_draw(self):
        pass

# =============================================================================

    def set_field_size(self, new_size: (int, int)):
        self.field_size = new_size

# =============================================================================

    def set_center_circle_radius(self, radius: int):
        self.center_circle_radius = radius

# =============================================================================

    def clear(self):
        pass

# =============================================================================

    def draw_field(self):
        pass

# =============================================================================

    def draw_robot(self, pos: (int, int), team: str):
        pass

# =============================================================================

    def draw_ball(self, pos: (int, int)):
        pass

# =============================================================================
