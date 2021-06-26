from __future__ import annotations
from math import sqrt, pow, pi
from aux.utils import red_print

import numpy as np

BLUE_TEAM = 'BLUE'
YELLOW_TEAM = 'YELLOW'
BALL = 'ORANGE'

MAX_FRAMES_UNSEEN = 50
DISTANCE_THRESHOLD = 35  # [mm]
ORIENTATION_THRESHOLD = 10 * pi/180.0  # [rad]
INF = 999999999999


class Position(object):
    def __init__(self, x=INF, y=INF, orientation=0):
        self.x = x
        self.y = y
        self.orientation = float(orientation)

    def __repr__(self):
        return '({}, {}, {:.3f})'.format(self.x, self.y, self.orientation)

    def set_pos(self, pos: Position):
        self.x = pos.x
        self.y = pos.y

    def to_numpy(self) -> np.array:
        return np.array([self.x, self.y])

    def distance(self, pos) -> int:
        return round(sqrt(pow(self.x - pos.x, 2) + pow(self.y - pos.y, 2)))

    def distance_orientation(self, pos) -> float:
        return abs(abs(self.orientation) - abs(pos.orientation))

# =============================================================================


class VisionObject(object):
    def __init__(self):
        self.unseen_frames = 0
        self.pos = Position()

    def update(self, **kargs):
        raise NotImplementedError()

    def in_vision(self) -> bool:
        return self.unseen_frames > 0

# =============================================================================


class Robot(VisionObject):
    def __init__(self, **kargs):
        super().__init__()
        self.id = -1
        self.team = BLUE_TEAM

        for key, value in kargs.items():
            if key == 'robot_id':
                self.id = value
            elif key == 'pos':
                self.pos = value
            elif key == 'team':
                self.team = value
            elif key == 'obj':
                self.pos = Position(*tuple(value['pos']))
            elif key == 'id':
                self.id = value['number']
                self.team = value['color']

    def __repr__(self):
        if self.in_vision():
            return 'Robot {}/{} = {}'.format(self.id, self.team, self.pos)
        return ''

    def update(self,  **kargs):
        is_robot = False
        pos = None

        for key, value in kargs.items():
            if key == 'id':
                if value['number'] == self.id and value['color'] == self.team:
                    is_robot = True

            elif key == 'obj':
                pos = Position(*tuple(value['pos']))

        if is_robot and pos != None:
            self.pos = pos
            self.unseen_frames = MAX_FRAMES_UNSEEN

        elif self.in_vision():
            self.unseen_frames = self.unseen_frames - 1

    def compare(self, data: Robot):
        if not self.in_vision():
            return False

        # Do not consider the robot id
        if self.pos.distance(data.pos) <= DISTANCE_THRESHOLD and \
                self.pos.distance_orientation(data.pos) <= ORIENTATION_THRESHOLD:
            return True
        return False

# =============================================================================


class Ball(VisionObject):
    def __init__(self, pos=None):
        super().__init__()

        if pos != None:
            self.pos = pos

    def __repr__(self):
        return 'Ball = {}'.format(self.pos)

    def update(self, **kargs):
        pos = None
        for key, data in kargs.items():
            if 'pos' == key:
                pos = Position(*tuple(data['pos']))

        if pos == None:
            red_print('Ball update | No position given in {}'.format(kargs))
            return

        if self.in_vision():
            if pos.distance(Position()) != 0:
                self.unseen_frames = MAX_FRAMES_UNSEEN
                self.pos = pos
        else:
            self.unseen_frames = MAX_FRAMES_UNSEEN
            self.pos = pos

        self.unseen_frames = self.unseen_frames - 1

    def compare(self, data: Ball):
        if not self.in_vision():
            return False

        return self.pos.distance(data.pos) <= DISTANCE_THRESHOLD
