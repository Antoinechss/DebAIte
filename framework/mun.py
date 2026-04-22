from framework import Delegate, Motion


class MUN:
    def __init__(self,
                 time,
                 title,
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
        self.title = title
    
    def intro(self): 
        return f""" 
        Welcome to Model United Nations General Committe debate
        Topic on the agenda today is: {self.title}
        Members present in the committee are: {self.committee}
        """"
    