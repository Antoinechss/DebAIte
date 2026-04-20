from framework import Delegate, Motion


class MUN:
    def __init__(self,
                 committee: list[Delegate],
                 state: str,
                 agenda: list[Motion]):
        self.committee = committee
        self.state = state
        self.requires_chair_action = False
        self.agenda = agenda