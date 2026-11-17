from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from bot.handlers.events import (
    events_command,
    food_command,
    free_command,
    hackathons_command,
    offline_command,
    paid_command,
    today_command,
    week_command,
    weekend_command,
)
from bot.handlers.search import search_button
from bot.handlers.settings import settings_command, subscribe_command
from bot.handlers.start import start
from bot.keyboards.inline import (
    EVENTS_BUTTON,
    FOOD_BUTTON,
    FREE_BUTTON,
    HACKATHONS_BUTTON,
    OFFLINE_BUTTON,
    PAID_BUTTON,
    SEARCH_BUTTON,
    SETTINGS_BUTTON,
    SUBSCRIBE_BUTTON,
    TODAY_BUTTON,
    WEEK_BUTTON,
    WEEKEND_BUTTON,
    main_menu,
)
from database.models import Event, UserPreferences


class Message:
    def __init__(self) -> None:
        self.from_user = SimpleNamespace(id=42)
        self.chat = SimpleNamespace(id=42)
        self.answer = AsyncMock()


class Repository:
    def __init__(self) -> None:
        self.ensure_user = AsyncMock()
        self.update_preferences = AsyncMock()

    async def get_preferences(self, telegram_id: int) -> UserPreferences:
        return UserPreferences(telegram_id)


class EventService:
    def __init__(self) -> None:
        self.event = Event(
            "Berlin AI Hackathon",
            datetime.now(timezone.utc) + timedelta(hours=1),
            "Berlin Mitte",
            "https://example.com/event",
            "test",
            categories=["AI & Machine Learning", "Hackathons"],
            price=10,
        )
        self.upcoming = AsyncMock(return_value=[self.event])
        self.between = AsyncMock(return_value=[self.event])


@pytest.mark.asyncio
async def test_all_main_menu_actions_respond():
    repository = Repository()
    service = EventService()
    handlers = [
        lambda message: start(message, repository),
        lambda message: events_command(message, service, repository),
        lambda message: today_command(message, service, repository),
        lambda message: week_command(message, service, repository),
        lambda message: weekend_command(message, service, repository),
        lambda message: free_command(message, service, repository),
        lambda message: food_command(message, service, repository),
        lambda message: paid_command(message, service, repository),
        lambda message: hackathons_command(message, service, repository),
        lambda message: offline_command(message, service, repository),
        search_button,
        lambda message: settings_command(message, repository),
        lambda message: subscribe_command(message, repository),
    ]
    for handler in handlers:
        message = Message()
        await handler(message)
        message.answer.assert_awaited()


def test_main_menu_contains_each_unique_button():
    expected = {
        EVENTS_BUTTON, TODAY_BUTTON, WEEK_BUTTON, WEEKEND_BUTTON, FREE_BUTTON, PAID_BUTTON,
        FOOD_BUTTON, HACKATHONS_BUTTON, OFFLINE_BUTTON, SEARCH_BUTTON, SETTINGS_BUTTON, SUBSCRIBE_BUTTON,
    }
    keyboard = main_menu()
    actual = [button.text for row in keyboard.keyboard for button in row]
    assert set(actual) == expected
    assert len(actual) == len(expected)
