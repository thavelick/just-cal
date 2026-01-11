"""Tests for Config management."""

from pathlib import Path
from unittest.mock import patch

import pytest

from just_cal.config import Config
from just_cal.exceptions import ConfigurationError


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file path."""
    return tmp_path / "config.toml"


@pytest.fixture
def sample_config_data():
    """Sample configuration data."""
    return {
        "caldav": {
            "url": "https://example.com/dav",
            "username": "testuser",
            "password": "",
            "calendar": "Personal",
        },
        "preferences": {
            "default_duration": 60,
            "timezone": "America/New_York",
            "date_format": "%Y-%m-%d %H:%M",
        },
        "security": {
            "use_keyring": True,
        },
    }


def test_config_initialization():
    """Test Config initialization with default path."""
    config = Config()
    assert config.config_path == Path.home() / ".config" / "justcal" / "config.toml"
    assert config.data == {}


def test_config_initialization_with_custom_path():
    """Test Config initialization with custom path."""
    custom_path = Path("/tmp/test.toml")
    config = Config(config_path=custom_path)
    assert config.config_path == custom_path


def test_config_load_nonexistent_file():
    """Test loading config when file doesn't exist raises error."""
    config = Config(config_path=Path("/nonexistent/config.toml"))

    with pytest.raises(ConfigurationError, match="Configuration not found"):
        config.load()


def test_config_load_success(temp_config_file, sample_config_data):
    """Test successfully loading configuration."""
    # Create a temporary config file
    import tomli_w

    with open(temp_config_file, "wb") as f:
        tomli_w.dump(sample_config_data, f)

    config = Config(config_path=temp_config_file)
    config.load()

    assert config.data == sample_config_data
    assert config.get("caldav", "url") == "https://example.com/dav"


def test_config_save(temp_config_file, sample_config_data):
    """Test saving configuration."""
    config = Config(config_path=temp_config_file)
    config.data = sample_config_data
    config.save()

    # Verify file was created
    assert temp_config_file.exists()

    # Verify file permissions (600)
    file_stat = temp_config_file.stat()
    assert file_stat.st_mode & 0o777 == 0o600

    # Verify content
    import tomli

    with open(temp_config_file, "rb") as f:
        loaded_data = tomli.load(f)
    assert loaded_data == sample_config_data


def test_config_get():
    """Test getting configuration values."""
    config = Config()
    config.data = {
        "section1": {"key1": "value1", "key2": "value2"},
        "section2": {"key3": "value3"},
    }

    assert config.get("section1", "key1") == "value1"
    assert config.get("section1", "key2") == "value2"
    assert config.get("section2", "key3") == "value3"
    assert config.get("nonexistent", "key") is None
    assert config.get("section1", "nonexistent", "default") == "default"


def test_config_set():
    """Test setting configuration values."""
    config = Config()

    config.set("caldav", "url", "https://test.com")
    assert config.data == {"caldav": {"url": "https://test.com"}}

    config.set("caldav", "username", "testuser")
    assert config.data == {"caldav": {"url": "https://test.com", "username": "testuser"}}

    config.set("preferences", "timezone", "UTC")
    assert config.data["preferences"] == {"timezone": "UTC"}


@patch("just_cal.config.keyring")
def test_get_password_from_keyring(mock_keyring):
    """Test getting password from keyring."""
    mock_keyring.get_password.return_value = "test-password"

    config = Config()
    config.data = {
        "caldav": {"username": "testuser"},
        "security": {"use_keyring": True},
    }

    password = config.get_password()

    assert password == "test-password"
    mock_keyring.get_password.assert_called_once_with("justcal", "testuser")


@patch("just_cal.config.keyring")
def test_get_password_from_config(mock_keyring):
    """Test getting password from config file when keyring returns None."""
    mock_keyring.get_password.return_value = None

    config = Config()
    config.data = {
        "caldav": {"username": "testuser", "password": "config-password"},
        "security": {"use_keyring": True},
    }

    password = config.get_password()

    assert password == "config-password"


def test_get_password_no_username():
    """Test getting password when username is not configured."""
    config = Config()
    config.data = {"caldav": {}}

    with pytest.raises(ConfigurationError, match="Username not configured"):
        config.get_password()


@patch("just_cal.config.keyring")
def test_get_password_not_found(mock_keyring):
    """Test getting password when it's not in keyring or config."""
    mock_keyring.get_password.return_value = None

    config = Config()
    config.data = {
        "caldav": {"username": "testuser", "password": ""},
        "security": {"use_keyring": True},
    }

    with pytest.raises(ConfigurationError, match="Password not found"):
        config.get_password()


@patch("just_cal.config.keyring")
def test_set_password_to_keyring(mock_keyring):
    """Test setting password to keyring."""
    config = Config()
    config.data = {
        "caldav": {"username": "testuser"},
        "security": {"use_keyring": True},
    }

    config.set_password("my-password")

    mock_keyring.set_password.assert_called_once_with("justcal", "testuser", "my-password")
    assert config.get("caldav", "password") == ""


@patch("just_cal.config.keyring")
def test_set_password_keyring_fails(mock_keyring, capsys):
    """Test setting password falls back to config when keyring fails."""
    mock_keyring.set_password.side_effect = Exception("Keyring not available")

    config = Config()
    config.data = {
        "caldav": {"username": "testuser"},
        "security": {"use_keyring": True},
    }

    config.set_password("my-password")

    # Should fall back to storing in config
    assert config.get("caldav", "password") == "my-password"

    # Should print warning
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "Keyring not available" in captured.out


def test_set_password_no_username():
    """Test setting password when username is not configured."""
    config = Config()
    config.data = {"caldav": {}}

    with pytest.raises(ConfigurationError, match="Username must be set"):
        config.set_password("password")


def test_show_config(sample_config_data):
    """Test displaying configuration (with password masked)."""
    config = Config()
    config.data = sample_config_data.copy()
    config.data["caldav"]["password"] = "secret-password"

    output = config.show()

    assert "secret-password" not in output
    assert "***" in output
    assert "https://example.com/dav" in output
    assert "testuser" in output


@patch("just_cal.config.keyring")
@patch("getpass.getpass")
@patch("builtins.input")
def test_initialize_interactive_with_valid_input(
    mock_input, mock_getpass, mock_keyring, temp_config_file
):
    """Test interactive initialization with valid input."""
    # Mock user inputs
    mock_input.side_effect = [
        "https://nextcloud.example.com/remote.php/dav",  # URL
        "testuser",  # username
        "Personal",  # calendar
        "America/New_York",  # timezone
    ]
    mock_getpass.return_value = "testpassword"

    config = Config(config_path=temp_config_file)
    config.initialize_interactive()

    # Verify config was saved
    assert temp_config_file.exists()

    # Verify password was stored in keyring
    mock_keyring.set_password.assert_called_once_with("justcal", "testuser", "testpassword")

    # Verify config data
    assert config.get("caldav", "url") == "https://nextcloud.example.com/remote.php/dav"
    assert config.get("caldav", "username") == "testuser"
    assert config.get("caldav", "calendar") == "Personal"
    assert config.get("preferences", "timezone") == "America/New_York"
    assert config.get("caldav", "password") == ""  # Should be empty when using keyring


@patch("just_cal.config.keyring")
@patch("getpass.getpass")
@patch("builtins.input")
def test_initialize_interactive_with_defaults(
    mock_input, mock_getpass, mock_keyring, temp_config_file
):
    """Test interactive initialization using default values."""
    # Mock user inputs (empty strings to use defaults)
    mock_input.side_effect = [
        "",  # URL (should use default)
        "testuser",  # username
        "",  # calendar (should use default "Personal")
        "",  # timezone (should use default "America/New_York")
    ]
    mock_getpass.return_value = "testpassword"

    config = Config(config_path=temp_config_file)
    config.initialize_interactive()

    # Verify defaults were used
    assert config.get("caldav", "url") == "https://nextcloud.example.com/remote.php/dav"
    assert config.get("caldav", "username") == "testuser"
    assert config.get("caldav", "calendar") == "Personal"
    assert config.get("preferences", "timezone") == "America/New_York"


@patch("getpass.getpass")
@patch("builtins.input")
def test_initialize_interactive_empty_username(mock_input, mock_getpass, temp_config_file):
    """Test interactive initialization fails with empty username."""
    mock_input.side_effect = [
        "https://nextcloud.example.com/remote.php/dav",  # URL
        "",  # Empty username
    ]
    mock_getpass.return_value = "testpassword"

    config = Config(config_path=temp_config_file)

    with pytest.raises(ConfigurationError, match="Username is required"):
        config.initialize_interactive()


@patch("getpass.getpass")
@patch("builtins.input")
def test_initialize_interactive_empty_password(mock_input, mock_getpass, temp_config_file):
    """Test interactive initialization fails with empty password."""
    mock_input.side_effect = [
        "https://nextcloud.example.com/remote.php/dav",  # URL
        "testuser",  # username
    ]
    mock_getpass.return_value = ""  # Empty password

    config = Config(config_path=temp_config_file)

    with pytest.raises(ConfigurationError, match="Password is required"):
        config.initialize_interactive()


@patch("just_cal.config.keyring")
@patch("getpass.getpass")
@patch("builtins.input")
def test_initialize_interactive_keyring_failure(
    mock_input, mock_getpass, mock_keyring, temp_config_file, capsys
):
    """Test interactive initialization handles keyring failure by falling back to config file."""
    # Mock keyring to fail
    mock_keyring.set_password.side_effect = Exception("Keyring not available")

    mock_input.side_effect = [
        "https://nextcloud.example.com/remote.php/dav",  # URL
        "testuser",  # username
        "Personal",  # calendar
        "America/New_York",  # timezone
    ]
    mock_getpass.return_value = "testpassword"

    config = Config(config_path=temp_config_file)
    config.initialize_interactive()

    # Verify password was stored in config file as fallback
    assert config.get("caldav", "password") == "testpassword"

    # Verify warning was printed
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "Keyring not available" in captured.out
