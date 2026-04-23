from mun import MUN
from cognition.prompts import persona_context, generation_rules, motion_submission_rules
from cognition.engine import think


class Delegate:
    def __init__(self, id: str, name: str, country: str):
        self.id = id
        self.name = name
        self.country = country

    def motion(self, session: MUN):
        choose_prompt = f"""

        {persona_context(self, session)}

        Chair asks "Are there any motions on the floor ?"
        Based on your current incentives, the history of the debate, your objectives for the session, 
        choose if you want to submit a motion proposition, and in this case give its parameters. 

        You must return a JSON object with EXACTLY this format:
        {{"type": str | None,
          "parameters": dict | None, 
          "vote_score": O
        }}

        Motion types and parameters should STRICTLY follow this format: 
        {motion_submission_rules}

        {generation_rules}
        """
        response = think(choose_prompt)

        return response

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

    def present_amendment(self, amendment):
        amendment.present()

    def present_draft_resolution(self, draft_resolution):
        draft_resolution.present()

    def vote_motions(self, motions: dict, session: MUN): 
        """
        Delegate sees : 
        motions = {'country1': {"type": str, "parameters": dict | None, "vote_score": O}, 
                    'country2': {"type": str, "parameters": dict | None, "vote_score": O}}
        And votes for the motions he wants to be realised
        Returns the updated dict of motions
        """
        vote_prompt = f"""{persona_context(self, session)}

        Chair has asked for motion claims on the floor and the following motions have been proposed: 
        {motions}

        Vote based on your national interests and the topics you might want to discuss (or avoid), 
        the current history of the debate and the geopolitical context. 
        Some common sense to make your vote: 
        - Prioritise presentation of resolutions if there has previously been an unmod
        - Prioritise mods or general speakers list if early in the debate 
        - Prioritise voting of resolutions if it has previously been presented 
        - Unmods are more constructive when they come after a mod
        - End the session only when really feeling like there has been enough discussion

        You must return a JSON object with EXACTLY this format:
        {{"supported_motions": ['country1', 'country3', ...]}}
        i.e. a dict with the list of countries (with correct orthograph) you support the motions. 
        {generation_rules}
        """
        response = think(vote_prompt)
        supported_motions = response["supported_motions"]
        # Updating motions dict: 
        for country in supported_motions: 
            motions[country]["vote_score"] += 1
        
        return motions


class SpeakersList:
    def __init__(self, speech_duration: int | None):
        self.queue = []
        self.speech_duration = speech_duration


class ModeratedCaucus:
    def __init__(
        self,
        id,
        topic: str,
        proposer: Delegate,
        num_speakers: int,
        speech_duration: int,
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
    def __init__(self, id, topic: str, proposer: Delegate):
        self.id = id
        self.topic = topic
        self.duration = 30
        self.blocs_brief = {}
        self.proposer = proposer
        self.temp_memory = {}
        self.positions = {}

    def present(self):
        return f"""
        Unmoderated Caucus on the topic of {self.topic} proposed by {self.proposer.country}. 
        Duration of free debate session : {self.duration} dialogue iterations. 
        """

    def make_blocs_brief(self, selected_blocs: dict, session: MUN):
        print("Building bloc brief")
        for bloc_id, member_countries in selected_blocs.items():
            self.blocs_brief[bloc_id] = {
                "id": bloc_id,
                "members": [
                    delegate
                    for delegate in session.committee
                    if delegate.country in member_countries
                ],
                "positions": {
                    country: self.positions[country] for country in member_countries
                },
                "ideas": [],
                "agreements": [],
                "conflicts": [],
            }

    def update_bloc_state(self, bloc_id: str, action: dict):
        action_type = action["type"]
        content = action["content"]
        bloc_brief = self.blocs_brief[bloc_id]

        if action_type == "propose":
            bloc_brief["ideas"].append(content)
        if action_type == "support":
            bloc_brief["agreements"].append(content)
        if action_type == "oppose":
            bloc_brief["conflicts"].append(content)


# ------------ PROCEDURES ------------

MOTION_TYPES = [
    "open speakers list",
    "moderated caucus",
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
    ):
        self.id = id
        self.title = ""
        self.sponsors = []
        self.preambulatory_clauses = []
        self.operative_clauses = []

    def build_paper(self, blocs_brief: dict, bloc_id: str):

        prompt = f"""
        You are a UN drafting expert
        Based on the following agreed elements within the bloc of countries: {blocs_brief[bloc_id]["members"]}
        Ideas:
        {blocs_brief[bloc_id]["ideas"]}
        Agreements:
        {blocs_brief[bloc_id]["agreements"]}
        Write a working paper using formal UN style.

        - Stay true to the content given
        - Do not invent additional components
        - Be concise and factual

        You must return a JSON object with EXACTLY this format:
        {{
        "title": your_title,
        "preambulatory_clauses": [clause1, clause2...],
        "operative_clauses": [clause1, clause2...]
        }}

        {generation_rules}
        """

        response = think(prompt)
        self.title = response["title"]
        self.preambulatory_clauses = response["preambulatory_clauses"]
        self.operative_clauses = response["operative_clauses"]
        self.sponsors = blocs_brief[bloc_id]["members"]

    def present(self):
        return f"""
        Working paper n° {self.id}

        {self.title}

        Sponsors: {self.sponsors}

        ------------------------------------------------------
        Preambulatory Clauses: 

        {self.preambulatory_clauses}

        Operative Clauses: 

        {self.operative_clauses}
        """

    def evaluate(self):
        prompt = f"""
            You are a UN committee chair
            Evaluate the following working paper established within a bloc during unmoderated caucus: 

            {self.display()}

            Decide if it is sufficiently developed to be introduced as a draft resolution
            Criterias: 
            - Contains clear operative clauses 
            - Coherent and structured 
            - Actionable measures 

            You must return a JSON object with EXACTLY this format:
            {{"valid": True}}
            OR
            {{"valid": False}}

            {generation_rules}
        """
        response = think(prompt)
        decision = response["valid"]
        return decision


class DraftResolution:
    """Formal document to be debated on and voted on"""

    def __init__(
        self,
        id: str,
    ):
        self.id = id
        self.title = ""
        self.sponsors = []
        self.signatories = []
        self.preambulatory_clauses = []
        self.operative_clauses = []
        self.passed = None

    def build_from_paper(self, paper: WorkingPaper):
        prompt = f"""
            You are a UN redaction expert in a Model United Nations Debate.
            During unmoderated caucus, bloc of country has put together the following working paper:
            {paper.present()}
            Formalise it into a draft resolution using formal UN style
            
            - Stay true to the content given 
            - Do not invent additional components
            - Be concise and factual

            You must return a JSON object with EXACTLY this format:
            {{
            "title": your_title,
            "sponsors": [country1, country2, ...],
            "preambulatory_clauases": [1. clause1; , 2. clause2; ..., N. clauseN.]
            "operative_clauses": [1. clause1; , 2. clause2; ..., N. clauseN.]
            }}

            {generation_rules}
            """
        response = think(prompt)
        self.title = response["title"]
        self.sponsors = response["sponsors"]
        self.preambulatory_clauases = response["preambulatory_clauases"]
        self.operative_clauses = response["operative_clauses"]

    def present(self):
        return f""" 
            DRAFT RESOLUTION
            {self.title}

            Sponsors: {self.sponsors}
            Signatories: {self.signatories}
            -----------------------------------------------------------------------------
            
            Preambulatory Clauses : 
            {self.preambulatory_clauses}


            Operative clauses :
            {self.operative_clauses}
            
            Signatories : {self.signatories}

            Status: {self.passed}
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
