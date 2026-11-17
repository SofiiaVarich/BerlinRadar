"""Pure filtering and category classification functions."""
from __future__ import annotations

from datetime import datetime
import re

from database.models import Category, Event, UserPreferences

KEYWORDS = {
    Category.AI_ML: ("ai", "machine learning", "data science", "llm"),
    Category.SOFTWARE: ("software", "developer", "programming", "devops", "cloud"),
    Category.CYBERSECURITY: ("cybersecurity", "cyber security", "information security", "infosec", "cloud security"),
    Category.STARTUPS: ("startup", "founder", "entrepreneur"),
    Category.BUSINESS: ("business", "networking", "entrepreneurship"),
    Category.VENTURE_CAPITAL: ("venture capital", "investment", "fundraising", "vc"),
    Category.PRODUCT: ("product management", "product manager"),
    Category.MARKETING: ("marketing", "growth", "sales strategy", "business development"),
    Category.HACKATHONS: ("hackathon", "hack day", "hack night", "coding challenge"),
    Category.FOOD: ("food", "lunch", "dinner", "breakfast", "brunch", "snacks", "pizza", "catering", "refreshments"),
}

EXCLUDED_TERMS = (
    "rave", "nightclub", "nightlife", "concert", "theatre performance", "family brunch",
    "boat show", "camping caravan", "equestrian", "fishing show", "motorbike fair",
)


def is_professionally_relevant(event: Event) -> bool:
    text = f"{event.title} {event.description}".casefold()
    return bool(event.categories) and not any(term in text for term in EXCLUDED_TERMS)


def classify(event: Event) -> Event:
    text = f"{event.title} {event.description}".casefold()
    inferred = [
        str(category)
        for category, words in KEYWORDS.items()
        if any(re.search(rf"(?<!\w){re.escape(word)}(?!\w)", text) for word in words)
    ]
    event.categories = list(dict.fromkeys(event.categories + inferred))
    return event


def filter_events(events: list[Event], start: datetime | None = None, end: datetime | None = None,
                  keyword: str | None = None, preferences: UserPreferences | None = None) -> list[Event]:
    result = events
    if start:
        result = [event for event in result if event.starts_at >= start]
    if end:
        result = [event for event in result if event.starts_at < end]
    if keyword:
        term = keyword.casefold()
        result = [event for event in result if term in f"{event.title} {event.description} {' '.join(event.categories)}".casefold()]
    if preferences:
        if preferences.free_only:
            result = [event for event in result if event.price == 0]
        if preferences.categories:
            selected = set(preferences.categories)
            result = [event for event in result if selected.intersection(event.categories)]
    return sorted(result, key=lambda event: event.starts_at)
