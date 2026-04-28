from __future__ import annotations

import json
import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from framework.mun import MUN

LOG_PATH = "logs/log.json"
PASSED_RESOLUTIONS_PATH = "logs/passed_resolutions.json"
ACTIVITY_TAIL = 25  # recent events (besides pinned) to include in the brief
PINNED_KINDS = {
    "session_opened",
    "session_ended",
    "vote",
    "resolution_drafted",
    "resolution_passed",
    "resolution_presented",
}


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
    from logs.memory import init_memory

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    log = create_initial_log(session)
    session.log = log
    for delegate in session.committee:
        init_memory(delegate)
    log_activity(
        session,
        kind="session_opened",
        summary=(
            f"Session opened on '{session.title}' with delegations: "
            f"{', '.join(d.country for d in session.committee)}"
        ),
    )


def load_session(committee, agenda=None):
    """Rebuild an MUN session from logs/log.json — resume from where we left off.

    Per-delegate memory files and the passed-resolutions file persist
    independently and are not touched here (they already live on disk).

    Resume granularity is between general_debate iterations: any in-flight
    caucus or vote at the time of the previous crash is discarded. The
    session's structured state (resolutions, GSL queue, counters, state)
    is reconstructed from the log.
    """
    from datetime import datetime
    from framework.mun import MUN
    from framework.framework import DraftResolution

    if not os.path.exists(LOG_PATH):
        raise FileNotFoundError(
            f"No log at {LOG_PATH}; nothing to resume from."
        )
    with open(LOG_PATH) as f:
        log = json.load(f)

    title = log["meta"]["topic"]
    expected_committee = set(log["committee"]["delegates"].keys())
    actual_committee = {d.country for d in committee}
    if expected_committee != actual_committee:
        raise ValueError(
            "Committee mismatch — cannot resume.\n"
            f"  log expects: {sorted(expected_committee)}\n"
            f"  pack provides: {sorted(actual_committee)}"
        )

    state = log["meta"].get("state", "START")
    session = MUN(
        time=datetime.now(),
        title=title,
        committee=committee,
        agenda=agenda or [],
        log=log,
        state=state,
    )

    saved_counters = log["meta"].get("counters")
    if saved_counters:
        for prefix, value in saved_counters.items():
            if prefix in session._counters:
                session._counters[prefix] = value

    for rid, r in log.get("resolutions", {}).items():
        resolution = DraftResolution(id=rid)
        resolution.title = r.get("title", "")
        resolution.sponsors = list(r.get("sponsors", []))
        resolution.signatories = list(r.get("signatories", []))
        resolution.preambulatory_clauses = list(
            r.get("preambulatory_clauses", [])
        )
        resolution.operative_clauses = list(r.get("operative_clauses", []))
        resolution.passed = r.get("passed")
        session.resolutions.append(resolution)

    by_country = {d.country: d for d in committee}
    queue_countries = log.get("general_speakers_list", {}).get(
        "current_queue", []
    )
    for country in queue_countries:
        if country in by_country:
            session.general_speakers_list.queue.append(by_country[country])
    session.general_speakers_list.speeches = dict(
        log.get("general_speakers_list", {}).get("speeches", {})
    )

    log_activity(
        session,
        kind="session_resumed",
        summary=(
            f"Session resumed — {len(session.resolutions)} resolution(s) "
            f"on the table, GSL queue: "
            f"{[d.country for d in session.general_speakers_list.queue]}"
        ),
    )
    return session


def save_state(session):
    session.log["meta"]["current_time"] = datetime.now().isoformat()
    session.log["meta"]["state"] = session.state
    session.log["meta"]["counters"] = dict(session._counters)
    with open(LOG_PATH, "w") as f:
        json.dump(session.log, f, indent=4, ensure_ascii=False)


def append_passed_resolution(resolution) -> None:
    """Append a passed resolution to the durable passed-resolutions file.

    This file is the canonical record of what the committee actually adopted.
    Delegates can be shown its contents during debate and at session end.
    """
    os.makedirs(os.path.dirname(PASSED_RESOLUTIONS_PATH), exist_ok=True)
    if os.path.exists(PASSED_RESOLUTIONS_PATH):
        with open(PASSED_RESOLUTIONS_PATH) as f:
            data = json.load(f)
    else:
        data = {"resolutions": []}

    data["resolutions"].append({
        "id": resolution.id,
        "title": resolution.title,
        "sponsors": resolution.sponsors,
        "signatories": resolution.signatories,
        "preambulatory_clauses": resolution.preambulatory_clauses,
        "operative_clauses": resolution.operative_clauses,
        "adopted_at": datetime.now().isoformat(timespec="seconds"),
    })
    with open(PASSED_RESOLUTIONS_PATH, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def passed_resolutions_brief() -> str:
    """Render the passed-resolutions file as prose for prompts/end-of-session."""
    if not os.path.exists(PASSED_RESOLUTIONS_PATH):
        return "(no resolutions adopted yet)"
    with open(PASSED_RESOLUTIONS_PATH) as f:
        data = json.load(f)
    if not data.get("resolutions"):
        return "(no resolutions adopted yet)"
    lines = ["Adopted resolutions:"]
    for r in data["resolutions"]:
        lines.append(f"  - {r['id']} '{r['title']}' (sponsors: {', '.join(r['sponsors'])})")
        for c in r.get("operative_clauses", []):
            lines.append(f"      {c}")
    return "\n".join(lines)


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


def session_brief(session, focus_resolution_id: str | None = None) -> str:
    """Compact prose digest of the session for prompt injection.

    If focus_resolution_id is given, that resolution's full clauses are shown
    (used when delegates are about to vote on / present it).
    """
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

    if focus_resolution_id and focus_resolution_id in resolutions:
        r = resolutions[focus_resolution_id]
        lines.append("")
        lines.append(f"--- {focus_resolution_id} full text ---")
        lines.append(f"Title: {r.get('title', '')}")
        lines.append("Preambulatory clauses:")
        for c in r.get("preambulatory_clauses", []):
            lines.append(f"  {c}")
        lines.append("Operative clauses:")
        for c in r.get("operative_clauses", []):
            lines.append(f"  {c}")

    queue = log.get("general_speakers_list", {}).get("current_queue", [])
    if queue:
        lines.append("")
        lines.append(f"General Speakers List queue: {', '.join(queue)}")

    activity = log.get("activity", [])
    pinned = [e for e in activity if e["kind"] in PINNED_KINDS]
    other = [e for e in activity if e["kind"] not in PINNED_KINDS]

    if pinned:
        lines.append("")
        lines.append("Key milestones (chronological):")
        for ev in pinned:
            lines.append(f"  [{ev['t']}] {ev['summary']}")

    if other:
        lines.append("")
        lines.append(f"Recent activity (last {ACTIVITY_TAIL}):")
        for ev in other[-ACTIVITY_TAIL:]:
            lines.append(f"  [{ev['t']}] {ev['summary']}")

    if not activity:
        lines.append("")
        lines.append("Session history: (no activity yet)")

    return "\n".join(lines)
