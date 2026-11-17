"""Token-free, robots-compliant collector for Berlin.de trade fairs."""
from __future__ import annotations

import asyncio
from datetime import datetime
import logging
import re
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from collectors.base import BaseCollector
from database.models import Event

logger = logging.getLogger(__name__)


class BerlinDeCollector(BaseCollector):
    name = "berlin.de"
    listing_url = "https://www.berlin.de/en/trade-fairs/"
    _date_pattern = re.compile(r"([A-Za-z]+)\s+(\d{1,2})(?:\s*-\s*\d{1,2})?,\s*(\d{4})")

    def __init__(self, client, timezone: str = "Europe/Berlin", request_delay: float = 0.25) -> None:
        super().__init__(client)
        self.timezone = ZoneInfo(timezone)
        self.request_delay = request_delay

    async def collect(self) -> list[Event]:
        response = await self.client.get(self.listing_url, follow_redirects=True)
        response.raise_for_status()
        links = self._listing_links(response.text)
        events: list[Event] = []
        for link in links:
            try:
                await asyncio.sleep(self.request_delay)
                detail = await self.client.get(link, follow_redirects=True)
                detail.raise_for_status()
                event = self._parse_detail(detail.text, link)
                if event is not None:
                    events.append(event)
            except Exception as exc:
                logger.warning("Unable to collect Berlin.de event %s: %s", link, exc)
        return events

    def _listing_links(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = {
            urljoin(self.listing_url, anchor["href"])
            for anchor in soup.select('a[href^="/en/trade-fairs/"][href$=".html"]')
            if anchor.get("href")
        }
        return sorted(links)

    def _parse_detail(self, html: str, url: str) -> Event | None:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.h1.get_text(" ", strip=True) if soup.h1 else ""
        fields = self._definition_fields(soup)
        starts_at = self._parse_date(fields.get("date", ""))
        if not title or starts_at is None:
            return None
        venue = fields.get("location", "")
        address = fields.get("address", "")
        location = ", ".join(dict.fromkeys(filter(None, (venue, address))))
        description_tag = soup.select_one('meta[name="description"]')
        description = description_tag.get("content", "") if description_tag else ""
        external_id = url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".en.html")
        return self.event({
            "external_id": external_id,
            "title": title,
            "starts_at": starts_at,
            "location": location or "Unknown location",
            "url": url,
            "description": description,
        })

    @staticmethod
    def _definition_fields(soup: BeautifulSoup) -> dict[str, str]:
        fields: dict[str, str] = {}
        for term in soup.select("dl dt"):
            value = term.find_next_sibling("dd")
            if value:
                fields[term.get_text(" ", strip=True).casefold()] = value.get_text(" ", strip=True)
        return fields

    def _parse_date(self, value: str) -> datetime | None:
        match = self._date_pattern.search(value)
        if not match:
            return None
        parsed = datetime.strptime(" ".join(match.groups()), "%B %d %Y")
        return parsed.replace(hour=9, tzinfo=self.timezone)
