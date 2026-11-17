"""Token-free collector for Messe Berlin's public event calendar."""
from __future__ import annotations

from datetime import datetime
import re
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup, Tag

from collectors.base import BaseCollector
from database.models import Event


class MesseBerlinCollector(BaseCollector):
    name = "messe-berlin"
    calendar_url = "https://www.messe-berlin.de/en/events/event-calendar/"
    _range_same_month = re.compile(r"(\d{1,2})\.\s*-\s*(\d{1,2})/(\d{1,2})/(\d{4})")
    _range_cross_month = re.compile(r"(\d{1,2})/(\d{1,2})\s*-\s*(\d{1,2})/(\d{1,2})/(\d{4})")
    _single = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")

    def __init__(self, client, timezone: str = "Europe/Berlin") -> None:
        super().__init__(client)
        self.timezone = ZoneInfo(timezone)

    async def collect(self) -> list[Event]:
        response = await self.client.get(self.calendar_url, follow_redirects=True)
        response.raise_for_status()
        return self._parse(response.text)

    def _parse(self, html: str) -> list[Event]:
        soup = BeautifulSoup(html, "html.parser")
        events: list[Event] = []
        for item in soup.select('[data-component="event-list-item"]'):
            event = self._parse_item(item)
            if event is not None:
                events.append(event)
        return events

    def _parse_item(self, item: Tag) -> Event | None:
        heading = item.find("h4")
        if heading is None:
            return None
        title = heading.get_text(" ", strip=True)
        starts_at, date_text = self._parse_date(item.get_text(" ", strip=True))
        if not title or starts_at is None:
            return None
        link = heading.find_parent("a", href=True) or item.find("a", href=True)
        url = str(link["href"]) if link else self.calendar_url
        prefix = item.get_text(" ", strip=True).split(title, 1)[0]
        location = prefix.replace(date_text, "", 1).strip()
        if "berlin" not in location.casefold():
            return None
        full_text = item.get_text(" ", strip=True)
        description = full_text.split(title, 1)[1].replace("More info", "").replace("Save appointment", "").strip()
        return self.event({
            "external_id": url,
            "title": title,
            "starts_at": starts_at,
            "location": location,
            "url": url,
            "description": description,
        })

    def _parse_date(self, text: str) -> tuple[datetime | None, str]:
        match = self._range_same_month.search(text)
        if match:
            start_day, month, _end_day, year = map(int, match.groups())
            return datetime(year, month, start_day, 9, tzinfo=self.timezone), match.group(0)
        match = self._range_cross_month.search(text)
        if match:
            month, day, _end_month, _end_day, year = map(int, match.groups())
            return datetime(year, month, day, 9, tzinfo=self.timezone), match.group(0)
        match = self._single.search(text)
        if match:
            month, day, year = map(int, match.groups())
            return datetime(year, month, day, 9, tzinfo=self.timezone), match.group(0)
        return None, ""
