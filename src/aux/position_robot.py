import json
import time
import numpy as np
from enum import Enum
from os.path import isfile
from aux.RobotBall import Position, Ball, Robot, BLUE_TEAM, YELLOW_TEAM, BALL
from aux.utils import red_print, blue_print, green_print, purple_print

CONFIRMATION_DT = 2  # in seconds


class PositionStates(Enum):
    POSITIONING = 0,
    POSITIONED = 1


class Challenge_Data(Robot):
    def __init__(self):
        super().__init__()
        self.ok = False
        self.type = BLUE_TEAM

    def __repr__(self) -> str:
        return '{}/{}/{} = {}'.format(self.type, self.id, self.ok, self.pos)

    def from_Robot(self, robot: Robot):
        self.pos = robot.pos
        self.type = robot.team
        self.id = robot.id
        self.unseen_frames = robot.unseen_frames

    def from_Ball(self, ball: Ball):
        self.pos = ball.pos
        self.type = BALL


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
            green_print('[POSITION FSM] Callback Set!')

# =============================================================================

    def read_challenge_file(self, filename):
        if not isfile(filename):
            red_print("The file {} doesn't exist!".format(filename))
            exit(1)

        with open(filename) as challenge_file:
            json_data = json.load(challenge_file)

        data_keys = list(json_data.keys())
        self.challenge_pos = [Challenge_Data()
                              for i in range(len(json_data['bots']) + 1)]

        if 'ball' in data_keys:
            self.use_ball = True
            self.challenge_pos[0].from_Ball(
                Ball(Position(*tuple(json_data['ball']['pos']))))

        if 'bots' in data_keys:
            [self.challenge_pos[n+int(self.use_ball)].from_Robot(Robot(obj=bot_data['obj'], id=bot_data['id']))
             for n, bot_data in enumerate(json_data['bots'])]

        blue_print('Challenge data {}'.format(self.challenge_pos))

# =============================================================================

    def update_positions(self, blue_robots: [Robot], yellow_robots: [Robot],
                         ball: Ball):
        for pos_data in self.challenge_pos:
            pos_data.ok = False
            if pos_data.type == BLUE_TEAM:
                for blue_robot in blue_robots:
                    if blue_robot.compare(pos_data):
                        pos_data.ok = True

            elif pos_data.type == YELLOW_TEAM:
                for yellow_robot in yellow_robots:
                    if yellow_robot.compare(pos_data):
                        pos_data.ok = True

            elif pos_data.type == BALL:
                if ball.compare(pos_data):
                    pos_data.ok = True

        if self.state == PositionStates.POSITIONING:
            self.check_positions_ok()

# =============================================================================

    def check_positions_ok(self):
        # All objects are in the correct place
        #          blue_print(self.challenge_pos_ok, '\r')
        if not any(np.invert([data.ok for data in self.challenge_pos])):
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

# =============================================================================

    def get_challenge_positions(self) -> [Challenge_Data]:
        return self.challenge_pos
