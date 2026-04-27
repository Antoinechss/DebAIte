"""Safe JSON parsing for LLM responses.

The LLM is asked to return strict JSON, but it can still drift: stray text
around the JSON, single quotes, trailing commas, code-fenced blocks. This
module wraps `json.loads` with a few forgiving fallbacks and a single retry
hook for callers.
"""

from __future__ import annotations

import json
import re
from typing import Any

JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class LLMParseError(ValueError):
    """Raised when an LLM response cannot be parsed as JSON after fallbacks."""


def _strip_code_fence(text: str) -> str:
    m = JSON_FENCE.search(text)
    return m.group(1) if m else text


def _extract_json_object(text: str) -> str | None:
    """Return the substring from the first `{` to its matching `}`, or None."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def safe_json_loads(raw: str) -> dict[str, Any]:
    """Parse `raw` as JSON, with forgiving fallbacks.

    Tries, in order:
    1. plain json.loads
    2. strip a ```json ... ``` fence
    3. extract the first balanced {...} substring

    Raises LLMParseError if all attempts fail.
    """
    if not isinstance(raw, str):
        raise LLMParseError(f"expected str, got {type(raw).__name__}")

    candidates = [raw, _strip_code_fence(raw)]
    extracted = _extract_json_object(raw)
    if extracted is not None:
        candidates.append(extracted)

    last_err: Exception | None = None
    for c in candidates:
        try:
            value = json.loads(c)
        except json.JSONDecodeError as e:
            last_err = e
            continue
        if not isinstance(value, dict):
            last_err = LLMParseError(f"expected JSON object, got {type(value).__name__}")
            continue
        return value

    raise LLMParseError(f"could not parse LLM response as JSON: {last_err}")
