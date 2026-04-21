from framework.framework import DraftResolution, Vote, ModeratedCaucus, UnmoderatedCaucus
from framework.mun import MUN
from cognition.prompts import persona_context


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
    # Present caucus and gather voluntary candidates
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

    # Chair manually select speakers
    chair_selection = input(
        f"""Select less or equal than {caucus.num_speakers} IDs of 
        selected speakers for the Moderated Caucus, return a list of strings >"""
    )
    speakers = [delegate for delegate in session.committee if delegate.id in chair_selection]

    # Run and log speeches: no questions or back and forth yet 
    for delegate in speakers:
        speech_context_prompt = f"""
        You are taking part in the following ongoing Moderated Caucus: 
        {caucus.present}
        Delegates also speaking are {[delegate.country for delegate in speakers]}
        The speeches already are in the dict 'speeches'
        """
        speech = delegate.make_speech(topic_prompt=speech_context_prompt,
                                      speech_duration=caucus.speech_duration,
                                      session=session)
        caucus.speeches[str(delegate.country)] = speech
    
    # Log caucus
    session.log = session.log + caucus.present

    # Go back to general debate
    general_debate()

def process_unmoderated_caucus(caucus: UnmoderatedCaucus, session: MUN): 
    temp_delegate_memory = {delegate.id: "" for delegate in session.committee}

    # Bloc formation 
    # Positioning 
    # Negociation and drafting 
    # Consolidation
