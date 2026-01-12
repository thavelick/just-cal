"""Tests for add command."""

import argparse
from unittest.mock import Mock, patch

import pytest

from just_cal.exceptions import JustCalError


class TestHandleAddCommand:
    """Tests for handle_add_command function."""

    def test_empty_title_raises_error(self):
        """Test that empty title raises ValueError."""
        from just_cal.commands.add import handle_add_command

        args = argparse.Namespace(
            title="",
            start="tomorrow at 2pm",
            end=None,
            description=None,
            location=None,
            all_day=False,
        )

        with pytest.raises(ValueError, match="Title cannot be empty"):
            handle_add_command(args)

    def test_whitespace_title_raises_error(self):
        """Test that whitespace-only title raises ValueError."""
        from just_cal.commands.add import handle_add_command

        args = argparse.Namespace(
            title="   ",
            start="tomorrow at 2pm",
            end=None,
            description=None,
            location=None,
            all_day=False,
        )

        with pytest.raises(ValueError, match="Title cannot be empty"):
            handle_add_command(args)

    @patch("just_cal.commands.add.CalDAVClient")
    @patch("just_cal.commands.add.Config")
    def test_invalid_start_date_raises_error(self, mock_config_class, mock_caldav_class):
        """Test that invalid start date raises JustCalError."""
        from just_cal.commands.add import handle_add_command

        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        args = argparse.Namespace(
            title="Test Event",
            start="not a valid date",
            end=None,
            description=None,
            location=None,
            all_day=False,
        )

        with pytest.raises(JustCalError, match="Invalid start date/time"):
            handle_add_command(args)

    @patch("just_cal.commands.add.CalDAVClient")
    @patch("just_cal.commands.add.Config")
    def test_invalid_end_date_raises_error(self, mock_config_class, mock_caldav_class):
        """Test that invalid end date raises JustCalError."""
        from just_cal.commands.add import handle_add_command

        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        args = argparse.Namespace(
            title="Test Event",
            start="tomorrow at 2pm",
            end="invalid date",
            description=None,
            location=None,
            all_day=False,
        )

        with pytest.raises(JustCalError, match="Invalid end date/time"):
            handle_add_command(args)

    @patch("just_cal.commands.add.CalDAVClient")
    @patch("just_cal.commands.add.Config")
    def test_default_end_time_one_hour(self, mock_config_class, mock_caldav_class):
        """Test that end defaults to start + 1 hour when not specified."""
        from datetime import timedelta

        from just_cal.commands.add import handle_add_command

        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.side_effect = lambda section, key, default=None: {
            ("preferences", "timezone"): "America/New_York",
            ("preferences", "default_duration"): 60,
        }.get((section, key), default)
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_client.add_event.return_value = "test-uid"
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            title="Test Event",
            start="2026-01-20 14:00:00",
            end=None,  # No end specified
            description=None,
            location=None,
            all_day=False,
        )

        handle_add_command(args)

        # Verify add_event was called
        mock_client.add_event.assert_called_once()
        event = mock_client.add_event.call_args[0][0]

        # Check that end is start + 60 minutes
        assert event.end == event.start + timedelta(minutes=60)

    @patch("just_cal.commands.add.CalDAVClient")
    @patch("just_cal.commands.add.Config")
    def test_custom_default_duration(self, mock_config_class, mock_caldav_class):
        """Test that custom default_duration from config is used."""
        from datetime import timedelta

        from just_cal.commands.add import handle_add_command

        # Mock config with 30 minute default
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.side_effect = lambda section, key, default=None: {
            ("preferences", "timezone"): "America/New_York",
            ("preferences", "default_duration"): 30,
        }.get((section, key), default)
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_client.add_event.return_value = "test-uid"
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            title="Test Event",
            start="2026-01-20 14:00:00",
            end=None,
            description=None,
            location=None,
            all_day=False,
        )

        handle_add_command(args)

        # Verify end is start + 30 minutes
        event = mock_client.add_event.call_args[0][0]
        assert event.end == event.start + timedelta(minutes=30)

    @patch("just_cal.commands.add.CalDAVClient")
    @patch("just_cal.commands.add.Config")
    def test_explicit_all_day_flag(self, mock_config_class, mock_caldav_class):
        """Test that explicit --all-day flag creates all-day event."""
        from just_cal.commands.add import handle_add_command

        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_client.add_event.return_value = "test-uid"
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            title="Test Event",
            start="2026-01-20 14:00:00",  # Non-midnight time
            end=None,
            description=None,
            location=None,
            all_day=True,  # Explicit all-day flag
        )

        handle_add_command(args)

        # Verify event is created as all-day
        event = mock_client.add_event.call_args[0][0]
        assert event.all_day is True

    @patch("just_cal.commands.add.CalDAVClient")
    @patch("just_cal.commands.add.Config")
    def test_midnight_auto_detects_all_day(self, mock_config_class, mock_caldav_class):
        """Test that midnight start time auto-detects as all-day event."""
        from just_cal.commands.add import handle_add_command

        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_client.add_event.return_value = "test-uid"
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            title="Test Event",
            start="2026-01-20 00:00:00",  # Midnight time
            end=None,
            description=None,
            location=None,
            all_day=False,  # No explicit flag, but should auto-detect
        )

        handle_add_command(args)

        # Verify event is auto-detected as all-day
        event = mock_client.add_event.call_args[0][0]
        assert event.all_day is True

    @patch("just_cal.commands.add.CalDAVClient")
    @patch("just_cal.commands.add.Config")
    def test_midnight_with_date_only_auto_detects(self, mock_config_class, mock_caldav_class):
        """Test that date-only format auto-detects as all-day event."""
        from just_cal.commands.add import handle_add_command

        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_client.add_event.return_value = "test-uid"
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            title="Test Event",
            start="2026-01-20",  # Date only (parses to midnight)
            end=None,
            description=None,
            location=None,
            all_day=False,
        )

        handle_add_command(args)

        # Verify event is auto-detected as all-day
        event = mock_client.add_event.call_args[0][0]
        assert event.all_day is True

    @patch("just_cal.commands.add.CalDAVClient")
    @patch("just_cal.commands.add.Config")
    def test_non_midnight_not_all_day(self, mock_config_class, mock_caldav_class):
        """Test that non-midnight time is NOT auto-detected as all-day."""
        from just_cal.commands.add import handle_add_command

        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.side_effect = lambda section, key, default=None: {
            ("preferences", "timezone"): "America/New_York",
            ("preferences", "default_duration"): 60,
        }.get((section, key), default)
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_client.add_event.return_value = "test-uid"
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            title="Test Event",
            start="2026-01-20 14:00:00",  # Non-midnight time
            end=None,
            description=None,
            location=None,
            all_day=False,
        )

        handle_add_command(args)

        # Verify event is NOT all-day
        event = mock_client.add_event.call_args[0][0]
        assert event.all_day is False

    @patch("just_cal.commands.add.CalDAVClient")
    @patch("just_cal.commands.add.Config")
    def test_all_day_event_defaults_to_same_day_end(self, mock_config_class, mock_caldav_class):
        """Test that all-day events default to same day for end time."""
        from just_cal.commands.add import handle_add_command

        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.return_value = "America/New_York"
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_client.add_event.return_value = "test-uid"
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            title="Test Event",
            start="2026-01-20",  # Date only
            end=None,  # No end specified
            description=None,
            location=None,
            all_day=False,  # Will auto-detect
        )

        handle_add_command(args)

        # Verify end is same as start for all-day event
        event = mock_client.add_event.call_args[0][0]
        assert event.all_day is True
        assert event.end.date() == event.start.date()  # Same day


class TestEventCreationIntegration:
    """Tests for CalDAV integration in event creation."""

    @patch("just_cal.commands.add.CalDAVClient")
    @patch("just_cal.commands.add.Config")
    def test_event_creation_calls_caldav_client(self, mock_config_class, mock_caldav_class):
        """Test that event creation calls CalDAV client's add_event method."""
        from just_cal.commands.add import handle_add_command

        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.side_effect = lambda section, key, default=None: {
            ("preferences", "timezone"): "America/New_York",
            ("preferences", "default_duration"): 60,
        }.get((section, key), default)
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_client.add_event.return_value = "test-uid-123"
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            title="Team Meeting",
            start="2026-01-20 14:00:00",
            end="2026-01-20 15:00:00",
            description="Discuss project progress",
            location="Conference Room A",
            all_day=False,
        )

        handle_add_command(args)

        # Verify CalDAV client was instantiated with config
        mock_caldav_class.assert_called_once_with(mock_config)

        # Verify client.connect() was called
        mock_client.connect.assert_called_once()

        # Verify add_event was called exactly once
        mock_client.add_event.assert_called_once()

    @patch("just_cal.commands.add.CalDAVClient")
    @patch("just_cal.commands.add.Config")
    def test_event_properties_passed_to_caldav(self, mock_config_class, mock_caldav_class):
        """Test that event properties are correctly passed to CalDAV client."""
        from just_cal.commands.add import handle_add_command

        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.side_effect = lambda section, key, default=None: {
            ("preferences", "timezone"): "America/New_York",
            ("preferences", "default_duration"): 60,
        }.get((section, key), default)
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_client.add_event.return_value = "test-uid-456"
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            title="Doctor Appointment",
            start="2026-01-25 10:00:00",
            end="2026-01-25 11:00:00",
            description="Annual checkup",
            location="Medical Center",
            all_day=False,
        )

        handle_add_command(args)

        # Get the Event object passed to add_event
        event = mock_client.add_event.call_args[0][0]

        # Verify all properties are correctly set
        assert event.title == "Doctor Appointment"
        assert event.description == "Annual checkup"
        assert event.location == "Medical Center"
        assert event.all_day is False

    @patch("just_cal.commands.add.CalDAVClient")
    @patch("just_cal.commands.add.Config")
    def test_event_with_no_description_or_location(self, mock_config_class, mock_caldav_class):
        """Test event creation with no description or location."""
        from just_cal.commands.add import handle_add_command

        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.side_effect = lambda section, key, default=None: {
            ("preferences", "timezone"): "America/New_York",
            ("preferences", "default_duration"): 60,
        }.get((section, key), default)
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_client.add_event.return_value = "test-uid-789"
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            title="Quick Meeting",
            start="2026-01-20 14:00:00",
            end=None,
            description=None,  # No description
            location=None,  # No location
            all_day=False,
        )

        handle_add_command(args)

        # Get the Event object
        event = mock_client.add_event.call_args[0][0]

        # Verify properties
        assert event.title == "Quick Meeting"
        assert event.description is None
        assert event.location is None

    @patch("just_cal.commands.add.CalDAVClient")
    @patch("just_cal.commands.add.Config")
    def test_success_message_displayed(self, mock_config_class, mock_caldav_class, capsys):
        """Test that success message is displayed after event creation."""
        from just_cal.commands.add import handle_add_command

        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.side_effect = lambda section, key, default=None: {
            ("preferences", "timezone"): "America/New_York",
            ("preferences", "default_duration"): 60,
        }.get((section, key), default)
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_client.add_event.return_value = "created-event-uid"
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            title="Test Event",
            start="2026-01-20 14:00:00",
            end=None,
            description=None,
            location=None,
            all_day=False,
        )

        handle_add_command(args)

        # Check output
        captured = capsys.readouterr()
        assert "Event created successfully" in captured.out
        assert "Test Event" in captured.out
        assert "created-event-uid" in captured.out

    @patch("just_cal.commands.add.CalDAVClient")
    @patch("just_cal.commands.add.Config")
    def test_event_uid_generated(self, mock_config_class, mock_caldav_class):
        """Test that event has a UID when passed to CalDAV client."""
        from just_cal.commands.add import handle_add_command

        # Mock config
        mock_config = Mock()
        mock_config.load = Mock()
        mock_config.get.side_effect = lambda section, key, default=None: {
            ("preferences", "timezone"): "America/New_York",
            ("preferences", "default_duration"): 60,
        }.get((section, key), default)
        mock_config_class.return_value = mock_config

        # Mock CalDAV client
        mock_client = Mock()
        mock_client.add_event.return_value = "server-assigned-uid"
        mock_caldav_class.return_value = mock_client

        args = argparse.Namespace(
            title="Test Event",
            start="2026-01-20 14:00:00",
            end=None,
            description=None,
            location=None,
            all_day=False,
        )

        handle_add_command(args)

        # Get the Event object
        event = mock_client.add_event.call_args[0][0]

        # Verify event has a UID (should be a UUID)
        assert event.uid is not None
        assert len(event.uid) > 0
        # UUID format check (basic - should have hyphens)
        assert "-" in event.uid
