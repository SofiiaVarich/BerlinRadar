"""Standards-friendly collector for pages exposing schema.org Event JSON-LD."""
from __future__ import annotations

import json
import logging
from typing import Any, Iterable

from bs4 import BeautifulSoup

from collectors.base import BaseCollector, CollectorError
from database.models import Event

logger = logging.getLogger(__name__)


class WebsiteCollector(BaseCollector):
    name = "website"

    def __init__(self, client, urls: Iterable[str]) -> None:
        super().__init__(client)
        self.urls = tuple(urls)

    async def collect(self) -> list[Event]:
        events: list[Event] = []
        for url in self.urls:
            try:
                response = await self.client.get(url, follow_redirects=True)
                response.raise_for_status()
                events.extend(self._parse(response.text, str(response.url)))
            except Exception as exc:
                logger.warning("Unable to collect %s: %s", url, exc)
        return events

    def _parse(self, html: str, page_url: str) -> list[Event]:
        soup = BeautifulSoup(html, "html.parser")
        result: list[Event] = []
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                payload = json.loads(script.string or "{}")
            except json.JSONDecodeError:
                continue
            for item in self._items(payload):
                if item.get("@type") != "Event" or not item.get("startDate") or not item.get("name"):
                    continue
                location = item.get("location") or {}
                if isinstance(location, list):
                    location = location[0] if location else {}
                address = location.get("address", {}) if isinstance(location, dict) else {}
                if isinstance(address, dict):
                    address = ", ".join(filter(None, (address.get("streetAddress"), address.get("addressLocality"))))
                offers = item.get("offers") or {}
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                venue_name = location.get("name", "") if isinstance(location, dict) else ""
                display_location = ", ".join(dict.fromkeys(filter(None, (venue_name, address)))) or "Unknown location"
                result.append(self.event({"external_id": item.get("@id"), "title": item["name"],
                    "starts_at": item["startDate"], "location": display_location,
                    "url": item.get("url") or page_url, "description": item.get("description", ""),
                    "price": self._price(offers.get("price")), "currency": offers.get("priceCurrency", "EUR")}))
        return result

    @classmethod
    def _items(cls, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for value in payload for item in cls._items(value)]
        if not isinstance(payload, dict):
            return []
        if "@graph" in payload:
            return cls._items(payload["@graph"])
        return [payload]

    @staticmethod
    def _price(value: Any) -> float | None:
        try:
            return float(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None
