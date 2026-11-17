from datetime import datetime, timedelta, timezone

import pytest

from database.models import Event, UserPreferences
from database.repository import Repository


@pytest.mark.asyncio
async def test_repository_round_trip_and_notification_history(tmp_path):
    repository = Repository(tmp_path / "events.db")
    await repository.initialize()
    event = Event("Python Meetup", datetime.now(timezone.utc) + timedelta(days=1), "Berlin", "https://example.com", "test")
    await repository.upsert_events([event])
    stored = await repository.list_events(datetime.now(timezone.utc), datetime.now(timezone.utc) + timedelta(days=2))
    assert len(stored) == 1
    assert stored[0].title == "Python Meetup"
    assert await repository.unsent(42, stored) == stored
    await repository.mark_sent(42, stored[0].id)
    assert await repository.unsent(42, stored) == []


@pytest.mark.asyncio
async def test_preferences_are_persisted(tmp_path):
    repository = Repository(tmp_path / "events.db")
    await repository.initialize()
    expected = UserPreferences(7, ["Startups"], True, True)
    await repository.update_preferences(expected)
    assert await repository.get_preferences(7) == expected
    await repository.delete_user(7)
    assert await repository.get_preferences(7) == UserPreferences(7)


@pytest.mark.asyncio
async def test_existing_source_event_is_updated(tmp_path):
    repository = Repository(tmp_path / "events.db")
    await repository.initialize()
    starts_at = datetime.now(timezone.utc) + timedelta(days=1)
    original = Event("Python Meetup", starts_at, "Berlin Mitte", "https://example.com/1", "feed", external_id="123")
    await repository.upsert_events([original])
    updated = Event("Python Meetup Updated", starts_at + timedelta(hours=1), "Berlin Kreuzberg",
                    "https://example.com/2", "feed", external_id="123")
    await repository.upsert_events([updated])
    stored = await repository.list_events(datetime.now(timezone.utc), datetime.now(timezone.utc) + timedelta(days=2))
    assert len(stored) == 1
    assert stored[0].title == "Python Meetup Updated"
    assert stored[0].location == "Berlin Kreuzberg"
