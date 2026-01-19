"""Recurrence pattern parsing for calendar events."""


def _build_day_abbreviations() -> dict[str, str]:
    """Build dictionary mapping day names/variants to RRULE abbreviations."""
    days_data = [
        ("MO", ["monday", "mondays", "mon"]),
        ("TU", ["tuesday", "tuesdays", "tue"]),
        ("WE", ["wednesday", "wednesdays", "wed"]),
        ("TH", ["thursday", "thursdays", "thu"]),
        ("FR", ["friday", "fridays", "fri"]),
        ("SA", ["saturday", "saturdays", "sat"]),
        ("SU", ["sunday", "sundays", "sun"]),
    ]
    result: dict[str, str] = {}
    for abbr, variants in days_data:
        for variant in variants:
            result[variant] = abbr
    return result


class RecurrenceParser:
    """Parser for natural language recurrence patterns to RRULE format."""

    PATTERNS = {
        "daily": "FREQ=DAILY",
        "weekly": "FREQ=WEEKLY",
        "monthly": "FREQ=MONTHLY",
        "yearly": "FREQ=YEARLY",
        "weekdays": "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR",
        "weekends": "FREQ=WEEKLY;BYDAY=SA,SU",
    }

    DAYS = _build_day_abbreviations()

    ORDINALS = {
        "1st": 1,
        "first": 1,
        "2nd": 2,
        "second": 2,
        "3rd": 3,
        "third": 3,
        "4th": 4,
        "fourth": 4,
        "5th": 5,
        "fifth": 5,
        "last": -1,
    }

    INTERVAL_UNITS = {
        "day": "DAILY",
        "week": "WEEKLY",
        "month": "MONTHLY",
        "year": "YEARLY",
    }

    @classmethod
    def parse(cls, pattern: str | None) -> str | None:
        """Parse recurrence pattern to RRULE format.

        Args:
            pattern: Recurrence pattern (natural language or RRULE)

        Returns:
            RRULE string or None if invalid

        Examples:
            "daily" -> "FREQ=DAILY"
            "weekly on Monday" -> "FREQ=WEEKLY;BYDAY=MO"
            "monthly on the 15th" -> "FREQ=MONTHLY;BYMONTHDAY=15"
            "FREQ=DAILY;COUNT=10" -> "FREQ=DAILY;COUNT=10" (passthrough)
        """
        if not pattern:
            return None

        normalized = pattern.lower().strip()

        if pattern.upper().startswith("FREQ="):
            return pattern.upper()

        if normalized in cls.PATTERNS:
            return cls.PATTERNS[normalized]

        if normalized.startswith("weekly on "):
            return cls._parse_weekly_on(normalized[10:])

        if normalized.startswith("monthly on the "):
            return cls._parse_monthly_on(normalized[15:])

        if normalized.startswith("every "):
            return cls._parse_interval(normalized)

        return None

    @classmethod
    def _parse_weekly_on(cls, day_part: str) -> str | None:
        """Parse 'weekly on <day>' or 'weekly on <day> and <day>' patterns."""
        day_part = day_part.strip()

        if " and " in day_part:
            day_names = [d.strip() for d in day_part.split(" and ")]
            day_abbrs = [cls.DAYS.get(name) for name in day_names]
            if None in day_abbrs:
                return None
            return f"FREQ=WEEKLY;BYDAY={','.join(day_abbrs)}"  # type: ignore[arg-type]

        day_abbr = cls.DAYS.get(day_part)
        if day_abbr:
            return f"FREQ=WEEKLY;BYDAY={day_abbr}"
        return None

    @classmethod
    def _parse_monthly_on(cls, day_part: str) -> str | None:
        """Parse 'monthly on the <day>' patterns (e.g., '15th' or '3rd Wednesday')."""
        day_part = day_part.strip()

        for ordinal, position in cls.ORDINALS.items():
            if day_part.startswith(ordinal + " "):
                weekday_name = day_part[len(ordinal) + 1 :].strip()
                weekday_abbr = cls.DAYS.get(weekday_name)
                if weekday_abbr:
                    return f"FREQ=MONTHLY;BYDAY={weekday_abbr};BYSETPOS={position}"

        day_num = cls._extract_day_number(day_part)
        if day_num is not None and 1 <= day_num <= 31:
            return f"FREQ=MONTHLY;BYMONTHDAY={day_num}"

        return None

    @classmethod
    def _parse_interval(cls, pattern: str) -> str | None:
        """Parse 'every <n> days/weeks/months' patterns."""
        parts = pattern.split()
        if len(parts) < 3:
            return None

        try:
            interval = int(parts[1])
        except ValueError:
            return None

        unit = parts[2].rstrip("s")
        freq = cls.INTERVAL_UNITS.get(unit)
        if freq:
            return f"FREQ={freq};INTERVAL={interval}"
        return None

    @staticmethod
    def _extract_day_number(text: str) -> int | None:
        """Extract numeric day from ordinal text (e.g., '15th' -> 15)."""
        cleaned = (
            text.replace("st", "").replace("nd", "").replace("rd", "").replace("th", "").strip()
        )
        try:
            return int(cleaned)
        except ValueError:
            return None
