from framework import Delegate, Motion, SpeakersList


class MUN:
    def __init__(self,
                 time,
                 title,
                 committee: list[Delegate],
                 agenda: list[Motion],
                 log,
                 state="START"):
        self.time = time
        self.committee = committee
        self.state = state
        self.requires_chair_action = False
        self.agenda = agenda
        self.log = log
        self.title = title
        self.resolutions = []
        self.general_speakers_list = SpeakersList(speech_duration=None)
    
    def intro(self): 
        return f""" 
        Welcome to Model United Nations General Committe debate
        Topic on the agenda today is: {self.title}
        Members present in the committee are: {self.committee}
        """"
    
    def build_log(self):
        pass
    