"""Event collection and query orchestration."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from zoneinfo import ZoneInfo

from collectors.base import BaseCollector
from database.models import Event, UserPreferences
from database.repository import Repository
from services.deduplication import deduplicate
from services.filtering import classify, filter_events, is_professionally_relevant

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
        successful_sources: set[str] = set()
        for collector in self.collectors:
            try:
                collected = await collector.collect()
                gathered.extend(collected)
                successful_sources.add(collector.name)
                logger.info("Collector %s returned %d events", collector.name, len(collected))
            except Exception:
                logger.exception("Collector %s failed", collector.name)
        normalized = [classify(event) for event in gathered if self.city.casefold() in event.location.casefold()]
        relevant = [event for event in normalized if is_professionally_relevant(event)]
        unique = deduplicate(relevant)
        changed = await self.repository.upsert_events(unique)
        for source in successful_sources.intersection({"berlin.de", "luma", "messe-berlin"}):
            external_ids = {event.external_id for event in unique if event.source == source and event.external_id}
            await self.repository.prune_source(source, external_ids)
        await self.repository.delete_expired(datetime.now(self.timezone))
        logger.info("Collection stored %d relevant events (%d database changes)", len(unique), changed)
        return changed

    async def upcoming(self, days: int = 30, preferences: UserPreferences | None = None,
                       keyword: str | None = None, limit: int = 20) -> list[Event]:
        now = datetime.now(self.timezone)
        events = await self.repository.list_events(now, now + timedelta(days=days), max(limit * 5, 50))
        return filter_events(events, keyword=keyword, preferences=preferences)[:limit]

    async def between(self, start: datetime, end: datetime, preferences: UserPreferences | None = None,
                      limit: int = 20) -> list[Event]:
        events = await self.repository.list_events(start, end, max(limit * 5, 50))
        return filter_events(events, preferences=preferences)[:limit]
