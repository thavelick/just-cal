"""Pytest configuration and shared fixtures.

Network Isolation:
    pytest-socket is installed and will block all socket connections during tests
    by default. This prevents tests from making real network calls. Any test that
    attempts external connections will fail with a SocketBlockedError.

    To run tests with network access (not recommended for unit tests):
        pytest --disable-socket-allow-hosts=example.com

    All tests should mock external dependencies rather than making real network calls.
"""
