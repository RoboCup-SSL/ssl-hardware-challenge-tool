#!/usr/bin/python3.8
import json
import argparse
import time
import numpy as np
from os.path import isfile

from ProcessUDPData import UDPCommunication, DEFAULT_VISION_PORT, DEFAULT_VISION_IP, \
    DEFAULT_REFEREE_PORT, DEFAULT_REFEREE_IP
from DrawSSL import DrawSSL

from aux.GCSocket import GCCommands, GCSocket
from aux.position_robot import PositionFSM

from aux.RobotBall import Robot, Ball, Position, BLUE_TEAM, YELLOW_TEAM, \
    DISTANCE_THRESHOLD, INF
from aux.utils import red_print, blue_print, green_print, purple_print

from aux.hw_challenge_fsm import ChallengeFSM, ROBOT_STOP_TRESHOLD
from aux.challenge_aux import ChallengeEvents

DEBUG = False
MAX_ROBOTS = 16


class SpecialBotPosition(Position):
    def __init__(self):
        super().__init__()
        self.t = 0


class HWChallengeManager(object):
    def __init__(self):
        args = self.parse_args()
        self.running = False

        self.udp_communication = UDPCommunication(v_port=args['vision_port'],
                                                  v_group=args['vision_ip'],
                                                  r_port=args['referee_port'],
                                                  r_group=args['referee_ip'])
        self.gc_socket = GCSocket()
        self.gc_socket.send_command(GCCommands.HALT)

        self.challenge_running = False
        self.challenge_number = int(args['challenge_number'])

        self.position_fsm = PositionFSM(args['challenge_file'])
        self.position_fsm.set_end_callback(self.objects_positioned)
        self.position_fsm.set_challenge(self.challenge_number)

        self.gc_socket.set_placement_pos(self.position_fsm.get_placement())

        self.manager_fsm = ChallengeFSM()
        self.manager_fsm.set_challenge(self.challenge_number)
        self.manager_fsm.set_end_callback(self.challenge_end)

        # Init data
        self.challenge_3_bot_pos = [SpecialBotPosition(), SpecialBotPosition()]
        self.ball = Ball()
        self.blue_robots = [Robot(team=BLUE_TEAM, robot_id=i)
                            for i in range(MAX_ROBOTS)]
        self.yellow_robots = [Robot(team=YELLOW_TEAM, robot_id=i)
                              for i in range(MAX_ROBOTS)]
        self.init_drawings()

# =============================================================================

    def parse_args(self):
        arg_parser = argparse.ArgumentParser()
        if DEBUG:
            arg_parser.add_argument('-f', '--challenge-file', required=False,
                                    help='JSON file that contains the challenge positioning',
                                    default='./example.json')
            arg_parser.add_argument('-c', '--challenge-number', required=False,
                                    help='ID of the hardware challenge, must be between 1 and 4',
                                    default=2)
        else:
            arg_parser.add_argument('-f', '--challenge-file', required=True,
                                    help='JSON file that contains the challenge positioning')
            arg_parser.add_argument('-c', '--challenge-number', required=True,
                                    help='ID of the hardware challenge, must be between 1 and 4')

        arg_parser.add_argument('-p', '--vision-port', required=False,
                                help='UDP Vision Port, default value is {}'.format(
                                    DEFAULT_VISION_PORT),
                                default=DEFAULT_VISION_PORT)
        arg_parser.add_argument('-i', '--vision-ip', required=False,
                                help='UDP Vision IP, default value is {}'.format(
                                    DEFAULT_VISION_IP),
                                default=DEFAULT_VISION_IP)
        arg_parser.add_argument('-P', '--referee-port', required=False,
                                help='UDP Referee Port, default value is {}'.format(
                                    DEFAULT_REFEREE_PORT),
                                default=DEFAULT_REFEREE_PORT)
        arg_parser.add_argument('-I', '--referee-ip', required=False,
                                help='UDP Referee IP, default value is {}'.format(
                                    DEFAULT_REFEREE_IP),
                                default=DEFAULT_REFEREE_IP)

        return vars(arg_parser.parse_args())

# =============================================================================

    def init_drawings(self):
        self.draw = DrawSSL()
        self.draw.start()
        self.running = True

# =============================================================================

    def update_vision_data(self):
        vision_data, geometry_data = self.udp_communication.get_vision_socket_data()

        if geometry_data != None:
            self.draw.set_field_size(geometry_data['field_size'])
            self.draw.set_center_circle_radius(geometry_data['center_circle'])

        if vision_data != None:
            data_keys = list(vision_data.keys())
            if 'ball' in data_keys:
                self.ball.update(pos=vision_data['ball'])
                self.draw.update_ball(self.ball.pos)

            blue_bots = []
            yellow_bots = []
            if 'bots' in data_keys:
                for robot in vision_data['bots']:
                    for r_id in range(MAX_ROBOTS):
                        self.blue_robots[r_id].update(obj=robot['obj'],
                                                      id=robot['id'])

                        if r_id == self.position_fsm.json_blue_id:
                            self.update_challenge_3_bot_position(
                                self.blue_robots[r_id].pos,
                                self.position_fsm.get_pos(r_id, BLUE_TEAM))

                        self.yellow_robots[r_id].update(obj=robot['obj'],
                                                        id=robot['id'])
                # In case there are no robots in the field, make sure they get
                # their 'in_vision' state updated
                if len(vision_data['bots']) == 0:
                    for r_id in range(MAX_ROBOTS):
                        self.blue_robots[r_id].update(
                            id={'number': r_id, 'color': BLUE_TEAM})
                        self.yellow_robots[r_id].update(
                            id={'number': r_id, 'color': YELLOW_TEAM})

                blue_bots.extend([bot for bot in self.blue_robots
                                  if bot.in_vision()])
                yellow_bots.extend([bot for bot in self.yellow_robots
                                    if bot.in_vision()])

            self.draw.update_robots(blue_bots, BLUE_TEAM)
            self.draw.update_robots(yellow_bots, YELLOW_TEAM)

            self.check_challenge_positions()
            self.draw.update_challenge_data(
                self.position_fsm.get_challenge_positions())

# =============================================================================

    def update_referee_data(self):
        referee_data = self.udp_communication.get_referee_socket_data()

        if self.challenge_running:
            if referee_data != None and \
                (referee_data['Command'] == 'GOAL_BLUE' or
                 referee_data['Command'] == 'GOAL_YELLOW'):
                purple_print('\nGoal!')
                self.manager_fsm.challenge_external_event(ChallengeEvents.GOAL)
            elif referee_data != None and referee_data['Command'] == 'STOP':
                self.manager_fsm.challenge_external_event(ChallengeEvents.STOP)

# =============================================================================

    def check_challenge_positions(self):
        self.position_fsm.update_positions(self.blue_robots,
                                           self.yellow_robots, self.ball)

    def objects_positioned(self):
        green_print('Start')
        self.challenge_running = True

    def run_challenge(self):
        gc_command = self.manager_fsm.get_current_command()

        if gc_command != GCCommands.NONE:
            self.gc_socket.send_command(gc_command, BLUE_TEAM)
            purple_print('Sent', gc_command.name)

    def challenge_end(self):
        blue_print('Challenge Ended!')
        self.gc_socket.send_command(GCCommands.HALT)
        challenge_time = self.manager_fsm.get_challenge_time()

        green_print('Challenge took {:.2f} seconds'.format(challenge_time))

        self.challenge_running = False
        self.running = False

# =============================================================================

    def update_challenge_3_bot_position(self, pos: Position, start_pos: Position):
        if pos.x >= INF:
            return

        if self.challenge_number == 3 and self.challenge_running:
            if self.challenge_3_bot_pos[0].t <= 0:
                if DEBUG:
                    purple_print('Start counting')
                self.challenge_3_bot_pos[0].t = time.time_ns()/1e9
                self.challenge_3_bot_pos[1].t = time.time_ns()/1e9
                self.challenge_3_bot_pos[0].set_pos(pos)
                self.challenge_3_bot_pos[1].set_pos(pos)
            else:
                self.challenge_3_bot_pos[1].t = time.time_ns()/1e9
                self.challenge_3_bot_pos[1].set_pos(pos)

            dist = self.challenge_3_bot_pos[1].distance(
                self.challenge_3_bot_pos[0])

            dist_start = self.challenge_3_bot_pos[0].distance(start_pos)
            dt = self.challenge_3_bot_pos[1].t - self.challenge_3_bot_pos[0].t

            if dist >= DISTANCE_THRESHOLD:
                self.challenge_3_bot_pos[0].t = 0
                self.challenge_3_bot_pos[1].t = 0

            elif dt >= ROBOT_STOP_TRESHOLD:
                if DEBUG:
                    purple_print('Stop counting')
                if dist <= DISTANCE_THRESHOLD and dist_start > 500:
                    self.manager_fsm.challenge_external_event(
                        ChallengeEvents.ROBOT_STOPPED)


# =============================================================================


    def end_program(self):
        self.running = False

# =============================================================================


if __name__ == "__main__":
    manager = HWChallengeManager()

    while manager.running:
        manager.update_vision_data()
        manager.update_referee_data()

        if manager.challenge_running:
            manager.run_challenge()

        ui_msg = manager.draw.get_ui_event()
        if ui_msg == 'QUIT':
            break

    manager.draw.stop()
    red_print('\nQuit')
