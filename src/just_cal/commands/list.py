"""List command for displaying calendar events."""

import argparse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from just_cal.caldav_client import CalDAVClient
from just_cal.config import Config
from just_cal.exceptions import JustCalError
from just_cal.utils.date_parser import DateParser
from just_cal.utils.output import print_events_json, print_events_table


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
        print_events_json(events)
    else:
        print_events_table(events, use_when_column=True)
