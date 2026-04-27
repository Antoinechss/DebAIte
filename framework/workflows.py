from framework.framework import (
    Amendment,
    DraftResolution,
    Vote,
    ModeratedCaucus,
    UnmoderatedCaucus,
    WorkingPaper,
    validate_motion,
)
from framework.mun import MUN
from framework.chair import (
    chair_filter_motions,
    chair_select_speakers,
    chair_form_blocs,
)
from cognition.prompts import persona_context, generation_rules
from cognition.engine import think
from logs.log import save_state, log_activity, append_passed_resolution
from logs.memory import append_bloc_history


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
    session.log["resolutions"][resolution.id]["passed"] = resolution.passed
    log_activity(
        session,
        kind="vote",
        summary=(
            f"Vote {vote.id} on {resolution.id} ({resolution.title}): "
            f"{vote.favor_count} in favor, {vote.against_count} against, "
            f"{vote.refraining_count} abstain — "
            f"{'PASSED' if resolution.passed else 'REJECTED'}"
        ),
        ref_id=vote.id,
    )
    if resolution.passed:
        append_passed_resolution(resolution)
        log_activity(
            session,
            kind="resolution_passed",
            summary=(
                f"{resolution.id} '{resolution.title}' adopted by the committee."
            ),
            ref_id=resolution.id,
        )
    save_state(session)


def process_moderated_caucus(caucus: ModeratedCaucus, session: MUN):
    print(f"MODERATED CAUCUS SESSION {caucus.id}")
    log_activity(
        session,
        kind="caucus_opened",
        summary=(
            f"{caucus.id} (moderated) opened on '{caucus.topic}' — "
            f"{caucus.num_speakers} speakers, {caucus.speech_duration}s "
            f"(proposer: {caucus.proposer.country})"
        ),
        ref_id=caucus.id,
    )

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

    selected_ids = chair_select_speakers(speaker_candidates, caucus.num_speakers)
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
        log_activity(
            session,
            kind="speech",
            summary=(
                f"{delegate.country} spoke in {caucus.id}: "
                f"{speech[:140]}{'...' if len(speech) > 140 else ''}"
            ),
            ref_id=caucus.id,
        )

    caucus_log = caucus.to_dict()
    session.log["moderated_caucuses"][caucus.id] = caucus_log
    log_activity(
        session,
        kind="caucus_closed",
        summary=(
            f"{caucus.id} closed — speakers: "
            f"{', '.join(caucus.speeches.keys()) or 'none'}"
        ),
        ref_id=caucus.id,
    )
    save_state(session)

    print(" ======= End of Moderated Caucus, back to general debate =======")


def process_unmoderated_caucus(caucus: UnmoderatedCaucus, session: MUN):
    print(f"UNMODERATED CAUCUS SESSION {caucus.id}")
    log_activity(
        session,
        kind="caucus_opened",
        summary=(
            f"{caucus.id} (unmoderated) opened on '{caucus.topic}' "
            f"(proposer: {caucus.proposer.country})"
        ),
        ref_id=caucus.id,
    )

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

    selected_blocs = chair_form_blocs(
        bloc_requests, [d.country for d in session.committee]
    )
    caucus.make_blocs_brief(selected_blocs, session)
    log_activity(
        session,
        kind="blocs_formed",
        summary=(
            f"Blocs in {caucus.id}: "
            + "; ".join(
                f"{bid}=[{', '.join(members)}]"
                for bid, members in selected_blocs.items()
            )
        ),
        ref_id=caucus.id,
    )

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

    # Information asymmetry: write each bloc's deliberation to its members'
    # private memory only. The public session_brief never sees this.
    for bloc_id, bloc in caucus.blocs_brief.items():
        entry = {
            "caucus_id": caucus.id,
            "bloc_id": bloc_id,
            "members": [d.country for d in bloc["members"]],
            "ideas": list(bloc.get("ideas", [])),
            "agreements": list(bloc.get("agreements", [])),
            "conflicts": list(bloc.get("conflicts", [])),
        }
        for delegate in bloc["members"]:
            append_bloc_history(delegate.id, entry)

    print(" ======== Building working papers with a neutral LLM agent ======== ")
    working_papers = []
    for bloc_id in caucus.blocs_brief:
        print(f"Building paper for bloc {bloc_id}")
        paper = WorkingPaper(id=session.next_id("P"))
        paper.bloc_id = bloc_id
        paper.build_paper(caucus.blocs_brief, bloc_id)
        print(paper.present())
        working_papers.append(paper)
        log_activity(
            session,
            kind="paper_built",
            summary=(
                f"{paper.id} drafted by bloc {bloc_id}: '{paper.title}' "
                f"(sponsors: {', '.join(d.country for d in paper.sponsors)})"
            ),
            ref_id=paper.id,
        )

    print(" ======== Draft resolutions ======== ")
    promoted_count = 0
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
        promoted_count += 1
        session.log["resolutions"][resolution.id] = {
            "title": resolution.title,
            "sponsors": resolution.sponsors,
            "preambulatory_clauses": resolution.preambulatory_clauses,
            "operative_clauses": resolution.operative_clauses,
            "passed": resolution.passed,
        }
        log_activity(
            session,
            kind="resolution_drafted",
            summary=(
                f"{resolution.id} promoted from {paper.id}: "
                f"'{resolution.title}' (sponsors: {', '.join(resolution.sponsors)})"
            ),
            ref_id=resolution.id,
        )
        _gather_signatories(resolution, session)
        session.log["resolutions"][resolution.id]["signatories"] = list(
            resolution.signatories
        )

    session.log["unmoderated_caucuses"][caucus.id] = {
        "topic": caucus.topic,
        "proposer": caucus.proposer.country,
        "positions": caucus.positions,
        "blocs": {bid: [d.country for d in b["members"]]
                  for bid, b in caucus.blocs_brief.items()},
    }
    log_activity(
        session,
        kind="caucus_closed",
        summary=(
            f"{caucus.id} closed — papers: {len(working_papers)}, "
            f"resolutions promoted: {promoted_count}"
        ),
        ref_id=caucus.id,
    )
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
        log_activity(
            session,
            kind="speech",
            summary=(
                f"{delegate.country} spoke in GSL: "
                f"{speech[:140]}{'...' if len(speech) > 140 else ''}"
            ),
        )

    session.log["general_speakers_list"]["speeches"].update(past_speeches)
    session.log["general_speakers_list"]["current_queue"] = [
        d.country for d in session.general_speakers_list.queue
    ]
    save_state(session)

    print(" ===== Closing General Speakers List ======== ")
    

def process_amendment(amendment: Amendment, session: MUN):
    """Process a proposed amendment: friendly check → apply, else procedural vote.

    Friendly: all sponsors of the target resolution accept → applied automatically.
    Unfriendly: simple-majority procedural vote among the whole committee → applied if passes.
    """
    print(f" ======= Amendment {amendment.id} ======= ")
    print(amendment.present())

    # Friendly check: poll the sponsors
    sponsors = set(amendment.target_resolution.sponsors)
    sponsor_delegates = [
        d for d in session.committee if d.country in sponsors
    ]
    sponsor_responses = {}
    for delegate in sponsor_delegates:
        proposal = (
            f"You are a sponsor of {amendment.target_resolution.id}. "
            f"An amendment has been proposed:\n\n{amendment.present()}\n\n"
            f"Do you accept this as a friendly amendment (i.e. agree to it "
            f"without a vote)?"
        )
        sponsor_responses[delegate.country] = delegate.decide(proposal)

    all_sponsors_agree = (
        len(sponsor_delegates) > 0
        and all(v == "yes" for v in sponsor_responses.values())
    )

    if all_sponsors_agree:
        amendment.is_friendly = True
        amendment.apply()
        # Mirror the change into the session log so future briefs reflect it.
        session.log["resolutions"][amendment.target_resolution.id][
            "operative_clauses"
        ] = list(amendment.target_resolution.operative_clauses)
        log_activity(
            session,
            kind="amendment_applied",
            summary=(
                f"Friendly amendment {amendment.id} applied to "
                f"{amendment.target_resolution.id} "
                f"({amendment.action}, clause {amendment.clause_target_id})"
            ),
            ref_id=amendment.id,
        )
        save_state(session)
        return

    # Unfriendly: procedural vote
    amendment.is_friendly = False
    vote = Vote(
        id=session.next_id("V"),
        topic=f"Amendment {amendment.id} on {amendment.target_resolution.id}",
        type="procedural",
        supporting_document=amendment,
        delegates_refraining=[],
        delegates_in_favor=[],
        delegates_against=[],
    )
    for delegate in session.committee:
        delegate.vote(vote, session)

    passed = vote.evaluate()
    vote.log(session.log, session.time)
    log_activity(
        session,
        kind="vote",
        summary=(
            f"Vote {vote.id} on amendment {amendment.id}: "
            f"{vote.favor_count} for, {vote.against_count} against, "
            f"{vote.refraining_count} abstain — "
            f"{'PASSED' if passed else 'REJECTED'}"
        ),
        ref_id=vote.id,
    )
    if passed:
        amendment.apply()
        session.log["resolutions"][amendment.target_resolution.id][
            "operative_clauses"
        ] = list(amendment.target_resolution.operative_clauses)
        log_activity(
            session,
            kind="amendment_applied",
            summary=(
                f"Unfriendly amendment {amendment.id} applied to "
                f"{amendment.target_resolution.id} "
                f"({amendment.action}, clause {amendment.clause_target_id})"
            ),
            ref_id=amendment.id,
        )
    else:
        amendment.status = "rejected"
    save_state(session)


def _gather_signatories(resolution: DraftResolution, session: MUN):
    """At end of unmod, ask each non-sponsor delegate whether to sign."""
    sponsors = set(resolution.sponsors)
    for delegate in session.committee:
        if delegate.country in sponsors:
            continue
        proposal = (
            f"Resolution {resolution.id} '{resolution.title}' has been "
            f"drafted with sponsors {sorted(sponsors)}.\n\n"
            f"{resolution.present()}\n\n"
            f"As {delegate.country}, would you like to sign this resolution "
            f"as a signatory? Signing brings it to the floor without "
            f"committing to support it. Decide based on your national "
            f"interests and the current debate state."
        )
        decision = delegate.decide(proposal)
        if decision == "yes":
            resolution.signatories.append(delegate.country)
    log_activity(
        session,
        kind="signatories_collected",
        summary=(
            f"{resolution.id} signatories: "
            f"{', '.join(resolution.signatories) or '(none)'}"
        ),
        ref_id=resolution.id,
    )


def present_resolution(resolution: DraftResolution, session: MUN):
    """Sponsors present the resolution to the committee, then each non-sponsor
    delegate gives a short reaction. Reactions go into the activity log.
    """
    print(f" ======= Presentation of {resolution.id} ======= ")
    print(resolution.present())
    log_activity(
        session,
        kind="resolution_presented",
        summary=(
            f"{resolution.id} '{resolution.title}' presented to the committee "
            f"(sponsors: {', '.join(resolution.sponsors)})"
        ),
        ref_id=resolution.id,
    )

    sponsors = set(resolution.sponsors)
    for delegate in session.committee:
        if delegate.country in sponsors:
            continue
        reaction_prompt = (
            f"Draft resolution {resolution.id} has just been presented. "
            f"Give a short reaction (one or two sentences) explaining whether "
            f"your delegation supports it, opposes it, or wants amendments — "
            f"and the main reason."
        )
        speech = delegate.make_speech(
            topic_prompt=reaction_prompt,
            speech_duration=80,
            session=session,
        )
        print(f"{delegate.country}: {speech}")
        log_activity(
            session,
            kind="speech",
            summary=(
                f"{delegate.country} reacted to {resolution.id}: "
                f"{speech[:140]}{'...' if len(speech) > 140 else ''}"
            ),
            ref_id=resolution.id,
        )
    save_state(session)


def general_debate(session: MUN):

    print("==== Gathering delegate motion claims ====")
    motion_claims = {}
    for delegate in session.committee:
        delegate_claim = delegate.motion(session)
        motion_claims[delegate.country] = delegate_claim
    print(motion_claims)

    proposed = {}
    for country, raw in motion_claims.items():
        clean, reason = validate_motion(raw)
        if clean is None:
            if raw and raw.get("type") is not None:
                print(f"  dropping motion from {country}: {reason}")
            continue
        proposed[country] = clean

    valid_motions = chair_filter_motions(proposed) if proposed else {}

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
    log_activity(
        session,
        kind="motion_passed",
        summary=(
            f"Motion passed: '{motion['type']}' by {proposing_country} "
            f"(parameters: {motion.get('parameters')})"
        ),
    )

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
        resolution_id = motion["parameters"]["resolution_id"]
        resolution = next(
            (r for r in session.resolutions if r.id == resolution_id), None
        )
        if resolution is None:
            print(f"  resolution {resolution_id} not found, skipping presentation")
        else:
            present_resolution(resolution, session)

    elif motion["type"] == "vote_resolution":
        resolution_id = motion["parameters"]["resolution_id"]
        resolution = next(r for r in session.resolutions if r.id == resolution_id)
        vote_draft_resolution(resolution, session)

    elif motion["type"] == "amendment":
        params = motion["parameters"]
        resolution = next(
            (r for r in session.resolutions if r.id == params["resolution_id"]),
            None,
        )
        if resolution is None:
            print(f"  resolution {params['resolution_id']} not found, skipping amendment")
        else:
            amendment = Amendment(
                id=session.next_id("A"),
                target_resolution=resolution,
                proposer=proposer,
                action=params["action"],
                clause_target_id=int(params["clause_id"]),
                new_text=params.get("new_text", ""),
            )
            log_activity(
                session,
                kind="amendment_proposed",
                summary=(
                    f"Amendment {amendment.id} proposed by {proposer.country} "
                    f"on {resolution.id} ({amendment.action}, clause "
                    f"{amendment.clause_target_id})"
                ),
                ref_id=amendment.id,
            )
            process_amendment(amendment, session)

    elif motion["type"] == "end":
        print("======= End of the MUN session =======")
        session.state = "END"
        log_activity(session, kind="session_ended", summary="Session ended.")
        save_state(session)
