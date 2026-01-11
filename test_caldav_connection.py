"""Test script to verify CalDAV connection."""

import sys
sys.path.insert(0, 'src')

from just_cal.config import Config
from just_cal.caldav_client import CalDAVClient

# Create a test configuration with dev credentials
config = Config()
config.data = {
    "caldav": {
        "url": "https://nextcloud.tristanhavelick.com/remote.php/dav",
        "username": "claude",
        "password": "super-dooper,fun-pw-time",
        "calendar": "Personal",
    },
    "preferences": {
        "default_duration": 60,
        "timezone": "America/New_York",
        "date_format": "%Y-%m-%d %H:%M",
    },
    "security": {
        "use_keyring": False,  # Use password from config for testing
    },
}

print("Testing CalDAV connection...")
print(f"URL: {config.get('caldav', 'url')}")
print(f"Username: {config.get('caldav', 'username')}")

try:
    client = CalDAVClient(config)
    client.connect()
    print(f"✓ Successfully connected to CalDAV server")
    print(f"✓ Calendar: {client.calendar.name if client.calendar else 'None'}")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    sys.exit(1)

print("\n✓ Phase 2: Core Infrastructure - CalDAV connection test passed!")
