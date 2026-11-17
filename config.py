"""Application configuration loaded from environment variables."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


@dataclass(frozen=True, slots=True)
class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///events.db")
    default_city: str = os.getenv("DEFAULT_CITY", "Berlin")
    timezone: str = os.getenv("TIMEZONE", "Europe/Berlin")
    event_update_interval_hours: int = _int("EVENT_UPDATE_INTERVAL_HOURS", 6)
    notification_hour: int = _int("NOTIFICATION_HOUR", 9)
    eventbrite_token: str = os.getenv("EVENTBRITE_TOKEN", "")
    meetup_access_token: str = os.getenv("MEETUP_ACCESS_TOKEN", "")
    event_feed_urls: tuple[str, ...] = tuple(
        value.strip() for value in os.getenv("EVENT_FEED_URLS", "").split(",") if value.strip()
    )

    @property
    def database_path(self) -> Path:
        parsed = urlparse(self.database_url)
        if parsed.scheme != "sqlite":
            raise ValueError("The MVP supports sqlite DATABASE_URL values only")
        value = parsed.path
        if self.database_url.startswith("sqlite:///./"):
            value = self.database_url.removeprefix("sqlite:///")
        elif self.database_url.startswith("sqlite:///"):
            value = self.database_url.removeprefix("sqlite:///")
        if value == ":memory:":
            return Path(":memory:")
        return Path(value).expanduser()


settings = Settings()
