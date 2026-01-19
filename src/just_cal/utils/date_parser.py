"""Natural language date parsing utilities."""

from datetime import datetime

import dateparser


class DateParser:
    """Parse natural language and ISO format dates."""

    def __init__(self, timezone: str = "America/New_York") -> None:
        """Initialize date parser with timezone."""
        self.timezone = timezone

    def parse(self, date_string: str) -> datetime | None:
        """Parse natural language or ISO dates.

        Args:
            date_string: Date string to parse (e.g., "tomorrow at 3pm", "2026-01-20 14:00")

        Returns:
            Parsed datetime object, or None if parsing fails
        """
        if not date_string or not date_string.strip():
            return None

        result = dateparser.parse(
            date_string,
            settings={
                "PREFER_DATES_FROM": "future",
                "TIMEZONE": self.timezone,
                "RETURN_AS_TIMEZONE_AWARE": True,
            },
        )
        if result:
            return result

        try:
            return datetime.fromisoformat(date_string)
        except (ValueError, TypeError):
            return None
