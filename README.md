# just-cal

A Python CLI utility for managing Nextcloud calendars via CalDAV.

## Current Status

**Phase 2 Complete** - Core infrastructure is implemented and tested. Configuration management and CalDAV connectivity are fully functional.

### Working Features
- ✅ Configuration management (`justcal config`)
- ✅ CalDAV connection testing
- ✅ Secure password storage (system keyring)

### Coming Soon
- 🚧 Add events (`justcal add`)
- 🚧 List events (`justcal list`)
- 🚧 Search events (`justcal search`)
- 🚧 Edit events (`justcal edit`)
- 🚧 Delete events (`justcal delete`)
- 🚧 Recurring events support

## Installation

### Prerequisites
- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/just-cal.git
cd just-cal

# Install dependencies
uv sync

# Install the CLI tool
uv pip install -e .
```

## Configuration

### Initial Setup

Configure just-cal to connect to your Nextcloud calendar:

```bash
justcal config --init
```

This will interactively prompt you for:
- CalDAV URL (e.g., `https://nextcloud.example.com/remote.php/dav`)
- Username
- Password (stored securely in system keychain)
- Calendar name (default: "Personal")
- Timezone (default: "America/New_York")

**Note:** If you have 2FA enabled on Nextcloud, create an app-specific password:
1. Go to Nextcloud → Settings → Security
2. Under "Devices & sessions", create a new app password
3. Use this password when configuring just-cal

### Configuration File

Configuration is stored at `~/.config/justcal/config.toml`:

```toml
[caldav]
url = "https://nextcloud.example.com/remote.php/dav"
username = "your-username"
password = ""  # Empty = password stored in system keyring
calendar = "Personal"

[preferences]
default_duration = 60  # minutes
timezone = "America/New_York"
date_format = "%Y-%m-%d %H:%M"

[security]
use_keyring = true  # Store password in system keychain
```

## Usage

### Configuration Commands

#### View Current Configuration
```bash
justcal config --show
```

Displays your current configuration with the password masked for security.

#### Test CalDAV Connection
```bash
justcal config --test
```

Verifies that just-cal can successfully connect to your Nextcloud calendar server.

#### Update Configuration Values
```bash
justcal config --set caldav.calendar "Work"
justcal config --set preferences.timezone "UTC"
justcal config --set preferences.default_duration 30
```

Updates individual configuration values. Key format is `section.key`.

#### Re-initialize Configuration
```bash
justcal config --init
```

Run the interactive setup again to reconfigure from scratch.

## Development

### Running Tests
```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
uv run pytest tests/test_config.py -v
```

### Linting and Formatting
```bash
# Check for linting issues
make lint

# Auto-fix linting issues
make lint-fix

# Format code
make format
```

### Project Management

This project uses `bd` (beads) for task tracking:

```bash
# View available tasks
bd ready

# View all tasks
bd list

# View specific task
bd show jc-123
```

## Technology Stack

- **CalDAV**: `python-caldav` (Nextcloud-tested)
- **CLI**: `argparse` (standard library)
- **Date Parsing**: `dateparser` (natural language support)
- **Config**: TOML format (`tomli`/`tomli-w`)
- **Security**: `keyring` (system keychain integration)
- **Testing**: `pytest` with coverage

## Roadmap

- **Phase 3**: Date/time utilities with natural language parsing
- **Phase 4**: Add command (basic events)
- **Phase 5**: List and search commands
- **Phase 6**: Edit and delete commands
- **Phase 7**: Recurring events support
- **Phase 8**: Polish and documentation

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run `make lint` and `make test`
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Troubleshooting

### Keyring Issues

If you encounter keyring errors during `--init`:
```
Warning: Failed to store password in keyring
```

The password will fall back to being stored in the config file. To enable keyring support, install a keyring backend:

```bash
# On Linux with GNOME Keyring
uv pip install keyring secretstorage

# On macOS (should work out of the box)
# Keyring uses the system Keychain

# On Windows (should work out of the box)
# Keyring uses Windows Credential Manager
```

### Connection Issues

If `justcal config --test` fails:

1. Verify your CalDAV URL is correct (should end with `/remote.php/dav`)
2. Check your username and password
3. If using 2FA, ensure you're using an app-specific password
4. Verify the calendar name exists in your Nextcloud instance

### Configuration Not Found

If you see "Configuration not found" errors, run:
```bash
justcal config --init
```

This will create a new configuration file at `~/.config/justcal/config.toml`.
