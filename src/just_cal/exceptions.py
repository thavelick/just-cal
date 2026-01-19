"""Custom exceptions for justcal."""


class JustCalError(Exception):
    """Base exception for justcal."""


class ConfigurationError(JustCalError):
    """Raised for configuration-related errors."""


class AuthenticationError(JustCalError):
    """Raised for CalDAV authentication failures."""


class ConnectionError(JustCalError):
    """Raised for network or connection issues."""


class EventNotFoundError(JustCalError):
    """Raised when a requested event cannot be found."""


class InvalidDateError(JustCalError):
    """Raised for date parsing errors."""
