"""Recurrence pattern parsing for calendar events."""


class RecurrenceParser:
    """Parser for natural language recurrence patterns to RRULE format."""

    # Common pattern mappings
    PATTERNS = {
        "daily": "FREQ=DAILY",
        "weekly": "FREQ=WEEKLY",
        "monthly": "FREQ=MONTHLY",
        "yearly": "FREQ=YEARLY",
        "weekdays": "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR",
        "weekends": "FREQ=WEEKLY;BYDAY=SA,SU",
    }

    # Day abbreviations for BYDAY
    DAYS = {
        "monday": "MO",
        "mon": "MO",
        "tuesday": "TU",
        "tue": "TU",
        "wednesday": "WE",
        "wed": "WE",
        "thursday": "TH",
        "thu": "TH",
        "friday": "FR",
        "fri": "FR",
        "saturday": "SA",
        "sat": "SA",
        "sunday": "SU",
        "sun": "SU",
    }

    @classmethod
    def parse(cls, pattern: str | None) -> str | None:
        """Parse recurrence pattern to RRULE format.

        Args:
            pattern: Recurrence pattern (natural language or RRULE)

        Returns:
            RRULE string or None if invalid

        Examples:
            "daily" → "FREQ=DAILY"
            "weekly on Monday" → "FREQ=WEEKLY;BYDAY=MO"
            "monthly on the 15th" → "FREQ=MONTHLY;BYMONTHDAY=15"
            "FREQ=DAILY;COUNT=10" → "FREQ=DAILY;COUNT=10" (passthrough)
        """
        if not pattern:
            return None

        pattern_lower = pattern.lower().strip()

        # If it's already an RRULE (starts with FREQ=), pass through
        if pattern.upper().startswith("FREQ="):
            return pattern.upper()

        # Check for exact pattern matches
        if pattern_lower in cls.PATTERNS:
            return cls.PATTERNS[pattern_lower]

        # Parse "weekly on <day>"
        if pattern_lower.startswith("weekly on "):
            day_part = pattern_lower.replace("weekly on ", "").strip()
            day_abbr = cls.DAYS.get(day_part)
            if day_abbr:
                return f"FREQ=WEEKLY;BYDAY={day_abbr}"

        # Parse "monthly on the <day>"
        if pattern_lower.startswith("monthly on the "):
            day_part = pattern_lower.replace("monthly on the ", "").replace("th", "").strip()
            try:
                day_num = int(day_part)
                if 1 <= day_num <= 31:
                    return f"FREQ=MONTHLY;BYMONTHDAY={day_num}"
            except ValueError:
                pass

        # Parse "every <n> days/weeks/months"
        if pattern_lower.startswith("every "):
            parts = pattern_lower.split()
            if len(parts) >= 3:
                try:
                    interval = int(parts[1])
                    unit = parts[2].rstrip("s")  # Remove trailing 's'
                    freq_map = {
                        "day": "DAILY",
                        "week": "WEEKLY",
                        "month": "MONTHLY",
                        "year": "YEARLY",
                    }
                    if unit in freq_map:
                        return f"FREQ={freq_map[unit]};INTERVAL={interval}"
                except (ValueError, IndexError):
                    pass

        return None
