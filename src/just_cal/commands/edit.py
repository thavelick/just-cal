"""Edit command for updating existing calendar events."""

import argparse

from just_cal.caldav_client import CalDAVClient
from just_cal.config import Config
from just_cal.exceptions import JustCalError
from just_cal.utils.date_parser import DateParser


def handle_edit_command(args: argparse.Namespace) -> None:
    """Handle the edit command.

    Args:
        args: Parsed command-line arguments containing:
            - event_id: UID of the event to edit (required)
            - title: New title (optional)
            - start: New start date/time (optional)
            - end: New end date/time (optional)
            - description: New description (optional)
            - location: New location (optional)
    """
    config = Config()
    config.load()
    timezone = config.get("preferences", "timezone", "America/New_York")
    date_parser = DateParser(timezone=timezone)

    client = CalDAVClient(config)
    client.connect()
    event = client.get_event_by_uid(args.event_id)

    changes = []

    # Update simple text fields
    for field in ("title", "description", "location"):
        value = getattr(args, field)
        if value is not None:
            setattr(event, field, value)
            changes.append(f"{field} -> {value}")

    # Update date/time fields
    for field, arg_value in [("start", args.start), ("end", args.end)]:
        if arg_value is not None:
            parsed_dt = date_parser.parse(arg_value)
            if not parsed_dt:
                raise JustCalError(f"Invalid {field} date/time: {arg_value}")
            setattr(event, field, parsed_dt)
            changes.append(f"{field} -> {parsed_dt}")

    if not changes:
        print("No changes specified. Use -t, -s, -e, -d, or -l to update fields.")
        return

    client.update_event(args.event_id, event)

    print(f"✓ Event updated successfully: {event.title}")
    print(f"  UID: {args.event_id}")
    print("\nChanges:")
    for change in changes:
        print(f"  - {change}")
