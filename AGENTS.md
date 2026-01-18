# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**just-cal** is a Python CLI utility for managing Nextcloud calendars via CalDAV. It provides natural language date parsing, secure credential storage, and comprehensive calendar operations.

**Tech Stack:**
- CalDAV: `python-caldav` (Nextcloud-tested)
- CLI: `argparse` (standard library)
- Date Parsing: `dateparser` (natural language support)
- Config: TOML format (`tomli`/`tomli-w`)
- Security: `keyring` (system keychain integration)
- Testing: `pytest` with coverage

## Development Commands

### Setup and Dependencies
```bash
make setup          # Install dependencies with uv sync
make update         # Update all dependencies
uv add <package>    # Add runtime dependency
uv add --dev <pkg>  # Add dev dependency
```

### Running Tests
```bash
make test                    # Run all tests (65 tests currently)
make test-coverage          # Run with coverage report (target: >90%)
uv run pytest tests/        # Run all tests directly
uv run pytest tests/test_caldav_client.py  # Run single test file
uv run pytest tests/test_caldav_client.py::test_connect_success  # Run single test
uv run pytest -k "search"   # Run tests matching pattern
```

### Linting and Formatting
```bash
make lint           # Run ruff + pyright type checking
make lint-fix       # Auto-fix issues with ruff
make format         # Format code with ruff
uv run ruff check src/ tests/              # Lint specific directories
uv run ruff check --fix src/ tests/        # Auto-fix linting issues
uv run pyright src/ tests/                 # Type check
```

**Important:** Use `uv run` prefix for all Python tools to ensure proper virtual environment usage.

### Cleaning
```bash
make clean          # Remove __pycache__, .pytest_cache, etc.
```

## Architecture

### Core Components

**config.py** - Configuration management
- Loads/saves TOML config from `~/.config/justcal/config.toml`
- Integrates with system keyring for secure password storage
- Note: `initialize_interactive()` exists but not yet wired to CLI

**caldav_client.py** - CalDAV operations wrapper
- Wraps `python-caldav` library for Nextcloud communication
- Stores `_caldav_object` reference on events returned from CalDAV for later update/delete operations

**event.py** - Event model
- Event dataclass with iCalendar format conversion using `icalendar` library

**exceptions.py** - Custom exception hierarchy
- All custom exceptions inherit from `JustCalError` base class

**cli.py** - Command-line interface (currently minimal)
- Entry point defined in pyproject.toml
- Will route to commands in `commands/` directory (not yet implemented)

### Data Flow

```
CLI (cli.py)
  ↓
Config (config.py) ← reads ~/.config/justcal/config.toml
  ↓                 ← gets password from system keyring
CalDAVClient (caldav_client.py) ← uses python-caldav library
  ↓
Event (event.py) ← converts to/from iCalendar format
  ↓
Nextcloud CalDAV Server
```

### Configuration

Config file location: `~/.config/justcal/config.toml`

```toml
[caldav]
url = "https://nextcloud.example.com/remote.php/dav"
username = "username"
password = ""  # Empty = use keyring (recommended)
calendar = "Personal"

[preferences]
default_duration = 60  # minutes
timezone = "America/New_York"
date_format = "%Y-%m-%d %H:%M"

[security]
use_keyring = true  # Store password in system keychain
```

Password security: Passwords stored in system keyring by default. Config file gets 600 permissions on save.

## Project Rules

### Linting and Code Quality

**NEVER ignore linting errors by adding them to ignore lists.**

If you encounter a linting issue:
1. **First choice:** Fix it immediately if straightforward
2. **NEVER:** Add it to ignore list in pyproject.toml or suppress with comments

Only acceptable ignores:
- Genuine false positives across entire codebase
- Style preferences conflicting with formatter (e.g., E501 line length)

### Exception Handling

Always use proper exception chaining with `from e`:
```python
try:
    risky_operation()
except Exception as e:
    raise CustomError(f"Operation failed: {e}") from e
```

This fixes B904 linting errors and preserves stack traces.

### Don't Build Features Prematurely

Follow YAGNI (You Aren't Gonna Need It):
- Don't add parameters for future features (like `recurrence_mode` before Phase 7)
- Don't raise `NotImplementedError` for unbuilt features
- Don't write code that isn't needed yet
- Add features when they're actually being implemented

Example of what NOT to do:
```python
def delete_event(self, uid: str, recurrence_mode: str = "all"):
    if recurrence_mode != "all":
        raise NotImplementedError("Coming in Phase 7")
    # ... actual implementation
```

Better: Remove the parameter entirely until Phase 7.
