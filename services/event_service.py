"""Event collection and query orchestration."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from zoneinfo import ZoneInfo

from collectors.base import BaseCollector
from database.models import Event, UserPreferences
from database.repository import Repository
from services.deduplication import deduplicate
from services.filtering import classify, filter_events

logger = logging.getLogger(__name__)


class EventService:
    def __init__(self, repository: Repository, collectors: list[BaseCollector], timezone: str = "Europe/Berlin",
                 city: str = "Berlin") -> None:
        self.repository = repository
        self.collectors = collectors
        self.timezone = ZoneInfo(timezone)
        self.city = city

    async def collect(self) -> int:
        gathered: list[Event] = []
        for collector in self.collectors:
            try:
                gathered.extend(await collector.collect())
            except Exception:
                logger.exception("Collector %s failed", collector.name)
        normalized = [classify(event) for event in gathered if self.city.casefold() in event.location.casefold()]
        relevant = [event for event in normalized if event.categories]
        return await self.repository.upsert_events(deduplicate(relevant))

    async def upcoming(self, days: int = 30, preferences: UserPreferences | None = None,
                       keyword: str | None = None, limit: int = 20) -> list[Event]:
        now = datetime.now(self.timezone)
        events = await self.repository.list_events(now, now + timedelta(days=days), max(limit * 5, 50))
        return filter_events(events, keyword=keyword, preferences=preferences)[:limit]

    async def between(self, start: datetime, end: datetime, preferences: UserPreferences | None = None,
                      limit: int = 20) -> list[Event]:
        events = await self.repository.list_events(start, end, max(limit * 5, 50))
        return filter_events(events, preferences=preferences)[:limit]
