class Delegate:
    def __init__(self, id: str, name: str, country: str, context):
        self.id = id
        self.name = name
        self.country = country
        self.context = context

    def vote(self, topic):
        pass

    def raise_motion():
        pass

    def raise_point():
        pass

    def make_speech():
        pass


class SpeakersList:
    def __init__(self, queue: list[Delegate], speech_duration: int):
        self.queue = queue
        self.speech_duration = speech_duration


class ModeratedCaucus:
    def __init__(self, topic: str, num_speakers: int, speech_duration: int):
        self.topic = topic
        self.num_speakers = num_speakers
        self.speech_duration = speech_duration


class UnmoderatedCaucus:
    def __init__(self, duration: int):
        self.duration = duration


# ------------ PROCEDURES ------------

MOTION_TYPES = [
    "open speakers list",
    "moderated caucus",
    "unmoderated caucus",
    "introduce draft resolution",
    "close debate",
    "vote",
]


class Motion:
    def __init__(
        self, id: str, type: str, proposer: Delegate, parameters: dict, status: str
    ):
        self.id = id
        self.type = type
        self.proposer = proposer
        self.parameters = parameters
        self.status = status


POINT_TYPES = ["order", "inquiry"]


class Point:
    def __init__(self, id: str, proposer: Delegate, type: str, status: str):
        self.id = id
        self.proposer = proposer
        self.type = type
        self.status = status


VOTING_TYPES = ["procedural", "substantive"]


class Vote:
    def __init__(
        self,
        id: str,
        type: str,
        delegates_refraining: list[Delegate],
        delegates_in_favor: list[Delegate],
        delegates_against: list[Delegate],
    ):
        self.id = id
        self.type = type
        self.delegates_refraining = delegates_refraining
        self.refraining_count = len(delegates_refraining)
        self.delegates_in_favor = delegates_in_favor
        self.favor_count = len(delegates_in_favor)
        self.delegates_against = delegates_against
        self.against_count = len(delegates_against)

    def evaluate(self, type) -> bool:
        """Evaluate if a vote passes according to its type"""
        if type == "procedural":  # Simple majority
            return self.favor_count >= 0.5(
                self.favor_count + self.against_count + self.refraining_count
            )
        if type == "substantiative":  # Two thirds
            return self.favor_count >= 0.66 * (
                self.favor_count + self.against_count + self.refraining_count
            )


# ------------ DOCUMENTS ------------


class WorkingPaper:
    """Informal Document put together during the unmods"""

    def __init__(
        self,
        id: str,
        sponsors: list[Delegate],
        signatories: list[Delegate],
        clauses: list[str],
        status: str,
    ):
        self.id = id
        self.sponsors = sponsors
        self.signatories = signatories
        self.clauses = clauses
        self.status = status


class DraftResolution:
    """Formal document to be debated on and voted on"""

    def __init__(
        self,
        id: str,
        topic: str,
        sponsors: list[Delegate],
        signatories: list[Delegate],
        preambulatory_clauses: list[(int, str)],
        operative_clauses: list[(int, str)],
        introduced: bool,
        passed: bool | None,
    ):
        self.id = id
        self.topic = topic
        self.sponsors = sponsors
        self.signatories = signatories
        self.preambulatory_clauses = preambulatory_clauses
        self.operative_clauses = operative_clauses
        self.introduced = introduced
        self.passed = passed


class Amendment:
    """change proposed to a draft resolution"""

    def __init__(
        self,
        id: str,
        target_resolution: DraftResolution,
        proposer: Delegate,
        clause_target_id: int,
        amendment_type: str,
        new_text: str,
        is_friendly: bool,
    ):
        self.id = id
        self.target_resolution = target_resolution
        self.proposer = proposer
        self.clause_target_id = clause_target_id
        self.amendment_type = amendment_type
        self.new_text = new_text
        self.is_friendly = is_friendly
