#!/usr/bin/python3.8
import turtle
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

from aux.RobotBall import Robot, Ball, Position, BLUE_TEAM, YELLOW_TEAM
from aux.utils import red_print, blue_print, green_print, purple_print

from aux.hw_challenge_fsm import ChallengeFSM
from aux.challenge_aux import ChallengeEvents

DEBUG = True
MAX_ROBOTS = 16


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

        self.position_fsm = PositionFSM(args['challenge_file'])
        self.position_fsm.set_end_callback(self.objects_positioned)

        self.challenge_running = False
        self.manager_fsm = ChallengeFSM()
        self.manager_fsm.set_challenge(args['challenge_number'])
        self.manager_fsm.set_end_callback(self.challenge_end)

        # Init data
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
                                    default=1)
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

            if 'bots' in data_keys:
                blue_bots = []
                yellow_bots = []
                for robot in vision_data['bots']:
                    for r_id in range(MAX_ROBOTS):
                        self.blue_robots[r_id].update(obj=robot['obj'],
                                                      id=robot['id'])
                        blue_bots.append(self.blue_robots[r_id].pos)

                        self.yellow_robots[r_id].update(obj=robot['obj'],
                                                        id=robot['id'])
                        yellow_bots.append(self.yellow_robots[r_id].pos)

                self.draw.update_robots(blue_bots, BLUE_TEAM)
                self.draw.update_robots(yellow_bots, YELLOW_TEAM)

            self.check_challenge_positions()
            self.draw.update_challenge_data(
                self.position_fsm.get_challenge_positions())

# =============================================================================

    def update_referee_data(self):
        referee_data = self.udp_communication.get_referee_socket_data()

        if self.challenge_running and referee_data != None \
                and (referee_data['Command'] == 'GOAL_BLUE' or
                     referee_data['Command'] == 'GOAL_YELLOW'):
            purple_print('\nGoal!')
            self.manager_fsm.challenge_external_event(ChallengeEvents.GOAL)

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
            purple_print('Send', gc_command.name)
            self.gc_socket.send_command(gc_command, BLUE_TEAM)

    def challenge_end(self):
        blue_print('Challenge Ended!')
        self.gc_socket.send_command(GCCommands.HALT)
        challenge_time = self.manager_fsm.get_challenge_time()

        green_print('Challenge took {:.2f} seconds'.format(challenge_time))

        self.challenge_running = False
        self.running = False

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
