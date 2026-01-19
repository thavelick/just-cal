"""Output formatting utilities for displaying events."""

import json

from just_cal.event import Event


def event_to_dict(event: Event) -> dict:
    """Convert an event to a dictionary for JSON output.

    Args:
        event: Event to convert

    Returns:
        Dictionary representation of the event
    """
    return {
        "uid": event.uid,
        "title": event.title,
        "start": event.start.isoformat(),
        "end": event.end.isoformat(),
        "description": event.description,
        "location": event.location,
        "all_day": event.all_day,
    }


def print_events_json(events: list[Event]) -> None:
    """Print events in JSON format.

    Args:
        events: List of events to print
    """
    events_data = [event_to_dict(event) for event in events]
    print(json.dumps(events_data, indent=2))


def format_time_range(event: Event) -> str:
    """Format the time range for an event.

    Returns:
        Formatted string showing when the event occurs:
        - All-day events: "Sat, 2026-01-10 - Mon, 2026-01-12"
        - Same-day timed events: "Sun, 2026-01-11 07:00 PM - 08:00 PM"
        - Multi-day timed events: "Sat, 2026-01-10 7:00 PM - Mon, 2026-01-12 9:00 AM"
    """
    if event.all_day:
        start_str = event.start.strftime("%a, %Y-%m-%d")
        end_str = event.end.strftime("%a, %Y-%m-%d")
        return f"{start_str} - {end_str}"

    same_day = event.start.date() == event.end.date()

    if same_day:
        date_str = event.start.strftime("%a, %Y-%m-%d")
        start_time = event.start.strftime("%I:%M %p").lstrip("0")
        end_time = event.end.strftime("%I:%M %p").lstrip("0")
        return f"{date_str} {start_time} - {end_time}"

    # Multi-day timed event
    start_str = event.start.strftime("%a, %Y-%m-%d %I:%M %p").replace(" 0", " ")
    end_str = event.end.strftime("%a, %Y-%m-%d %I:%M %p").replace(" 0", " ")
    return f"{start_str} - {end_str}"


def print_events_table(events: list[Event], use_when_column: bool = True) -> None:
    """Print events in table format.

    Args:
        events: List of events to print
        use_when_column: If True, use consolidated WHEN column (for list command).
                        If False, use separate START/END columns (for search command).
    """
    if not events:
        print("No events found.")
        return

    uid_width = 12
    title_width = max(min(max(len(e.title) for e in events), 40), 5)

    if use_when_column:
        when_width = max(max(len(format_time_range(e)) for e in events), 4)
        print(
            f"{'UID':<{uid_width}} {'TITLE':<{title_width}} {'WHEN':<{when_width}} {'LOCATION':<20}"
        )
        print("-" * (uid_width + title_width + when_width + 35))

        for event in events:
            uid = event.uid[:uid_width]
            title = event.title[:title_width]
            when = format_time_range(event)
            location = (event.location or "")[:20]
            print(f"{uid:<{uid_width}} {title:<{title_width}} {when:<{when_width}} {location:<20}")
    else:
        print(
            f"{'UID':<{uid_width}} {'TITLE':<{title_width}} "
            f"{'START':<20} {'END':<20} {'LOCATION':<20}"
        )
        print("-" * (uid_width + title_width + 65))

        for event in events:
            uid = event.uid[:uid_width]
            title = event.title[:title_width]
            location = (event.location or "")[:20]

            if event.all_day:
                start_str = event.start.strftime("%Y-%m-%d")
                end_str = event.end.strftime("%Y-%m-%d")
            else:
                start_str = event.start.strftime("%Y-%m-%d %H:%M")
                end_str = event.end.strftime("%Y-%m-%d %H:%M")

            print(
                f"{uid:<{uid_width}} {title:<{title_width}} {start_str:<20} "
                f"{end_str:<20} {location:<20}"
            )

    print(f"\nTotal: {len(events)} event(s)")
