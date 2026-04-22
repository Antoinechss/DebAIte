# main simulation loop

from framework.mun import MUN
from committee import committee
from datetime import datetime

SESSION_TITLE = "Finding compromise for the ongoing war in Iran"

if __name__ == "main":
    print(" ======== MODEL UNITED NATIONS ======== ")

    # ---- Session Opening ----
    print(" Opening Session ")
    session = MUN(time=datetime.now(),
                  title=SESSION_TITLE,
                  committee=committee,
                  agenda=[],
                  log={})
    print("Session Opened")
    # -----------------------------

    