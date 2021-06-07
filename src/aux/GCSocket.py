import websocket
import time
from enum import Enum

from aux.RobotBall import BLUE_TEAM, YELLOW_TEAM
from aux.utils import red_print, blue_print, green_print, purple_print

WEB_SOCKET_URL = 'ws://localhost:8081/api/control'

#  websocket.enableTrace(True)


class GCCommands(Enum):
    NONE = 0,
    HALT = 1,
    STOP = 2,
    FORCE_START = 3,
    FREE_KICK = 4


class GCSocket(object):
    def __init__(self):
        self.w_socket = None
        self.RETRY_LIMIT = 20

        while not self.connect_web_socket() and self.RETRY_LIMIT > 0:
            self.RETRY_LIMIT -= 1
            time.sleep(1)

        if self.RETRY_LIMIT == 0:
            red_print(
                '[W Socket] Connect to web socket failed too many times, exiting...')
            exit(1)
        green_print('[W Socket] Connected to the GC socket!')

    def __del__(self):
        if self.w_socket != None:
            self.w_socket.close()

    def connect_web_socket(self) -> bool:
        try:
            self.w_socket = websocket.create_connection(WEB_SOCKET_URL)
            return True
        except ConnectionRefusedError:
            red_print('[W Socket] Failed to connect to the Game Controller!')
        except Exception as expt:
            red_print('[W Socket]', expt)
        blue_print('Trying again...')
        return False

    def send_command(self, gc_command: GCCommands, team=None) -> bool:
        if team == None or (team != BLUE_TEAM and team != YELLOW_TEAM):
            team = 'UNKNOWN'

        # Must send STOP before ForceStart ou Direct
        if gc_command == GCCommands.FREE_KICK or gc_command == GCCommands.FORCE_START:
            self.send_command(GCCommands.STOP)

        if gc_command.name == 'FREE_KICK':
            cmd_str = 'DIRECT'
            if team == None:
                raise ValueError(
                    'The command {} must have a team associated, got {}'.format(cmd_str, team))
        else:
            cmd_str = gc_command.name

        try:
            cmd_str = '{"change":{"newCommand":{"command":{"type":"' + \
                cmd_str + '","forTeam":"' + team + '"}},"origin":"UI"}}'
            self.w_socket.send(cmd_str)
            return True

        except Exception as expt:
            red_print('[W Socket]', expt, type(expt))

        return False
