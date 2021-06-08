import json
import time
import numpy as np
from enum import Enum
from os.path import isfile
from aux.RobotBall import Position, Ball, Robot, BLUE_TEAM, YELLOW_TEAM
from aux.utils import red_print, blue_print, green_print, purple_print

CONFIRMATION_DT = 2  # in seconds


class PositionStates(Enum):
    POSITIONING = 0,
    POSITIONED = 1


class PositionFSM(object):
    """
    Finite State Machine that checks wheter the robots/ball are correctly
    positioned before the hardware challenge starts
    """

    def __init__(self, challenge_filename: str):
        self.use_ball = False
        self.read_challenge_file(challenge_filename)

        self.state = PositionStates.POSITIONING
        self.object_positioned_callback = None

        self.objects_in_place = False
        self.objects_t1 = 0
        self.objects_t2 = 0

# =============================================================================

    def set_end_callback(self, callback_fn=None):
        if callback_fn != None:
            self.object_positioned_callback = callback_fn
            green_print('[Pos.] Callback Set!')

# =============================================================================

    def read_challenge_file(self, filename):
        if not isfile(filename):
            red_print("The file {} doesn't exist!".format(filename))
            exit(1)

        with open(filename) as challenge_file:
            json_data = json.load(challenge_file)

        data_keys = list(json_data.keys())

        if 'ball' in data_keys:
            self.use_ball = True
            self.challenge_ball = Ball(
                Position(*tuple(json_data['ball']['pos'])))

        if 'bots' in data_keys:
            self.challenge_pos = [Robot(obj=bot_data['obj'], id=bot_data['id'])
                                  for bot_data in json_data['bots']]

        self.reset_challenge_pos_ok()

        blue_print('Ball data {}'.format(self.challenge_ball))
        blue_print('Bots data {}'.format(self.challenge_pos))

# =============================================================================

    def reset_challenge_pos_ok(self):
        self.challenge_pos_ok = [False for i in range(len(self.challenge_pos))]

        if self.use_ball:
            self.challenge_pos_ok.append(False)  # Ball position

# =============================================================================

    def update_positions(self, blue_robots: [Robot], yellow_robots: [Robot],
                         ball: Ball):
        self.reset_challenge_pos_ok()

        for n, pos_data in enumerate(self.challenge_pos):
            if pos_data.team == BLUE_TEAM:
                for blue_robot in blue_robots:
                    if blue_robot.compare(pos_data):
                        self.challenge_pos_ok[n] = True

            elif pos_data.team == YELLOW_TEAM:
                for yellow_robot in yellow_robots:
                    if yellow_robot.compare(pos_data):
                        self.challenge_pos_ok[n] = True

        if self.use_ball and self.challenge_ball.compare(ball):
            self.challenge_pos_ok[-1] = True

        if self.state == PositionStates.POSITIONING:
            self.check_positions_ok()

# =============================================================================

    def check_positions_ok(self):
        # All objects are in the correct place
        blue_print(self.challenge_pos_ok, '\r')
        if not any(np.invert(self.challenge_pos_ok)):
            if self.objects_in_place == False:
                self.objects_in_place = True
                self.objects_t1 = time.time_ns()
                self.objects_t2 = CONFIRMATION_DT

                green_print('All robots and ball are placed correctly!')

            elif self.objects_t2 > 0:
                self.objects_t2 -= 1e-9*(time.time_ns() - self.objects_t1)
                self.objects_t1 = time.time_ns()

                print('Wait {:.2f} seconds'.format(self.objects_t2), end='\r')

            elif self.objects_in_place and self.objects_t2 <= 0:
                self.state = PositionStates.POSITIONED

                green_print(
                    'Starting the challenge, press Enter to continue...')
                input()

                if self.object_positioned_callback != None:
                    self.object_positioned_callback()

        elif self.objects_in_place == True:
            self.objects_in_place = False
            self.objects_t1 = 0
            self.objects_t1 = 0
