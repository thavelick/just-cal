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
    # Load configuration
    config = Config()
    config.load()
    timezone = config.get("preferences", "timezone", "America/New_York")

    # Connect to CalDAV and fetch the event
    client = CalDAVClient(config)
    client.connect()

    event = client.get_event_by_uid(args.event_id)

    # Track if any changes were made
    changes = []

    # Update title if provided
    if args.title is not None:
        event.title = args.title
        changes.append(f"title -> {args.title}")

    # Update description if provided
    if args.description is not None:
        event.description = args.description
        changes.append(f"description -> {args.description}")

    # Update location if provided
    if args.location is not None:
        event.location = args.location
        changes.append(f"location -> {args.location}")

    # Parse and update dates if provided
    date_parser = DateParser(timezone=timezone)

    if args.start is not None:
        start_dt = date_parser.parse(args.start)
        if not start_dt:
            raise JustCalError(f"Invalid start date/time: {args.start}")
        event.start = start_dt
        changes.append(f"start -> {start_dt}")

    if args.end is not None:
        end_dt = date_parser.parse(args.end)
        if not end_dt:
            raise JustCalError(f"Invalid end date/time: {args.end}")
        event.end = end_dt
        changes.append(f"end -> {end_dt}")

    # Check if any changes were made
    if not changes:
        print("No changes specified. Use -t, -s, -e, -d, or -l to update fields.")
        return

    # Save changes
    client.update_event(args.event_id, event)

    # Display success message
    print(f"✓ Event updated successfully: {event.title}")
    print(f"  UID: {args.event_id}")
    print("\nChanges:")
    for change in changes:
        print(f"  - {change}")
