"""Tests for Event model."""

from datetime import UTC, datetime

import pytest

from just_cal.event import Event


def test_event_creation():
    """Test creating a basic event."""
    event = Event(
        uid="test-uid",
        title="Test Event",
        start=datetime(2026, 1, 15, 14, 0, tzinfo=UTC),
        end=datetime(2026, 1, 15, 15, 0, tzinfo=UTC),
    )
    assert event.uid == "test-uid"
    assert event.title == "Test Event"
    assert event.description is None
    assert event.location is None
    assert event.recurrence is None
    assert event.all_day is False


def test_event_with_all_fields():
    """Test creating an event with all fields."""
    event = Event(
        uid="test-uid",
        title="Test Event",
        start=datetime(2026, 1, 15, 14, 0, tzinfo=UTC),
        end=datetime(2026, 1, 15, 15, 0, tzinfo=UTC),
        description="Test Description",
        location="Test Location",
        recurrence="FREQ=DAILY",
        all_day=False,
    )
    assert event.description == "Test Description"
    assert event.location == "Test Location"
    assert event.recurrence == "FREQ=DAILY"


def test_event_to_ical():
    """Test converting event to iCalendar format."""
    event = Event(
        uid="test-uid-123",
        title="Test Event",
        start=datetime(2026, 1, 15, 14, 0, tzinfo=UTC),
        end=datetime(2026, 1, 15, 15, 0, tzinfo=UTC),
    )
    ical_data = event.to_ical()

    assert "BEGIN:VCALENDAR" in ical_data
    assert "BEGIN:VEVENT" in ical_data
    assert "UID:test-uid-123" in ical_data
    assert "SUMMARY:Test Event" in ical_data
    assert "DTSTART" in ical_data
    assert "DTEND" in ical_data
    assert "END:VEVENT" in ical_data
    assert "END:VCALENDAR" in ical_data


def test_event_to_ical_with_description():
    """Test converting event with description to iCalendar."""
    event = Event(
        uid="test-uid",
        title="Test Event",
        start=datetime(2026, 1, 15, 14, 0, tzinfo=UTC),
        end=datetime(2026, 1, 15, 15, 0, tzinfo=UTC),
        description="This is a test",
    )
    ical_data = event.to_ical()

    assert "DESCRIPTION:This is a test" in ical_data


def test_event_to_ical_with_location():
    """Test converting event with location to iCalendar."""
    event = Event(
        uid="test-uid",
        title="Test Event",
        start=datetime(2026, 1, 15, 14, 0, tzinfo=UTC),
        end=datetime(2026, 1, 15, 15, 0, tzinfo=UTC),
        location="Conference Room A",
    )
    ical_data = event.to_ical()

    assert "LOCATION:Conference Room A" in ical_data


def test_event_from_ical():
    """Test parsing event from iCalendar format."""
    ical_data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:test-uid-456
SUMMARY:Test Event
DTSTART:20260115T140000Z
DTEND:20260115T150000Z
END:VEVENT
END:VCALENDAR"""

    event = Event.from_ical(ical_data)

    assert event.uid == "test-uid-456"
    assert event.title == "Test Event"
    assert event.start.year == 2026
    assert event.start.month == 1
    assert event.start.day == 15
    assert event.start.hour == 14


def test_event_from_ical_with_description():
    """Test parsing event with description from iCalendar."""
    ical_data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:test-uid
SUMMARY:Test Event
DTSTART:20260115T140000Z
DTEND:20260115T150000Z
DESCRIPTION:Test description here
END:VEVENT
END:VCALENDAR"""

    event = Event.from_ical(ical_data)

    assert event.description == "Test description here"


def test_event_from_ical_with_location():
    """Test parsing event with location from iCalendar."""
    ical_data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:test-uid
SUMMARY:Test Event
DTSTART:20260115T140000Z
DTEND:20260115T150000Z
LOCATION:Room 101
END:VEVENT
END:VCALENDAR"""

    event = Event.from_ical(ical_data)

    assert event.location == "Room 101"


def test_event_from_ical_no_vevent():
    """Test parsing iCalendar without VEVENT raises error."""
    ical_data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
END:VCALENDAR"""

    with pytest.raises(ValueError, match="No VEVENT found"):
        Event.from_ical(ical_data)


def test_generate_uid():
    """Test UID generation."""
    uid1 = Event.generate_uid()
    uid2 = Event.generate_uid()

    assert uid1 != uid2
    assert len(uid1) > 0
    assert len(uid2) > 0
