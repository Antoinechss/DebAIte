from framework import Delegate


class MUN: 
    def __init__(self,
                 committee: list[Delegate],
                 state: str):
        self.committee = committee
        self.state = state
        self.requires_chair_action = False