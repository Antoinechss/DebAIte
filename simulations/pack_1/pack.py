"""Pack 1 — Preemptive Action and the Iran Crisis.

A 15-delegation simulation evaluating the legality and consequences of
preemptive military action against sovereign states, set in the context of an
escalating conflict involving the Islamic Republic of Iran.

Each delegate's brief is loaded from `briefs/{country}.md` so the briefs can
be edited independently of the code.
"""

from pathlib import Path

from framework.framework import Delegate

PACK_DIR = Path(__file__).parent
BRIEFS_DIR = PACK_DIR / "briefs"

TOPIC = (
    "Evaluating the legality and consequences of preemptive military action "
    "against sovereign states in the context of escalating conflict involving "
    "the Islamic Republic of Iran."
)


def _brief(filename: str) -> str:
    return (BRIEFS_DIR / filename).read_text()


# (id, name, country, brief_filename)
_DELEGATE_SPECS = [
    ("USA", "Sarah Whitman",      "USA",            "USA.md"),
    ("IRN", "Amir Hosseini",      "Iran",           "Iran.md"),
    ("ISR", "Daniel Regev",       "Israel",         "Israel.md"),
    ("RUS", "Sergei Volkov",      "Russia",         "Russia.md"),
    ("CHN", "Liu Wen",            "China",          "China.md"),
    ("FRA", "Claire Dubois",      "France",         "France.md"),
    ("GBR", "James Carter",       "United Kingdom", "United_Kingdom.md"),
    ("SAU", "Faisal Al Saud",     "Saudi Arabia",   "Saudi_Arabia.md"),
    ("ARE", "Noura Al Mazrouei",  "UAE",            "UAE.md"),
    ("TUR", "Mehmet Kaya",        "Turkey",         "Turkey.md"),
    ("IND", "Rajiv Mehta",        "India",          "India.md"),
    ("BRA", "Ana Ribeiro",        "Brazil",         "Brazil.md"),
    ("DEU", "Lukas Schneider",    "Germany",        "Germany.md"),
    ("ZAF", "Thandi Nkosi",       "South Africa",   "South_Africa.md"),
    ("JPN", "Hiroshi Tanaka",     "Japan",          "Japan.md"),
]

COMMITTEE = [
    Delegate(id_, name, country, _brief(brief_file))
    for id_, name, country, brief_file in _DELEGATE_SPECS
]
