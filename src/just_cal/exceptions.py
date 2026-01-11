"""Custom exceptions for justcal."""


class JustCalError(Exception):
    """Base exception for justcal."""
    pass


class ConfigurationError(JustCalError):
    """Configuration related errors."""
    pass


class AuthenticationError(JustCalError):
    """CalDAV authentication failures."""
    pass


class ConnectionError(JustCalError):
    """Network/connection issues."""
    pass


class EventNotFoundError(JustCalError):
    """Event not found."""
    pass


class InvalidDateError(JustCalError):
    """Date parsing errors."""
    pass
