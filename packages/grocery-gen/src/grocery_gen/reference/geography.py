"""AU state/suburb/postcode reference data — a curated sample, not exhaustive.

Matches the rest of reference/ (brands.py, fresh_goods.py): hand-crafted,
deterministic pools rather than a name-generation library, so store and
customer geography stays realistic without pulling in Faker.
"""

from typing import Literal

State = Literal["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"]

# Approximate share of national population per state (ABS, rounded) — used to
# weight where stores and customers are generated so the mix looks realistic
# rather than uniform across 8 states.
STATE_POPULATION_WEIGHTS: dict[State, float] = {
    "NSW": 0.31,
    "VIC": 0.26,
    "QLD": 0.20,
    "WA": 0.11,
    "SA": 0.07,
    "TAS": 0.02,
    "ACT": 0.017,
    "NT": 0.013,
}

# (state, suburb, postcode) — real AU locations, a representative handful per
# state rather than a full postcode directory.
SUBURBS: list[tuple[State, str, str]] = [
    ("NSW", "Bondi Junction", "2022"),
    ("NSW", "Parramatta", "2150"),
    ("NSW", "Newcastle", "2300"),
    ("NSW", "Wollongong", "2500"),
    ("VIC", "Southbank", "3006"),
    ("VIC", "Box Hill", "3128"),
    ("VIC", "Geelong", "3220"),
    ("VIC", "Ballarat", "3350"),
    ("QLD", "Fortitude Valley", "4006"),
    ("QLD", "Toowoomba", "4350"),
    ("QLD", "Cairns", "4870"),
    ("WA", "Fremantle", "6160"),
    ("WA", "Joondalup", "6027"),
    ("SA", "Glenelg", "5045"),
    ("SA", "Mount Gambier", "5290"),
    ("TAS", "Hobart", "7000"),
    ("TAS", "Launceston", "7250"),
    ("ACT", "Belconnen", "2617"),
    ("NT", "Darwin", "0800"),
]

SUBURBS_BY_STATE: dict[State, list[tuple[str, str]]] = {}
for _state, _suburb, _postcode in SUBURBS:
    SUBURBS_BY_STATE.setdefault(_state, []).append((_suburb, _postcode))
