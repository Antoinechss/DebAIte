from framework.framework import Delegate, SpeakersList


ID_PREFIXES = {"MC", "UMC", "P", "DR", "V", "A"}


class MUN:
    def __init__(self,
                 time,
                 title,
                 committee: list[Delegate],
                 agenda,
                 log,
                 state="START"):
        self.time = time
        self.committee = committee
        self.state = state
        self.requires_chair_action = False
        self.log = log
        self.title = title
        self.agenda = agenda
        self.resolutions = []
        self.general_speakers_list = SpeakersList(speech_duration=None)
        self._counters = {prefix: 0 for prefix in ID_PREFIXES}

    def next_id(self, prefix: str) -> str:
        if prefix not in self._counters:
            raise ValueError(
                f"Unknown ID prefix '{prefix}'. See IDS.md for the legend."
            )
        self._counters[prefix] += 1
        return f"{prefix}{self._counters[prefix]}"

    def intro(self):
        return f"""
        Welcome to Model United Nations General Committe debate
        Topic on the agenda today is: {self.title}
        Members present in the committee are: {self.committee}
        """
