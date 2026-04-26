from __future__ import annotations

import json
import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from framework.mun import MUN

LOG_PATH = "logs/log.json"
ACTIVITY_TAIL = 25  # how many recent events to include in the brief


def create_initial_log(session: MUN):
    return {
        "meta": {
            "committee_name": "UN General Assembly",
            "topic": session.title,
            "state": session.state,
            "starting_time": datetime.now().isoformat(),
            "current_time": datetime.now().isoformat(),
        },
        "committee": {
            "delegates": {
                delegate.country: delegate.to_dict()
                for delegate in session.committee
            }
        },
        "general_speakers_list": {
            "current_queue": [],
            "speeches": {},
        },
        "moderated_caucuses": {},
        "unmoderated_caucuses": {},
        "resolutions": {},
        "activity": [],
        "votings": {},
    }


def init_log(session):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    log = create_initial_log(session)
    session.log = log
    log_activity(
        session,
        kind="session_opened",
        summary=(
            f"Session opened on '{session.title}' with delegations: "
            f"{', '.join(d.country for d in session.committee)}"
        ),
    )


def save_state(session):
    session.log["meta"]["current_time"] = datetime.now().isoformat()
    with open(LOG_PATH, "w") as f:
        json.dump(session.log, f, indent=4, ensure_ascii=False)


def log_activity(session, kind: str, summary: str, ref_id: str | None = None):
    """Append a chronological event to the session activity log and persist."""
    event = {
        "t": datetime.now().isoformat(timespec="seconds"),
        "kind": kind,
        "summary": summary,
    }
    if ref_id is not None:
        event["ref_id"] = ref_id
    session.log["activity"].append(event)
    save_state(session)


def _resolution_status(passed):
    if passed is True:
        return "PASSED"
    if passed is False:
        return "REJECTED"
    return "pending"


def session_brief(session) -> str:
    """Compact prose digest of the session for prompt injection."""
    log = session.log
    lines = []

    lines.append(f"Topic: {log['meta']['topic']}")
    lines.append(
        f"Committee: {', '.join(log['committee']['delegates'].keys())}"
    )

    resolutions = log.get("resolutions", {})
    if resolutions:
        lines.append("")
        lines.append("Draft resolutions on the table:")
        for rid, r in resolutions.items():
            sponsors = ", ".join(r.get("sponsors", []))
            lines.append(
                f"  - {rid} [{_resolution_status(r.get('passed'))}] "
                f"{r.get('title', '')} — sponsors: {sponsors}"
            )

    queue = log.get("general_speakers_list", {}).get("current_queue", [])
    if queue:
        lines.append("")
        lines.append(f"General Speakers List queue: {', '.join(queue)}")

    activity = log.get("activity", [])
    if activity:
        lines.append("")
        lines.append("Session history (most recent last):")
        for ev in activity[-ACTIVITY_TAIL:]:
            lines.append(f"  [{ev['t']}] {ev['summary']}")
    else:
        lines.append("")
        lines.append("Session history: (no activity yet)")

    return "\n".join(lines)
