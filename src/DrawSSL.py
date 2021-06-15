import pygame
import pygame.freetype
import time
import numpy as np

from multiprocessing import Process, Queue
from math import sqrt, acos, pi, trunc, cos, sin

from aux.RobotBall import Robot, Position, BLUE_TEAM, YELLOW_TEAM, BALL, INF,\
    DISTANCE_THRESHOLD, ORIENTATION_THRESHOLD
from aux.utils import red_print, blue_print, green_print, purple_print
from aux.position_robot import Challenge_Data

FIELD_LINE_PEN_SZ = 6
SCREEN_SIZE = [800, 600]
FIELD_BORDER = 500

BALL_RADIUS = 42  # a bit bigger just to be more visible
BOT_RADIUS = 90

BLUE_C = 'blue'
C_BLUE_C = (102, 204, 255)  # = #66ccff

YELLOW_C = (179, 179, 0)  # = #b3b300
D_YELLOW_C = (153, 102, 0)  # = #996600

GREEN_C = (153, 255, 153)  # = #99ff99
D_GREEN_C = (0, 102, 0)  # = #006600
BLACK_C = 'black'

ORANGE_C = (255, 153, 0)  # = #ff9900


class DrawSSL(object):
    def __init__(self):
        self.ui_init = False

        self.field_size = np.array([800, 600])
        self.center_circle_radius = 100
        self.ball = np.array([INF, INF])
        self.blue_robots = []
        self.yellow_robots = []
        self.challenge_positions = []

# =============================================================================

    def draw(self):
        while True:
            if not self.process_queue.empty():
                if self.parse_process_msg():
                    break

            if not self.ui_init:
                self.ui_init = True
                self.init_ui()
            else:
                self.update_drawings()
                self.event_loop()

                pygame.display.update()
                self.clock.tick(60)

# =============================================================================

    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.ui_queue.put_nowait('QUIT')

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_q:
                    self.ui_queue.put_nowait('QUIT')
            elif event.type == pygame.WINDOWRESIZED:
                win_sz = self.window.get_size()
                global SCREEN_SIZE
                SCREEN_SIZE = [win_sz[0], win_sz[1]]

# =============================================================================

    def parse_process_msg(self) -> str:
        end_ui = False
        while not self.process_queue.empty():
            msg = self.process_queue.get_nowait()
            if 'END' in msg.keys() and msg['END']:
                end_ui = True
            elif 'FieldSZ' in msg.keys():
                self.field_size = msg['FieldSZ']
                end_ui = False
            elif 'CircleSZ' in msg.keys():
                self.center_circle_radius = msg['CircleSZ']
                end_ui = False
            elif 'BallP' in msg.keys():
                self.ball = msg['BallP']
                end_ui = False
            elif 'BotYP' in msg.keys():
                self.yellow_robots = msg['BotYP']
                end_ui = False
            elif 'BotBP' in msg.keys():
                self.blue_robots = msg['BotBP']
                end_ui = False
            elif 'ChallengeP' in msg.keys():
                self.challenge_positions = msg['ChallengeP']
                end_ui = False
        return end_ui

# =============================================================================

    def update_drawings(self):
        self.window.fill(D_GREEN_C)

        scaled_field = self.scale(self.field_size)
        self.draw_field(scaled_field)
        self.draw_ball(scaled_field)
        self.draw_robots(scaled_field)
        self.draw_challenges_positions(scaled_field)

# =============================================================================

    def init_ui(self):
        pygame.init()
        self.font = pygame.freetype.Font(r'resources/Days.ttf', 14)
        self.font.antialiased = True

        self.clock = pygame.time.Clock()

        self.canvas = pygame.Surface(SCREEN_SIZE)
        flags = pygame.RESIZABLE
        self.window = pygame.display.set_mode(SCREEN_SIZE, flags)
        pygame.display.set_caption('Field View')

# =============================================================================

    def start(self):
        green_print('[UI] Started!\n\t Press Q/q or close the window to exit!')
        self.ui_queue = Queue()
        # 16 = MAX_ROBOTS
        self.process_queue = Queue(16*3 + 5)
        self.process = Process(target=self.draw)

        self.process.start()

# =============================================================================

    def stop(self):
        self.process_queue.put({'END': True})
        self.process.join()
        pygame.quit()

# =============================================================================

    def set_field_size(self, new_size: [int, int]):
        if self.process.is_alive() and not self.process_queue.full():
            self.field_size = np.array(new_size)
            self.process_queue.put_nowait({'FieldSZ': self.field_size})

# =============================================================================

    def set_center_circle_radius(self, radius: int):
        if self.process.is_alive() and not self.process_queue.full():
            self.center_circle_radius = radius
            self.process_queue.put_nowait({'CircleSZ': radius})

# =============================================================================

    def draw_field(self, scaled_field: np.array):
        adj_border = self.scale_val(FIELD_BORDER)

        pygame.draw.rect(self.window, 'white', width=FIELD_LINE_PEN_SZ,
                         rect=(adj_border[0], adj_border[1],
                               scaled_field[0], scaled_field[1]))

        for line in self.field_lines(scaled_field, adj_border):
            pygame.draw.line(self.window, 'white',
                             width=round(FIELD_LINE_PEN_SZ/2),
                             start_pos=line[0], end_pos=line[1])

        pygame.draw.circle(self.window, 'white',
                           width=round(FIELD_LINE_PEN_SZ/2),
                           center=self.adjust_axis(np.array([0, 0]),
                                                   scaled_field),
                           radius=self.scale_rad(self.center_circle_radius))


# =============================================================================

    def draw_ball(self, scaled_field: np.array):
        ball_p = self.scale(self.ball, scaled_field)

        if isinstance(scaled_field, np.ndarray) or isinstance(ball_p, np.ndarray) or \
                len(ball_p) + len(scaled_field) == 4:
            pygame.draw.circle(self.window, ORANGE_C, ball_p,
                               self.scale_rad(BALL_RADIUS))

# =============================================================================

    def draw_robots(self, scaled_field: np.array):
        for bot in self.blue_robots:
            if bot.pos.x < INF:
                b_pos = np.array([bot.pos.x, bot.pos.y])
                self.draw_bot(b_pos, bot.pos.orientation, BLUE_C, scaled_field,
                              bot.id)

        for bot in self.yellow_robots:
            if bot.pos.x < INF:
                b_pos = np.array([bot.pos.x, bot.pos.y])
                self.draw_bot(b_pos, bot.pos.orientation, YELLOW_C, scaled_field,
                              bot.id)

    def draw_bot(self, pos: np.array, orientation: float, color,
                 scaled_field: np.array, id: int):
        # Both arguments must be a numpy array and have a length of 2 each
        if not isinstance(scaled_field, np.ndarray) or \
                not isinstance(pos, np.ndarray) or \
                len(pos) + len(scaled_field) != 4:
            red_print('Invalid data received ', pos, scaled_field, type(pos),
                      type(scaled_field))
            return

        b_pos = self.scale(pos, scaled_field)
        id_pos = self.scale(pos - np.array([0.6*BOT_RADIUS, -0.5*BOT_RADIUS]),
                            scaled_field)

        bot_rad = self.scale_rad(BOT_RADIUS)
        bot_teta = self.convert_orientation(orientation)
        angle_vec = np.array([cos(bot_teta)*bot_rad, -sin(bot_teta)*bot_rad])

        pygame.draw.circle(self.window, color, b_pos, bot_rad)
        try:
            self.font.render_to(self.window, id_pos, f'{id}', (0, 0, 0))
        except TypeError:
            pass
        except Exception as except_msg:
            blue_print(id_pos, type(id_pos), except_msg)

        b_pos = b_pos + angle_vec
        angle_pos = b_pos + angle_vec
        pygame.draw.line(self.window, 'red', b_pos, angle_pos, 3)

    def convert_orientation(self, orientation) -> float:
        if abs(orientation) > 2*pi:
            factor = orientation/(2*pi) - trunc(orientation/(2*pi))
            orientation = factor * 2*pi

        if orientation < 0:
            orientation += 2*pi

        if orientation > 2*pi:
            orientation = orientation - 2*pi

        return orientation

# =============================================================================

    def draw_challenges_positions(self, scaled_field: np.array):
        color = BLUE_C
        for position in self.challenge_positions:
            draw_orientation = True
            text_c = BLACK_C

            if position.type == BLUE_TEAM:
                color = C_BLUE_C
            elif position.type == YELLOW_TEAM:
                color = D_YELLOW_C
            elif position.type == BALL:
                color = ORANGE_C
                draw_orientation = False

            if position.ok:
                color = GREEN_C
                text_c = GREEN_C

            id_pos = position.pos.to_numpy()
            id_pos = self.scale(id_pos + np.array([BOT_RADIUS, 2*BOT_RADIUS]),
                                scaled_field)

            c_pos = self.scale(position.pos.to_numpy(), scaled_field)
            c_rad = self.scale_rad(BOT_RADIUS)
            pygame.draw.circle(self.window, color, c_pos, c_rad, width=2)

            if not draw_orientation:
                continue

            c_teta = self.convert_orientation(position.pos.orientation)

            min_thr = c_teta - ORIENTATION_THRESHOLD
            max_thr = c_teta + ORIENTATION_THRESHOLD

            angle_vec_min = 2 * c_rad * np.array([cos(min_thr), -sin(min_thr)])
            angle_vec_max = 2 * c_rad * np.array([cos(max_thr), -sin(max_thr)])

            p_min = c_pos + angle_vec_min
            p_max = c_pos + angle_vec_max
            pos_ang = [p_max, p_min, c_pos]

            pygame.draw.aalines(self.window, text_c, True, pos_ang)


# =============================================================================

    def update_robots(self, robots: [Robot], team: str):
        if self.process.is_alive() and not self.process_queue.full():
            if team == YELLOW_TEAM:
                self.yellow_robots = robots
                self.process_queue.put_nowait({'BotYP': self.yellow_robots})
            elif team == BLUE_TEAM:
                self.blue_robots = robots
                self.process_queue.put_nowait({'BotBP': self.blue_robots})

# =============================================================================

    def update_ball(self, pos: Position):
        if self.process.is_alive() and not self.process_queue.full():
            self.ball = np.array([pos.x, pos.y])
            self.process_queue.put_nowait({'BallP': self.ball})

# =============================================================================

    def update_challenge_data(self, chl_data: [Challenge_Data]):
        if self.process.is_alive() and not self.process_queue.full():
            self.challenge_positions = chl_data
            self.process_queue.put_nowait({'ChallengeP': chl_data})

# =============================================================================

    def scale(self, pos: np.array, field_sz=None) -> np.array:
        field_sz_border = self.field_size + \
            np.array([2*FIELD_BORDER, 2*FIELD_BORDER])
        scale_val = np.divide(np.array(SCREEN_SIZE), field_sz_border)

        if not isinstance(field_sz, np.ndarray):
            return np.multiply(pos, scale_val)

        return self.adjust_axis(np.multiply(pos, scale_val), field_sz)

    def scale_val(self, val) -> [float, float]:
        field_sz_border = self.field_size + \
            np.array([2*FIELD_BORDER, 2*FIELD_BORDER])
        scale_val = np.divide(np.array(SCREEN_SIZE), field_sz_border)

        return val * scale_val

    def scale_rad(self, val) -> float:
        field_sz_border = self.field_size + \
            np.array([2*FIELD_BORDER, 2*FIELD_BORDER])
        scale_val = np.divide(np.array(SCREEN_SIZE), field_sz_border)

        return val * sqrt(scale_val[0]**2 + scale_val[1]**2)

    def adjust_axis(self, pos: np.array, field_sz: np.array) -> np.array:
        border = self.scale_val(FIELD_BORDER)
        adj_p = np.add(pos, field_sz/2)
        adj_p[1] = field_sz[1] - adj_p[1]
        adj_p = np.add(adj_p, border)

        return adj_p

# =============================================================================

    def field_lines(self, field_sz: np.array, field_border: np.array):
        l1 = np.array([[field_sz[0]/2 + field_border[0], field_border[1]],
                       [field_sz[0]/2 + field_border[0], field_sz[1] + field_border[1]]])
        l2 = np.array([[field_border[0], field_sz[1]/2 + field_border[1]],
                       [field_sz[0] + field_border[0], field_sz[1]/2 + field_border[1]]])

        return [l1.tolist(), l2.tolist()]

# =============================================================================

    def get_ui_event(self) -> str:
        if self.init_ui and not self.ui_queue.empty():
            return self.ui_queue.get_nowait()
