from pathlib import Path
from framework.mun import MUN
from datetime import datetime
import json
import os


def create_initial_log(session: MUN):
    return {
            "meta": {
                "committee_name": "UN General Assembly",
                "topic": session.title,
                "state": session.state,
                "starting_time": datetime.now().isoformat(),
                "current_time": datetime.now().isoformat()
            },
            "committee": {
                "delegates": {
                    delegate.country: delegate.to_dict()
                    for delegate in session.committee
                    }
            },
            "general_speakers_list": {
                "current_queue": [],
                "speeches": {}
            },
            "moderated_caucuses": {
            },
            "unmoderated_caucuses": {
            },
            "resolutions": {
            },
            "activity": {
            },
            "votings": {
            }
        }


def init_log(session):
    os.makedirs("session_logs", exist_ok=True)
    log = create_initial_log(session)
    session.log = log
    with open("logs/log.json", "w") as f:
        json.dump(log, f, indent=4, ensure_ascii=False)


def save_state(session):
    print("Saving session state")
    with open("logs/log.json", "w") as f:
        json.dump(session.log, f, indent=4, ensure_ascii=False)
