"""Tests for CLI interface."""

from unittest.mock import MagicMock, patch

import pytest

from just_cal.cli import handle_config_command, main
from just_cal.exceptions import ConfigurationError


@patch("just_cal.cli.Config")
def test_handle_config_init(mock_config_class):
    """Test config --init command."""
    mock_config = MagicMock()
    mock_config_class.return_value = mock_config

    args = MagicMock()
    args.init = True
    args.show = False
    args.test = False
    args.set = None

    handle_config_command(args)

    mock_config.initialize_interactive.assert_called_once()


@patch("just_cal.cli.Config")
def test_handle_config_show(mock_config_class):
    """Test config --show command."""
    mock_config = MagicMock()
    mock_config.show.return_value = '[caldav]\nurl = "test"'
    mock_config_class.return_value = mock_config

    args = MagicMock()
    args.init = False
    args.show = True
    args.test = False
    args.set = None

    handle_config_command(args)

    mock_config.load.assert_called_once()
    mock_config.show.assert_called_once()


@patch("just_cal.cli.CalDAVClient")
@patch("just_cal.cli.Config")
def test_handle_config_test(mock_config_class, mock_client_class):
    """Test config --test command."""
    mock_config = MagicMock()
    mock_config_class.return_value = mock_config
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    args = MagicMock()
    args.init = False
    args.show = False
    args.test = True
    args.set = None

    handle_config_command(args)

    mock_config.load.assert_called_once()
    mock_client_class.assert_called_once_with(mock_config)
    mock_client.test_connection.assert_called_once()


@patch("just_cal.cli.Config")
def test_handle_config_set(mock_config_class):
    """Test config --set command."""
    mock_config = MagicMock()
    mock_config_class.return_value = mock_config

    args = MagicMock()
    args.init = False
    args.show = False
    args.test = False
    args.set = ["caldav.url", "https://example.com"]

    handle_config_command(args)

    mock_config.load.assert_called_once()
    mock_config.set.assert_called_once_with("caldav", "url", "https://example.com")
    mock_config.save.assert_called_once()


@patch("just_cal.cli.Config")
def test_handle_config_set_invalid_key(mock_config_class):
    """Test config --set with invalid key format."""
    mock_config = MagicMock()
    mock_config_class.return_value = mock_config

    args = MagicMock()
    args.init = False
    args.show = False
    args.test = False
    args.set = ["invalidkey", "value"]

    with pytest.raises(ValueError, match="Key must be in format 'section.key'"):
        handle_config_command(args)


@patch("sys.argv", ["justcal"])
def test_main_no_command(capsys):
    """Test main with no command shows help."""
    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "usage: justcal" in captured.out


@patch("sys.argv", ["justcal", "config", "--show"])
@patch("just_cal.cli.Config")
def test_main_config_show(mock_config_class):
    """Test main with config --show command."""
    mock_config = MagicMock()
    mock_config.show.return_value = '[caldav]\nurl = "test"'
    mock_config_class.return_value = mock_config

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    mock_config.load.assert_called_once()


@patch("sys.argv", ["justcal", "config", "--init"])
@patch("just_cal.cli.Config")
def test_main_config_init_error(mock_config_class, capsys):
    """Test main with config --init that raises error."""
    mock_config = MagicMock()
    mock_config.initialize_interactive.side_effect = ConfigurationError("Test error")
    mock_config_class.return_value = mock_config

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Test error" in captured.err


@patch("sys.argv", ["justcal", "config", "--show"])
@patch("just_cal.cli.Config")
def test_main_keyboard_interrupt(mock_config_class, capsys):
    """Test main handles KeyboardInterrupt."""
    mock_config = MagicMock()
    mock_config.load.side_effect = KeyboardInterrupt()
    mock_config_class.return_value = mock_config

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 130
    captured = capsys.readouterr()
    assert "Operation cancelled by user" in captured.err


@patch("sys.argv", ["justcal", "config", "--show"])
@patch("just_cal.cli.Config")
def test_main_unexpected_error(mock_config_class, capsys):
    """Test main handles unexpected errors."""
    mock_config = MagicMock()
    mock_config.load.side_effect = RuntimeError("Unexpected error")
    mock_config_class.return_value = mock_config

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Unexpected error: Unexpected error" in captured.err


@patch("sys.argv", ["justcal", "unknown"])
def test_main_unknown_command(capsys):
    """Test main with unknown command."""
    with pytest.raises(SystemExit) as exc_info:
        main()

    # argparse exits with code 2 for invalid arguments
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "invalid choice: 'unknown'" in captured.err
