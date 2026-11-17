"""Duplicate detection for events gathered from multiple sources."""
from __future__ import annotations

from difflib import SequenceMatcher
from database.models import Event


def deduplicate(events: list[Event], similarity: float = 0.9) -> list[Event]:
    unique: list[Event] = []
    for candidate in sorted(events, key=lambda event: event.starts_at):
        duplicate = next((existing for existing in unique if _same(candidate, existing, similarity)), None)
        if duplicate is None:
            unique.append(candidate)
        else:
            duplicate.categories = list(dict.fromkeys(duplicate.categories + candidate.categories))
            if len(candidate.description) > len(duplicate.description):
                duplicate.description = candidate.description
    return unique


def _same(left: Event, right: Event, similarity: float) -> bool:
    if abs((left.starts_at - right.starts_at).total_seconds()) > 3 * 60 * 60:
        return False
    title = SequenceMatcher(None, left.title.casefold(), right.title.casefold()).ratio()
    location = SequenceMatcher(None, left.location.casefold(), right.location.casefold()).ratio()
    return title >= similarity and location >= 0.65
