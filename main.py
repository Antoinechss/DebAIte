"""Main simulation loop.

Pick a simulation pack from `simulations/` and run the debate loop.
"""

from datetime import datetime

from framework.mun import MUN
from framework.workflows import general_debate
from logs.log import init_log
from simulations.pack_1 import committee, topic


if __name__ == "__main__":
    print(" ======== MODEL UNITED NATIONS ======== ")

    print(" Opening Session ")
    session = MUN(
        time=datetime.now(),
        title=topic,
        committee=committee,
        agenda=[],
        log={},
    )
    print("Session Opened")
    print(session.intro())

    print("Creating session log")
    init_log(session)

    while session.state != "END":
        general_debate(session)
