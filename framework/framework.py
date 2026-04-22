from mun import MUN
from cognition.prompts import persona_context, generation_rules
from cognition.engine import think


class Delegate:
    def __init__(self, id: str, name: str, country: str):
        self.id = id
        self.name = name
        self.country = country

    def vote(self, vote, session: MUN):
        vote_brief = vote.brief()

        prompt = f"""
            {persona_context(self, session)}

            This is a voting procedure.

            You are asked to vote on the following resolution:
            {vote_brief}

            Decide based on:
            - your national interests
            - geopolitical context
            - the current state of the debate

            You must return a JSON object with EXACTLY this format:
            {{"vote": "yes"}}
            OR
            {{"vote": "no"}}
            OR
            {{"vote": "blank"}}

            {generation_rules}
            """

        response = think(prompt)
        delegate_vote = response["vote"]

        if delegate_vote == "yes":
            vote.delegates_in_favor.append(self.id)
        if delegate_vote == "no":
            vote.delegates_against.append(self.id)
        if delegate_vote == "blank":
            vote.delegates_refraining.append(self.id)
        else:  # Default blank vote
            vote.delegates_refraining.append(self.id)

    def make_speech(self, topic_prompt: str, speech_duration: int, session: MUN):
        prompt = f"""
            {persona_context(self, session)}

            Representing the delegation of {self.country}, deliver a speech to the committee. 
            The context and instructions of the speech is the following:
            {topic_prompt} 

            Built it based on:
            - your national interests
            - geopolitical context
            - the current state of the debate and the current motion it happens in

            You must return a JSON object with EXACTLY this format:
            {{"speech": "your_speech"}}

            The speech should be {speech_duration} words MAX. 

            {generation_rules}
            """
        response = think(prompt)
        speech = response["speech"]
        return speech

    def raise_motion(self, motion):
        motion.claim()

    def decide(self, proposal):
        prompt = f"""
            {proposal}
            You must return a JSON object with EXACTLY this format:
            {{"decision": "yes"}}
            OR
            {{"decision": "no"}}
            
            {generation_rules}
            """
        response = think(prompt)
        delegate_decision = response["decision"]
        return delegate_decision

    def raise_point(self, point):
        point.claim()

    def present_amendment(self, amendment):
        amendment.present()

    def present_draft_resolution(self, draft_resolution):
        draft_resolution.present()


class SpeakersList:
    def __init__(self, speech_duration: int):
        self.queue = []
        self.speech_duration = speech_duration


class ModeratedCaucus:
    def __init__(
        self, id, topic: str, proposer: Delegate, num_speakers: int, speech_duration: int
    ):
        self.id = id
        self.topic = topic
        self.proposer = proposer
        self.num_speakers = num_speakers
        self.speech_duration = speech_duration
        self.speeches = {}

    def present(self):
        return f"""
        Moderated Caucus on the topic of {self.topic} proposed by {self.proposer.country}
        {self.num_speakers} speakers for {self.speech_duration} speaking time

        Speeches already given (empty if caucus has not started yet): 
        {self.speeches}
        """


class UnmoderatedCaucus:
    def __init__(self, id, duration: int, topic: str, proposer: Delegate):
        self.id = id
        self.topic = topic
        self.duration = duration
        self.blocs_brief = {}
        self.proposer = proposer
        self.temp_memory = {}
        self.positions = {}
    
    def present(self): 
        return f"""
        Unmoderated Caucus on the topic of {self.topic} proposed by {self.proposer.country}. 
        Duration of free debate session : {self.duration}
        """ 
    
    def make_blocs_brief(self, selected_blocs: dict):
        for bloc_id, members in selected_blocs.items(): 
            self.blocs_brief[bloc_id] = {
                "members": members,
                "positions": {
                    country: self.positions[country] for country in members
                }
            }

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


# POINT_TYPES = ["order", "inquiry"]


# class Point:
#     def __init__(
#         self, id: str, proposer: Delegate, type: str, status: str, content: str
#     ):
#         self.id = id
#         self.proposer = proposer
#         self.type = type
#         self.status = status
#         self.content = content

#     def claim(self):
#         return f"""
#             Point {self.id} of {self.type} claimed by {self.proposer}: {self.content}
#             """


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

    def log(self, session_log, timestamp):
        vote_brief = self.brief()
        issue = self.evaluate()
        session_log.write(
            f"""
            Time: {timestamp}
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
