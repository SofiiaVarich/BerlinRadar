from datetime import datetime, timedelta, timezone

import pytest

from database.models import Event, UserPreferences
from services.deduplication import deduplicate
from services.filtering import classify, filter_events, is_professionally_relevant


def event(title="Berlin AI Meetup", hours=1, location="Berlin Mitte", price=0):
    return Event(title=title, starts_at=datetime.now(timezone.utc) + timedelta(hours=hours),
                 location=location, url="https://example.com", source="test", price=price,
                 description="Machine learning and startup networking")


def test_classify_and_filter_preferences():
    first = classify(event())
    second = classify(event("Cloud Engineering", 2, price=20))
    preferences = UserPreferences(1, categories=["AI & Machine Learning"], free_only=True)
    assert filter_events([second, first], preferences=preferences) == [first]


def test_deduplicate_merges_similar_cross_source_events():
    first = event()
    second = event("Berlin AI Meet-up", location="Berlin-Mitte")
    second.starts_at = first.starts_at + timedelta(minutes=10)
    second.categories = ["Startups"]
    unique = deduplicate([first, second], similarity=0.8)
    assert len(unique) == 1
    assert "Startups" in unique[0].categories


def test_event_normalizes_timestamp_to_utc():
    value = datetime.now(timezone(timedelta(hours=2))) + timedelta(days=1)
    assert event(hours=1).starts_at.utcoffset() == timedelta(0)
    normalized = Event("Tech", value, "Berlin", "https://example.com", "test")
    assert normalized.starts_at.utcoffset() == timedelta(0)


def test_event_rejects_naive_timestamp():
    with pytest.raises(ValueError, match="timezone"):
        Event("Tech", datetime.now(), "Berlin", "https://example.com", "test")


def test_food_is_classified_only_when_explicitly_mentioned():
    event_with_food = Event("Founder breakfast", datetime.now(timezone.utc) + timedelta(days=1),
                            "Berlin", "https://example.com", "test")
    assert "Food" in classify(event_with_food).categories


def test_hackathon_is_classified():
    hackathon = Event("Berlin AI Hackathon", datetime.now(timezone.utc) + timedelta(days=1),
                      "Berlin", "https://example.com", "test")
    assert "Hackathons" in classify(hackathon).categories


def test_entertainment_and_broad_security_terms_are_not_relevant():
    rave = Event("Family Brunch Rave", datetime.now(timezone.utc) + timedelta(days=1),
                 "Berlin", "https://example.com", "test")
    security = Event("Future food security", datetime.now(timezone.utc) + timedelta(days=1),
                     "Berlin", "https://example.com", "test")
    assert not is_professionally_relevant(classify(rave))
    assert "Cybersecurity" not in classify(security).categories


def test_ai_keyword_does_not_match_inside_word():
    unrelated = Event("Sailing evening", datetime.now(timezone.utc) + timedelta(days=1),
                      "Berlin", "https://example.com", "test")
    assert classify(unrelated).categories == []
