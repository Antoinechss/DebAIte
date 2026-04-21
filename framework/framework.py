class Delegate:
    def __init__(self, id: str, name: str, country: str, context: str):
        self.id = id
        self.name = name
        self.country = country
        self.context = context

    def vote(self, vote):
        vote_brief = vote.brief()
        response = f"LLM_ENGINE_RESPONSE {vote_brief}"
        if response == "yes":
            vote.delegates_in_favor.append(self.id)
        if response == "no":
            vote.delegates_against.append(self.id)
        if response == "blank":
            vote.delegates_refraining.append(self.id)

    def raise_motion(self, motion):
        motion.claim()

    def raise_point(self, point):
        point.claim()

    def present_amendment(self, amendment):
        amendment.present()

    def present_draft_resolution(self, draft_resolution):
        draft_resolution.present()

    def make_speech(self, speech_duration: int):
        pass


class SpeakersList:
    def __init__(self, speech_duration: int):
        self.queue = []
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
    "introduce amendment" "close debate",
    "vote",
]


class Motion:
    def __init__(
        self,
        id: str,
        type: str,
        proposer: Delegate,
        parameters: dict,
        status: str,
        document,
    ):
        self.id = id
        self.type = type
        self.proposer = proposer
        self.parameters = parameters | None
        self.document = document | None
        self.status = status

    def claim(self):
        return f"""
            Motion {self.id} to {self.type} claimed by {self.proposer}.
            Parameters: {self.parameters}
            """


POINT_TYPES = ["order", "inquiry"]


class Point:
    def __init__(
        self, id: str, proposer: Delegate, type: str, status: str, content: str
    ):
        self.id = id
        self.proposer = proposer
        self.type = type
        self.status = status
        self.content = content

    def claim(self):
        return f"""
            Point {self.id} of {self.type} claimed by {self.proposer}: {self.content}
            """


VOTING_TYPES = ["procedural", "substantive"]


class Vote:
    def __init__(
        self,
        id: str,
        topic: str,
        type: str,
        supporting_document,
        delegates_refraining: list[str],
        delegates_in_favor: list[str],
        delegates_against: list[str],
    ):
        self.id = id
        self.type = type
        self.topic = topic
        self.delegates_refraining = delegates_refraining
        self.refraining_count = len(delegates_refraining)
        self.delegates_in_favor = delegates_in_favor
        self.favor_count = len(delegates_in_favor)
        self.delegates_against = delegates_against
        self.against_count = len(delegates_against)
        self.supporting_document = supporting_document

    def brief(self):
        brief = f"""
        {self.type} vote on the topic: {self.topic}
        Supporting documents: {self.supporting_document.present()}
        """
        return brief

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

    def log(self, session_log):
        vote_brief = self.brief()
        issue = self.evaluate()
        session_log.write(
            f"""
            VOTE:
            {vote_brief}
            issue: {issue}
            """
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

    def present(self):
        self.introduced = True
        return f""" 
            Draft Resolution sponsored by {self.sponsors} on the topic of {self.topic}
            -----------------------------------------------------------------------------
            
            Preambulatory Clauses : 
            {self.preambulatory_clauses}


            Operative clauses :
            {self.operative_clauses}
            
            Signatories : {self.signatories}
            """


class Amendment:
    """change proposed to a draft resolution"""

    def __init__(
        self,
        id: str,
        target_resolution: DraftResolution,
        proposer: Delegate,
        clause_target_id: int,
        new_text: str,
        is_friendly: bool,
        status: str,
    ):
        self.id = id
        self.target_resolution = target_resolution
        self.proposer = proposer
        self.clause_target_id = clause_target_id
        self.new_text = new_text
        self.is_friendly = is_friendly
        self.status = status

    def present(self):
        return f""" 
            {self.is_friendly} amendment {self.id} proposed by {self.proposer} 
            targetting resolution {self.target_resolution.id}
            -----------------------------------------------------------------------------
            
            Target clause: {self.clause_target_id}

            Replace clause by: {self.new_text}
            """
