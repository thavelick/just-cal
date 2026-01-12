"""Tests for delete command."""

import argparse
from datetime import UTC, datetime
from unittest.mock import Mock, patch

from just_cal.commands.delete import handle_delete_command
from just_cal.event import Event


class TestHandleDeleteCommand:
    """Tests for handle_delete_command function."""

    @patch("just_cal.commands.delete.CalDAVClient")
    @patch("just_cal.commands.delete.Config")
    def test_delete_with_yes_flag(self, mock_config_class, mock_caldav_class, capsys):
        """Test deleting event with -y flag (skip confirmation)."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
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

        args = argparse.Namespace(event_id="test-uid", yes=True)

        handle_delete_command(args)

        # Verify delete_event was called
        mock_client.delete_event.assert_called_once_with("test-uid")

        # Check output
        captured = capsys.readouterr()
        assert "Event deleted successfully" in captured.out
        assert "Test Event" in captured.out

    @patch("just_cal.commands.delete.input", return_value="y")
    @patch("just_cal.commands.delete.CalDAVClient")
    @patch("just_cal.commands.delete.Config")
    def test_delete_with_confirmation_yes(
        self, mock_config_class, mock_caldav_class, mock_input, capsys
    ):
        """Test deleting event with confirmation prompt (user says yes)."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_event = Event(
            uid="test-uid",
            title="Test Event",
            start=datetime(2026, 1, 20, 14, 0, tzinfo=UTC),
            end=datetime(2026, 1, 20, 15, 0, tzinfo=UTC),
            description="Test description",
            location="Test location",
        )
        mock_client.get_event_by_uid.return_value = mock_event
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(event_id="test-uid", yes=False)

        handle_delete_command(args)

        # Verify confirmation prompt was called
        mock_input.assert_called_once()

        # Verify delete_event was called
        mock_client.delete_event.assert_called_once_with("test-uid")

        # Check output shows event details
        captured = capsys.readouterr()
        assert "Test Event" in captured.out
        assert "Test description" in captured.out
        assert "Test location" in captured.out
        assert "Event deleted successfully" in captured.out

    @patch("just_cal.commands.delete.input", return_value="yes")
    @patch("just_cal.commands.delete.CalDAVClient")
    @patch("just_cal.commands.delete.Config")
    def test_delete_confirmation_accepts_yes_word(
        self, mock_config_class, mock_caldav_class, mock_input, capsys
    ):
        """Test that 'yes' (full word) is accepted as confirmation."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
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

        args = argparse.Namespace(event_id="test-uid", yes=False)

        handle_delete_command(args)

        # Verify delete_event was called
        mock_client.delete_event.assert_called_once_with("test-uid")

    @patch("just_cal.commands.delete.input", return_value="n")
    @patch("just_cal.commands.delete.CalDAVClient")
    @patch("just_cal.commands.delete.Config")
    def test_delete_with_confirmation_no(
        self, mock_config_class, mock_caldav_class, mock_input, capsys
    ):
        """Test cancelling deletion when user says no."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
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

        args = argparse.Namespace(event_id="test-uid", yes=False)

        # Should exit with code 0 when cancelled
        try:
            handle_delete_command(args)
        except SystemExit as e:
            assert e.code == 0

        # Verify delete_event was NOT called
        mock_client.delete_event.assert_not_called()

        # Check output
        captured = capsys.readouterr()
        assert "Deletion cancelled" in captured.out

    @patch("just_cal.commands.delete.input", return_value="")
    @patch("just_cal.commands.delete.CalDAVClient")
    @patch("just_cal.commands.delete.Config")
    def test_delete_confirmation_default_no(self, mock_config_class, mock_caldav_class, mock_input):
        """Test that empty response (Enter key) defaults to no."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
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

        args = argparse.Namespace(event_id="test-uid", yes=False)

        # Should exit when cancelled
        try:
            handle_delete_command(args)
        except SystemExit:
            pass

        # Verify delete_event was NOT called
        mock_client.delete_event.assert_not_called()

    @patch("just_cal.commands.delete.CalDAVClient")
    @patch("just_cal.commands.delete.Config")
    def test_delete_calls_get_event_by_uid(self, mock_config_class, mock_caldav_class):
        """Test that delete command fetches event by UID."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_event = Event(
            uid="test-uid-456",
            title="Test Event",
            start=datetime(2026, 1, 20, 14, 0, tzinfo=UTC),
            end=datetime(2026, 1, 20, 15, 0, tzinfo=UTC),
        )
        mock_client.get_event_by_uid.return_value = mock_event
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(event_id="test-uid-456", yes=True)

        handle_delete_command(args)

        # Verify get_event_by_uid was called with correct UID
        mock_client.get_event_by_uid.assert_called_once_with("test-uid-456")

    @patch("just_cal.commands.delete.CalDAVClient")
    @patch("just_cal.commands.delete.Config")
    def test_delete_shows_event_details(self, mock_config_class, mock_caldav_class, capsys):
        """Test that delete command displays event details before deletion."""
        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_event = Event(
            uid="test-uid",
            title="Important Meeting",
            start=datetime(2026, 1, 20, 14, 0, tzinfo=UTC),
            end=datetime(2026, 1, 20, 15, 0, tzinfo=UTC),
            description="Quarterly review",
            location="Conference Room B",
        )
        mock_client.get_event_by_uid.return_value = mock_event
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(event_id="test-uid", yes=True)

        handle_delete_command(args)

        # Check that event details appear in output
        captured = capsys.readouterr()
        assert "Important Meeting" in captured.out
        assert "test-uid" in captured.out
