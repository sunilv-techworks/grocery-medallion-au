"""Tests for dim_calendar generation."""

from datetime import date

import pytest

from grocery_gen.dimensions.calendar import generate_calendar_dates


def test_covers_every_date_in_range_inclusive() -> None:
    rows = generate_calendar_dates(date(2024, 1, 1), date(2024, 1, 5))
    assert [r.date for r in rows] == [
        date(2024, 1, 1),
        date(2024, 1, 2),
        date(2024, 1, 3),
        date(2024, 1, 4),
        date(2024, 1, 5),
    ]


def test_single_day_range() -> None:
    rows = generate_calendar_dates(date(2024, 6, 30), date(2024, 6, 30))
    assert len(rows) == 1


def test_end_before_start_raises() -> None:
    with pytest.raises(ValueError):
        generate_calendar_dates(date(2024, 1, 5), date(2024, 1, 1))


def test_date_key_format() -> None:
    rows = generate_calendar_dates(date(2024, 3, 7), date(2024, 3, 7))
    assert rows[0].date_key == 20240307


def test_weekend_flag() -> None:
    rows = {r.date: r for r in generate_calendar_dates(date(2024, 1, 1), date(2024, 1, 7))}
    assert rows[date(2024, 1, 6)].is_weekend is True  # Saturday
    assert rows[date(2024, 1, 7)].is_weekend is True  # Sunday
    assert rows[date(2024, 1, 5)].is_weekend is False  # Friday


def test_fiscal_year_boundary_at_30_june() -> None:
    rows = {r.date: r for r in generate_calendar_dates(date(2024, 6, 29), date(2024, 7, 2))}
    assert rows[date(2024, 6, 30)].fiscal_year == 2024
    assert rows[date(2024, 6, 30)].fiscal_quarter == 4
    assert rows[date(2024, 7, 1)].fiscal_year == 2025
    assert rows[date(2024, 7, 1)].fiscal_quarter == 1


def test_known_public_holidays_flagged() -> None:
    rows = {r.date: r for r in generate_calendar_dates(date(2024, 1, 1), date(2024, 12, 31))}
    assert rows[date(2024, 1, 1)].is_public_holiday is True
    assert rows[date(2024, 1, 1)].holiday_name == "New Year's Day"
    assert rows[date(2024, 12, 25)].is_public_holiday is True
    assert rows[date(2024, 1, 2)].is_public_holiday is False
    assert rows[date(2024, 1, 2)].holiday_name is None


def test_reproducible() -> None:
    a = generate_calendar_dates(date(2024, 1, 1), date(2024, 12, 31))
    b = generate_calendar_dates(date(2024, 1, 1), date(2024, 12, 31))
    assert a == b


def test_no_duplicate_dates() -> None:
    rows = generate_calendar_dates(date(2024, 1, 1), date(2026, 12, 31))
    dates = [r.date for r in rows]
    assert len(dates) == len(set(dates))
