"""Tests for recurrence pattern parser."""

from just_cal.utils.recurrence_parser import RecurrenceParser


class TestRecurrenceParser:
    """Tests for RecurrenceParser class."""

    def test_parse_daily(self):
        """Test parsing 'daily' pattern."""
        assert RecurrenceParser.parse("daily") == "FREQ=DAILY"

    def test_parse_weekly(self):
        """Test parsing 'weekly' pattern."""
        assert RecurrenceParser.parse("weekly") == "FREQ=WEEKLY"

    def test_parse_monthly(self):
        """Test parsing 'monthly' pattern."""
        assert RecurrenceParser.parse("monthly") == "FREQ=MONTHLY"

    def test_parse_yearly(self):
        """Test parsing 'yearly' pattern."""
        assert RecurrenceParser.parse("yearly") == "FREQ=YEARLY"

    def test_parse_weekdays(self):
        """Test parsing 'weekdays' pattern."""
        assert RecurrenceParser.parse("weekdays") == "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR"

    def test_parse_weekends(self):
        """Test parsing 'weekends' pattern."""
        assert RecurrenceParser.parse("weekends") == "FREQ=WEEKLY;BYDAY=SA,SU"

    def test_parse_weekly_on_day(self):
        """Test parsing 'weekly on <day>' pattern."""
        assert RecurrenceParser.parse("weekly on Monday") == "FREQ=WEEKLY;BYDAY=MO"
        assert RecurrenceParser.parse("weekly on mon") == "FREQ=WEEKLY;BYDAY=MO"
        assert RecurrenceParser.parse("weekly on Friday") == "FREQ=WEEKLY;BYDAY=FR"
        assert RecurrenceParser.parse("weekly on fri") == "FREQ=WEEKLY;BYDAY=FR"

    def test_parse_monthly_on_day(self):
        """Test parsing 'monthly on the <day>' pattern."""
        assert RecurrenceParser.parse("monthly on the 15th") == "FREQ=MONTHLY;BYMONTHDAY=15"
        assert RecurrenceParser.parse("monthly on the 1") == "FREQ=MONTHLY;BYMONTHDAY=1"
        assert RecurrenceParser.parse("monthly on the 31") == "FREQ=MONTHLY;BYMONTHDAY=31"

    def test_parse_every_n_days(self):
        """Test parsing 'every <n> days' pattern."""
        assert RecurrenceParser.parse("every 2 days") == "FREQ=DAILY;INTERVAL=2"
        assert RecurrenceParser.parse("every 3 weeks") == "FREQ=WEEKLY;INTERVAL=3"
        assert RecurrenceParser.parse("every 6 months") == "FREQ=MONTHLY;INTERVAL=6"

    def test_parse_raw_rrule_passthrough(self):
        """Test that raw RRULE strings pass through unchanged."""
        assert RecurrenceParser.parse("FREQ=DAILY;COUNT=10") == "FREQ=DAILY;COUNT=10"
        assert RecurrenceParser.parse("FREQ=WEEKLY;BYDAY=MO,WE,FR") == "FREQ=WEEKLY;BYDAY=MO,WE,FR"
        assert (
            RecurrenceParser.parse("freq=daily;count=5") == "FREQ=DAILY;COUNT=5"
        )  # Case insensitive

    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        assert RecurrenceParser.parse("") is None
        assert RecurrenceParser.parse(None) is None

    def test_parse_invalid_pattern(self):
        """Test parsing invalid pattern returns None."""
        assert RecurrenceParser.parse("every Tuesday maybe") is None
        assert RecurrenceParser.parse("sometimes") is None
        assert RecurrenceParser.parse("xyz123") is None

    def test_parse_case_insensitive(self):
        """Test that parsing is case insensitive."""
        assert RecurrenceParser.parse("DAILY") == "FREQ=DAILY"
        assert RecurrenceParser.parse("Weekly") == "FREQ=WEEKLY"
        assert RecurrenceParser.parse("WEEKLY ON MONDAY") == "FREQ=WEEKLY;BYDAY=MO"

    def test_parse_weekly_on_multiple_days(self):
        """Test parsing 'weekly on <day> and <day>' patterns."""
        assert RecurrenceParser.parse("weekly on Sundays and Tuesdays") == "FREQ=WEEKLY;BYDAY=SU,TU"
        assert RecurrenceParser.parse("weekly on Monday and Friday") == "FREQ=WEEKLY;BYDAY=MO,FR"
        assert (
            RecurrenceParser.parse("weekly on Wednesdays and Saturdays")
            == "FREQ=WEEKLY;BYDAY=WE,SA"
        )

    def test_parse_monthly_on_nth_weekday(self):
        """Test parsing 'monthly on the Nth weekday' patterns."""
        assert (
            RecurrenceParser.parse("monthly on the 1st Monday")
            == "FREQ=MONTHLY;BYDAY=MO;BYSETPOS=1"
        )
        assert (
            RecurrenceParser.parse("monthly on the 2nd Tuesday")
            == "FREQ=MONTHLY;BYDAY=TU;BYSETPOS=2"
        )
        assert (
            RecurrenceParser.parse("monthly on the 3rd Wednesday")
            == "FREQ=MONTHLY;BYDAY=WE;BYSETPOS=3"
        )
        assert (
            RecurrenceParser.parse("monthly on the 4th Thursday")
            == "FREQ=MONTHLY;BYDAY=TH;BYSETPOS=4"
        )
        assert (
            RecurrenceParser.parse("monthly on the last Friday")
            == "FREQ=MONTHLY;BYDAY=FR;BYSETPOS=-1"
        )

    def test_parse_monthly_on_nth_weekday_text(self):
        """Test parsing 'monthly on the Nth weekday' with text ordinals."""
        assert (
            RecurrenceParser.parse("monthly on the first Monday")
            == "FREQ=MONTHLY;BYDAY=MO;BYSETPOS=1"
        )
        assert (
            RecurrenceParser.parse("monthly on the second Tuesday")
            == "FREQ=MONTHLY;BYDAY=TU;BYSETPOS=2"
        )
        assert (
            RecurrenceParser.parse("monthly on the third Wednesday")
            == "FREQ=MONTHLY;BYDAY=WE;BYSETPOS=3"
        )
