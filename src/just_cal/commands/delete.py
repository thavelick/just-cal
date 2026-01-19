"""Delete command for removing calendar events."""

import argparse

from just_cal.caldav_client import CalDAVClient
from just_cal.config import Config


def handle_delete_command(args: argparse.Namespace) -> None:
    """Handle the delete command.

    Args:
        args: Parsed command-line arguments containing:
            - event_id: UID of the event to delete (required)
            - yes: Skip confirmation prompt (optional)
    """
    config = Config()
    config.load()

    client = CalDAVClient(config)
    client.connect()

    event = client.get_event_by_uid(args.event_id)

    if not args.yes:
        print(f"Delete event: {event.title}")
        print(f"  UID: {args.event_id}")
        print(f"  Start: {event.start}")
        print(f"  End: {event.end}")
        if event.description:
            print(f"  Description: {event.description}")
        if event.location:
            print(f"  Location: {event.location}")
        print()

        response = input("Are you sure you want to delete this event? (y/N): ")
        if response.lower() not in ("y", "yes"):
            print("Deletion cancelled.")
            return

    client.delete_event(args.event_id)

    print(f"✓ Event deleted successfully: {event.title}")
    print(f"  UID: {args.event_id}")
