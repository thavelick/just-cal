"""Event model for calendar events."""

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any

from icalendar import Calendar
from icalendar import Event as ICalEvent


def _get_optional_field(component: Any, field_name: str) -> str | None:
    """Extract an optional string field from an iCalendar component."""
    value = component.get(field_name)
    return str(value) if value else None


def _to_datetime(dt: date | datetime) -> datetime:
    """Convert a date or datetime to datetime, using midnight for dates."""
    if isinstance(dt, datetime):
        return dt
    return datetime.combine(dt, time.min)


@dataclass
class Event:
    """Represents a calendar event."""

    uid: str
    title: str
    start: datetime
    end: datetime
    description: str | None = None
    location: str | None = None
    recurrence: str | None = None  # RRULE string
    all_day: bool = False
    _caldav_object: Any = field(default=None, init=False, repr=False)

    def to_ical(self) -> str:
        """Convert to iCalendar format using icalendar library.

        Returns:
            str: iCalendar formatted string
        """
        cal = Calendar()
        cal.add("prodid", "-//justcal//EN")
        cal.add("version", "2.0")

        event = ICalEvent()
        event.add("uid", self.uid)
        event.add("summary", self.title)

        # For all-day events, use date objects instead of datetime
        if self.all_day:
            event.add("dtstart", self.start.date())
            event.add("dtend", self.end.date())
        else:
            event.add("dtstart", self.start)
            event.add("dtend", self.end)

        if self.description:
            event.add("description", self.description)

        if self.location:
            event.add("location", self.location)

        if self.recurrence:
            event.add("rrule", self.recurrence)

        cal.add_component(event)
        return cal.to_ical().decode("utf-8")

    @classmethod
    def from_ical(cls, ical_data: str) -> "Event":
        """Parse from iCalendar format.

        Args:
            ical_data: iCalendar formatted string

        Returns:
            Event: Parsed event object
        """
        cal = Calendar.from_ical(ical_data)

        event_component = next(
            (c for c in cal.walk() if c.name == "VEVENT"),
            None,
        )
        if not event_component:
            raise ValueError("No VEVENT found in iCalendar data")

        dtstart = event_component.get("dtstart")
        dtend = event_component.get("dtend")

        if not dtstart:
            raise ValueError("Event missing required DTSTART field")
        if not dtend:
            raise ValueError("Event missing required DTEND field")

        start = dtstart.dt
        end = dtend.dt

        return cls(
            uid=str(event_component.get("uid")),
            title=str(event_component.get("summary", "")),
            start=_to_datetime(start),
            end=_to_datetime(end),
            description=_get_optional_field(event_component, "description"),
            location=_get_optional_field(event_component, "location"),
            recurrence=_get_optional_field(event_component, "rrule"),
            all_day=not isinstance(start, datetime),
        )

    @staticmethod
    def generate_uid() -> str:
        """Generate a unique event ID.

        Returns:
            str: UUID string
        """
        return str(uuid.uuid4())
