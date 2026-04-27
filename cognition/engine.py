from openai import OpenAI

from cognition.parsing import safe_json_loads, LLMParseError

MODEL = "gpt-4o-mini"
MAX_TOKENS = 400
PARSE_RETRIES = 1

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def _call_llm(prompt: str) -> str:
    response = _get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=MAX_TOKENS,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def think(prompt: str) -> dict:
    """Call the LLM and return a parsed JSON dict.

    On parse failure, retries up to PARSE_RETRIES times with a corrective
    nudge appended to the prompt. Raises LLMParseError if all attempts fail.
    """
    last_err: Exception | None = None
    current_prompt = prompt
    for attempt in range(PARSE_RETRIES + 1):
        raw = _call_llm(current_prompt)
        try:
            return safe_json_loads(raw)
        except LLMParseError as e:
            last_err = e
            current_prompt = (
                prompt
                + "\n\nYour previous response could not be parsed as JSON. "
                "Return ONLY a single valid JSON object, nothing else."
            )
    raise LLMParseError(
        f"LLM produced unparseable output after {PARSE_RETRIES + 1} attempts: {last_err}"
    )
