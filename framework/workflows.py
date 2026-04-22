from framework.framework import (
    DraftResolution,
    Vote,
    ModeratedCaucus,
    UnmoderatedCaucus,
    WorkingPaper
)
from framework.mun import MUN
from cognition.prompts import persona_context, generation_rules
from cognition.engine import think
from pathlib import Path


def create_session_logs():
    Path("session_logs").mkdir(exist_ok=True)


def general_debate():
    pass


# LATER ON IMPLEMENT AMENDMENTS
def process_draft_resolution(resolution: DraftResolution, session: MUN):

    vote = Vote(
        id="v" + session.time,
        topic="Draft Resolution",
        type="substantive",
        supporting_document=resolution,
        delegates_refraining=[],
        delegates_in_favor=[],
        delegates_against=[],
    )

    for delegate in session.committee:
        delegate.vote(vote, session)

    # Log issue of log
    vote.log(session.log, session.time)


def process_moderated_caucus(caucus: ModeratedCaucus, session: MUN):
    print(f"MODERATED CAUCUS SESSION {caucus.id}")

    print(" ======= Voluntary speakers =======")
    speaker_candidates = []
    for delegate in session.committee:
        proposal_prompt = f"""
            {persona_context(delegate, session)}

            The following Moderated Caucus has been suggested on the floor: 
            {caucus.present()}

            Would you like to take part as a speaker for this caucus? 
            Decide based on:
            - your national interests
            - geopolitical context
            - the current state of the debate
            """
        delegate_decision = delegate.decide(proposal_prompt)
        if delegate_decision == "yes":
            speaker_candidates.append(delegate.id)

    print("======= Speaker list selection by the chair =======")
    print(f"List of speaker candidates: {speaker_candidates}")
    chair_selection = input(
        f"""Select less or equal than {caucus.num_speakers} IDs of 
        selected speakers for the Moderated Caucus, return a list of strings 
        >>>"""
    )
    speakers = [
        delegate for delegate in session.committee if delegate.id in chair_selection
    ]

    print(" ======= Speeches ======= ")
    for delegate in speakers:
        speech_context_prompt = f"""
        You are taking part in the following ongoing Moderated Caucus: 
        {caucus.present}
        Delegates also speaking are {[delegate.country for delegate in speakers]}
        The speeches already are in the dict 'speeches'
        """
        speech = delegate.make_speech(
            topic_prompt=speech_context_prompt,
            speech_duration=caucus.speech_duration,
            session=session,
        )
        print(
            f"""Delegation of {delegate.country} takes the floor: 
              ----------------------------------------------------
              {speech}
            """
        )
        print("Speech logged")
        caucus.speeches[str(delegate.country)] = speech

    print(" ======= End of Moderated Caucus, back to general debate =======")
    session.log = session.log + caucus.present
    general_debate()


def process_unmoderated_caucus(caucus: UnmoderatedCaucus, session: MUN):
    print(f"UNMODERATED CAUCUS SESSION {caucus.id}")

    print("======== Initial Positions ========")
    for delegate in session.committee:
        position_prompt = f"""
            {persona_context(delegate, session)}

            The following unmoderated caucus is now being processed:

            {caucus.present()}

            State your initial positions regarding this topic. As the delegate of {delegate.country},
            state your priorities, red lines, initial ideas etc. Reason based on your national interests
            geopolitical context and the current state of the debate. 

            You must return a JSON object with EXACTLY this format:
            {{"position": "your_position"}}

            {generation_rules}
        """
        response = think(position_prompt)
        position = response["position"]
        caucus.positions[delegate.country] = position
    print(f"Gathered initial positions : {caucus.positions}")

    print(" ======= Blocs formation ======= ")
    bloc_requests = {}
    for delegate in session.committee:
        bloc_choice_prompt = f"""
            {persona_context(delegate, session)}

            The following unmoderated caucus is now being processed:

            {caucus.present()}

            Members of the committee (you included) have stated their initial positions regading the topic.
            Read them here : 
            {caucus.positions}

            You will now have a time to debate, share ideas and draft resolutions in blocs of delegations.
            Select the countries you want to be grouped with among the committee : {[delegate.country for delegate in session.committee]}
            Choose based on your national interests, the positions stated by the other delegates and the 
            current state of the debate. 

            You must return a JSON object with EXACTLY this format:
            {{"bloc": ["USA", "France", ...]}}

            {generation_rules}
        """
        response = think(bloc_choice_prompt)
        bloc_choice = response["bloc"]
        bloc_requests[delegate.country] = bloc_choice

    print(" ======== Blocs formation by the Chair ======== ")
    print(
        f"Delegates have made the following wishes regarding their blocs: {bloc_requests}"
    )

    selected_blocs = input(
        """Manually form blocs by submitting a dictionary in the form: 
                "B1": ["Country1","Country2",...]
                >>>"""
    )
    caucus.make_blocs_brief(selected_blocs, session)

    print(" ======== Free negociations within blocs ======== ")
    T = caucus.duration
    print(f"Running {T} thinking iterations per bloc")
    for t in range(T):
        for bloc in caucus.blocs_brief:
            for delegate in bloc["members"]:
                contribution_prompt = f"""
                    {persona_context(delegate, session)}

                    You are currently discussing with your bloc within the following unmoderated caucus:
                    {caucus.present()}

                    Members of your bloc are : {bloc["members"]}

                    The following ideas, agreements, conflicts have already been shared:
                    {caucus.blocs_brief[bloc["id"]]}

                    You can contribute to the discussion in one of the 3 forms:
                    - Propose a new idea
                    - Support an idea
                    - Oppose an idea

                    You must return a JSON object with EXACTLY this format:
                    {{"type": "propose" | "support" | "oppose",
                      "content": "your country + content of your contribution"}}

                    Keep it short (1-2 sentences max), focused on the caucus topic and targetted.
                    
                    {generation_rules}

                """
                action = think(contribution_prompt)
                caucus.update_bloc_state(bloc["id"], action)
        
    print(" ======== Building working papers with a neutral LLM agent ======== ")
    print(" Logging papers in session memory ")
    working_papers = []
    for bloc in caucus.blocs_brief: 
        bloc_id = bloc['id']
        print(f"Building paper for bloc {bloc_id}")
        paper_id = "P"+bloc_id
        paper = WorkingPaper(id=paper_id)
        paper.build_paper(caucus.blocs_brief, bloc_id)
        paper.display()
        print("Logging paper in session memory")
        #session.log.write(paper)
        working_papers.append(paper)
    
    print(" ======== Draft resolutions ======== ")
    print("Selecting working papers")
    for paper in working_papers: 
        draft = paper.evaluate()
        if not draft:
            print(f"Paper {paper.id} not retained for draft resolution")
        if draft:
            print(f"Drafting {paper.id} into resolution")
            # TODO : build resolution


    
    
    

