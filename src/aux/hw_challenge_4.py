import numpy as np
from aux.challenge_aux import ChallengeSteps, ChallengeEvents, Action
from aux.GCSocket import GCCommands
from aux.RobotBall import Robot, DISTANCE_THRESHOLD


class Challenge_4(object):
    max_steps = 2
    id = 4
    max_attack_robots = 6
    min_attack_robots = 3
    has_extra_data = True
    robots_restriction = 'MiddleLine'

    @staticmethod
    def Step(step: ChallengeSteps) -> Action:
        if step == ChallengeSteps.STEP_0:
            return Action(False)
        elif step == ChallengeSteps.STEP_1:
            return Challenge_4.Step_1()
        elif step == ChallengeSteps.STEP_2:
            return Challenge_4.Step_2()

    @staticmethod
    def Step_1() -> Action:
        return Action(True, command=GCCommands.FORCE_START)

    @staticmethod
    def Step_2() -> Action:
        return Action(False, timer=300)

    @staticmethod
    def check_restriction(robots: [Robot]) -> (bool, int):
        away_from_line = [1 for bot in robots
                          if abs(bot.pos.x) > 3*DISTANCE_THRESHOLD and
                          bot.in_vision()]

        if np.sum(np.array(away_from_line)) > 0:
            return False, 0
        return True, 0
