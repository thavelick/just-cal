"""Search command for finding calendar events."""

import argparse
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from just_cal.caldav_client import CalDAVClient
from just_cal.config import Config
from just_cal.exceptions import JustCalError
from just_cal.utils.date_parser import DateParser


def handle_search_command(args: argparse.Namespace) -> None:
    """Handle the search command.

    Args:
        args: Parsed command-line arguments containing:
            - query: Search query string (required)
            - field: Field to search in - 'title', 'description', 'location', or 'all'
            - from_date: Start of date range (optional)
            - to_date: End of date range (optional)
            - format: Output format - 'table' or 'json' (default: table)
    """
    # Load configuration for timezone
    config = Config()
    config.load()
    timezone = config.get("preferences", "timezone", "America/New_York")

    # Parse dates if provided
    date_parser = DateParser(timezone=timezone)

    # Default date range to all time if not specified
    from_dt = None
    to_dt = None

    if args.from_date:
        from_dt = date_parser.parse(args.from_date)
        if not from_dt:
            raise JustCalError(f"Invalid from date: {args.from_date}")

    if args.to_date:
        to_dt = date_parser.parse(args.to_date)
        if not to_dt:
            raise JustCalError(f"Invalid to date: {args.to_date}")

    # If only one date is specified, create a reasonable range
    if from_dt and not to_dt:
        # Search from specified date to far future
        to_dt = from_dt + timedelta(days=365 * 10)  # 10 years ahead
    elif to_dt and not from_dt:
        # Search from far past to specified date
        from_dt = to_dt - timedelta(days=365 * 10)  # 10 years back

    # If no dates specified, use a wide range (past 1 year to future 1 year)
    if not from_dt and not to_dt:
        tz = ZoneInfo(timezone)
        now = datetime.now(tz=tz)
        from_dt = now - timedelta(days=365)
        to_dt = now + timedelta(days=365)

    # Connect to CalDAV and fetch events in date range
    client = CalDAVClient(config)
    client.connect()

    # Ensure dates are set (they should always be set by this point)
    assert from_dt is not None, "from_dt should be set"
    assert to_dt is not None, "to_dt should be set"

    # Get events in the specified date range
    all_events = client.list_events(from_dt, to_dt)

    # Filter events by search query
    events = _filter_events(all_events, args.query, args.field)

    # Format output (reuse list command formatters)
    if args.format == "json":
        _print_json(events)
    else:
        _print_table(events)


def _filter_events(events: list, query: str, field: str) -> list:
    """Filter events by search query.

    Args:
        events: List of events to filter
        query: Search query (case-insensitive)
        field: Field to search in - 'title', 'description', 'location', or 'all'

    Returns:
        List of events matching the query
    """
    query_lower = query.lower()
    filtered = []

    for event in events:
        match = False

        if field == "all":
            # Search in all fields
            if query_lower in event.title.lower():
                match = True
            elif event.description and query_lower in event.description.lower():
                match = True
            elif event.location and query_lower in event.location.lower():
                match = True
        elif field == "title":
            match = query_lower in event.title.lower()
        elif field == "description":
            match = event.description and query_lower in event.description.lower()
        elif field == "location":
            match = event.location and query_lower in event.location.lower()

        if match:
            filtered.append(event)

    return filtered


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
        start_str = event.start.strftime("%Y-%m-%d %H:%M")
        end_str = event.end.strftime("%Y-%m-%d %H:%M")
        location = (event.location or "")[:20]

        print(
            f"{uid:<{uid_width}} {title:<{title_width}} {start_str:<20} "
            f"{end_str:<20} {location:<20}"
        )

    print(f"\nTotal: {len(events)} event(s)")
