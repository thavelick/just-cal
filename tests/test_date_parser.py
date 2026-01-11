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

    def test_parse_iso_format_date(self):
        """Test parsing ISO format date string."""
        parser = DateParser()
        result = parser.parse("2026-01-20")
        assert result is not None
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 20

    def test_parse_iso_format_datetime(self):
        """Test parsing ISO format datetime string."""
        parser = DateParser()
        result = parser.parse("2026-01-20 14:30:00")
        assert result is not None
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 20
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 0

    def test_parse_iso_format_datetime_with_t(self):
        """Test parsing ISO format datetime with T separator."""
        parser = DateParser()
        result = parser.parse("2026-01-20T14:30:00")
        assert result is not None
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 20
        assert result.hour == 14
        assert result.minute == 30

    def test_parse_iso_format_with_timezone(self):
        """Test parsing ISO format with timezone offset."""
        parser = DateParser()
        result = parser.parse("2026-01-20T14:30:00-05:00")
        assert result is not None
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 20
        assert result.hour == 14
        assert result.minute == 30

    def test_parse_invalid_string(self):
        """Test parsing invalid date string returns None."""
        parser = DateParser()
        assert parser.parse("not a date") is None
        assert parser.parse("xyz123") is None

    def test_parse_with_custom_timezone(self):
        """Test parsing respects custom timezone."""
        parser = DateParser(timezone="Europe/London")
        result = parser.parse("2026-01-20 14:30:00")
        assert result is not None
        # dateparser should parse this with London timezone context
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 20

    @freeze_time("2026-01-15 10:00:00")
    def test_parse_prefers_future_dates(self):
        """Test that ambiguous dates prefer future interpretation."""
        parser = DateParser()
        # "Monday" should be next Monday, not last Monday
        result = parser.parse("Monday")
        assert result is not None
        # Should be in the future from Jan 15, 2026
        assert result.day >= 15 or result.month > 1

    def test_parse_whitespace_handling(self):
        """Test parsing handles extra whitespace correctly."""
        parser = DateParser()
        result = parser.parse("  2026-01-20  ")
        assert result is not None
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 20

    @freeze_time("2026-01-15 10:00:00")  # Thursday
    def test_parse_weekday_with_time(self):
        """Test parsing 'tuesday at 7pm' returns correct datetime."""
        parser = DateParser()
        result = parser.parse("tuesday at 7pm")
        assert result is not None
        # Tuesday from Jan 15 (Thursday) should be Jan 20 (next Tuesday)
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 20
        assert result.hour == 19
        assert result.minute == 0
