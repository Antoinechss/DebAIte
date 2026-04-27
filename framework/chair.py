"""Helpers for the human chair's interactive prompts.

The chair drives three decisions today:
  - filtering which proposed motions are valid (in `general_debate`)
  - selecting speakers for a moderated caucus
  - forming blocs at the start of an unmoderated caucus

Each helper retries on bad input so a typo doesn't blow up the run.
"""

from __future__ import annotations

import json


def _hr(width: int = 70) -> str:
    return "-" * width


def banner(title: str) -> None:
    print()
    print(_hr())
    print(f" CHAIR ACTION REQUIRED — {title}")
    print(_hr())


def chair_filter_motions(proposed: dict) -> dict:
    """Ask the chair which proposed motions to keep.

    `proposed` is {country: motion_dict}. Empty input means keep all.
    Retries until input parses; user can type `?` for help.
    """
    banner("Filter motions on the floor")
    print("Proposed motions:")
    for country, motion in proposed.items():
        params = motion.get("parameters")
        print(f"  - {country}: {motion['type']}  params={params}")

    while True:
        raw = input(
            "\nEnter comma-separated countries to KEEP (empty = keep all, "
            "'?' for help):\n>>> "
        ).strip()
        if raw == "?":
            print(
                "Type the country names exactly as listed above, separated "
                "by commas. Leave empty to accept every proposed motion."
            )
            continue
        if raw == "":
            return dict(proposed)
        keep_set = {c.strip() for c in raw.split(",") if c.strip()}
        unknown = keep_set - set(proposed.keys())
        if unknown:
            print(f"  unknown countries: {sorted(unknown)} — try again.")
            continue
        return {c: m for c, m in proposed.items() if c in keep_set}


def chair_select_speakers(candidates: list[str], max_count: int) -> list[str]:
    """Ask the chair to pick up to `max_count` speaker IDs from `candidates`."""
    banner("Select speakers for the moderated caucus")
    print(f"Candidates who volunteered: {candidates}")
    print(f"You may select up to {max_count} of them.")

    while True:
        raw = input(
            "\nEnter comma-separated speaker IDs (in speaking order):\n>>> "
        ).strip()
        if raw == "":
            print("  selection cannot be empty — try again.")
            continue
        ids = [s.strip() for s in raw.split(",") if s.strip()]
        unknown = [i for i in ids if i not in candidates]
        if unknown:
            print(f"  unknown IDs: {unknown} — try again.")
            continue
        if len(ids) > max_count:
            print(f"  too many ({len(ids)}>{max_count}) — try again.")
            continue
        return ids


def chair_form_blocs(
    bloc_requests: dict, all_countries: list[str]
) -> dict:
    """Ask the chair to form the blocs as a JSON dict.

    `bloc_requests` is {country: [requested bloc-mates]} from delegates.
    Returns {bloc_id: [country, ...]}.
    """
    banner("Form blocs for the unmoderated caucus")
    print("Delegates' bloc-mate requests:")
    for country, wishlist in bloc_requests.items():
        print(f"  - {country} wants: {wishlist}")
    print(f"\nAvailable countries: {all_countries}")
    print('Format: JSON object, e.g. {"B1": ["USA","France"], "B2": ["Iran"]}')

    while True:
        raw = input("\n>>> ").strip()
        if not raw:
            print("  empty input — try again.")
            continue
        try:
            blocs = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"  invalid JSON ({e}) — try again.")
            continue
        if not isinstance(blocs, dict) or not all(
            isinstance(v, list) for v in blocs.values()
        ):
            print("  expected an object whose values are lists — try again.")
            continue
        flat = [c for members in blocs.values() for c in members]
        unknown = [c for c in flat if c not in all_countries]
        if unknown:
            print(f"  unknown countries: {unknown} — try again.")
            continue
        if len(flat) != len(set(flat)):
            print("  a country appears in multiple blocs — try again.")
            continue
        missing = [c for c in all_countries if c not in flat]
        if missing:
            print(f"  warning: {missing} is/are not in any bloc — confirm? (y/N)")
            confirm = input(">>> ").strip().lower()
            if confirm != "y":
                continue
        return blocs
