"""Pytest configuration and shared fixtures.

Network Isolation:
    pytest-socket is configured to allow socket creation (for library capability
    detection) but block actual network connections during tests. This prevents
    tests from making real network calls while allowing libraries like urllib3
    to query system capabilities at import time.

    All tests should mock external dependencies rather than making real network calls.
"""

from pathlib import Path
from unittest.mock import Mock

# Import caldav BEFORE pytest-socket activates to allow urllib3's capability detection
# This must happen at module level, before any pytest hooks run
import caldav  # noqa: F401
import pytest


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file path."""
    return tmp_path / "config.toml"


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
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


@pytest.fixture
def mock_config():
    """Create a mock Config object with standard test settings.

    This fixture provides a Config mock configured with:
    - CalDAV URL: https://example.com/dav
    - Username: testuser
    - Password: testpass
    - Calendar: Personal
    - Timezone: America/New_York
    - Default duration: 60 minutes

    The mock's get() method uses side_effect to return appropriate values
    based on section and key parameters.
    """
    config = Mock()
    config.config_path = Path.home() / ".config" / "justcal" / "config.toml"
    config.load = Mock()
    config.get.side_effect = lambda section, key, default=None: {
        ("caldav", "url"): "https://example.com/dav",
        ("caldav", "username"): "testuser",
        ("caldav", "calendar"): "Personal",
        ("preferences", "timezone"): "America/New_York",
        ("preferences", "default_duration"): 60,
        ("preferences", "date_format"): "%Y-%m-%d %H:%M",
    }.get((section, key), default)
    config.get_password.return_value = "testpass"
    return config


@pytest.fixture
def mock_caldav_client(mock_config):
    """Create a mock CalDAVClient with standard configuration.

    Returns a Mock object configured to behave like a CalDAVClient.
    The client has connect(), add_event(), list_events(), and other
    common methods pre-configured as mocks.
    """
    client = Mock()
    client.config = mock_config
    client.client = None
    client.calendar = None
    client.connect = Mock()
    client.add_event = Mock(return_value="test-uid-123")
    client.list_events = Mock(return_value=[])
    client.search_events = Mock(return_value=[])
    client.get_event_by_uid = Mock()
    client.update_event = Mock()
    client.delete_event = Mock()
    return client
