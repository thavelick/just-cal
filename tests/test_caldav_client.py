"""Tests for CalDAVClient."""

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from just_cal.caldav_client import CalDAVClient
from just_cal.event import Event
from just_cal.exceptions import (
    AuthenticationError,
    ConnectionError,
    EventNotFoundError,
    JustCalError,
)


@pytest.fixture
def client(mock_config):
    """Create a CalDAVClient instance."""
    return CalDAVClient(mock_config)


def test_caldav_client_initialization(mock_config):
    """Test CalDAVClient initialization."""
    client = CalDAVClient(mock_config)
    assert client.config == mock_config
    assert client.client is None
    assert client.calendar is None


@patch("just_cal.caldav_client.caldav")
def test_connect_success(mock_caldav, client, mock_config):
    """Test successful CalDAV connection."""
    # Mock the calendar
    mock_calendar = Mock()
    mock_calendar.name = "Personal"

    # Mock the principal and calendars
    mock_principal = Mock()
    mock_principal.calendars.return_value = [mock_calendar]

    # Mock the DAV client
    mock_dav_client = Mock()
    mock_dav_client.principal.return_value = mock_principal
    mock_caldav.DAVClient.return_value = mock_dav_client

    client.connect()

    assert client.client == mock_dav_client
    assert client.calendar == mock_calendar
    mock_caldav.DAVClient.assert_called_once_with(
        url="https://example.com/dav", username="testuser", password="testpass"
    )


@patch("just_cal.caldav_client.caldav")
def test_connect_password_error(mock_caldav, client, mock_config):
    """Test connection when password retrieval fails."""
    mock_config.get_password.side_effect = Exception("Keyring error")

    with pytest.raises(AuthenticationError, match="Failed to get password"):
        client.connect()


@patch("just_cal.caldav_client.caldav")
def test_connect_no_url(mock_caldav, mock_config):
    """Test connection when URL is not configured."""
    mock_config.get.side_effect = lambda section, key, default=None: {
        ("caldav", "url"): None,
        ("caldav", "username"): "testuser",
        ("caldav", "calendar"): "Personal",
    }.get((section, key), default)

    client = CalDAVClient(mock_config)

    with pytest.raises(ConnectionError, match="CalDAV URL and username must be configured"):
        client.connect()


@patch("just_cal.caldav_client.caldav")
def test_connect_auth_error(mock_caldav, client):
    """Test connection when authentication fails."""
    mock_caldav.lib.error.AuthorizationError = Exception
    mock_caldav.DAVClient.return_value.principal.side_effect = Exception("Unauthorized")

    with pytest.raises(AuthenticationError, match="Authentication failed"):
        client.connect()


@patch("just_cal.caldav_client.caldav")
def test_connect_no_calendars(mock_caldav, client):
    """Test connection when no calendars found."""

    # Create a proper exception class for AuthorizationError
    class AuthorizationError(Exception):
        pass

    mock_caldav.lib.error.AuthorizationError = AuthorizationError

    mock_principal = Mock()
    mock_principal.calendars.return_value = []

    mock_dav_client = Mock()
    mock_dav_client.principal.return_value = mock_principal
    mock_caldav.DAVClient.return_value = mock_dav_client

    with pytest.raises(ConnectionError, match="No calendars found"):
        client.connect()


@patch("just_cal.caldav_client.caldav")
def test_connect_calendar_not_found(mock_caldav, client):
    """Test connection when specified calendar is not found."""

    # Create a proper exception class for AuthorizationError
    class AuthorizationError(Exception):
        pass

    mock_caldav.lib.error.AuthorizationError = AuthorizationError

    mock_calendar1 = Mock()
    mock_calendar1.name = "Work"
    mock_calendar2 = Mock()
    mock_calendar2.name = "Other"

    mock_principal = Mock()
    mock_principal.calendars.return_value = [mock_calendar1, mock_calendar2]

    mock_dav_client = Mock()
    mock_dav_client.principal.return_value = mock_principal
    mock_caldav.DAVClient.return_value = mock_dav_client

    with pytest.raises(ConnectionError, match="Calendar 'Personal' not found"):
        client.connect()


def test_find_calendar(client):
    """Test finding calendar by name."""
    cal1 = Mock()
    cal1.name = "Work"
    cal2 = Mock()
    cal2.name = "Personal"
    cal3 = Mock()
    cal3.name = "Other"

    calendars = [cal1, cal2, cal3]

    result = client._find_calendar(calendars, "Personal")
    assert result == cal2

    result = client._find_calendar(calendars, "NonExistent")
    assert result is None


def test_add_event_not_connected(client):
    """Test adding event when not connected."""
    event = Event(
        uid="test-uid",
        title="Test Event",
        start=datetime(2026, 1, 15, 14, 0, tzinfo=UTC),
        end=datetime(2026, 1, 15, 15, 0, tzinfo=UTC),
    )

    with pytest.raises(ConnectionError, match="Not connected"):
        client.add_event(event)


def test_add_event_success(client):
    """Test successfully adding an event."""
    client.calendar = Mock()
    client.calendar.save_event.return_value = Mock()

    event = Event(
        uid="test-uid-123",
        title="Test Event",
        start=datetime(2026, 1, 15, 14, 0, tzinfo=UTC),
        end=datetime(2026, 1, 15, 15, 0, tzinfo=UTC),
    )

    uid = client.add_event(event)

    assert uid == "test-uid-123"
    client.calendar.save_event.assert_called_once()


def test_add_event_failure(client):
    """Test adding event when save fails."""
    client.calendar = Mock()
    client.calendar.save_event.side_effect = Exception("Save failed")

    event = Event(
        uid="test-uid",
        title="Test Event",
        start=datetime(2026, 1, 15, 14, 0, tzinfo=UTC),
        end=datetime(2026, 1, 15, 15, 0, tzinfo=UTC),
    )

    with pytest.raises(ConnectionError, match="Failed to add event"):
        client.add_event(event)


def test_list_events_not_connected(client):
    """Test listing events when not connected."""
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)

    with pytest.raises(ConnectionError, match="Not connected"):
        client.list_events(start, end)


def test_list_events_success(client):
    """Test successfully listing events."""
    client.calendar = Mock()

    # Create mock calendar events
    mock_cal_event1 = Mock()
    mock_cal_event1.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:event-1
SUMMARY:Event 1
DTSTART:20260115T140000Z
DTEND:20260115T150000Z
END:VEVENT
END:VCALENDAR"""

    mock_cal_event2 = Mock()
    mock_cal_event2.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:event-2
SUMMARY:Event 2
DTSTART:20260116T140000Z
DTEND:20260116T150000Z
END:VEVENT
END:VCALENDAR"""

    client.calendar.search.return_value = [mock_cal_event1, mock_cal_event2]

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)

    events = client.list_events(start, end)

    assert len(events) == 2
    assert events[0].uid == "event-1"
    assert events[0].title == "Event 1"
    assert events[1].uid == "event-2"
    assert events[1].title == "Event 2"


def test_list_events_chronological_order(client):
    """Test that list_events returns events in chronological order."""
    client.calendar = Mock()

    # Create mock events in non-chronological order
    # Event 3: Jan 17
    mock_cal_event3 = Mock()
    mock_cal_event3.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:event-3
SUMMARY:Event 3
DTSTART:20260117T140000Z
DTEND:20260117T150000Z
END:VEVENT
END:VCALENDAR"""

    # Event 1: Jan 15 (earliest)
    mock_cal_event1 = Mock()
    mock_cal_event1.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:event-1
SUMMARY:Event 1
DTSTART:20260115T140000Z
DTEND:20260115T150000Z
END:VEVENT
END:VCALENDAR"""

    # Event 2: Jan 16
    mock_cal_event2 = Mock()
    mock_cal_event2.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:event-2
SUMMARY:Event 2
DTSTART:20260116T140000Z
DTEND:20260116T150000Z
END:VEVENT
END:VCALENDAR"""

    # Return events in non-chronological order
    client.calendar.search.return_value = [mock_cal_event3, mock_cal_event1, mock_cal_event2]

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)

    events = client.list_events(start, end)

    # Verify events are sorted chronologically
    assert len(events) == 3
    assert events[0].uid == "event-1"  # Jan 15 (earliest)
    assert events[1].uid == "event-2"  # Jan 16
    assert events[2].uid == "event-3"  # Jan 17 (latest)


def test_list_events_mixed_timezones(client):
    """Test that list_events handles mix of timezone-aware and naive datetimes."""
    client.calendar = Mock()

    # Create mock events with different timezone configurations
    # Event 1: All-day event (naive datetime after parsing)
    mock_cal_event1 = Mock()
    mock_cal_event1.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:event-1
SUMMARY:All Day Event
DTSTART;VALUE=DATE:20260115
DTEND;VALUE=DATE:20260116
END:VEVENT
END:VCALENDAR"""

    # Event 2: Timed event with timezone (aware datetime)
    mock_cal_event2 = Mock()
    mock_cal_event2.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:event-2
SUMMARY:Timed Event
DTSTART:20260116T140000Z
DTEND:20260116T150000Z
END:VEVENT
END:VCALENDAR"""

    # Event 3: Another all-day event (naive datetime after parsing)
    mock_cal_event3 = Mock()
    mock_cal_event3.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:event-3
SUMMARY:Another All Day
DTSTART;VALUE=DATE:20260117
DTEND;VALUE=DATE:20260118
END:VEVENT
END:VCALENDAR"""

    client.calendar.search.return_value = [mock_cal_event2, mock_cal_event3, mock_cal_event1]

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)

    # Should not raise an error about comparing naive and aware datetimes
    events = client.list_events(start, end)

    # Verify events are sorted chronologically
    assert len(events) == 3
    assert events[0].uid == "event-1"  # Jan 15 all-day
    assert events[1].uid == "event-2"  # Jan 16 timed
    assert events[2].uid == "event-3"  # Jan 17 all-day


def test_list_events_parse_error(client, capsys):
    """Test listing events when some events fail to parse."""
    client.calendar = Mock()

    # Create one valid and one invalid event
    mock_cal_event1 = Mock()
    mock_cal_event1.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:event-1
SUMMARY:Event 1
DTSTART:20260115T140000Z
DTEND:20260115T150000Z
END:VEVENT
END:VCALENDAR"""

    mock_cal_event2 = Mock()
    mock_cal_event2.data = "INVALID DATA"

    client.calendar.search.return_value = [mock_cal_event1, mock_cal_event2]

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)

    events = client.list_events(start, end)

    # Should only get the valid event
    assert len(events) == 1
    assert events[0].uid == "event-1"

    # Check warning was printed
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "Failed to parse event" in captured.out


def test_search_events_not_connected(client):
    """Test searching events when not connected."""
    with pytest.raises(ConnectionError, match="Not connected"):
        client.search_events("test")


@patch.object(CalDAVClient, "list_events")
def test_search_events_by_title(mock_list_events, client):
    """Test searching events by title."""
    client.calendar = Mock()  # Set calendar to make not-connected check pass

    # Create test events
    event1 = Event(
        uid="event-1",
        title="Team Meeting",
        start=datetime(2026, 1, 15, 14, 0, tzinfo=UTC),
        end=datetime(2026, 1, 15, 15, 0, tzinfo=UTC),
    )
    event2 = Event(
        uid="event-2",
        title="Project Review",
        start=datetime(2026, 1, 16, 14, 0, tzinfo=UTC),
        end=datetime(2026, 1, 16, 15, 0, tzinfo=UTC),
    )
    event3 = Event(
        uid="event-3",
        title="Team Lunch",
        start=datetime(2026, 1, 17, 12, 0, tzinfo=UTC),
        end=datetime(2026, 1, 17, 13, 0, tzinfo=UTC),
    )

    mock_list_events.return_value = [event1, event2, event3]

    results = client.search_events("team", field="title")

    assert len(results) == 2
    assert results[0].title == "Team Meeting"
    assert results[1].title == "Team Lunch"


@patch.object(CalDAVClient, "list_events")
def test_search_events_all_fields(mock_list_events, client):
    """Test searching events across all fields."""
    client.calendar = Mock()

    event1 = Event(
        uid="event-1",
        title="Meeting",
        start=datetime(2026, 1, 15, 14, 0, tzinfo=UTC),
        end=datetime(2026, 1, 15, 15, 0, tzinfo=UTC),
        description="Important discussion",
    )
    event2 = Event(
        uid="event-2",
        title="Project Review",
        start=datetime(2026, 1, 16, 14, 0, tzinfo=UTC),
        end=datetime(2026, 1, 16, 15, 0, tzinfo=UTC),
        location="Conference Room",
    )

    mock_list_events.return_value = [event1, event2]

    # Search for "conference" should find event2 by location
    results = client.search_events("conference", field="all")
    assert len(results) == 1
    assert results[0].uid == "event-2"


def test_get_event_by_uid_not_connected(client):
    """Test getting event by UID when not connected."""
    with pytest.raises(ConnectionError, match="Not connected"):
        client.get_event_by_uid("test-uid")


def test_get_event_by_uid_success(client):
    """Test successfully getting event by UID."""
    client.calendar = Mock()

    mock_cal_event = Mock()
    mock_cal_event.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:target-uid
SUMMARY:Target Event
DTSTART:20260115T140000Z
DTEND:20260115T150000Z
END:VEVENT
END:VCALENDAR"""

    client.calendar.events.return_value = [mock_cal_event]

    event = client.get_event_by_uid("target-uid")

    assert event.uid == "target-uid"
    assert event.title == "Target Event"
    assert hasattr(event, "_caldav_object")
    assert event._caldav_object == mock_cal_event


def test_get_event_by_uid_not_found(client):
    """Test getting event by UID when not found."""
    client.calendar = Mock()

    mock_cal_event = Mock()
    mock_cal_event.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:other-uid
SUMMARY:Other Event
DTSTART:20260115T140000Z
DTEND:20260115T150000Z
END:VEVENT
END:VCALENDAR"""

    client.calendar.events.return_value = [mock_cal_event]

    with pytest.raises(EventNotFoundError, match="Event with UID 'target-uid' not found"):
        client.get_event_by_uid("target-uid")


def test_get_event_by_partial_uid_single_match(client):
    """Test getting event by partial UID with single match."""
    client.calendar = Mock()

    mock_cal_event = Mock()
    mock_cal_event.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:abc123def456
SUMMARY:Test Event
DTSTART:20260115T140000Z
DTEND:20260115T150000Z
END:VEVENT
END:VCALENDAR"""

    client.calendar.events.return_value = [mock_cal_event]

    # Should find event with partial UID
    event = client.get_event_by_uid("abc123")

    assert event.uid == "abc123def456"
    assert event.title == "Test Event"


def test_get_event_by_partial_uid_multiple_matches(client):
    """Test getting event by partial UID with multiple matches."""
    client.calendar = Mock()

    mock_cal_event1 = Mock()
    mock_cal_event1.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:abc123def456
SUMMARY:Event 1
DTSTART:20260115T140000Z
DTEND:20260115T150000Z
END:VEVENT
END:VCALENDAR"""

    mock_cal_event2 = Mock()
    mock_cal_event2.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:abc123xyz789
SUMMARY:Event 2
DTSTART:20260116T140000Z
DTEND:20260116T150000Z
END:VEVENT
END:VCALENDAR"""

    client.calendar.events.return_value = [mock_cal_event1, mock_cal_event2]

    # Should raise error for ambiguous partial UID
    with pytest.raises(JustCalError, match="Partial UID 'abc123' matches multiple events"):
        client.get_event_by_uid("abc123")


def test_get_event_by_partial_uid_no_match(client):
    """Test getting event by partial UID with no matches."""
    client.calendar = Mock()

    mock_cal_event = Mock()
    mock_cal_event.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:xyz789
SUMMARY:Other Event
DTSTART:20260115T140000Z
DTEND:20260115T150000Z
END:VEVENT
END:VCALENDAR"""

    client.calendar.events.return_value = [mock_cal_event]

    # Should not find event with non-matching partial UID
    with pytest.raises(EventNotFoundError, match="Event with UID 'abc123' not found"):
        client.get_event_by_uid("abc123")


def test_update_event_not_connected(client):
    """Test updating event when not connected."""
    event = Event(
        uid="test-uid",
        title="Updated Event",
        start=datetime(2026, 1, 15, 14, 0, tzinfo=UTC),
        end=datetime(2026, 1, 15, 15, 0, tzinfo=UTC),
    )

    with pytest.raises(ConnectionError, match="Not connected"):
        client.update_event("test-uid", event)


@patch.object(CalDAVClient, "get_event_by_uid")
@patch.object(CalDAVClient, "add_event")
def test_update_event_success(mock_add_event, mock_get_event, client):
    """Test successfully updating an event."""
    client.calendar = Mock()

    # Mock the original event
    original_event = Mock()
    original_event._caldav_object = Mock()
    mock_get_event.return_value = original_event

    updated_event = Event(
        uid="new-uid",  # Will be overwritten
        title="Updated Event",
        start=datetime(2026, 1, 15, 14, 0, tzinfo=UTC),
        end=datetime(2026, 1, 15, 15, 0, tzinfo=UTC),
    )

    client.update_event("original-uid", updated_event)

    # Verify original was deleted
    original_event._caldav_object.delete.assert_called_once()

    # Verify new event was added with original UID
    mock_add_event.assert_called_once()
    assert updated_event.uid == "original-uid"


@patch.object(CalDAVClient, "get_event_by_uid")
def test_update_event_not_found(mock_get_event, client):
    """Test updating event when not found."""
    client.calendar = Mock()
    mock_get_event.side_effect = EventNotFoundError("Not found")

    updated_event = Event(
        uid="test-uid",
        title="Updated Event",
        start=datetime(2026, 1, 15, 14, 0, tzinfo=UTC),
        end=datetime(2026, 1, 15, 15, 0, tzinfo=UTC),
    )

    with pytest.raises(EventNotFoundError):
        client.update_event("test-uid", updated_event)


def test_delete_event_not_connected(client):
    """Test deleting event when not connected."""
    with pytest.raises(ConnectionError, match="Not connected"):
        client.delete_event("test-uid")


@patch.object(CalDAVClient, "get_event_by_uid")
def test_delete_event_success(mock_get_event, client):
    """Test successfully deleting an event."""
    client.calendar = Mock()

    # Mock the event to delete
    event = Mock()
    event._caldav_object = Mock()
    mock_get_event.return_value = event

    client.delete_event("test-uid")

    # Verify event was deleted
    event._caldav_object.delete.assert_called_once()


@patch.object(CalDAVClient, "get_event_by_uid")
def test_delete_event_not_found(mock_get_event, client):
    """Test deleting event when not found."""
    client.calendar = Mock()
    mock_get_event.side_effect = EventNotFoundError("Not found")

    with pytest.raises(EventNotFoundError):
        client.delete_event("test-uid")


@patch.object(CalDAVClient, "get_event_by_uid")
def test_delete_event_no_caldav_object(mock_get_event, client):
    """Test deleting event when _caldav_object is missing."""
    client.calendar = Mock()

    # Mock event without _caldav_object
    event = Mock(spec=[])  # No _caldav_object attribute
    mock_get_event.return_value = event

    with pytest.raises(ConnectionError, match="Event object doesn't have CalDAV reference"):
        client.delete_event("test-uid")


def test_delete_event_with_partial_uid(client):
    """Test deleting event using partial UID."""
    client.calendar = Mock()

    # Create mock event with long UID
    mock_cal_event = Mock()
    mock_cal_event.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//test//EN
BEGIN:VEVENT
UID:abc123def456ghi789
SUMMARY:Test Event
DTSTART:20260115T140000Z
DTEND:20260115T150000Z
END:VEVENT
END:VCALENDAR"""

    mock_cal_event.delete = Mock()

    client.calendar.events.return_value = [mock_cal_event]

    # Should successfully delete using partial UID
    client.delete_event("abc123")

    # Verify delete was called
    mock_cal_event.delete.assert_called_once()


@patch.object(CalDAVClient, "connect")
def test_test_connection_success(mock_connect, client):
    """Test connection test when successful."""
    result = client.test_connection()

    assert result is True
    mock_connect.assert_called_once()


@patch.object(CalDAVClient, "connect")
def test_test_connection_failure(mock_connect, client):
    """Test connection test when connection fails."""
    mock_connect.side_effect = ConnectionError("Connection failed")

    with pytest.raises(ConnectionError, match="Connection failed"):
        client.test_connection()
