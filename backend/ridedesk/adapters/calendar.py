import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class CalendarProvider(Protocol):
    """Availability per calendar. Each business has its own calendar id."""

    def is_free(self, calendar_id: str, start: datetime, end: datetime) -> bool:
        """True when nothing overlaps [start, end). Raises ValueError if end <= start."""
        ...

    def add_event(self, calendar_id: str, start: datetime, end: datetime, title: str) -> str:
        """Block the time and return the event id."""
        ...

    def remove_event(self, calendar_id: str, event_id: str) -> None: ...


@dataclass(frozen=True)
class _Event:
    start: datetime
    end: datetime
    title: str


def _check_window(start: datetime, end: datetime) -> None:
    if end <= start:
        raise ValueError("end must be after start")


class MockCalendar:
    """In-memory calendars, kept apart by calendar id."""

    def __init__(self) -> None:
        self.calendars: defaultdict[str, dict[str, _Event]] = defaultdict(dict)

    def is_free(self, calendar_id: str, start: datetime, end: datetime) -> bool:
        _check_window(start, end)
        events = self.calendars[calendar_id].values()
        return all(e.end <= start or e.start >= end for e in events)

    def add_event(self, calendar_id: str, start: datetime, end: datetime, title: str) -> str:
        _check_window(start, end)
        event_id = uuid.uuid4().hex
        self.calendars[calendar_id][event_id] = _Event(start, end, title)
        return event_id

    def remove_event(self, calendar_id: str, event_id: str) -> None:
        self.calendars[calendar_id].pop(event_id, None)
