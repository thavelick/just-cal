"""Pytest configuration and shared fixtures.

Network Isolation:
    pytest-socket is configured to allow socket creation (for library capability
    detection) but block actual network connections during tests. This prevents
    tests from making real network calls while allowing libraries like urllib3
    to query system capabilities at import time.

    All tests should mock external dependencies rather than making real network calls.
"""

# Import caldav BEFORE pytest-socket activates to allow urllib3's capability detection
# This must happen at module level, before any pytest hooks run
import caldav  # noqa: F401
