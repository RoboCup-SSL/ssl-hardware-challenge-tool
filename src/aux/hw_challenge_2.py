from aux.challenge_aux import ChallengeSteps, ChallengeEvents, Action
from aux.GCSocket import GCCommands
from aux.RobotBall import Position


class Challenge_2(object):
    max_steps = 2
    id = 2
    max_attack_robots = 0
    min_attack_robots = 0
    has_extra_data = True
    robots_restriction = 'BallDist'
    ball_dist = 300  # in mm

    @staticmethod
    def Step(step: ChallengeSteps) -> Action:
        if step == ChallengeSteps.STEP_0:
            return Action(False)
        elif step == ChallengeSteps.STEP_1:
            return Challenge_2.Step_1()
        elif step == ChallengeSteps.STEP_2:
            return Challenge_2.Step_2()

    @staticmethod
    def Step_1() -> Action:
        return Action(True, command=GCCommands.FORCE_START)

    @staticmethod
    def Step_2() -> Action:
        return Action(False, timer=30)

    @staticmethod
    def check_restriction(robot_pos: Position, ball_pos: Position) -> (bool, int):
        dist = round(robot_pos.distance(ball_pos))
        if dist < Challenge_2.ball_dist:
            return False, dist
        return True, dist
