from __future__ import annotations

from typing import TYPE_CHECKING

from logs.log import session_brief

if TYPE_CHECKING:
    from framework.framework import Delegate
    from framework.mun import MUN


def persona_context(delegate: Delegate, session: MUN):
    return f"""
    You are {delegate.name} representing the delegation of {delegate.country} in a Model United Nations
    General Assembly debate session on the topic of {session.title}.
    Your delegation's standing brief: {delegate.brief}
    The committee present is composed of {[d.country for d in session.committee]}.

    Current session state:
    {session_brief(session)}
    """


generation_rules = """
            Rules:
            - Do NOT include any explanation
            - Do NOT output your reasoning
            - Do NOT include any extra text
            - Do NOT include formatting or markdown
            - Output ONLY valid JSON

            If your output does not follow this format, your reponse will be discarded.
            """

motion_submission_rules = """
Follow EXACTLY this format for your output:

- No motion to propose: set "type" and "parameters" to None
- Motion for Unmoderated Caucus:
    {"type": "unmod", "parameters": {"topic": your topic (str)}}
- Motion for Moderated Caucus:
    {"type": "mod", "parameters": {"topic": your topic (str),
                                   "num_speakers": number of speakers (int),
                                   "speech_duration": number of max words per speech (int)}}
- Motion to go through General Speakers List:
    {"type": "general_speakers_list", "parameters": None}
- Motion to present a draft resolution:
    {"type": "present_resolution", "parameters": {"resolution_id": id of the resolution}}
- Motion to vote on resolution:
    {"type": "vote_resolution", "parameters": {"resolution_id": id of the resolution}}
- Motion to end the session:
    {"type": "end", "parameters": None}
"""
