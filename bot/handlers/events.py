"""Event listing commands."""
from __future__ import annotations

from datetime import datetime, timedelta
from html import escape
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.inline import (
    EVENTS_BUTTON,
    FOOD_BUTTON,
    FREE_BUTTON,
    HACKATHONS_BUTTON,
    OFFLINE_BUTTON,
    PAID_BUTTON,
    TODAY_BUTTON,
    WEEK_BUTTON,
    WEEKEND_BUTTON,
    event_keyboard,
)
from database.models import Event, UserPreferences
from database.repository import Repository
from services.event_service import EventService

router = Router()


def format_event(event: Event, timezone: str = "Europe/Berlin") -> str:
    local = event.starts_at.astimezone(ZoneInfo(timezone))
    price = "Free" if event.price == 0 else (f"{event.price:g} {escape(event.currency)}" if event.price is not None else "See event page")
    categories = ", ".join(escape(value) for value in event.categories) or "Professional event"
    description = escape(event.description.strip())
    if len(description) > 350:
        description = description[:347] + "…"
    body = (
        f"🚀 <b>{escape(event.title)}</b>\n\n📅 {local:%A, %d %B %Y}\n"
        f"🕕 {local:%H:%M}\n📍 {escape(event.location)}\n💰 {price}\n\n🏷 {categories}"
    )
    return body + (f"\n\n📝 {description}" if description else "")


async def send_events(message: Message, events: list[Event], timezone: str = "Europe/Berlin",
                      empty_message: str = "No matching upcoming events found. Try again later or change your settings.") -> None:
    if not events:
        await message.answer(empty_message)
        return
    ordered_events = sorted(events, key=lambda event: event.starts_at, reverse=True)
    await message.answer(f"Found <b>{len(ordered_events)}</b> event{'s' if len(ordered_events) != 1 else ''}:")
    for event in ordered_events:
        await message.answer(format_event(event, timezone), reply_markup=event_keyboard(event), disable_web_page_preview=True)


@router.message(Command("events"))
@router.message(F.text == EVENTS_BUTTON)
async def events_command(message: Message, event_service: EventService, repository: Repository) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    preferences = await repository.get_preferences(user_id)
    await send_events(message, await event_service.upcoming(preferences=preferences), preferences.timezone)


@router.message(Command("today"))
@router.message(F.text == TODAY_BUTTON)
async def today_command(message: Message, event_service: EventService, repository: Repository) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    preferences = await repository.get_preferences(user_id)
    now = datetime.now(ZoneInfo(preferences.timezone))
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    events = await event_service.between(start, end, preferences)
    await send_events(
        message, events, preferences.timezone,
        "No matching events remain today. New source data is checked every two hours.",
    )


@router.message(Command("free"))
@router.message(F.text == FREE_BUTTON)
async def free_command(message: Message, event_service: EventService, repository: Repository) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    preferences = await repository.get_preferences(user_id)
    preferences.free_only = True
    await send_events(message, await event_service.upcoming(preferences=preferences), preferences.timezone)


def _without_filters(preferences: UserPreferences) -> UserPreferences:
    return UserPreferences(
        telegram_id=preferences.telegram_id,
        subscribed=preferences.subscribed,
        timezone=preferences.timezone,
    )


@router.message(Command("paid"))
@router.message(F.text == PAID_BUTTON)
async def paid_command(message: Message, event_service: EventService, repository: Repository) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    preferences = await repository.get_preferences(user_id)
    events = await event_service.upcoming(days=365, preferences=_without_filters(preferences), limit=100)
    paid = [
        event for event in events
        if (event.price is not None and event.price > 0) or "buy tickets" in event.description.casefold()
    ]
    await send_events(
        message, paid, preferences.timezone,
        "No events with an explicit price or a ‘Buy tickets’ notice are currently available.",
    )


@router.message(Command("hackathons"))
@router.message(F.text == HACKATHONS_BUTTON)
async def hackathons_command(message: Message, event_service: EventService, repository: Repository) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    preferences = await repository.get_preferences(user_id)
    events = await event_service.upcoming(days=365, preferences=_without_filters(preferences), limit=100)
    hackathons = [event for event in events if "Hackathons" in event.categories]
    await send_events(
        message, hackathons, preferences.timezone,
        "No announced Berlin hackathons were found in the next year. The list refreshes every two hours.",
    )


@router.message(Command("offline"))
@router.message(F.text == OFFLINE_BUTTON)
async def offline_command(message: Message, event_service: EventService, repository: Repository) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    preferences = await repository.get_preferences(user_id)
    events = await event_service.upcoming(days=90, preferences=_without_filters(preferences), limit=100)
    offline = [event for event in events if event.location.casefold() != "unknown location"]
    await send_events(message, offline, preferences.timezone)


@router.message(Command("food"))
@router.message(F.text == FOOD_BUTTON)
async def food_command(message: Message, event_service: EventService, repository: Repository) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    preferences = await repository.get_preferences(user_id)
    events = await event_service.upcoming(days=365, preferences=_without_filters(preferences), limit=100)
    food_events = [event for event in events if "Food" in event.categories]
    await send_events(
        message, food_events, preferences.timezone,
        "No professional events explicitly mentioning food or refreshments were found in the next year.",
    )


@router.message(Command("week"))
@router.message(F.text == WEEK_BUTTON)
async def week_command(message: Message, event_service: EventService, repository: Repository) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    preferences = await repository.get_preferences(user_id)
    now = datetime.now(ZoneInfo(preferences.timezone))
    end = (now + timedelta(days=7 - now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    await send_events(message, await event_service.between(now, end, preferences), preferences.timezone)


@router.message(Command("weekend"))
@router.message(F.text == WEEKEND_BUTTON)
async def weekend_command(message: Message, event_service: EventService, repository: Repository) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    preferences = await repository.get_preferences(user_id)
    now = datetime.now(ZoneInfo(preferences.timezone))
    days_to_saturday = (5 - now.weekday()) % 7
    start = (now + timedelta(days=days_to_saturday)).replace(hour=0, minute=0, second=0, microsecond=0)
    if now.weekday() >= 5:
        start = now
    end = (start + timedelta(days=2 if start.weekday() == 5 else 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    await send_events(
        message, await event_service.between(start, end, preferences), preferences.timezone,
        "No matching events are currently announced for this weekend. The list refreshes every two hours.",
    )
