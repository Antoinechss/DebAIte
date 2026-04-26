import json

from framework.framework import (
    DraftResolution,
    Vote,
    ModeratedCaucus,
    UnmoderatedCaucus,
    WorkingPaper,
)
from framework.mun import MUN
from cognition.prompts import persona_context, generation_rules
from cognition.engine import think
from logs.log import save_state


# LATER ON IMPLEMENT AMENDMENTS
def vote_draft_resolution(resolution: DraftResolution, session: MUN):

    vote = Vote(
        id=session.next_id("V"),
        topic=f"Draft Resolution {resolution.id}",
        type="substantive",
        supporting_document=resolution,
        delegates_refraining=[],
        delegates_in_favor=[],
        delegates_against=[],
    )

    for delegate in session.committee:
        delegate.vote(vote, session)

    resolution.passed = vote.evaluate()
    vote.log(session.log, session.time)
    save_state(session)


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
        f"""Select up to {caucus.num_speakers} speaker IDs (comma-separated)
        >>>"""
    )
    selected_ids = {s.strip() for s in chair_selection.split(",") if s.strip()}
    speakers = [
        delegate for delegate in session.committee if delegate.id in selected_ids
    ]

    print(" ======= Speeches: ======= ")
    for delegate in speakers:
        speech_context_prompt = f"""
        You are taking part in the following ongoing Moderated Caucus:
        {caucus.present()}
        Delegates also speaking are {[d.country for d in speakers]}
        The speeches already given are in the dict 'speeches'
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

    caucus_log = caucus.to_dict()
    session.log["moderated_caucuses"][caucus.id] = caucus_log
    save_state(session)

    print(" ======= End of Moderated Caucus, back to general debate =======")


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

    raw_blocs = input(
        """Manually form blocs as JSON, e.g. {"B1": ["USA","France"], "B2": ["Iran"]}
                >>>"""
    )
    selected_blocs = json.loads(raw_blocs)
    caucus.make_blocs_brief(selected_blocs, session)

    print(" ======== Free negociations within blocs ======== ")
    T = caucus.duration
    print(f"Running {T} thinking iterations per bloc")
    for t in range(T):
        for bloc in caucus.blocs_brief.values():
            for delegate in bloc["members"]:
                contribution_prompt = f"""
                    {persona_context(delegate, session)}

                    You are currently discussing with your bloc within the following unmoderated caucus:
                    {caucus.present()}

                    Members of your bloc are : {[d.country for d in bloc["members"]]}

                    The following ideas, agreements, conflicts have already been shared:
                    {bloc}

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
    working_papers = []
    for bloc_id in caucus.blocs_brief:
        print(f"Building paper for bloc {bloc_id}")
        paper = WorkingPaper(id=session.next_id("P"))
        paper.bloc_id = bloc_id
        paper.build_paper(caucus.blocs_brief, bloc_id)
        print(paper.present())
        working_papers.append(paper)

    print(" ======== Draft resolutions ======== ")
    for paper in working_papers:
        draft = paper.evaluate()
        if not draft:
            print(f"Paper {paper.id} not retained for draft resolution")
            continue
        print(f"Drafting {paper.id} into resolution")
        resolution = DraftResolution(id=session.next_id("DR"))
        resolution.paper_id = paper.id
        resolution.build_from_paper(paper)
        print(resolution.present())
        session.resolutions.append(resolution)
        session.log["resolutions"][resolution.id] = {
            "title": resolution.title,
            "sponsors": resolution.sponsors,
            "preambulatory_clauses": resolution.preambulatory_clauses,
            "operative_clauses": resolution.operative_clauses,
            "passed": resolution.passed,
        }

    session.log["unmoderated_caucuses"][caucus.id] = {
        "topic": caucus.topic,
        "proposer": caucus.proposer.country,
        "positions": caucus.positions,
        "blocs": {bid: [d.country for d in b["members"]]
                  for bid, b in caucus.blocs_brief.items()},
    }
    save_state(session)

    print(" ======= End of the Unmoderated caucus, back to general debate ======= ")


def general_speakers_list(session: MUN):
    print(" GENERAL SPEAKERS LIST ")
    print("Reopening General Speakers List")
    general_speakers_list = session.general_speakers_list

    print(" ======== Updating queue with new voluntary speakers ======= ")
    for delegate in session.committee:
        if delegate in general_speakers_list.queue:
            removal_prompt = f"""
                {persona_context(delegate, session)}

                The general speakers list has been reopened and you are in the queue of voluntary speakers. 
                Based on the state of the debate, your national interests and your ideas, 
                you can be removed (exceptional move) from this list.

                Choose if you want to stay or be removed from the list before delegates take the floor.

                You must return a JSON object with EXACTLY this format:
                {{"remove": True}}
                OR 
                {{"remove": False}}

                {generation_rules}
                """
            response = think(removal_prompt)
            remove_delegate = response["remove"]
            if remove_delegate:
                general_speakers_list.queue.remove(delegate)
        else: 
            invitation_prompt = f"""
                {persona_context(delegate, session)}

                The general speakers list has been reopened and you are asked if you would like 
                to be added to the speakers queue. Reason based on the current state of the debate,
                your national interest and current ideas you could express. 

                You must return a JSON object with EXACTLY this format:
                {{"add": True}}
                OR 
                {{"add": False}}

                {generation_rules}
                """
            response = think(invitation_prompt)
            add_delegate = response["add"]
            if add_delegate:
                general_speakers_list.queue.append(delegate)

    print(" ======== Running half of list before taking other motions ======= ")

    if len(general_speakers_list.queue) < 3:
        print("Not enough speakers to run General Speakers List")
        return

    num_speeches = len(general_speakers_list.queue) // 2
    past_speeches = {}
    for _ in range(num_speeches):
        delegate = general_speakers_list.queue.pop(0)
        print(f"Delegation of {delegate.country} takes the floor")
        gsl_prompt = f"""
            This speech is part of the general speakers list.
            It needs to be closely linked to the history of the debate,
            motions passed, unmods negociations and reflect your positions.

            The previous speeches have been the following:

            {past_speeches}

            You can respond to, trigger or comment those speeches if you feel it is pertinent.
        """
        speech = delegate.make_speech(
            topic_prompt=gsl_prompt, speech_duration=200, session=session
        )
        print(speech)
        past_speeches[delegate.country] = speech
        session.general_speakers_list.speeches[delegate.country] = speech

    session.log["general_speakers_list"]["speeches"].update(past_speeches)
    session.log["general_speakers_list"]["current_queue"] = [
        d.country for d in session.general_speakers_list.queue
    ]
    save_state(session)

    print(" ===== Closing General Speakers List ======== ")
    

def general_debate(session: MUN):

    print("==== Gathering delegate motion claims ====")
    motion_claims = {}
    for delegate in session.committee:
        delegate_claim = delegate.motion(session)
        motion_claims[delegate.country] = delegate_claim
    print(motion_claims)

    proposed = {c: m for c, m in motion_claims.items() if m.get("type")}

    print("==== Chair filters valid motions ====")
    print(f"Proposed motions: {proposed}")
    keep = input(
        "Comma-separated countries whose motions to keep (empty = all): >>>"
    )
    if keep.strip():
        keep_set = {c.strip() for c in keep.split(",") if c.strip()}
        valid_motions = {c: m for c, m in proposed.items() if c in keep_set}
    else:
        valid_motions = proposed

    if len(valid_motions) == 0:
        print("No valid motions at this time, opening general speakers list default")
        general_speakers_list(session)
        return

    print("==== Voting on proposed motions ====")
    for delegate in session.committee:
        valid_motions = delegate.vote_motions(valid_motions, session)
    proposing_country, motion = max(
        valid_motions.items(),
        key=lambda item: item[1]["vote_score"]
    )

    print(f"Running motion proposed by {proposing_country}")
    proposer = next(d for d in session.committee if d.country == proposing_country)

    if motion["type"] == "unmod":
        caucus = UnmoderatedCaucus(
            id=session.next_id("UMC"),
            topic=motion["parameters"]["topic"],
            proposer=proposer,
        )
        process_unmoderated_caucus(caucus, session)

    elif motion["type"] == "mod":
        caucus = ModeratedCaucus(
            id=session.next_id("MC"),
            topic=motion["parameters"]["topic"],
            proposer=proposer,
            num_speakers=motion["parameters"]["num_speakers"],
            speech_duration=motion["parameters"]["speech_duration"],
        )
        process_moderated_caucus(caucus, session)

    elif motion["type"] == "general_speakers_list":
        general_speakers_list(session)

    elif motion["type"] == "present_resolution":
        pass

    elif motion["type"] == "vote_resolution":
        resolution_id = motion["parameters"]["resolution_id"]
        resolution = next(r for r in session.resolutions if r.id == resolution_id)
        vote_draft_resolution(resolution, session)

    elif motion["type"] == "end":
        print("======= End of the MUN session =======")
        session.state = "END"
