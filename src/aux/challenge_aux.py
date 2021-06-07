from enum import Enum
from aux.GCSocket import GCCommands


class ChallengeSteps(Enum):
    """
    Each challenge is composed of n steps:
        - Challenge 1
            - Step 1: Send Stop
            - Step 2: Wait for 5s
            - Step 3: Send FreeKick
            - Step 4: Wait until goal or 20s

        - Challenge 2
            - Step 1: Send ForceStart
            - Step 2: Wait until goal or 30s

        - Challenge 3
            - Step 1: Send ForceStart
            - Step 2: Wait until the robot completely stops or 2min

        - Challenge 4
            - Step 1: Send ForceStart
            - Step 2: Wait until 5min
    """
    STEP_0 = 0
    STEP_1 = 1
    STEP_2 = 2
    STEP_3 = 3
    STEP_4 = 4

    @staticmethod
    def next_step(step):
        if step == ChallengeSteps.STEP_0:
            return ChallengeSteps.STEP_1

        if step == ChallengeSteps.STEP_1:
            return ChallengeSteps.STEP_2

        if step == ChallengeSteps.STEP_2:
            return ChallengeSteps.STEP_3

        if step == ChallengeSteps.STEP_3:
            return ChallengeSteps.STEP_4

        if step == ChallengeSteps.STEP_4:
            return ChallengeSteps.STEP_0


class ChallengeEvents(Enum):
    GOAL = 0,
    ROBOT_STOPPED = 1


class Action(object):
    def __init__(self, start_timer=False, command=GCCommands.NONE, timer=0):
        self.start_timer = start_timer
        self.command = command
        self.timer = timer  # in seconds

    def set_action(self, start_timer: bool, command=GCCommands.NONE, timer=0):
        self.execute = start_timer
        self.command = command
        self.timer = timer
