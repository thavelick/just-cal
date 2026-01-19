"""CalDAV client for interacting with Nextcloud calendars."""

from datetime import UTC, datetime, timedelta

import caldav

from .config import Config
from .event import Event
from .exceptions import AuthenticationError, ConnectionError, EventNotFoundError, JustCalError


class CalDAVClient:
    """Client for CalDAV operations."""

    def __init__(self, config: Config):
        """Initialize CalDAV client.

        Args:
            config: Configuration object
        """
        self.config = config
        self.client: caldav.DAVClient | None = None
        self.calendar: caldav.Calendar | None = None

    def connect(self) -> None:
        """Establish CalDAV connection.

        Raises:
            AuthenticationError: If authentication fails
            ConnectionError: If connection fails
        """
        url = self.config.get("caldav", "url")
        username = self.config.get("caldav", "username")

        try:
            password = self.config.get_password()
        except Exception as e:
            raise AuthenticationError(f"Failed to get password: {e}") from e

        if not url or not username:
            raise ConnectionError("CalDAV URL and username must be configured")

        try:
            self.client = caldav.DAVClient(url=url, username=username, password=password)

            # Test the connection by getting the principal
            principal = self.client.principal()

            # Get calendars
            calendars = principal.calendars()
            if not calendars:
                raise ConnectionError("No calendars found")

            # Find the specified calendar
            calendar_name = self.config.get("caldav", "calendar", "Personal")
            self.calendar = self._find_calendar(calendars, calendar_name)

            if not self.calendar:
                available = [cal.name for cal in calendars if cal.name]
                raise ConnectionError(
                    f"Calendar '{calendar_name}' not found. "
                    f"Available calendars: {', '.join(available)}"
                )

        except Exception as e:
            # Re-raise our custom exceptions
            if isinstance(e, (AuthenticationError, ConnectionError)):
                raise
            # Check if it's an authorization error from caldav library
            error_str = str(e).lower()
            error_type = str(type(e).__name__).lower()
            if "authorization" in error_type or "unauthorized" in error_str or "401" in error_str:
                raise AuthenticationError(f"Authentication failed: {e}") from e
            # All other exceptions become connection errors
            raise ConnectionError(f"Failed to connect to CalDAV server: {e}") from e

    def _find_calendar(
        self, calendars: list[caldav.Calendar], calendar_name: str
    ) -> caldav.Calendar | None:
        """Find a calendar by name.

        Args:
            calendars: List of calendars
            calendar_name: Name of calendar to find

        Returns:
            Calendar object or None if not found
        """
        return next((cal for cal in calendars if cal.name == calendar_name), None)

    def _require_connection(self) -> caldav.Calendar:
        """Ensure we have a valid calendar connection.

        Returns:
            The connected calendar object

        Raises:
            ConnectionError: If not connected
        """
        if not self.calendar:
            raise ConnectionError("Not connected. Call connect() first.")
        return self.calendar

    def add_event(self, event: Event) -> str:
        """Add event to calendar.

        Args:
            event: Event to add

        Returns:
            str: Event UID

        Raises:
            ConnectionError: If not connected or operation fails
        """
        calendar = self._require_connection()

        try:
            ical_data = event.to_ical()
            calendar.save_event(ical_data)
            return event.uid
        except Exception as e:
            raise ConnectionError(f"Failed to add event: {e}") from e

    def list_events(self, start: datetime, end: datetime) -> list[Event]:
        """List events in date range.

        Args:
            start: Start of date range
            end: End of date range

        Returns:
            List of events

        Raises:
            ConnectionError: If not connected or operation fails
        """
        calendar = self._require_connection()

        try:
            # Search for events in the date range
            events = calendar.search(start=start, end=end, event=True, expand=True)

            result = []
            for cal_event in events:
                try:
                    ical_data = cal_event.data
                    event = Event.from_ical(ical_data)
                    result.append(event)
                except Exception as e:
                    # Skip events that can't be parsed
                    print(f"Warning: Failed to parse event: {e}")

            # Sort events chronologically by start time
            # Handle both timezone-aware and naive datetimes
            def sort_key(event: Event) -> datetime:
                """Get sortable datetime, treating naive datetimes as UTC."""
                if event.start.tzinfo is None:
                    return event.start.replace(tzinfo=UTC)
                return event.start

            return sorted(result, key=sort_key)
        except Exception as e:
            raise ConnectionError(f"Failed to list events: {e}") from e

    def _event_matches_query(self, event: Event, query: str, field: str) -> bool:
        """Check if an event matches the search query.

        Args:
            event: Event to check
            query: Lowercase search query
            field: Field to search in (title, description, location, all)

        Returns:
            True if the event matches the query
        """
        if field == "title":
            return query in event.title.lower()
        if field == "description":
            return event.description is not None and query in event.description.lower()
        if field == "location":
            return event.location is not None and query in event.location.lower()
        # field == "all"
        return (
            query in event.title.lower()
            or (event.description is not None and query in event.description.lower())
            or (event.location is not None and query in event.location.lower())
        )

    def search_events(self, query: str, field: str = "all") -> list[Event]:
        """Search events by query.

        Args:
            query: Search query
            field: Field to search in (title, description, location, all)

        Returns:
            List of matching events

        Raises:
            ConnectionError: If not connected or operation fails
        """
        self._require_connection()

        try:
            # CalDAV doesn't have great search capabilities, so we search client-side
            start = datetime.now() - timedelta(days=365)
            end = datetime.now() + timedelta(days=365)
            all_events = self.list_events(start, end)

            query_lower = query.lower()
            return [e for e in all_events if self._event_matches_query(e, query_lower, field)]
        except Exception as e:
            raise ConnectionError(f"Failed to search events: {e}") from e

    def _parse_caldav_event(self, cal_event: caldav.CalendarObjectResource) -> Event | None:
        """Parse a CalDAV event and attach the caldav object reference.

        Args:
            cal_event: CalDAV event object

        Returns:
            Parsed Event with _caldav_object set, or None if parsing fails
        """
        try:
            event = Event.from_ical(cal_event.data)
            event._caldav_object = cal_event
            return event
        except Exception:
            return None

    def get_event_by_uid(self, uid: str) -> Event:
        """Get event by UID or partial UID.

        Supports both exact UID matches and partial UID prefixes (like git short hashes).
        If multiple events match the prefix, raises an error asking for more specificity.

        Args:
            uid: Event UID or UID prefix (minimum 8 characters for partial match)

        Returns:
            Event object

        Raises:
            EventNotFoundError: If event not found
            JustCalError: If partial UID matches multiple events
            ConnectionError: If operation fails
        """
        calendar = self._require_connection()

        try:
            # Try exact UID first (more efficient)
            try:
                cal_event = calendar.event_by_uid(uid)
                event = self._parse_caldav_event(cal_event)
                if event:
                    return event
            except Exception:
                pass

            # For partial matches, search through all events
            partial_matches = [
                event
                for cal_event in calendar.events()
                if (event := self._parse_caldav_event(cal_event)) and event.uid.startswith(uid)
            ]

            if not partial_matches:
                raise EventNotFoundError(f"Event with UID '{uid}' not found")
            if len(partial_matches) == 1:
                return partial_matches[0]

            matching_uids = [e.uid for e in partial_matches[:5]]
            raise JustCalError(
                f"Partial UID '{uid}' matches multiple events: {', '.join(matching_uids)}. "
                f"Please provide more characters."
            )

        except (EventNotFoundError, JustCalError):
            raise
        except Exception as e:
            raise ConnectionError(f"Failed to get event: {e}") from e

    def update_event(self, uid: str, updated_event: Event) -> None:
        """Update existing event.

        Args:
            uid: UID of event to update
            updated_event: Updated event data

        Raises:
            EventNotFoundError: If event not found
            ConnectionError: If operation fails
        """
        self._require_connection()

        try:
            # Get the original event
            original = self.get_event_by_uid(uid)

            # Delete the old event
            if hasattr(original, "_caldav_object"):
                original._caldav_object.delete()

            # Add the updated event with the same UID
            updated_event.uid = uid
            self.add_event(updated_event)
        except EventNotFoundError:
            raise
        except Exception as e:
            raise ConnectionError(f"Failed to update event: {e}") from e

    def delete_event(self, uid: str) -> None:
        """Delete event.

        Args:
            uid: UID of event to delete

        Raises:
            EventNotFoundError: If event not found
            ConnectionError: If operation fails
        """
        self._require_connection()

        try:
            event = self.get_event_by_uid(uid)

            if hasattr(event, "_caldav_object"):
                event._caldav_object.delete()
            else:
                raise ConnectionError("Event object doesn't have CalDAV reference")
        except EventNotFoundError:
            raise
        except Exception as e:
            raise ConnectionError(f"Failed to delete event: {e}") from e

    def test_connection(self) -> bool:
        """Test CalDAV connection.

        Returns:
            bool: True if connection successful

        Raises:
            AuthenticationError: If authentication fails
            ConnectionError: If connection fails
        """
        self.connect()
        return True
