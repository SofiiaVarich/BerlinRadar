"""Meetup GraphQL adapter, enabled only when an access token is configured."""
from __future__ import annotations

from collectors.base import BaseCollector, CollectorError
from database.models import Event


class MeetupCollector(BaseCollector):
    name = "meetup"
    query = """query($first: Int!) { self { events(first: $first) { edges { node {
      id title eventUrl dateTime description venue { name address city }
    } } } } }"""

    def __init__(self, client, token: str) -> None:
        super().__init__(client)
        self.token = token

    async def collect(self) -> list[Event]:
        if not self.token:
            return []
        response = await self.client.post("https://api.meetup.com/gql", json={"query": self.query, "variables": {"first": 100}},
                                          headers={"Authorization": f"Bearer {self.token}"})
        if response.is_error:
            raise CollectorError(f"Meetup request failed: {response.status_code}")
        payload = response.json()
        if payload.get("errors"):
            raise CollectorError(f"Meetup returned: {payload['errors'][0].get('message', 'unknown error')}")
        edges = (((payload.get("data") or {}).get("self") or {}).get("events") or {}).get("edges", [])
        events = []
        for edge in edges:
            item = edge["node"]
            venue = item.get("venue") or {}
            location = ", ".join(filter(None, (venue.get("name"), venue.get("address"), venue.get("city")))) or "Unknown location"
            events.append(self.event({"external_id": item["id"], "title": item["title"], "starts_at": item["dateTime"],
                                      "location": location, "url": item["eventUrl"], "description": item.get("description") or ""}))
        return events
