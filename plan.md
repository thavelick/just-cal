# justcal Implementation Plan

A Python CLI utility for managing Nextcloud calendars via CalDAV.

## Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| CalDAV Library | `python-caldav` | Active development, Nextcloud-tested, mature (v1.x until 2026-01) |
| CLI Framework | `argparse` | Standard library, zero external dependencies |
| Date Parsing | `dateparser` | Natural language support ("tomorrow at 3pm"), 200+ locales |
| Config Format | TOML | Human-readable, Python standard (`tomli`/`tomli-w`) |
| Password Storage | `keyring` | System keychain integration for secure credential storage |
| Testing | `pytest` | De-facto standard with comprehensive ecosystem |

**Dependencies:** `caldav`, `icalendar`, `dateparser`, `tomli`, `tomli-w`, `keyring`

## bd Basics

This project uses `bd` (beads) for issue tracking and task management:

- **View ready work:** `bd ready` - Shows tasks ready to work on (no blocking dependencies)
- **Task granularity:** Any task taking more than 2 minutes should be broken down into its own bd issue
- **Dependencies:** Manage task dependencies with `bd dep add <blocker> <blocked>` - the blocker must complete before the blocked task
- **Create tasks:** `bd create "Task description"` or `bd q "Task description"` (quick capture, outputs ID only)
- **Update status:** `bd update <id> --status in_progress` when starting, `bd close <id>` when done
- **View all tasks:** `bd list` or `bd list --status open`

During implementation, break down each phase into granular tasks and establish dependencies to ensure logical ordering.

## Project Structure

```
just-cal/
├── pyproject.toml              # uv project config, scripts entry point
├── README.md
├── .gitignore
├── src/just_cal/
│   ├── __init__.py
│   ├── __main__.py             # python -m just_cal entry point
│   ├── cli.py                  # CLI argument parsing, command routing
│   ├── config.py               # Configuration management, credential handling
│   ├── caldav_client.py        # CalDAV connection and operations
│   ├── event.py                # Event model, iCalendar conversion
│   ├── exceptions.py           # Custom exceptions (ConfigError, AuthError, etc.)
│   ├── commands/
│   │   ├── add.py              # Create events with recurrence support
│   │   ├── edit.py             # Update existing events
│   │   ├── delete.py           # Delete events (single/recurring)
│   │   ├── list.py             # List events in date range
│   │   └── search.py           # Search events by query
│   └── utils/
│       ├── date_parser.py      # Natural language date parsing
│       ├── validators.py       # Input validation
│       └── recurrence_parser.py # Recurrence rule parsing (Phase 7)
└── tests/
    ├── test_config.py
    ├── test_event.py
    ├── test_date_parser.py
    └── test_commands/
```

## Configuration

**Location:** `~/.config/justcal/config.toml`

```toml
[caldav]
url = "https://nextcloud.tristanhavelick.com/remote.php/dav"
username = "your-username"
password = ""  # Empty = use keyring (recommended)
calendar = "Personal"

[preferences]
default_duration = 60  # minutes
timezone = "America/New_York"
date_format = "%Y-%m-%d %H:%M"

[security]
use_keyring = true  # Store password in system keychain
```

**Security:** Password stored in system keyring by default. Config file gets 600 permissions. Support Nextcloud app passwords (recommended over main password).

## Command Interface

### Add Command
```bash
# Basic events (Phase 4)
justcal add -t "Team Meeting" -s "tomorrow at 2pm" -e "tomorrow at 3pm"
justcal add -t "Dentist" -s "2026-01-20 10:00" -l "123 Main St" -d "Annual checkup"
justcal add -t "Birthday" -s "2026-01-15" --all-day

# Recurring events (Phase 7)
justcal add -t "Daily Standup" -s "tomorrow at 9am" -r "FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR"

Options:
  -t, --title TEXT       Event title (required)
  -s, --start DATETIME   Start date/time (required, supports natural language)
  -e, --end DATETIME     End date/time (optional, defaults to start + 1 hour)
  -d, --description TEXT Event description
  -l, --location TEXT    Event location
  -r, --recur RRULE     Recurring rule (Phase 7) (e.g., "daily", "weekly", "FREQ=DAILY;COUNT=10")
  --all-day             Create all-day event
```

### List Command
```bash
justcal list
justcal list --from today --to "next month"
justcal list --format json
justcal list -n 10

Options:
  --from DATETIME        Start of range (default: today)
  --to DATETIME         End of range (default: 7 days from now)
  --format {table,json} Output format (default: table)
  -n, --limit INTEGER   Limit number of results
```

### Search Command
```bash
justcal search "meeting"
justcal search "dentist" --field location
justcal search "standup" --from "last week"

Options:
  --field {title,description,location,all}  Search field (default: all)
  --from DATETIME        Start of date range
  --to DATETIME         End of date range
  --format {table,json} Output format
```

### Edit Command
```bash
# Basic editing (Phase 6)
justcal edit EVENT_ID -t "Updated Meeting"
justcal edit EVENT_ID -s "tomorrow at 3pm"

# Recurrence editing (Phase 7)
justcal edit EVENT_ID --clear-recur

Options:
  -t, --title TEXT       New title
  -s, --start DATETIME   New start
  -e, --end DATETIME     New end
  -d, --description TEXT New description
  -l, --location TEXT    New location
  -r, --recur RRULE     New recurrence (Phase 7)
  --clear-recur         Remove recurrence (Phase 7)

Note: EVENT_ID obtained from list/search
```

### Delete Command
```bash
# Basic deletion (Phase 6)
justcal delete EVENT_ID
justcal delete EVENT_ID -y

# Recurring event deletion (Phase 7)
justcal delete EVENT_ID --this-instance "2026-01-20"

Options:
  -y, --yes                      Skip confirmation
  --this-instance DATETIME       Delete only this instance (Phase 7, recurring events)
  --this-and-future DATETIME     Delete this and future instances (Phase 7, recurring events)
```

### Config Command
```bash
justcal config --init              # Interactive setup
justcal config --show              # Display current config
justcal config --set caldav.calendar "Work"
justcal config --test              # Test CalDAV connection

Options:
  --init         Initialize configuration interactively
  --show         Display current configuration
  --set KEY VAL  Set configuration value
  --test         Test CalDAV connection
```

## Implementation Phases

**Note:** This plan is a reference document and does not need to be updated as work progresses. Use bd to track actual task completion.

### Phase 1: Project Setup
1. Copy this plan to `plan.md` in the project root for easy reference during implementation
2. `git init` in /home/tristan/Projects/just-cal
3. Create GitHub repository: `gh repo create just-cal --public --source=.`
4. Initialize bd: `bd init --prefix jc`
5. **Create high-level bd tasks for each phase:**
   ```bash
   bd create "Phase 1: Project Setup" -p 0
   bd create "Phase 2: Core Infrastructure" -p 0
   bd create "Phase 3: Date/Time Utilities" -p 0
   bd create "Phase 4: CLI Framework and Add Command (Basic)" -p 0
   bd create "Phase 5: List and Search Commands" -p 0
   bd create "Phase 6: Edit and Delete Commands (Basic)" -p 0
   bd create "Phase 7: Recurrence Support" -p 0
   bd create "Phase 8: Polish and Documentation" -p 0
   ```
6. **Establish phase dependencies:**
   ```bash
   # Get the IDs from bd list, then establish dependencies
   # Phase 2 blocks on Phase 1, Phase 3 blocks on Phase 2, etc.
   bd dep add jc-<phase1-id> jc-<phase2-id>
   bd dep add jc-<phase2-id> jc-<phase3-id>
   bd dep add jc-<phase3-id> jc-<phase4-id>
   bd dep add jc-<phase4-id> jc-<phase5-id>
   bd dep add jc-<phase5-id> jc-<phase6-id>
   bd dep add jc-<phase6-id> jc-<phase7-id>
   bd dep add jc-<phase7-id> jc-<phase8-id>
   ```
7. Initialize Python project: `uv init --lib`
8. Add dependencies: `uv add caldav icalendar dateparser tomli tomli-w keyring`
9. Add dev dependencies: `uv add --dev pytest pytest-cov pytest-mock freezegun`
10. Create project structure (directories, __init__.py files)
11. Configure `.gitignore` (Python, venv, *.toml config files)
12. Configure `pyproject.toml` with scripts entry point: `justcal = "justcal.cli:main"`

### Phase 2: Core Infrastructure
1. **config.py**: Configuration loading/saving, interactive setup, keyring integration
2. **event.py**: Event dataclass with to_ical/from_ical methods
3. **caldav_client.py**: Connection, authentication, calendar discovery
4. **exceptions.py**: Custom exceptions (ConfigurationError, AuthenticationError, etc.)
5. Test CalDAV connection with Nextcloud instance

### Phase 3: Date/Time Utilities
1. **utils/date_parser.py**: Natural language parsing with dateparser, ISO fallback
2. **utils/validators.py**: Input validation (dates, basic input sanitization)
3. Comprehensive unit tests for date parsing edge cases
4. Note: Recurrence handling deferred to Phase 7

### Phase 4: CLI Framework and Add Command (Basic)
1. **cli.py**: argparse-based CLI with subcommands, global options
2. **commands/add.py** (basic version, no recurrence):
   - Parse command-line arguments (title, start, end, description, location)
   - Parse dates with natural language support
   - Build Event object (without recurrence)
   - Call caldav_client.add_event()
3. Test basic add command end-to-end with Nextcloud

### Phase 5: List and Search Commands
1. **commands/list.py**:
   - Parse date range (--from, --to)
   - Fetch events from CalDAV
   - Format output (table by default, JSON optional)
2. **commands/search.py**:
   - Search by field (title, description, location, all)
   - Filter by date range
   - Format output
3. Test list and search functionality

### Phase 6: Edit and Delete Commands (Basic)
1. **commands/edit.py** (basic version, no recurrence):
   - Fetch event by ID
   - Update specified fields (title, start, end, description, location)
   - Save changes
2. **commands/delete.py** (basic version, simple deletion):
   - Fetch event by ID
   - Confirmation prompt (unless -y)
   - Delete event
3. Test edit and delete operations

### Phase 7: Recurrence Support
1. **utils/recurrence_parser.py**: New module for recurrence handling
   - Parse common patterns: "daily" → "FREQ=DAILY", "weekly on Monday" → "FREQ=WEEKLY;BYDAY=MO"
   - Allow raw RRULE strings for advanced users
   - Unit tests for recurrence parsing
2. **Update commands/add.py**: Add -r/--recur option, integrate recurrence parser
3. **Update commands/edit.py**: Add recurrence editing (--recur, --clear-recur)
4. **Update commands/delete.py**: Add recurring event deletion options (--this-instance, --this-and-future)
5. **Update event.py**: Enhance recurrence handling in to_ical/from_ical
6. Test recurring events end-to-end (create, list, edit, delete instances)

### Phase 8: Polish and Documentation
1. Error handling and user-friendly messages
2. Output formatting improvements (colors, tables)
3. README with installation, configuration, examples
4. Documentation for recurring events (recurring-events.md)
5. CI/CD with GitHub Actions (pytest, linting)

## Critical Files (Priority Order)

1. **src/just_cal/config.py** - Configuration management; required before any operations
2. **src/just_cal/caldav_client.py** - Core CalDAV operations; central integration with Nextcloud
3. **src/just_cal/event.py** - Event model; used by all commands
4. **src/just_cal/cli.py** - CLI routing; main entry point
5. **src/just_cal/utils/date_parser.py** - Date parsing; critical for user experience
6. **src/just_cal/commands/add.py** - Most complex command (date parsing, recurrence)

## Key Implementation Details

### Event Model (event.py)
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Event:
    uid: str
    title: str
    start: datetime
    end: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    recurrence: Optional[str] = None  # RRULE string
    all_day: bool = False

    def to_ical(self) -> str:
        """Convert to iCalendar format using icalendar library"""

    @classmethod
    def from_ical(cls, ical_data: str) -> 'Event':
        """Parse from iCalendar format"""
```

### CalDAV Client (caldav_client.py)
```python
import caldav

class CalDAVClient:
    def connect(self):
        """Establish connection using config credentials"""
        self.client = caldav.DAVClient(url=url, username=username, password=password)
        principal = self.client.principal()
        calendars = principal.calendars()
        self.calendar = self._find_calendar(calendars, calendar_name)

    def add_event(self, event: Event) -> str:
        """Add event, return UID"""

    def list_events(self, start: datetime, end: datetime) -> list[Event]:
        """List events in date range"""

    def search_events(self, query: str, field: str) -> list[Event]:
        """Search events by query"""

    def update_event(self, uid: str, event: Event):
        """Update existing event"""

    def delete_event(self, uid: str, recurrence_mode: str = 'all'):
        """Delete event (all, this, this-and-future)"""
```

### Date Parser (utils/date_parser.py)
```python
import dateparser

class DateParser:
    def parse(self, date_string: str) -> Optional[datetime]:
        """Parse natural language or ISO dates"""
        # Try dateparser with timezone settings
        dt = dateparser.parse(date_string, settings={
            'PREFER_DATES_FROM': 'future',
            'TIMEZONE': self.timezone,
            'RETURN_AS_TIMEZONE_AWARE': True
        })
        # Fallback to datetime.fromisoformat()
        return dt
```

### Recurrence Parsing
Map common patterns to RRULE:
- "daily" → "FREQ=DAILY"
- "weekly" → "FREQ=WEEKLY"
- "weekly on Monday" → "FREQ=WEEKLY;BYDAY=MO"
- "monthly on the 15th" → "FREQ=MONTHLY;BYMONTHDAY=15"
- Allow raw RRULE strings for advanced users

### Error Handling Strategy
- Catch `caldav.lib.error` exceptions → AuthenticationError, ConnectionError
- Validate dates before CalDAV operations → InvalidDateError
- User-friendly error messages with suggestions
- Exit codes: 0 (success), 1 (general error), 2 (config error), 3 (auth error)

## Nextcloud CalDAV Connection Details

- **URL format:** `https://nextcloud.tristanhavelick.com/remote.php/dav`
- **Authentication:** Nextcloud username/password (recommend app-specific password if 2FA enabled)
- **App password creation:** Settings → Security → Devices & sessions → Create new app password
- **Calendar discovery:** python-caldav auto-discovers calendars via CalDAV protocol
- **Default calendar:** Specify in config.toml (e.g., "Personal", "Work")

### Temporary Development Credentials

For development and testing, temporary credentials have been configured:
- **Username:** `claude`
- **Password:** `***********` (stored in `~/.config/justcal/config.toml`)
- **URL:** `https://nextcloud.tristanhavelick.com/remote.php/dav`

These credentials are specifically created for development. Feel free to create/delete test events as needed.

**Note:** The actual password is stored in the local config file at `~/.config/justcal/config.toml` and is not committed to the repository.

## Testing Strategy

### Unit Tests (pytest)
- Configuration: Load/save, validation, keyring integration
- Date parsing: Natural language, ISO format, edge cases, timezones
- Event model: to_ical/from_ical conversions, validation
- Recurrence parsing: Common patterns to RRULE

### Integration Tests
- Mock CalDAV server (python-caldav test utilities)
- Full command flows: add → list → edit → delete
- Authentication scenarios (valid, invalid, missing)
- Error handling (network failures, invalid inputs)
- Use `freezegun` for consistent datetime testing

### Manual Testing
1. Test `justcal config --init` for first-time setup
2. Test CalDAV connection: `justcal config --test`
3. Add events with various date formats: "tomorrow at 3pm", "2026-01-20 14:00"
4. Create recurring event: "daily standup"
5. List events: verify display formatting
6. Search events: verify search works across fields
7. Edit event: update title, time, location
8. Delete recurring event: test "this instance" vs "all"

## Verification Plan

After implementation:

1. **Setup verification:**
   ```bash
   cd /home/tristan/Projects/just-cal
   git status
   bd list
   uv sync
   justcal --version
   ```

2. **Configuration test:**
   ```bash
   justcal config --init
   # Enter Nextcloud credentials interactively
   justcal config --test
   # Should succeed with "Connection successful"
   ```

3. **Add event test:**
   ```bash
   justcal add -t "Test Event" -s "tomorrow at 2pm" -e "tomorrow at 3pm"
   # Should create event and return UID
   ```

4. **List event test:**
   ```bash
   justcal list
   # Should show "Test Event" in table format
   ```

5. **Search test:**
   ```bash
   justcal search "Test"
   # Should find "Test Event"
   ```

6. **Edit test:**
   ```bash
   justcal edit <UID> -t "Updated Test Event"
   justcal list
   # Should show updated title
   ```

7. **Delete test:**
   ```bash
   justcal delete <UID> -y
   justcal list
   # Should not show event anymore
   ```

8. **Recurring event test:**
   ```bash
   justcal add -t "Daily Standup" -s "tomorrow at 9am" -r "FREQ=DAILY;BYDAY=MO,TU,WE,TH,FR"
   justcal list --to "next week"
   # Should show multiple instances of Daily Standup
   ```

9. **Unit test execution:**
   ```bash
   uv run pytest tests/ -v
   # All tests should pass
   ```

10. **Verify with real Nextcloud:**
    - Open Nextcloud calendar web interface
    - Verify events created via CLI appear correctly
    - Verify edits and deletions sync properly

## Post-Implementation

- Create initial release: `gh release create v0.1.0`
- Set up GitHub Actions for CI (pytest, linting)
- Consider PyPI publication for easy installation: `uv pip install justcal`
- Document common issues and troubleshooting in README
