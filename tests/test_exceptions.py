"""Tests for custom exceptions."""

import pytest

from just_cal.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    EventNotFoundError,
    InvalidDateError,
    JustCalError,
)


def test_just_cal_error_is_exception():
    """Test that JustCalError is an Exception."""
    assert issubclass(JustCalError, Exception)


def test_configuration_error_is_just_cal_error():
    """Test that ConfigurationError inherits from JustCalError."""
    assert issubclass(ConfigurationError, JustCalError)


def test_authentication_error_is_just_cal_error():
    """Test that AuthenticationError inherits from JustCalError."""
    assert issubclass(AuthenticationError, JustCalError)


def test_connection_error_is_just_cal_error():
    """Test that ConnectionError inherits from JustCalError."""
    assert issubclass(ConnectionError, JustCalError)


def test_event_not_found_error_is_just_cal_error():
    """Test that EventNotFoundError inherits from JustCalError."""
    assert issubclass(EventNotFoundError, JustCalError)


def test_invalid_date_error_is_just_cal_error():
    """Test that InvalidDateError inherits from JustCalError."""
    assert issubclass(InvalidDateError, JustCalError)


def test_raise_configuration_error():
    """Test raising ConfigurationError."""
    with pytest.raises(ConfigurationError, match="test message"):
        raise ConfigurationError("test message")


def test_raise_authentication_error():
    """Test raising AuthenticationError."""
    with pytest.raises(AuthenticationError, match="auth failed"):
        raise AuthenticationError("auth failed")


def test_raise_connection_error():
    """Test raising ConnectionError."""
    with pytest.raises(ConnectionError, match="connection failed"):
        raise ConnectionError("connection failed")


def test_raise_event_not_found_error():
    """Test raising EventNotFoundError."""
    with pytest.raises(EventNotFoundError, match="event not found"):
        raise EventNotFoundError("event not found")


def test_raise_invalid_date_error():
    """Test raising InvalidDateError."""
    with pytest.raises(InvalidDateError, match="invalid date"):
        raise InvalidDateError("invalid date")
