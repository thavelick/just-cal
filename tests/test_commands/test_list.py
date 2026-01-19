"""Tests for list command."""

import argparse
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from just_cal.commands.list import handle_list_command
from just_cal.event import Event
from just_cal.exceptions import JustCalError


class TestHandleListCommand:
    """Tests for handle_list_command function."""

    @patch("just_cal.commands.list.CalDAVClient")
    @patch("just_cal.commands.list.Config")
    def test_list_with_defaults(self, mock_config_class, mock_caldav_class, capsys):
        """Test list command with default parameters."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client with events
        mock_client = Mock()
        mock_event = Event(
            uid="test-uid",
            title="Test Event",
            start=datetime(2026, 1, 20, 14, 0, tzinfo=UTC),
            end=datetime(2026, 1, 20, 15, 0, tzinfo=UTC),
        )
        mock_client.list_events.return_value = [mock_event]
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(from_date=None, to_date=None, format="table", limit=None)

        handle_list_command(args)

        # Verify CalDAV client was called
        mock_client.connect.assert_called_once()
        mock_client.list_events.assert_called_once()

        # Check output includes UID column, event title, day of week, and total
        captured = capsys.readouterr()
        assert "UID" in captured.out
        assert "test-uid" in captured.out
        assert "Test Event" in captured.out
        assert "Tue," in captured.out  # 2026-01-20 is a Tuesday
        assert "Total: 1 event(s)" in captured.out

    @patch("just_cal.commands.list.CalDAVClient")
    @patch("just_cal.commands.list.Config")
    def test_list_with_date_range(self, mock_config_class, mock_caldav_class):
        """Test list command with custom date range."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_client.list_events.return_value = []
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            from_date="2026-01-20", to_date="2026-01-25", format="table", limit=None
        )

        handle_list_command(args)

        # Verify list_events was called with parsed dates
        mock_client.list_events.assert_called_once()
        call_args = mock_client.list_events.call_args[0]
        assert call_args[0].year == 2026
        assert call_args[0].month == 1
        assert call_args[0].day == 20

    @patch("just_cal.commands.list.CalDAVClient")
    @patch("just_cal.commands.list.Config")
    def test_list_with_limit(self, mock_config_class, mock_caldav_class, capsys):
        """Test list command with result limit."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client with multiple events
        mock_client = Mock()
        events = [
            Event(
                uid=f"test-{i}",
                title=f"Event {i}",
                start=datetime(2026, 1, 20 + i, 14, 0, tzinfo=UTC),
                end=datetime(2026, 1, 20 + i, 15, 0, tzinfo=UTC),
            )
            for i in range(5)
        ]
        mock_client.list_events.return_value = events
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(from_date=None, to_date=None, format="table", limit=2)

        handle_list_command(args)

        # Check that only 2 events are shown
        captured = capsys.readouterr()
        assert "Total: 2 event(s)" in captured.out

    @patch("just_cal.commands.list.CalDAVClient")
    @patch("just_cal.commands.list.Config")
    def test_list_json_format(self, mock_config_class, mock_caldav_class, capsys):
        """Test list command with JSON output format."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_event = Event(
            uid="test-uid",
            title="Test Event",
            start=datetime(2026, 1, 20, 14, 0, tzinfo=UTC),
            end=datetime(2026, 1, 20, 15, 0, tzinfo=UTC),
            description="Test description",
        )
        mock_client.list_events.return_value = [mock_event]
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(from_date=None, to_date=None, format="json", limit=None)

        handle_list_command(args)

        # Check JSON output
        captured = capsys.readouterr()
        assert '"uid": "test-uid"' in captured.out
        assert '"title": "Test Event"' in captured.out
        assert '"description": "Test description"' in captured.out

    @patch("just_cal.commands.list.CalDAVClient")
    @patch("just_cal.commands.list.Config")
    def test_list_no_events(self, mock_config_class, mock_caldav_class, capsys):
        """Test list command with no events found."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client with no events
        mock_client = Mock()
        mock_client.list_events.return_value = []
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(from_date=None, to_date=None, format="table", limit=None)

        handle_list_command(args)

        # Check output
        captured = capsys.readouterr()
        assert "No events found." in captured.out

    @patch("just_cal.commands.list.Config")
    def test_list_invalid_from_date(self, mock_config_class):
        """Test list command with invalid from date."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        args = argparse.Namespace(
            from_date="invalid date", to_date=None, format="table", limit=None
        )

        with pytest.raises(JustCalError, match="Invalid from date"):
            handle_list_command(args)

    @patch("just_cal.commands.list.Config")
    def test_list_invalid_to_date(self, mock_config_class):
        """Test list command with invalid to date."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        args = argparse.Namespace(
            from_date="2026-01-20", to_date="invalid date", format="table", limit=None
        )

        with pytest.raises(JustCalError, match="Invalid to date"):
            handle_list_command(args)

    @patch("just_cal.commands.list.CalDAVClient")
    @patch("just_cal.commands.list.Config")
    def test_list_uses_12hour_format(self, mock_config_class, mock_caldav_class, capsys):
        """Test list command displays times in 12-hour AM/PM format."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client with events at different times
        mock_client = Mock()
        events = [
            Event(
                uid="morning-event",
                title="Morning Meeting",
                start=datetime(2026, 1, 20, 9, 30, tzinfo=UTC),
                end=datetime(2026, 1, 20, 10, 30, tzinfo=UTC),
            ),
            Event(
                uid="afternoon-event",
                title="Afternoon Meeting",
                start=datetime(2026, 1, 20, 14, 0, tzinfo=UTC),
                end=datetime(2026, 1, 20, 15, 0, tzinfo=UTC),
            ),
        ]
        mock_client.list_events.return_value = events
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(from_date=None, to_date=None, format="table", limit=None)

        handle_list_command(args)

        # Check output uses 12-hour format with AM/PM (leading zeros stripped)
        captured = capsys.readouterr()
        assert "9:30 AM" in captured.out
        assert "10:30 AM" in captured.out
        assert "2:00 PM" in captured.out
        assert "3:00 PM" in captured.out
        # Ensure 24-hour format is NOT used
        assert "14:00" not in captured.out
        assert "15:00" not in captured.out


class TestFormatWhenColumn:
    """Tests for format_time_range function."""

    def test_format_all_day_event(self):
        """Test formatting for all-day events."""
        from just_cal.utils.output import format_time_range

        event = Event(
            uid="test-uid",
            title="All Day Event",
            start=datetime(2026, 1, 10, 0, 0, tzinfo=UTC),
            end=datetime(2026, 1, 12, 0, 0, tzinfo=UTC),
            all_day=True,
        )

        result = format_time_range(event)
        assert result == "Sat, 2026-01-10 - Mon, 2026-01-12"

    def test_format_same_day_timed_event(self):
        """Test formatting for same-day timed events."""
        from just_cal.utils.output import format_time_range

        event = Event(
            uid="test-uid",
            title="Meeting",
            start=datetime(2026, 1, 11, 19, 0, tzinfo=UTC),  # 7:00 PM
            end=datetime(2026, 1, 11, 20, 0, tzinfo=UTC),  # 8:00 PM
            all_day=False,
        )

        result = format_time_range(event)
        assert result == "Sun, 2026-01-11 7:00 PM - 8:00 PM"

    def test_format_multi_day_timed_event(self):
        """Test formatting for multi-day timed events."""
        from just_cal.utils.output import format_time_range

        event = Event(
            uid="test-uid",
            title="Conference",
            start=datetime(2026, 1, 10, 19, 0, tzinfo=UTC),  # 7:00 PM
            end=datetime(2026, 1, 12, 9, 0, tzinfo=UTC),  # 9:00 AM
            all_day=False,
        )

        result = format_time_range(event)
        assert result == "Sat, 2026-01-10 7:00 PM - Mon, 2026-01-12 9:00 AM"
