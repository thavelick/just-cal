"""Tests for edit command."""

import argparse
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from just_cal.commands.edit import handle_edit_command
from just_cal.event import Event
from just_cal.exceptions import JustCalError


class TestHandleEditCommand:
    """Tests for handle_edit_command function."""

    @patch("just_cal.commands.edit.CalDAVClient")
    @patch("just_cal.commands.edit.Config")
    def test_edit_title(self, mock_config_class, mock_caldav_class, capsys):
        """Test editing event title."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client with existing event
        mock_client = Mock()
        mock_event = Event(
            uid="test-uid",
            title="Original Title",
            start=datetime(2026, 1, 20, 14, 0, tzinfo=UTC),
            end=datetime(2026, 1, 20, 15, 0, tzinfo=UTC),
        )
        mock_client.get_event_by_uid.return_value = mock_event
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            event_id="test-uid",
            title="Updated Title",
            start=None,
            end=None,
            description=None,
            location=None,
        )

        handle_edit_command(args)

        # Verify update_event was called
        mock_client.update_event.assert_called_once()
        updated_event = mock_client.update_event.call_args[0][1]
        assert updated_event.title == "Updated Title"

        # Check output
        captured = capsys.readouterr()
        assert "Event updated successfully" in captured.out
        assert "title -> Updated Title" in captured.out

    @patch("just_cal.commands.edit.CalDAVClient")
    @patch("just_cal.commands.edit.Config")
    def test_edit_start_time(self, mock_config_class, mock_caldav_class, capsys):
        """Test editing event start time."""
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
        mock_client.get_event_by_uid.return_value = mock_event
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            event_id="test-uid",
            title=None,
            start="2026-01-20 16:00:00",
            end=None,
            description=None,
            location=None,
        )

        handle_edit_command(args)

        # Verify start time was updated
        updated_event = mock_client.update_event.call_args[0][1]
        assert updated_event.start.hour == 16

        # Check output
        captured = capsys.readouterr()
        assert "start ->" in captured.out

    @patch("just_cal.commands.edit.CalDAVClient")
    @patch("just_cal.commands.edit.Config")
    def test_edit_multiple_fields(self, mock_config_class, mock_caldav_class, capsys):
        """Test editing multiple event fields at once."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_event = Event(
            uid="test-uid",
            title="Original",
            start=datetime(2026, 1, 20, 14, 0, tzinfo=UTC),
            end=datetime(2026, 1, 20, 15, 0, tzinfo=UTC),
            description="Old description",
            location="Old location",
        )
        mock_client.get_event_by_uid.return_value = mock_event
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            event_id="test-uid",
            title="New Title",
            start=None,
            end=None,
            description="New description",
            location="New location",
        )

        handle_edit_command(args)

        # Verify all fields were updated
        updated_event = mock_client.update_event.call_args[0][1]
        assert updated_event.title == "New Title"
        assert updated_event.description == "New description"
        assert updated_event.location == "New location"

        # Check output shows all changes
        captured = capsys.readouterr()
        assert "title -> New Title" in captured.out
        assert "description -> New description" in captured.out
        assert "location -> New location" in captured.out

    @patch("just_cal.commands.edit.CalDAVClient")
    @patch("just_cal.commands.edit.Config")
    def test_edit_no_changes(self, mock_config_class, mock_caldav_class, capsys):
        """Test editing with no changes specified."""
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
        mock_client.get_event_by_uid.return_value = mock_event
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            event_id="test-uid",
            title=None,
            start=None,
            end=None,
            description=None,
            location=None,
        )

        handle_edit_command(args)

        # Verify update_event was NOT called
        mock_client.update_event.assert_not_called()

        # Check output message
        captured = capsys.readouterr()
        assert "No changes specified" in captured.out

    @patch("just_cal.commands.edit.CalDAVClient")
    @patch("just_cal.commands.edit.Config")
    def test_edit_invalid_start_date(self, mock_config_class, mock_caldav_class):
        """Test edit with invalid start date."""
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
        mock_client.get_event_by_uid.return_value = mock_event
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            event_id="test-uid",
            title=None,
            start="invalid date",
            end=None,
            description=None,
            location=None,
        )

        with pytest.raises(JustCalError, match="Invalid start date/time"):
            handle_edit_command(args)

    @patch("just_cal.commands.edit.CalDAVClient")
    @patch("just_cal.commands.edit.Config")
    def test_edit_invalid_end_date(self, mock_config_class, mock_caldav_class):
        """Test edit with invalid end date."""
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
        mock_client.get_event_by_uid.return_value = mock_event
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            event_id="test-uid",
            title=None,
            start=None,
            end="invalid date",
            description=None,
            location=None,
        )

        with pytest.raises(JustCalError, match="Invalid end date/time"):
            handle_edit_command(args)

    @patch("just_cal.commands.edit.CalDAVClient")
    @patch("just_cal.commands.edit.Config")
    def test_edit_calls_get_event_by_uid(self, mock_config_class, mock_caldav_class):
        """Test that edit command fetches event by UID."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_event = Event(
            uid="test-uid-123",
            title="Test Event",
            start=datetime(2026, 1, 20, 14, 0, tzinfo=UTC),
            end=datetime(2026, 1, 20, 15, 0, tzinfo=UTC),
        )
        mock_client.get_event_by_uid.return_value = mock_event
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            event_id="test-uid-123",
            title="New Title",
            start=None,
            end=None,
            description=None,
            location=None,
        )

        handle_edit_command(args)

        # Verify get_event_by_uid was called with correct UID
        mock_client.get_event_by_uid.assert_called_once_with("test-uid-123")
