from pathlib import Path


def create_session_logs():
    Path("session_logs").mkdir(exist_ok=True)