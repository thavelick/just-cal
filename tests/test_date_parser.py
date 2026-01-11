"""Tests for date_parser module."""

from datetime import datetime
from zoneinfo import ZoneInfo

from freezegun import freeze_time

from just_cal.utils.date_parser import DateParser


class TestDateParser:
    """Tests for DateParser class."""

    def test_init_default_timezone(self):
        """Test DateParser initializes with default timezone."""
        parser = DateParser()
        assert parser.timezone == "America/New_York"

    def test_init_custom_timezone(self):
        """Test DateParser initializes with custom timezone."""
        parser = DateParser(timezone="Europe/London")
        assert parser.timezone == "Europe/London"

    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        parser = DateParser()
        assert parser.parse("") is None
        assert parser.parse("   ") is None

    def test_parse_none(self):
        """Test parsing None returns None."""
        parser = DateParser()
        assert parser.parse("") is None

    @freeze_time("2026-01-15 10:00:00")
    def test_parse_natural_language_tomorrow(self):
        """Test parsing 'tomorrow' returns correct date."""
        parser = DateParser()
        result = parser.parse("tomorrow")
        assert result is not None
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 16

    @freeze_time("2026-01-15 10:00:00")
    def test_parse_natural_language_tomorrow_at_time(self):
        """Test parsing 'tomorrow at 3pm' returns correct datetime."""
        parser = DateParser()
        result = parser.parse("tomorrow at 3pm")
        assert result is not None
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 16
        assert result.hour == 15
        assert result.minute == 0

    @freeze_time("2026-01-15 10:00:00")
    def test_parse_natural_language_next_week(self):
        """Test parsing 'next week' returns future date."""
        parser = DateParser()
        result = parser.parse("next week")
        assert result is not None
        # Create timezone-aware datetime for comparison
        comparison_date = datetime(2026, 1, 15, 10, 0, 0, tzinfo=ZoneInfo("America/New_York"))
        assert result > comparison_date

    @freeze_time("2026-01-15 10:00:00")
    def test_parse_natural_language_in_two_days(self):
        """Test parsing 'in 2 days' returns correct date."""
        parser = DateParser()
        result = parser.parse("in 2 days")
        assert result is not None
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 17
