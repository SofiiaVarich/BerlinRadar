"""Domain models shared by collectors, services, and persistence."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from typing import Any


class Category(StrEnum):
    AI_ML = "AI & Machine Learning"
    SOFTWARE = "Software Development"
    CYBERSECURITY = "Cybersecurity"
    STARTUPS = "Startups"
    BUSINESS = "Business & Networking"
    VENTURE_CAPITAL = "Venture Capital"
    PRODUCT = "Product Management"
    MARKETING = "Marketing & Sales"
    HACKATHONS = "Hackathons"
    FOOD = "Food"


@dataclass(slots=True)
class Event:
    title: str
    starts_at: datetime
    location: str
    url: str
    source: str
    description: str = ""
    categories: list[str] = field(default_factory=list)
    price: float | None = None
    currency: str = "EUR"
    external_id: str | None = None
    id: int | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.starts_at.tzinfo is None:
            raise ValueError("starts_at must include timezone information")
        self.starts_at = self.starts_at.astimezone(timezone.utc)
        self.title = " ".join(self.title.split())
        self.location = " ".join(self.location.split())
        self.categories = list(dict.fromkeys(self.categories))

    @property
    def fingerprint(self) -> str:
        key = "|".join((self.title.casefold(), self.starts_at.isoformat(), self.location.casefold()))
        return sha256(key.encode()).hexdigest()

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "Event":
        starts_at = data["starts_at"]
        if isinstance(starts_at, str):
            starts_at = datetime.fromisoformat(starts_at.replace("Z", "+00:00"))
        return cls(
            id=data.get("id"), title=data["title"], starts_at=starts_at,
            location=data.get("location", "Berlin"), url=data["url"], source=data["source"],
            description=data.get("description", ""), categories=list(data.get("categories", [])),
            price=data.get("price"), currency=data.get("currency", "EUR"),
            external_id=data.get("external_id"),
        )


@dataclass(slots=True)
class UserPreferences:
    telegram_id: int
    categories: list[str] = field(default_factory=list)
    free_only: bool = False
    subscribed: bool = False
    timezone: str = "Europe/Berlin"
