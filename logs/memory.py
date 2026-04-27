"""Per-delegate private memory.

One JSON file per delegate at `logs/memory/{delegate_id}.json`.
Each delegate's memory holds:
  - brief: the static delegation brief (also on the Delegate object)
  - bloc_history: list of bloc deliberations the delegate took part in
  - private_notes: free-form private notes the delegate may accumulate

This layer enforces information asymmetry: only delegates who participated
in a bloc get that bloc's deliberations. The public session_brief never
contains private memory contents.
"""

from __future__ import annotations

import json
import os

MEMORY_DIR = "logs/memory"


def _path(delegate_id: str) -> str:
    return os.path.join(MEMORY_DIR, f"{delegate_id}.json")


def init_memory(delegate) -> None:
    """Create the delegate's memory file seeded from their static brief."""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    payload = {
        "id": delegate.id,
        "country": delegate.country,
        "brief": delegate.brief,
        "bloc_history": [],
        "private_notes": [],
    }
    with open(_path(delegate.id), "w") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)


def load_memory(delegate_id: str) -> dict:
    with open(_path(delegate_id)) as f:
        return json.load(f)


def save_memory(delegate_id: str, payload: dict) -> None:
    with open(_path(delegate_id), "w") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)


def append_bloc_history(delegate_id: str, entry: dict) -> None:
    """Append a bloc-deliberation record to the delegate's memory."""
    mem = load_memory(delegate_id)
    mem["bloc_history"].append(entry)
    save_memory(delegate_id, mem)


def append_private_note(delegate_id: str, note: str) -> None:
    mem = load_memory(delegate_id)
    mem["private_notes"].append(note)
    save_memory(delegate_id, mem)


def memory_brief(delegate_id: str) -> str:
    """Render the delegate's private memory as prose for prompt injection."""
    try:
        mem = load_memory(delegate_id)
    except FileNotFoundError:
        return "(no private memory yet)"

    lines = []

    if mem.get("bloc_history"):
        lines.append("Your bloc deliberation history (private):")
        for entry in mem["bloc_history"]:
            members = ", ".join(entry.get("members", []))
            lines.append(
                f"  - {entry.get('caucus_id')} / bloc {entry.get('bloc_id')} "
                f"with {members}"
            )
            for idea in entry.get("ideas", []):
                lines.append(f"      idea: {idea}")
            for ag in entry.get("agreements", []):
                lines.append(f"      agreement: {ag}")
            for cf in entry.get("conflicts", []):
                lines.append(f"      conflict: {cf}")

    if mem.get("private_notes"):
        if lines:
            lines.append("")
        lines.append("Your private notes:")
        for n in mem["private_notes"]:
            lines.append(f"  - {n}")

    if not lines:
        return "(no private memory yet)"
    return "\n".join(lines)
