"""Test script to verify CalDAV connection.

This script uses the configuration from ~/.config/justcal/config.toml
Run 'justcal config --init' first to set up credentials.
"""

import sys

sys.path.insert(0, "src")

from just_cal.config import Config
from just_cal.caldav_client import CalDAVClient

# Load configuration from ~/.config/justcal/config.toml
config = Config()
try:
    config.load()
except Exception as e:
    print(f"✗ Failed to load configuration: {e}")
    print("Run 'justcal config --init' to set up credentials")
    sys.exit(1)

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
