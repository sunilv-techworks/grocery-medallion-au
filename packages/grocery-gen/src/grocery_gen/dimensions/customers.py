"""Customer (loyalty) dimension generator for a fictional AU grocery retailer."""

from datetime import date, timedelta
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict

from grocery_gen.reference.geography import STATE_POPULATION_WEIGHTS, SUBURBS_BY_STATE, State

LoyaltyTier = Literal["Bronze", "Silver", "Gold", "Platinum"]

# Skews heavily toward Bronze, like most real loyalty programs.
LOYALTY_TIER_WEIGHTS: dict[LoyaltyTier, float] = {
    "Bronze": 0.60,
    "Silver": 0.25,
    "Gold": 0.12,
    "Platinum": 0.03,
}

FIRST_NAMES: list[str] = [
    "Olivia",
    "Charlotte",
    "Ava",
    "Amelia",
    "Isla",
    "Mia",
    "Grace",
    "Zoe",
    "Chloe",
    "Ruby",
    "Sophie",
    "Ella",
    "Jack",
    "William",
    "Noah",
    "Oliver",
    "Lucas",
    "Henry",
    "Thomas",
    "James",
    "Ethan",
    "Liam",
    "Cooper",
    "Hunter",
    "Priya",
    "Wei",
    "Fatima",
    "Mohammed",
    "Nguyen",
    "Aisha",
]
LAST_NAMES: list[str] = [
    "Smith",
    "Jones",
    "Williams",
    "Brown",
    "Wilson",
    "Taylor",
    "Nguyen",
    "Kelly",
    "Ryan",
    "O'Brien",
    "Chen",
    "Singh",
    "Kumar",
    "Patel",
    "Lee",
    "Walker",
    "Anderson",
    "Thompson",
    "White",
    "Martin",
    "Clarke",
    "Ahmed",
]

# Fixed anchor for join_date so generation stays deterministic across runs.
_REFERENCE_DATE = date(2026, 1, 1)
_MAX_TENURE_DAYS = 365 * 8

# A deliberately non-existent store ID: an orphan preferred_store_id for
# Gold's referential-integrity check to have something real to catch (see
# gold_dim_customer.Notebook).
_ORPHAN_STORE_ID = "STR-9999"


class CustomerRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    customer_id: str
    first_name: str
    last_name: str
    loyalty_tier: LoyaltyTier
    join_date: date
    home_state: State
    home_suburb: str
    home_postcode: str
    preferred_store_id: str | None
    marketing_opt_in: bool


def generate_customers(n: int = 5000, seed: int = 42, num_stores: int = 150) -> list[CustomerRow]:
    """Deterministic, seeded customer list.

    preferred_store_id is drawn from the same STR-#### ID space
    generate_stores produces (1..num_stores), so it resolves for most
    customers — plus a small deliberate share of None (no preference) and
    a fixed invalid ID (a genuine orphan FK) for Gold's referential-
    integrity check to catch.
    """
    rng = np.random.default_rng(seed)

    states = list(STATE_POPULATION_WEIGHTS)
    state_p = [STATE_POPULATION_WEIGHTS[s] for s in states]
    tiers = list(LOYALTY_TIER_WEIGHTS)
    tier_p = [LOYALTY_TIER_WEIGHTS[t] for t in tiers]

    rows: list[CustomerRow] = []
    for i in range(n):
        home_state: State = rng.choice(states, p=state_p)
        suburb, postcode = SUBURBS_BY_STATE[home_state][
            rng.integers(0, len(SUBURBS_BY_STATE[home_state]))
        ]

        store_roll = rng.random()
        preferred_store_id: str | None
        if store_roll < 0.85:
            preferred_store_id = f"STR-{rng.integers(1, num_stores + 1):04d}"
        elif store_roll < 0.95:
            preferred_store_id = None
        else:
            preferred_store_id = _ORPHAN_STORE_ID

        rows.append(
            CustomerRow(
                customer_id=f"CUST-{i + 1:06d}",
                first_name=FIRST_NAMES[rng.integers(0, len(FIRST_NAMES))],
                last_name=LAST_NAMES[rng.integers(0, len(LAST_NAMES))],
                loyalty_tier=rng.choice(tiers, p=tier_p),
                join_date=_REFERENCE_DATE - timedelta(days=int(rng.integers(0, _MAX_TENURE_DAYS))),
                home_state=home_state,
                home_suburb=suburb,
                home_postcode=postcode,
                preferred_store_id=preferred_store_id,
                marketing_opt_in=rng.random() < 0.55,
            )
        )

    return rows


class RawCustomerRow(BaseModel):
    """Source-shaped customer extract, as a loyalty-program feed would hand
    it over — different column names, plus the same deliberate, deterministic
    quality issues (missing keys, duplicate rows) as to_raw_product_rows.
    """

    model_config = ConfigDict(frozen=True)

    member_id: str | None
    fname: str
    lname: str
    tier_code: str
    signup_dt: date
    state_code: State
    suburb_name: str
    postal_code: str
    home_store_code: str | None
    opt_in_flag: bool


def _to_raw_row(row: CustomerRow) -> RawCustomerRow:
    return RawCustomerRow(
        member_id=row.customer_id,
        fname=row.first_name,
        lname=row.last_name,
        tier_code=row.loyalty_tier,
        signup_dt=row.join_date,
        state_code=row.home_state,
        suburb_name=row.home_suburb,
        postal_code=row.home_postcode,
        home_store_code=row.preferred_store_id,
        opt_in_flag=row.marketing_opt_in,
    )


def to_raw_customer_rows(
    rows: list[CustomerRow], seed: int = 42, messy_rate: float = 0.01
) -> list[RawCustomerRow]:
    """Rename to source-shaped columns and inject deterministic quality
    issues: a null key on ~messy_rate of rows, and an equal share of exact
    duplicate rows appended. Mirrors to_raw_product_rows exactly.
    """
    rng = np.random.default_rng(seed * 17 + 7)
    raw_rows = [_to_raw_row(r) for r in rows]

    n = len(raw_rows)
    n_messy = max(1, int(n * messy_rate))

    null_key_idx = set(rng.choice(n, size=n_messy, replace=False).tolist())
    for idx in null_key_idx:
        raw_rows[idx] = raw_rows[idx].model_copy(update={"member_id": None})

    dup_source_idx = rng.choice(n, size=n_messy, replace=False).tolist()
    duplicates = [raw_rows[idx] for idx in dup_source_idx]

    return raw_rows + duplicates
