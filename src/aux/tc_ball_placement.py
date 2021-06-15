import numpy as np
from aux.challenge_aux import ChallengeSteps, ChallengeEvents, Action
from aux.GCSocket import GCCommands
from aux.RobotBall import Robot, DISTANCE_THRESHOLD


class BallPlacement(object):
    max_steps = 4
    id = 5
    max_attack_robots = 6
    min_attack_robots = 1
    has_extra_data = True
    robots_restriction = 'MiddleLine'

    @staticmethod
    def Step(step: ChallengeSteps) -> Action:
        if step == ChallengeSteps.STEP_0:
            return Action(False)
        elif step == ChallengeSteps.STEP_1:
            return BallPlacement.Step_1()
        elif step == ChallengeSteps.STEP_2:
            return BallPlacement.Step_2()
        elif step == ChallengeSteps.STEP_3:
            return BallPlacement.Step_3()
        elif step == ChallengeSteps.STEP_4:
            return BallPlacement.Step_4()

    @staticmethod
    def Step_1() -> Action:
        return Action(False, command=GCCommands.STOP)

    @staticmethod
    def Step_2() -> Action:
        return Action(False, timer=2)

    @staticmethod
    def Step_3() -> Action:
        return Action(True, command=GCCommands.BALL_PLACEMENT)

    @staticmethod
    def Step_4() -> Action:
        return Action(False, timer=30)

    @staticmethod
    def check_restriction(robots: [Robot]) -> (bool, int):
        away_from_line = [1 for bot in robots
                          if abs(bot.pos.x) > DISTANCE_THRESHOLD and
                          bot.in_vision()]

        if np.sum(np.array(away_from_line)) > 0:
            return False, 0
        return True, 0
