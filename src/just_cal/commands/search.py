"""Search command for finding calendar events."""

import argparse
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from just_cal.caldav_client import CalDAVClient
from just_cal.config import Config
from just_cal.event import Event
from just_cal.exceptions import JustCalError
from just_cal.utils.date_parser import DateParser

TEN_YEARS_IN_DAYS = 365 * 10


def _parse_date_range(
    args: argparse.Namespace, date_parser: DateParser, timezone: str
) -> tuple[datetime, datetime]:
    """Parse and normalize the date range from command arguments.

    Returns a tuple of (from_dt, to_dt) with sensible defaults applied.
    """
    from_dt: datetime | None = None
    to_dt: datetime | None = None

    if args.from_date:
        from_dt = date_parser.parse(args.from_date)
        if not from_dt:
            raise JustCalError(f"Invalid from date: {args.from_date}")

    if args.to_date:
        to_dt = date_parser.parse(args.to_date)
        if not to_dt:
            raise JustCalError(f"Invalid to date: {args.to_date}")

    if from_dt and to_dt:
        return from_dt, to_dt

    if from_dt:
        return from_dt, from_dt + timedelta(days=TEN_YEARS_IN_DAYS)

    if to_dt:
        return to_dt - timedelta(days=TEN_YEARS_IN_DAYS), to_dt

    tz = ZoneInfo(timezone)
    now = datetime.now(tz=tz)
    return now - timedelta(days=365), now + timedelta(days=365)


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
    config = Config()
    config.load()
    timezone = config.get("preferences", "timezone", "America/New_York")

    date_parser = DateParser(timezone=timezone)
    from_dt, to_dt = _parse_date_range(args, date_parser, timezone)

    client = CalDAVClient(config)
    client.connect()

    all_events = client.list_events(from_dt, to_dt)
    events = _filter_events(all_events, args.query, args.field)

    if args.format == "json":
        _print_json(events)
    else:
        _print_table(events)


def _matches_field(event: Event, query_lower: str, field: str) -> bool:
    """Check if an event matches the search query in the specified field."""
    if field == "title":
        return query_lower in event.title.lower()
    if field == "description":
        return bool(event.description and query_lower in event.description.lower())
    if field == "location":
        return bool(event.location and query_lower in event.location.lower())
    if field == "all":
        return (
            query_lower in event.title.lower()
            or (event.description is not None and query_lower in event.description.lower())
            or (event.location is not None and query_lower in event.location.lower())
        )
    return False


def _filter_events(events: list[Event], query: str, field: str) -> list[Event]:
    """Filter events by search query.

    Args:
        events: List of events to filter
        query: Search query (case-insensitive)
        field: Field to search in - 'title', 'description', 'location', or 'all'

    Returns:
        List of events matching the query
    """
    query_lower = query.lower()
    return [event for event in events if _matches_field(event, query_lower, field)]


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


def _print_table(events: list[Event]) -> None:
    """Print events in table format."""
    if not events:
        print("No events found.")
        return

    uid_width = 12
    title_width = min(max(len(e.title) for e in events), 40)
    title_width = max(title_width, 5)

    print(
        f"{'UID':<{uid_width}} {'TITLE':<{title_width}} {'START':<20} {'END':<20} {'LOCATION':<20}"
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
