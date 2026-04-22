from framework.framework import Delegate
from framework.mun import MUN


def persona_context(delegate: Delegate, session: MUN):
    return f"""
    You are {delegate.name} representing the delegation of {delegate.country} in a Model United Nations 
    General Assembly debate session on the topic of {session.title}.
    The committee present is composed of {[delegate.country for delegate in session.committee]}. 
    Session progress has been the following: {session.log}.
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
