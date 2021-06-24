import socket
import struct
import pickle
import time
import numpy as np
from google.protobuf.message import DecodeError
import proto

from socket import timeout as TimeoutException

import ssl_vision_detection_pb2 as detection
import ssl_vision_detection_tracked_pb2 as tigers_detection

import ssl_vision_geometry_pb2 as geometry
import ssl_gc_geometry_pb2 as tigers_geometry

import ssl_wrapper_pb2 as wrapper
import ssl_vision_wrapper_tracked_pb2 as tigers_wrapper

import referee_pb2 as referee
from ssl_vision_geometry_pb2 import SSL_GeometryData, SSL_GeometryFieldSize, SSL_FieldCircularArc

from aux.utils import red_print, blue_print, green_print, purple_print
from aux.RobotBall import BLUE_TEAM, YELLOW_TEAM

DEBUG = False
DEFAULT_VISION_PORT = 10006
DEFAULT_VISION_IP = '224.5.23.2'

DEFAULT_REFEREE_PORT = 10003
DEFAULT_REFEREE_IP = '224.5.23.1'

AUTOREF_TRACKED_PORT = 10010


class UDPCommunication(object):
    def __init__(self, v_port: int, v_group: str, r_port: int, r_group: str, use_autoref: bool):
        self.UDP_TIMEOUT = 0.0001  # in seconds
        self.packets_since_autoref = 0
        self.last_vision_packet = None
        green_print(f'Use AutoRef Data = {use_autoref}')

        self.v_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                      socket.IPPROTO_UDP)
        self.init_socket(self.v_socket, v_group, v_port)

        if use_autoref:
            self.autoref_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                                socket.IPPROTO_UDP)
            self.init_socket(self.autoref_socket, v_group,
                             AUTOREF_TRACKED_PORT)
        else:
            self.autoref_socket = None

        self.r_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                      socket.IPPROTO_UDP)
        self.init_socket(self.r_socket, r_group, r_port)

# =============================================================================

    def init_socket(self, socket_obj: socket, group, port):
        socket_obj.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socket_obj.bind((group, port))
        green_print(f'Connecting to {group}:{port}...')

        mreq = struct.pack('4sl', socket.inet_aton(group), socket.INADDR_ANY)
        socket_obj.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                              mreq)
        socket_obj.settimeout(self.UDP_TIMEOUT)

# =============================================================================

    def __del__(self):
        try:
            self.v_socket.close()
            blue_print('Closing UDP socket')
        except Exception:
            pass

# =============================================================================

    def process_vision_packet(self, packet) -> (bool, detection.SSL_DetectionFrame,
                                                geometry.SSL_GeometryData):
        if packet == None:
            return (False, None, None)

        data_ok = False
        wrapper_frame = wrapper.SSL_WrapperPacket()
        tigers_detection_frame = tigers_detection.TrackedFrame()
        tigers_wrapper_frame = tigers_wrapper.TrackerWrapperPacket()
        geometry_data = geometry.SSL_GeometryData()

        if len(packet) > 0:
            try:
                wrapper_frame.ParseFromString(packet)
                pkt_fields = wrapper_frame.ListFields()

                for field in pkt_fields:
                    if field[0].name == 'geometry':
                        geometry_data = wrapper_frame.geometry

                data_ok = True
                return (data_ok, wrapper_frame.detection, geometry_data)

            except DecodeError as except_type:
                tigers_wrapper_frame.ParseFromString(packet)
                tigers_detection_frame = tigers_wrapper_frame.tracked_frame

                data_ok = True
                return (data_ok, tigers_detection_frame, None)

            except Exception as except_type:
                red_print(except_type, type(except_type))

        return (data_ok, detection.SSL_DetectionFrame(), geometry.SSL_GeometryData())

# =============================================================================

    def process_referee_packet(self, packet) -> (bool, referee.SSL_Referee):
        data_ok = False
        referee_frame = referee.SSL_Referee()

        if len(packet) > 0:
            try:
                referee_frame.ParseFromString(packet)
                data_ok = True
                return (data_ok, referee_frame)

            except Exception as except_type:
                red_print(except_type)

        return (data_ok, referee.SSL_Referee())

# =============================================================================

    def detection_frame_to_dict(self, detection_frame: detection.SSL_DetectionFrame) -> dict:
        frame_dict = dict()

        if not isinstance(detection_frame, detection.SSL_DetectionFrame) and \
                not isinstance(detection_frame, tigers_detection.TrackedFrame):
            return frame_dict

        if isinstance(detection_frame, detection.SSL_DetectionFrame):
            ball_pos = [[round(ball.x), round(ball.y), 0]
                        for ball in detection_frame.balls]

            # Use the mean in case there is more than one ball
            if len(ball_pos) > 0:
                if len(ball_pos) > 1 and DEBUG:
                    red_print('WARNING! More than one ball detected')
                mean_pos = np.mean(np.array(ball_pos), axis=0)
                ball_pos = mean_pos.tolist()

            ball = {'pos': ball_pos}

            blue_robots = [{'obj': {'pos': [round(robot.x), round(robot.y), robot.orientation]},
                            'id': {'number': robot.robot_id, 'color': BLUE_TEAM}}
                           for robot in detection_frame.robots_blue]

            yellow_robots = [{'obj': {'pos': [round(robot.x), round(robot.y), robot.orientation]},
                              'id': {'number': robot.robot_id, 'color': YELLOW_TEAM}}
                             for robot in detection_frame.robots_yellow]
        elif isinstance(detection_frame, tigers_detection.TrackedFrame):
            ball_pos = [[round(ball.pos.x*1000), round(ball.pos.y*1000), 0]
                        for ball in detection_frame.balls]

            # Use the mean in case there is more than one ball
            if len(ball_pos) > 0:
                if len(ball_pos) > 1 and DEBUG:
                    red_print('WARNING! More than one ball detected')
                mean_pos = np.mean(np.array(ball_pos), axis=0)
                ball_pos = mean_pos.tolist()

            ball = {'pos': ball_pos}

            def conv_team(t_id): return BLUE_TEAM if t_id == 2 else YELLOW_TEAM

            blue_robots = [{'obj': {'pos': [round(robot.pos.x*1000), round(robot.pos.y*1000), robot.orientation]},
                            'id': {'number': robot.robot_id.id, 'color': conv_team(robot.robot_id.team)}}
                           for robot in detection_frame.robots]
            yellow_robots = []

        frame_dict['ball'] = ball
        frame_dict['bots'] = blue_robots
        frame_dict['bots'].extend(yellow_robots)

        return frame_dict

    def geometry_frame_to_dict(self, geometry_frame: geometry.SSL_GeometryData) -> dict():
        frame_dict = dict()

        if not isinstance(geometry_frame, geometry.SSL_GeometryData):
            return frame_dict

        if geometry_frame.field.field_length != 0:
            frame_dict['field_size'] = [geometry_frame.field.field_length,
                                        geometry_frame.field.field_width]
            for arc in geometry_frame.field.field_arcs:
                if arc.name == 'CenterCircle':
                    frame_dict['center_circle'] = arc.radius
            return frame_dict
        return None

# =============================================================================

    def get_vision_socket_data(self) -> (dict, dict):
        vision_packet = self.get_vision_packet()
        if self.autoref_socket != None:
            autoref_packet = self.get_autoref_vision_packet()
        else:
            autoref_packet = None

        vis_ok, det_data, geo_data = self.process_vision_packet(vision_packet)
        ar_ok, ar_det_data, _ = self.process_vision_packet(autoref_packet)

        if ar_ok:
            self.packets_since_autoref = 0
            det_data = ar_det_data
            self.last_vision_packet = det_data
        elif self.packets_since_autoref < 1000:
            det_data = self.last_vision_packet
        else:
            self.last_vision_packet = det_data

        if vis_ok or ar_ok:
            return (self.detection_frame_to_dict(det_data),
                    self.geometry_frame_to_dict(geo_data))
        else:
            red_print('[UDP] Failed to process vision packet!', '\r')
        return (None, None)

    def get_vision_packet(self):
        try:
            packet = self.v_socket.recv(4096)
            return packet
        except TimeoutException:
            self.packets_since_autoref += 1
            return None
        except Exception as except_type:
            red_print('[UDP]', except_type)
        return None

    def get_autoref_vision_packet(self):
        try:
            packet = self.autoref_socket.recv(4096)
            return packet
        except TimeoutException:
            return None
        except Exception as except_type:
            red_print('[UDP]', except_type)
        return None

# =============================================================================

    def get_referee_socket_data(self) -> dict:
        packet = b''
        ok = False
        ret_val = None
        try:
            packet = self.r_socket.recv(4096)
            ok = True
        except TimeoutException:
            return None

        except Exception as except_type:
            red_print('[UDP]', except_type)

        if ok:
            ok, ref_data = self.process_referee_packet(packet)
            if ok:
                ret_val = {'Command': ref_data.Command.Name(ref_data.command)}

            else:
                red_print('[UDP] Failed to process referee packet!', '\r')
                ret_val = None
        else:
            red_print('[UDP] Failed to receive referee packet!', '\r')
            ret_val = None
        return ret_val

# =============================================================================
