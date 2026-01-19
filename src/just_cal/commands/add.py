"""Add command for creating calendar events."""

import argparse
from datetime import timedelta

from just_cal.caldav_client import CalDAVClient
from just_cal.config import Config
from just_cal.event import Event
from just_cal.exceptions import JustCalError
from just_cal.utils.date_parser import DateParser
from just_cal.utils.recurrence_parser import RecurrenceParser
from just_cal.utils.validators import validate_non_empty


def handle_add_command(args: argparse.Namespace) -> None:
    """Handle the add command.

    Args:
        args: Parsed command-line arguments containing:
            - title: Event title (required)
            - start: Start date/time string (required)
            - end: End date/time string (optional)
            - description: Event description (optional)
            - location: Event location (optional)
            - all_day: Boolean flag for all-day events (optional)
            - recur: Recurrence pattern (optional)
    """
    # Validate required fields
    validate_non_empty(args.title, "Title")

    # Load configuration for timezone
    config = Config()
    config.load()
    timezone = config.get("preferences", "timezone", "America/New_York")

    # Parse dates
    date_parser = DateParser(timezone=timezone)

    start_dt = date_parser.parse(args.start)
    if not start_dt:
        raise JustCalError(f"Invalid start date/time: {args.start}")

    # Auto-detect all-day events when start time is midnight
    is_midnight = start_dt.hour == 0 and start_dt.minute == 0 and start_dt.second == 0
    is_all_day = args.all_day or is_midnight

    end_dt = None
    if args.end:
        end_dt = date_parser.parse(args.end)
        if not end_dt:
            raise JustCalError(f"Invalid end date/time: {args.end}")
    elif is_all_day:
        # For all-day events, end is same day (will be handled as 1-day event)
        end_dt = start_dt
    else:
        # Default end time to start + 1 hour
        default_duration = config.get("preferences", "default_duration", 60)
        end_dt = start_dt + timedelta(minutes=default_duration)

    # Parse recurrence pattern if provided
    recurrence = None
    if getattr(args, "recur", None):
        recurrence = RecurrenceParser.parse(args.recur)
        if not recurrence:
            raise JustCalError(f"Invalid recurrence pattern: {args.recur}")

    # Create event
    event = Event(
        uid=Event.generate_uid(),
        title=args.title,
        start=start_dt,
        end=end_dt,
        description=args.description,
        location=args.location,
        recurrence=recurrence,
        all_day=is_all_day,
    )

    # Connect to CalDAV and add event
    client = CalDAVClient(config)
    client.connect()
    event_uid = client.add_event(event)

    print(f"✓ Event created successfully: {args.title}")
    print(f"  UID: {event_uid}")
    print(f"  Start: {start_dt}")
    print(f"  End: {end_dt}")
    if is_all_day:
        print("  All-day event: Yes")
    if recurrence:
        print(f"  Recurrence: {recurrence}")
