"""List command for displaying calendar events."""

import argparse
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from just_cal.caldav_client import CalDAVClient
from just_cal.config import Config
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


def _print_json(events: list) -> None:
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


def _print_table(events: list) -> None:
    """Print events in table format."""
    if not events:
        print("No events found.")
        return

    # Calculate column widths
    title_width = max(len(e.title) for e in events) if events else 10
    title_width = max(title_width, 5)  # Minimum width for "TITLE" header
    title_width = min(title_width, 40)  # Maximum width to avoid super wide tables

    uid_width = 12  # Show first 12 characters of UID

    # Print header
    print(
        f"{'UID':<{uid_width}} {'TITLE':<{title_width}} {'START':<20} {'END':<20} {'LOCATION':<20}"
    )
    print("-" * (uid_width + title_width + 65))

    # Print events
    for event in events:
        uid = event.uid[:uid_width] if len(event.uid) > uid_width else event.uid
        title = event.title[:title_width] if len(event.title) > title_width else event.title

        # Format dates - show only date for all-day events, date + time for timed events
        if event.all_day:
            start_str = event.start.strftime("%Y-%m-%d")
            end_str = event.end.strftime("%Y-%m-%d")
        else:
            start_str = event.start.strftime("%Y-%m-%d %H:%M")
            end_str = event.end.strftime("%Y-%m-%d %H:%M")

        location = (event.location or "")[:20]

        print(
            f"{uid:<{uid_width}} {title:<{title_width}} {start_str:<20} "
            f"{end_str:<20} {location:<20}"
        )

    print(f"\nTotal: {len(events)} event(s)")
