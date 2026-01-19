"""Event model for calendar events."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Any

from icalendar import Calendar
from icalendar import Event as ICalEvent


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

        # Get the first event component
        event_component = None
        for component in cal.walk():
            if component.name == "VEVENT":
                event_component = component
                break

        if not event_component:
            raise ValueError("No VEVENT found in iCalendar data")

        uid = str(event_component.get("uid"))
        title = str(event_component.get("summary", ""))

        # Get start and end dates/times
        dtstart = event_component.get("dtstart")
        dtend = event_component.get("dtend")

        if not dtstart:
            raise ValueError("Event missing required DTSTART field")
        if not dtend:
            raise ValueError("Event missing required DTEND field")

        start = dtstart.dt
        end = dtend.dt
        description = (
            str(event_component.get("description", ""))
            if event_component.get("description")
            else None
        )
        location = (
            str(event_component.get("location", "")) if event_component.get("location") else None
        )
        recurrence = str(event_component.get("rrule", "")) if event_component.get("rrule") else None

        # Convert date to datetime if needed
        if isinstance(start, datetime):
            start_dt = start
        else:
            # It's a date object, convert to datetime
            start_dt = datetime.combine(start, time.min)

        if isinstance(end, datetime):
            end_dt = end
        else:
            end_dt = datetime.combine(end, time.min)

        # Determine if all-day event
        all_day = not isinstance(event_component.get("dtstart").dt, datetime)

        return cls(
            uid=uid,
            title=title,
            start=start_dt,
            end=end_dt,
            description=description,
            location=location,
            recurrence=recurrence,
            all_day=all_day,
        )

    @staticmethod
    def generate_uid() -> str:
        """Generate a unique event ID.

        Returns:
            str: UUID string
        """
        return str(uuid.uuid4())
