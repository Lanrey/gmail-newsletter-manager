"""Configuration management for newsletter manager."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class Config:
    """Manages configuration for the newsletter manager."""

    DEFAULT_CONFIG_DIR = Path.home() / ".gmail-newsletter-manager"
    DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"
    DEFAULT_DB_FILE = DEFAULT_CONFIG_DIR / "newsletters.db"

    DEFAULT_CONFIG = {
        "accounts": [],
        "default_account": None,
        "categories": {
            "Tech": {
                "keywords": [
                    "programming",
                    "developer",
                    "tech",
                    "software",
                    "coding",
                    "devops",
                    "cloud",
                ],
                "domains": ["dev.to", "hashnode.com", "medium.com", "substack.com"],
            },
            "Business": {
                "keywords": [
                    "business",
                    "entrepreneur",
                    "startup",
                    "marketing",
                    "sales",
                    "leadership",
                ],
                "domains": ["linkedin.com", "inc.com", "entrepreneur.com"],
            },
            "News": {
                "keywords": ["news", "daily", "briefing", "today", "headlines", "breaking"],
                "domains": ["nytimes.com", "cnn.com", "bbc.com"],
            },
            "Finance": {
                "keywords": ["finance", "investing", "stocks", "crypto", "market", "trading"],
                "domains": ["bloomberg.com", "wsj.com", "reuters.com"],
            },
            "Design": {
                "keywords": ["design", "ux", "ui", "creative", "graphic", "typography"],
                "domains": ["dribbble.com", "behance.net"],
            },
        },
        "newsletter_patterns": [
            "list-unsubscribe",
            "newsletter",
            "digest",
            "weekly update",
            "monthly roundup",
            "daily brief",
            "notification",
            "subscription",
        ],
        "known_platforms": [
            "substack.com",
            "beehiiv.com",
            "mailchimp.com",
            "constantcontact.com",
            "convertkit.com",
            "buttondown.email",
            "ghost.io",
            "revue.com",
            "sendfox.com",
            "mailerlite.com",
        ],
        "auto_archive_days": 30,
        "min_frequency_for_newsletter": 2,
        "max_search_days": 90,
        "batch_size": 100,
    }

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration."""
        self.config_path = config_path or self.DEFAULT_CONFIG_FILE
        self.config_dir = self.config_path.parent
        self.db_path = self.config_dir / "newsletters.db"
        self._config = None

    def load(self) -> Dict[str, Any]:
        """Load configuration from file, create with defaults if not exists."""
        if not self.config_path.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.save(self.DEFAULT_CONFIG)
            self._config = self.DEFAULT_CONFIG.copy()
        else:
            with open(self.config_path) as f:
                self._config = yaml.safe_load(f) or {}
                # Merge with defaults for any missing keys
                for key, value in self.DEFAULT_CONFIG.items():
                    if key not in self._config:
                        self._config[key] = value

        return self._config

    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        self._config = config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        if self._config is None:
            self.load()
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value and save."""
        if self._config is None:
            self.load()
        self._config[key] = value
        self.save(self._config)

    def get_categories(self) -> Dict[str, Dict[str, List[str]]]:
        """Get newsletter categories."""
        return self.get("categories", {})

    def get_newsletter_patterns(self) -> List[str]:
        """Get newsletter detection patterns."""
        return self.get("newsletter_patterns", [])

    def get_known_platforms(self) -> List[str]:
        """Get known newsletter platforms."""
        return self.get("known_platforms", [])

    def get_accounts(self) -> List[str]:
        """Get list of configured accounts."""
        return self.get("accounts", [])

    def get_default_account(self) -> Optional[str]:
        """Get default account email."""
        return self.get("default_account")

    def add_account(self, email: str) -> None:
        """Add a new account."""
        accounts = self.get_accounts()
        if email not in accounts:
            accounts.append(email)
            self.set("accounts", accounts)
            if not self.get_default_account():
                self.set("default_account", email)

    def remove_account(self, email: str) -> None:
        """Remove an account."""
        accounts = self.get_accounts()
        if email in accounts:
            accounts.remove(email)
            self.set("accounts", accounts)
            if self.get_default_account() == email:
                self.set("default_account", accounts[0] if accounts else None)

    def set_default_account(self, email: str) -> None:
        """Set default account."""
        accounts = self.get_accounts()
        if email in accounts:
            self.set("default_account", email)
        else:
            raise ValueError(f"Account {email} not found. Use 'account add' first.")
