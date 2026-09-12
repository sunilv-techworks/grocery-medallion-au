"""AU calendar dimension — date spine with fiscal year/quarter and national
public holidays.

Generated directly, not extracted from an upstream source: unlike product
and category, there's no real-world "raw" system a date dimension comes
from, so it skips Bronze/Silver entirely — config.gold_metadata registers
it with sources=[] and gold_dim_calendar.Notebook builds it straight into
Gold in Spark, mirroring this same logic (see DR-009 in
docs/decision-register.md).

AU fiscal year runs 1 July - 30 June, named by the year it ends in (e.g.
1 Jul 2023 - 30 Jun 2024 is FY2024). Holidays are national-only via the
`holidays` package (no state subdivision, since there's no store dimension
yet to vary by state).
"""

from datetime import date, timedelta

import holidays
from pydantic import BaseModel, ConfigDict

MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]
DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


class CalendarRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    date_key: int
    year: int
    quarter: int
    month: int
    month_name: str
    day_of_month: int
    day_of_week: int
    day_name: str
    week_of_year: int
    is_weekend: bool
    fiscal_year: int
    fiscal_quarter: int
    is_public_holiday: bool
    holiday_name: str | None


def _fiscal_year(d: date) -> int:
    return d.year + 1 if d.month >= 7 else d.year


def _fiscal_quarter(d: date) -> int:
    # FY Q1 = Jul-Sep, Q2 = Oct-Dec, Q3 = Jan-Mar, Q4 = Apr-Jun
    return ((d.month - 7) % 12) // 3 + 1


def generate_calendar_dates(start: date, end: date) -> list[CalendarRow]:
    """One row per date in [start, end] inclusive."""
    if end < start:
        raise ValueError(f"end ({end}) must not be before start ({start})")

    au_holidays = holidays.country_holidays("AU", years=range(start.year, end.year + 1))

    rows: list[CalendarRow] = []
    current = start
    while current <= end:
        rows.append(
            CalendarRow(
                date=current,
                date_key=int(current.strftime("%Y%m%d")),
                year=current.year,
                quarter=(current.month - 1) // 3 + 1,
                month=current.month,
                month_name=MONTH_NAMES[current.month - 1],
                day_of_month=current.day,
                day_of_week=current.isoweekday(),
                day_name=DAY_NAMES[current.isoweekday() - 1],
                week_of_year=current.isocalendar()[1],
                is_weekend=current.isoweekday() >= 6,
                fiscal_year=_fiscal_year(current),
                fiscal_quarter=_fiscal_quarter(current),
                is_public_holiday=current in au_holidays,
                holiday_name=au_holidays.get(current),
            )
        )
        current += timedelta(days=1)

    return rows
