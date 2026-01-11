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
