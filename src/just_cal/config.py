"""Configuration management for justcal."""

import getpass
import os
from pathlib import Path
from typing import Any

import keyring
import tomli
import tomli_w

from .exceptions import ConfigurationError


class Config:
    """Manages justcal configuration."""

    DEFAULT_CONFIG_DIR = Path.home() / ".config" / "justcal"
    DEFAULT_CONFIG_FILE = "config.toml"

    DEFAULT_CONFIG = {
        "caldav": {
            "url": "",
            "username": "",
            "password": "",
            "calendar": "Personal",
        },
        "preferences": {
            "default_duration": 60,
            "timezone": "America/New_York",
            "date_format": "%Y-%m-%d %H:%M",
        },
        "security": {
            "use_keyring": True,
        },
    }

    def __init__(self, config_path: Path | None = None):
        """Initialize configuration.

        Args:
            config_path: Optional path to config file. If not provided, uses default.
        """
        self.config_path = config_path or (self.DEFAULT_CONFIG_DIR / self.DEFAULT_CONFIG_FILE)
        self.data = {}

    def load(self) -> None:
        """Load configuration from file.

        Raises:
            ConfigurationError: If config file doesn't exist or is invalid
        """
        if not self.config_path.exists():
            raise ConfigurationError(
                f"Configuration not found at {self.config_path}. "
                "Run 'justcal config --init' to create it."
            )

        try:
            with open(self.config_path, "rb") as f:
                self.data = tomli.load(f)
        except Exception as e:
            raise ConfigurationError(f"Failed to load config: {e}") from e

    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.config_path, "wb") as f:
                tomli_w.dump(self.data, f)

            # Set restrictive permissions (owner read/write only)
            os.chmod(self.config_path, 0o600)
        except Exception as e:
            raise ConfigurationError(f"Failed to save config: {e}") from e

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            section: Configuration section (e.g., 'caldav')
            key: Configuration key (e.g., 'url')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.data.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set
        """
        if section not in self.data:
            self.data[section] = {}
        self.data[section][key] = value

    def get_password(self) -> str:
        """Get password from keyring or config file.

        Returns:
            str: Password

        Raises:
            ConfigurationError: If password is not found
        """
        use_keyring = self.get("security", "use_keyring", True)
        username = self.get("caldav", "username")

        if not username:
            raise ConfigurationError("Username not configured")

        if use_keyring:
            password = keyring.get_password("justcal", username)
            if password:
                return password

        # Fall back to password in config file
        password = self.get("caldav", "password", "")
        if not password:
            raise ConfigurationError(
                "Password not found in keyring or config file. "
                "Run 'justcal config --init' to set it up."
            )

        return password

    def set_password(self, password: str) -> None:
        """Store password in keyring or config file.

        Args:
            password: Password to store
        """
        use_keyring = self.get("security", "use_keyring", True)
        username = self.get("caldav", "username")

        if not username:
            raise ConfigurationError("Username must be set before password")

        if use_keyring:
            try:
                keyring.set_password("justcal", username, password)
                # Don't store password in config file if using keyring
                self.set("caldav", "password", "")
                return
            except Exception as e:
                print(f"Warning: Failed to store password in keyring: {e}")
                print("Falling back to storing password in config file (less secure)")

        # Store in config file as fallback
        self.set("caldav", "password", password)

    def initialize_interactive(self) -> None:
        """Interactive configuration setup."""
        print("justcal configuration setup")
        print("=" * 40)

        # Start with default config
        self.data = self.DEFAULT_CONFIG.copy()

        # CalDAV URL
        url = input(
            f"CalDAV URL [{self.DEFAULT_CONFIG['caldav']['url'] or 'https://nextcloud.example.com/remote.php/dav'}]: "
        ).strip()
        if url:
            self.set("caldav", "url", url)
        elif not self.get("caldav", "url"):
            self.set("caldav", "url", "https://nextcloud.example.com/remote.php/dav")

        # Username
        username = input("Username: ").strip()
        if username:
            self.set("caldav", "username", username)
        else:
            raise ConfigurationError("Username is required")

        # Password
        password = getpass.getpass("Password (will be stored securely): ").strip()
        if password:
            self.set_password(password)
        else:
            raise ConfigurationError("Password is required")

        # Calendar name
        calendar = input(f"Calendar name [{self.DEFAULT_CONFIG['caldav']['calendar']}]: ").strip()
        if calendar:
            self.set("caldav", "calendar", calendar)

        # Timezone
        timezone = input(f"Timezone [{self.DEFAULT_CONFIG['preferences']['timezone']}]: ").strip()
        if timezone:
            self.set("preferences", "timezone", timezone)

        # Save configuration
        self.save()
        print(f"\n✓ Configuration saved to {self.config_path}")

    def show(self) -> str:
        """Display current configuration (without password).

        Returns:
            str: Configuration as TOML string
        """
        # Create a copy without password
        display_data = {}
        for section, values in self.data.items():
            display_data[section] = {}
            for key, value in values.items():
                if key == "password":
                    display_data[section][key] = "***" if value else ""
                else:
                    display_data[section][key] = value

        return tomli_w.dumps(display_data)
