"""List command for displaying calendar events."""

import argparse
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from just_cal.caldav_client import CalDAVClient
from just_cal.config import Config
from just_cal.event import Event
from just_cal.exceptions import JustCalError
from just_cal.utils.date_parser import DateParser


def handle_list_command(args: argparse.Namespace) -> None:
    """Handle the list command.

    Args:
        args: Parsed command-line arguments containing:
            - from_date: Start of date range (optional, default: today)
            - to_date: End of date range (optional, default: 7 days from now)
            - format: Output format - 'table' or 'json' (default: table)
            - limit: Maximum number of results (optional)
    """
    # Load configuration for timezone
    config = Config()
    config.load()
    timezone = config.get("preferences", "timezone", "America/New_York")

    # Parse dates
    date_parser = DateParser(timezone=timezone)

    # Default from_date to today
    if args.from_date:
        from_dt = date_parser.parse(args.from_date)
        if not from_dt:
            raise JustCalError(f"Invalid from date: {args.from_date}")
    else:
        # Default to start of today
        tz = ZoneInfo(timezone)
        from_dt = datetime.now(tz=tz).replace(hour=0, minute=0, second=0, microsecond=0)

    # Default to_date to 7 days from now
    if args.to_date:
        to_dt = date_parser.parse(args.to_date)
        if not to_dt:
            raise JustCalError(f"Invalid to date: {args.to_date}")
    else:
        # Default to end of 7 days from now
        to_dt = from_dt + timedelta(days=7)
        to_dt = to_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Connect to CalDAV and fetch events
    client = CalDAVClient(config)
    client.connect()
    events = client.list_events(from_dt, to_dt)

    # Apply limit if specified
    if args.limit:
        events = events[: args.limit]

    # Format output
    if args.format == "json":
        _print_json(events)
    else:
        _print_table(events)


def _print_json(events: list[Event]) -> None:
    """Print events in JSON format."""
    events_data = [
        {
            "uid": event.uid,
            "title": event.title,
            "start": event.start.isoformat(),
            "end": event.end.isoformat(),
            "description": event.description,
            "location": event.location,
            "all_day": event.all_day,
        }
        for event in events
    ]
    print(json.dumps(events_data, indent=2))


def _format_when_column(event: Event) -> str:
    """Format the WHEN column for an event.

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


def _print_table(events: list[Event]) -> None:
    """Print events in table format."""
    if not events:
        print("No events found.")
        return

    uid_width = 12
    title_width = min(max(len(e.title) for e in events), 40)
    title_width = max(title_width, 5)  # Minimum width for "TITLE" header
    when_width = max(len(_format_when_column(e)) for e in events)
    when_width = max(when_width, 4)  # Minimum width for "WHEN" header

    print(f"{'UID':<{uid_width}} {'TITLE':<{title_width}} {'WHEN':<{when_width}} {'LOCATION':<20}")
    print("-" * (uid_width + title_width + when_width + 35))

    for event in events:
        uid = event.uid[:uid_width]
        title = event.title[:title_width]
        when = _format_when_column(event)
        location = (event.location or "")[:20]

        print(f"{uid:<{uid_width}} {title:<{title_width}} {when:<{when_width}} {location:<20}")

    print(f"\nTotal: {len(events)} event(s)")
