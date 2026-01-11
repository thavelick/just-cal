#!/usr/bin/env python3
"""Command-line interface for justcal."""

import argparse
import sys
from typing import NoReturn

from just_cal.config import Config
from just_cal.exceptions import JustCalError


def main() -> NoReturn:
    """Main entry point for the justcal CLI."""
    parser = argparse.ArgumentParser(
        prog="justcal",
        description="A Python CLI utility for managing Nextcloud calendars via CalDAV",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add subcommand
    add_parser = subparsers.add_parser("add", help="Add a new event")
    add_parser.add_argument("-t", "--title", required=True, help="Event title")
    add_parser.add_argument(
        "-s", "--start", required=True, help="Start date/time (natural language or ISO format)"
    )
    add_parser.add_argument(
        "-e", "--end", help="End date/time (optional, defaults to start + 1 hour)"
    )
    add_parser.add_argument("-d", "--description", help="Event description")
    add_parser.add_argument("-l", "--location", help="Event location")
    add_parser.add_argument("--all-day", action="store_true", help="Create all-day event")

    # List subcommand
    list_parser = subparsers.add_parser("list", help="List events")
    list_parser.add_argument(
        "--from",
        dest="from_date",
        help="Start of range (default: today, supports natural language)",
    )
    list_parser.add_argument("--to", dest="to_date", help="End of range (default: 7 days from now)")
    list_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    list_parser.add_argument("-n", "--limit", type=int, help="Limit number of results")

    # Search subcommand
    search_parser = subparsers.add_parser("search", help="Search events")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--field",
        choices=["title", "description", "location", "all"],
        default="all",
        help="Search field (default: all)",
    )
    search_parser.add_argument(
        "--from", dest="from_date", help="Start of date range (supports natural language)"
    )
    search_parser.add_argument("--to", dest="to_date", help="End of date range")
    search_parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )

    # Config subcommand
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_group = config_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument(
        "--init", action="store_true", help="Initialize configuration interactively"
    )
    config_group.add_argument("--show", action="store_true", help="Display current configuration")
    config_group.add_argument("--test", action="store_true", help="Test CalDAV connection")
    config_group.add_argument(
        "--set", nargs=2, metavar=("KEY", "VALUE"), help="Set configuration value"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "add":
            from just_cal.commands.add import handle_add_command

            handle_add_command(args)
        elif args.command == "list":
            from just_cal.commands.list import handle_list_command

            handle_list_command(args)
        elif args.command == "search":
            from just_cal.commands.search import handle_search_command

            handle_search_command(args)
        elif args.command == "config":
            handle_config_command(args)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)
    except JustCalError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


def handle_config_command(args: argparse.Namespace) -> None:
    """Handle config subcommand."""
    if args.init:
        config = Config()
        config.initialize_interactive()
        print("Configuration initialized successfully")
    elif args.show:
        config = Config()
        config.load()
        print(config.show())
    elif args.test:
        from just_cal.caldav_client import CalDAVClient

        config = Config()
        config.load()
        client = CalDAVClient(config)
        client.test_connection()
        print("Connection successful!")
    elif args.set:
        key, value = args.set
        # Parse key as section.key format
        if "." not in key:
            raise ValueError(f"Key must be in format 'section.key', got: {key}")
        section, key_name = key.split(".", 1)

        config = Config()
        config.load()
        config.set(section, key_name, value)
        config.save()
        print(f"Configuration updated: {key} = {value}")


if __name__ == "__main__":
    main()
