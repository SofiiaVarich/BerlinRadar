"""Eventbrite API adapter.

Eventbrite does not provide unrestricted public event search. This adapter uses the
authenticated user's organizations endpoint and is disabled without a token.
"""
from __future__ import annotations

from collectors.base import BaseCollector, CollectorError
from database.models import Event


class EventbriteCollector(BaseCollector):
    name = "eventbrite"

    def __init__(self, client, token: str) -> None:
        super().__init__(client)
        self.token = token

    async def collect(self) -> list[Event]:
        if not self.token:
            return []
        headers = {"Authorization": f"Bearer {self.token}"}
        response = await self.client.get("https://www.eventbriteapi.com/v3/users/me/organizations/", headers=headers)
        if response.is_error:
            raise CollectorError(f"Eventbrite organizations request failed: {response.status_code}")
        events: list[Event] = []
        for organization in response.json().get("organizations", []):
            result = await self.client.get(
                f"https://www.eventbriteapi.com/v3/organizations/{organization['id']}/events/",
                headers=headers, params={"status": "live", "order_by": "start_asc"})
            if result.is_error:
                continue
            for item in result.json().get("events", []):
                venue = item.get("venue") or {}
                address = venue.get("address") or {}
                location = address.get("localized_address_display") or "Unknown location"
                events.append(self.event({"external_id": item["id"], "title": item["name"]["text"],
                    "starts_at": item["start"]["utc"], "location": location, "url": item["url"],
                    "description": (item.get("description") or {}).get("text") or "",
                    "price": 0.0 if item.get("is_free") else None}))
        return events
