from aux.challenge_aux import ChallengeSteps, ChallengeEvents, Action
from aux.GCSocket import GCCommands


class Challenge_3(object):
    max_steps = 2
    id = 3

    @staticmethod
    def Step(step: ChallengeSteps) -> Action:
        if step == ChallengeSteps.STEP_0:
            return Action(False)
        elif step == ChallengeSteps.STEP_1:
            return Challenge_3.Step_1()
        elif step == ChallengeSteps.STEP_2:
            return Challenge_3.Step_2()

    @staticmethod
    def Step_1() -> Action:
        return Action(True, command=GCCommands.FORCE_START)

    @staticmethod
    def Step_2() -> Action:
        return Action(False, timer=120)
