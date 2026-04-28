"""Main simulation loop.

Pick a simulation pack from `simulations/` and run the debate loop. If a
prior `logs/log.json` exists, the program offers to resume from where the
last session left off.
"""

import os
from datetime import datetime

from framework.mun import MUN
from framework.workflows import general_debate
from logs.log import init_log, load_session, LOG_PATH
from simulations.pack_1 import committee, topic


def _start_or_resume():
    if os.path.exists(LOG_PATH):
        choice = input(
            f"\nExisting session log found at {LOG_PATH}.\n"
            "[r] Resume from there\n"
            "[n] Start a new session (overwrites the log)\n"
            "Choice (r/n): "
        ).strip().lower()
        if choice == "r":
            session = load_session(committee)
            print(
                f"\nResumed at state={session.state} | "
                f"counters={session._counters} | "
                f"resolutions={[r.id for r in session.resolutions]}"
            )
            return session

    session = MUN(
        time=datetime.now(),
        title=topic,
        committee=committee,
        agenda=[],
        log={},
    )
    init_log(session)
    return session


if __name__ == "__main__":
    print(" ======== MODEL UNITED NATIONS ======== ")

    session = _start_or_resume()
    print(session.intro())

    while session.state != "END":
        general_debate(session)
