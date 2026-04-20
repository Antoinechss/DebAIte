# main simulation loop

from framework.mun import MUN
from committee import committee

if __name__ == "main":
    session = MUN(committee, "start", True, [])
    while True:
        if session.requires_chair_action:
            pass  # TBC : wait for chair action
        else:
            pass
