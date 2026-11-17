"""Token-free collector for Luma's public Berlin event calendar."""
from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from collectors.base import BaseCollector, CollectorError
from database.models import Event


class LumaCollector(BaseCollector):
    name = "luma"
    calendar_url = "https://lu.ma/berlin"

    async def collect(self) -> list[Event]:
        response = await self.client.get(self.calendar_url, follow_redirects=True)
        response.raise_for_status()
        return self._parse(response.text)

    def _parse(self, html: str) -> list[Event]:
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", attrs={"type": "application/ld+json"})
        if script is None or not script.string:
            raise CollectorError("Luma Berlin calendar did not contain JSON-LD")
        try:
            payload = json.loads(script.string)
        except json.JSONDecodeError as exc:
            raise CollectorError("Luma Berlin calendar returned invalid JSON-LD") from exc
        events: list[Event] = []
        for entry in payload.get("itemListElement", []):
            item = entry.get("item", {})
            if item.get("@type") != "Event" or not item.get("name") or not item.get("startDate"):
                continue
            location = self._location(item.get("location"))
            offers = item.get("offers") or []
            offer = offers[0] if isinstance(offers, list) and offers else offers if isinstance(offers, dict) else {}
            events.append(self.event({
                "external_id": item.get("@id") or item.get("url"),
                "title": item["name"],
                "starts_at": item["startDate"],
                "location": location,
                "url": item.get("url") or item.get("@id"),
                "description": item.get("description", ""),
                "price": self._price(offer.get("price")),
                "currency": str(offer.get("priceCurrency") or "EUR").upper(),
            }))
        return events

    @staticmethod
    def _location(value: Any) -> str:
        if not isinstance(value, dict):
            return "Unknown location"
        address = value.get("address") or {}
        locality = address.get("addressLocality", "") if isinstance(address, dict) else ""
        name = value.get("name", "")
        parts = [name]
        if locality and locality.casefold() not in name.casefold():
            parts.append(locality)
        return ", ".join(filter(None, parts)) or "Unknown location"

    @staticmethod
    def _price(value: Any) -> float | None:
        try:
            return float(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None
