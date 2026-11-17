"""Collector interface and shared normalization helpers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import httpx

from database.models import Event


class CollectorError(RuntimeError):
    pass


class BaseCollector(ABC):
    name = "unknown"

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    @abstractmethod
    async def collect(self) -> list[Event]:
        """Fetch and normalize upcoming events."""

    def event(self, data: dict[str, Any]) -> Event:
        starts_at = data["starts_at"]
        if isinstance(starts_at, str):
            starts_at = datetime.fromisoformat(starts_at.replace("Z", "+00:00"))
        return Event(title=data["title"], starts_at=starts_at, location=data.get("location", "Berlin"),
                     url=data["url"], source=self.name, description=data.get("description", ""),
                     categories=data.get("categories", []), price=data.get("price"),
                     currency=data.get("currency", "EUR"), external_id=str(data.get("external_id", "")) or None)
