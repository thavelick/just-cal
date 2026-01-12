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
        "mondays": "MO",
        "mon": "MO",
        "tuesday": "TU",
        "tuesdays": "TU",
        "tue": "TU",
        "wednesday": "WE",
        "wednesdays": "WE",
        "wed": "WE",
        "thursday": "TH",
        "thursdays": "TH",
        "thu": "TH",
        "friday": "FR",
        "fridays": "FR",
        "fri": "FR",
        "saturday": "SA",
        "saturdays": "SA",
        "sat": "SA",
        "sunday": "SU",
        "sundays": "SU",
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

        # Parse "weekly on <day>" or "weekly on <day> and <day>"
        if pattern_lower.startswith("weekly on "):
            day_part = pattern_lower.replace("weekly on ", "").strip()

            # Handle multiple days separated by "and"
            if " and " in day_part:
                day_names = [d.strip() for d in day_part.split(" and ")]
                day_abbrs: list[str] = []
                for d in day_names:
                    abbr = cls.DAYS.get(d)
                    if abbr:
                        day_abbrs.append(abbr)
                    else:
                        # Invalid day name, return None
                        return None

                # All days are valid
                return f"FREQ=WEEKLY;BYDAY={','.join(day_abbrs)}"
            else:
                # Single day
                day_abbr = cls.DAYS.get(day_part)
                if day_abbr:
                    return f"FREQ=WEEKLY;BYDAY={day_abbr}"

        # Parse "monthly on the <day>" - supports both "15th" and "3rd Wednesday"
        if pattern_lower.startswith("monthly on the "):
            day_part = pattern_lower.replace("monthly on the ", "").strip()

            # Check if it contains a weekday (e.g., "3rd Wednesday")
            # Look for ordinals: 1st, 2nd, 3rd, 4th, etc.
            ordinal_map = {
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

            # Try to parse as "Nth weekday"
            for ordinal, pos in ordinal_map.items():
                if day_part.startswith(ordinal + " "):
                    weekday_name = day_part[len(ordinal) + 1 :].strip()
                    weekday_abbr = cls.DAYS.get(weekday_name)
                    if weekday_abbr:
                        return f"FREQ=MONTHLY;BYDAY={weekday_abbr};BYSETPOS={pos}"

            # Try to parse as simple day number (e.g., "15th")
            day_num_str = (
                day_part.replace("st", "")
                .replace("nd", "")
                .replace("rd", "")
                .replace("th", "")
                .strip()
            )
            try:
                day_num = int(day_num_str)
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
