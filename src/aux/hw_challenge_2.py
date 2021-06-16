from aux.challenge_aux import ChallengeSteps, ChallengeEvents, Action
from aux.GCSocket import GCCommands
from aux.RobotBall import Position


class Challenge_2(object):
    max_steps = 4
    id = 2
    max_attack_robots = 0
    min_attack_robots = 0
    has_extra_data = False

    @staticmethod
    def Step(step: ChallengeSteps) -> Action:
        if step == ChallengeSteps.STEP_0:
            return Action(False)
        elif step == ChallengeSteps.STEP_1:
            return Challenge_2.Step_1()
        elif step == ChallengeSteps.STEP_2:
            return Challenge_2.Step_2()
        elif step == ChallengeSteps.STEP_3:
            return Challenge_2.Step_3()
        elif step == ChallengeSteps.STEP_4:
            return Challenge_2.Step_4()

    @staticmethod
    def Step_1() -> Action:
        return Action(False, command=GCCommands.STOP)

    @staticmethod
    def Step_2() -> Action:
        return Action(False, timer=0.5)

    @staticmethod
    def Step_3() -> Action:
        return Action(True, command=GCCommands.FORCE_START)

    @staticmethod
    def Step_4() -> Action:
        return Action(False, timer=30)
