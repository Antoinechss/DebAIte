from framework import Delegate, Motion


class MUN:
    def __init__(self,
                 time,
                 committee: list[Delegate],
                 state: str,
                 agenda: list[Motion],
                 log):
        self.time = time
        self.committee = committee
        self.state = state
        self.requires_chair_action = False
        self.agenda = agenda
        self.log = log