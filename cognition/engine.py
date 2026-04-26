import json

from openai import OpenAI

MODEL = "gpt-5.3"

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def think(prompt):
    response = _get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
