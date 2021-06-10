import json
import time
import numpy as np

from enum import Enum
from tabulate import tabulate
from os.path import isfile
from aux.RobotBall import Position, Ball, Robot, BLUE_TEAM, YELLOW_TEAM, BALL,\
    DISTANCE_THRESHOLD
from aux.utils import red_print, blue_print, green_print, purple_print

from aux.hw_challenge_1 import Challenge_1
from aux.hw_challenge_2 import Challenge_2
from aux.hw_challenge_3 import Challenge_3
from aux.hw_challenge_4 import Challenge_4

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

    def to_table_format(self) -> []:
        obj = 'Robot {}'.format(self.type)
        if self.type == BALL:
            obj = 'Ball'
        return [self.ok, obj, self.id,
                self.pos.x, self.pos.y, self.pos.orientation]

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
        self.json_blue_id = -1
        self.read_challenge_file(challenge_filename)

        self.state = PositionStates.POSITIONING
        self.object_positioned_callback = None

        self.current_challenge = None
        self.objects_in_place = False
        self.objects_t1 = 0
        self.objects_t2 = 0

# =============================================================================

    def challenge_positions_print(self):
        header = ['Positioned', 'Object', 'ID',
                  'X [mm]', 'Y [mm]', 'Angle [rad]']
        data = [line.to_table_format() for line in self.challenge_pos]
        blue_print(tabulate(data, header), '\n')

# =============================================================================

    def set_end_callback(self, callback_fn=None):
        if callback_fn != None:
            self.object_positioned_callback = callback_fn
            green_print('[POSITION FSM] Callback Set!')

# =============================================================================

    def set_challenge(self, challenge: int):
        if not isinstance(challenge, int) or (challenge < 1 or challenge > 4):
            raise ValueError('Challenge ID must be between 1 and 4!')

        if challenge == 1:
            self.current_challenge = Challenge_1
        elif challenge == 2:
            self.current_challenge = Challenge_2
        elif challenge == 3:
            self.current_challenge = Challenge_3
        elif challenge == 4:
            self.current_challenge = Challenge_4

# =============================================================================

    def read_challenge_file(self, filename):
        if not isfile(filename):
            red_print("The file {} doesn't exist!".format(filename))
            exit(1)

        with open(filename) as challenge_file:
            json_data = json.load(challenge_file)

        data_keys = list(json_data.keys())

        n_bots = 0
        if 'bots' in data_keys:
            n_bots = len(json_data['bots'])
        self.challenge_pos = [Challenge_Data() for i in range(n_bots + 1)]

        if 'ball' in data_keys:
            self.use_ball = True
            self.challenge_pos[0].from_Ball(
                Ball(Position(*tuple(json_data['ball']['pos']))))

        if n_bots > 0:
            [self.challenge_pos[n+int(self.use_ball)].from_Robot(Robot(obj=bot_data['obj'], id=bot_data['id']))
             for n, bot_data in enumerate(json_data['bots'])]

        for bot in self.challenge_pos:
            if bot.type == BLUE_TEAM:
                self.json_blue_id = bot.id

        self.challenge_positions_print()

# =============================================================================

    def update_positions(self, blue_robots: [Robot], yellow_robots: [Robot],
                         ball: Ball):
        n_pos_ok = self.n_positions_ok()
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
            yellow_not_in_json = self.robot_ids_not_in_json(yellow_robots)
            blue_not_in_json = self.robot_ids_not_in_json(blue_robots)
            extra_robots_ok = True

            if len(yellow_not_in_json) > 0:
                extra_robots_ok = False
                red_print(
                    '[POSITION FSM] There are extra yellow robots in the field, please remove them!')

            if len(blue_not_in_json) > 0:
                extra_robots_ok = extra_robots_ok & self.check_extra_robots(blue_robots,
                                                                            blue_not_in_json,
                                                                            ball)

            self.check_positions_ok(extra_robots_ok)

        if self.n_positions_ok() > n_pos_ok:
            self.challenge_positions_print()

# =============================================================================

    def n_positions_ok(self) -> int:
        return np.sum(np.array([data.ok for data in self.challenge_pos]))

# =============================================================================

    def check_extra_robots(self, robots: [Robot], robot_ids: int, ball: Ball) -> bool:
        ok = True
        type_of_restriction = ''
        if self.current_challenge != None:
            if self.current_challenge.has_extra_data:
                type_of_restriction = self.current_challenge.robots_restriction
        else:
            red_print(
                '[POSITION FSM] Current challenge undefined, should not happen!')
            return False

        if len(robot_ids) > self.max_attackers():
            ok = False
            red_print("""[POSITION FSM] There are extra blue robots in the field
                         \t Found = {}, Max = {}""".format(len(robot_ids),
                                                           self.max_attackers()))
        elif len(robot_ids) < self.min_attackers():
            ok = False
            red_print("""[POSITION FSM] Not enough blue robots in the field
                         \t Found = {}, Min = {}""".format(len(robot_ids),
                                                           self.min_attackers()))

        # If the number of robots is ok, check their positions
        if ok:
            msg = ''
            if type_of_restriction == 'MiddleLine':
                ok, _ = self.current_challenge.check_restriction(robots)

                if not ok:
                    msg = '[POSITION FSM] The robots must stay in the middle line (x = 0)'

            elif type_of_restriction == 'BallDist':
                ok, dist = self.current_challenge.check_restriction(robots[0].pos,
                                                                    ball.pos)
                if not ok:
                    msg = """[POSITION FSM] The robot must be further away from
                             the ball\n\t Current distance = {} mm, Minimum
                             distance = {} mm""".format(dist,
                                                        self.current_challenge.ball_dist)
            if len(msg) > 0 and not ok:
                red_print(msg)

        return ok

# =============================================================================

    def check_positions_ok(self, extra_robots_ok: bool):
        # All objects are in the correct place
        if not any(np.invert([data.ok for data in self.challenge_pos])) and extra_robots_ok:
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

# =============================================================================

    def robot_ids_not_in_json(self, robots: [Robot]) -> [int]:
        challenge_ids = [data.id for data in self.challenge_pos
                         if data.type == robots[0].team]

        ids_not_json = [robot.id for robot in robots
                        if not challenge_ids.__contains__(robot.id) and robot.in_vision()]

        return ids_not_json

# =============================================================================

    def max_attackers(self) -> int:
        if self.current_challenge != None:
            return self.current_challenge.max_attack_robots
        # There are no limits
        raise ValueError(
            '[POSITION FSM] Current challenge undefined, should not happen!')

    def min_attackers(self) -> int:
        if self.current_challenge != None:
            return self.current_challenge.min_attack_robots
        # There are no limits
        raise ValueError(
            '[POSITION FSM] Current challenge undefined, should not happen!')

# =============================================================================

    def get_pos(self, id: int, type: str) -> Position:
        for pos in self.challenge_pos:
            if pos.id == id and pos.type == type:
                return pos.pos
        return Position()
