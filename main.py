# main simulation loop

from framework.mun import MUN
from committee import committee
from datetime import datetime
from framework.workflows import general_debate
from logs.log import init_log

SESSION_TITLE = "Finding compromise for the ongoing war in Iran"

if __name__ == "__main__":
    print(" ======== MODEL UNITED NATIONS ======== ")

    # ---- Session Opening ----
    print(" Opening Session ")
    session = MUN(time=datetime.now(),
                  title=SESSION_TITLE,
                  committee=committee,
                  agenda=[],
                  log={})
    print("Session Opened")
    print(session.intro())
    # -----------------------------

    print("Creating session log")
    
    init_log(session)

    while session.state != "END":
        general_debate(session)

