"""Tests for search command."""

import argparse
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from just_cal.commands.search import handle_search_command
from just_cal.event import Event
from just_cal.exceptions import JustCalError


class TestHandleSearchCommand:
    """Tests for handle_search_command function."""

    @patch("just_cal.commands.search.CalDAVClient")
    @patch("just_cal.commands.search.Config")
    def test_search_in_all_fields(self, mock_config_class, mock_caldav_class, capsys):
        """Test search command searching in all fields."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client with events
        mock_client = Mock()
        events = [
            Event(
                uid="test-1",
                title="Team Meeting",
                start=datetime(2026, 1, 20, 14, 0, tzinfo=UTC),
                end=datetime(2026, 1, 20, 15, 0, tzinfo=UTC),
            ),
            Event(
                uid="test-2",
                title="Lunch Break",
                start=datetime(2026, 1, 21, 12, 0, tzinfo=UTC),
                end=datetime(2026, 1, 21, 13, 0, tzinfo=UTC),
            ),
        ]
        mock_client.list_events.return_value = events
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            query="meeting",
            field="all",
            from_date=None,
            to_date=None,
            format="table",
        )

        handle_search_command(args)

        # Check output contains only matching event
        captured = capsys.readouterr()
        assert "Team Meeting" in captured.out
        assert "Lunch Break" not in captured.out
        assert "Total: 1 event(s)" in captured.out

    @patch("just_cal.commands.search.CalDAVClient")
    @patch("just_cal.commands.search.Config")
    def test_search_by_title(self, mock_config_class, mock_caldav_class, capsys):
        """Test search command searching in title field only."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client with events
        mock_client = Mock()
        events = [
            Event(
                uid="test-1",
                title="Doctor Appointment",
                description="Checkup meeting",
                start=datetime(2026, 1, 20, 14, 0, tzinfo=UTC),
                end=datetime(2026, 1, 20, 15, 0, tzinfo=UTC),
            ),
        ]
        mock_client.list_events.return_value = events
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            query="meeting",
            field="title",
            from_date=None,
            to_date=None,
            format="table",
        )

        handle_search_command(args)

        # Should not find it (meeting is only in description, not title)
        captured = capsys.readouterr()
        assert "No events found." in captured.out

    @patch("just_cal.commands.search.CalDAVClient")
    @patch("just_cal.commands.search.Config")
    def test_search_by_description(self, mock_config_class, mock_caldav_class, capsys):
        """Test search command searching in description field."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client with events
        mock_client = Mock()
        events = [
            Event(
                uid="test-1",
                title="Team Sync",
                description="Discuss project progress",
                start=datetime(2026, 1, 20, 14, 0, tzinfo=UTC),
                end=datetime(2026, 1, 20, 15, 0, tzinfo=UTC),
            ),
        ]
        mock_client.list_events.return_value = events
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            query="project",
            field="description",
            from_date=None,
            to_date=None,
            format="table",
        )

        handle_search_command(args)

        # Should find it
        captured = capsys.readouterr()
        assert "Team Sync" in captured.out
        assert "Total: 1 event(s)" in captured.out

    @patch("just_cal.commands.search.CalDAVClient")
    @patch("just_cal.commands.search.Config")
    def test_search_by_location(self, mock_config_class, mock_caldav_class, capsys):
        """Test search command searching in location field."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client with events
        mock_client = Mock()
        events = [
            Event(
                uid="test-1",
                title="Conference",
                location="Room 301",
                start=datetime(2026, 1, 20, 14, 0, tzinfo=UTC),
                end=datetime(2026, 1, 20, 15, 0, tzinfo=UTC),
            ),
        ]
        mock_client.list_events.return_value = events
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            query="room",
            field="location",
            from_date=None,
            to_date=None,
            format="table",
        )

        handle_search_command(args)

        # Should find it
        captured = capsys.readouterr()
        assert "Conference" in captured.out
        assert "Total: 1 event(s)" in captured.out

    @patch("just_cal.commands.search.CalDAVClient")
    @patch("just_cal.commands.search.Config")
    def test_search_case_insensitive(self, mock_config_class, mock_caldav_class, capsys):
        """Test that search is case-insensitive."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client with events
        mock_client = Mock()
        events = [
            Event(
                uid="test-1",
                title="IMPORTANT Meeting",
                start=datetime(2026, 1, 20, 14, 0, tzinfo=UTC),
                end=datetime(2026, 1, 20, 15, 0, tzinfo=UTC),
            ),
        ]
        mock_client.list_events.return_value = events
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            query="important",
            field="all",
            from_date=None,
            to_date=None,
            format="table",
        )

        handle_search_command(args)

        # Should find it (case-insensitive)
        captured = capsys.readouterr()
        assert "IMPORTANT Meeting" in captured.out

    @patch("just_cal.commands.search.CalDAVClient")
    @patch("just_cal.commands.search.Config")
    def test_search_with_date_range(self, mock_config_class, mock_caldav_class):
        """Test search command with custom date range."""
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
            query="test",
            field="all",
            from_date="2026-01-20",
            to_date="2026-01-25",
            format="table",
        )

        handle_search_command(args)

        # Verify list_events was called with parsed dates
        mock_client.list_events.assert_called_once()
        call_args = mock_client.list_events.call_args[0]
        assert call_args[0].year == 2026
        assert call_args[0].month == 1
        assert call_args[0].day == 20

    @patch("just_cal.commands.search.CalDAVClient")
    @patch("just_cal.commands.search.Config")
    def test_search_json_format(self, mock_config_class, mock_caldav_class, capsys):
        """Test search command with JSON output."""
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
        )
        mock_client.list_events.return_value = [mock_event]
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            query="test",
            field="all",
            from_date=None,
            to_date=None,
            format="json",
        )

        handle_search_command(args)

        # Check JSON output
        captured = capsys.readouterr()
        assert '"uid": "test-uid"' in captured.out
        assert '"title": "Test Event"' in captured.out

    @patch("just_cal.commands.search.Config")
    def test_search_invalid_from_date(self, mock_config_class):
        """Test search command with invalid from date."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        args = argparse.Namespace(
            query="test",
            field="all",
            from_date="invalid date",
            to_date=None,
            format="table",
        )

        with pytest.raises(JustCalError, match="Invalid from date"):
            handle_search_command(args)

    @patch("just_cal.commands.search.Config")
    def test_search_invalid_to_date(self, mock_config_class):
        """Test search command with invalid to date."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        args = argparse.Namespace(
            query="test",
            field="all",
            from_date="2026-01-20",
            to_date="invalid date",
            format="table",
        )

        with pytest.raises(JustCalError, match="Invalid to date"):
            handle_search_command(args)
