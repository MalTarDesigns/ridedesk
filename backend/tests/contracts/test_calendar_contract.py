from datetime import UTC, datetime, timedelta

import pytest

from ridedesk.adapters.calendar import CalendarProvider

NOON = datetime(2026, 12, 4, 12, 0, tzinfo=UTC)
HOUR = timedelta(hours=1)
CAL = "business-a"


def test_an_empty_calendar_is_free(calendar: CalendarProvider) -> None:
    assert calendar.is_free(CAL, NOON, NOON + HOUR)


def test_an_event_blocks_overlapping_time_only(calendar: CalendarProvider) -> None:
    event_id = calendar.add_event(CAL, NOON, NOON + HOUR, "Ride")

    try:
        assert not calendar.is_free(CAL, NOON + HOUR / 2, NOON + 2 * HOUR)
        assert calendar.is_free(CAL, NOON + HOUR, NOON + 2 * HOUR)  # back to back is fine
        assert calendar.is_free(CAL, NOON - HOUR, NOON)
    finally:
        calendar.remove_event(CAL, event_id)


def test_one_calendar_does_not_block_another(calendar: CalendarProvider) -> None:
    event_id = calendar.add_event(CAL, NOON, NOON + HOUR, "Ride")

    try:
        assert calendar.is_free("business-b", NOON, NOON + HOUR)
    finally:
        calendar.remove_event(CAL, event_id)


def test_removing_an_event_frees_its_time(calendar: CalendarProvider) -> None:
    event_id = calendar.add_event(CAL, NOON, NOON + HOUR, "Ride")
    calendar.remove_event(CAL, event_id)

    assert calendar.is_free(CAL, NOON, NOON + HOUR)


def test_a_window_that_ends_before_it_starts_is_rejected(calendar: CalendarProvider) -> None:
    with pytest.raises(ValueError):
        calendar.is_free(CAL, NOON, NOON - HOUR)
