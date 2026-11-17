"""Inline keyboards used by event and settings messages."""
from datetime import timedelta
from urllib.parse import urlencode

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Category, Event, UserPreferences


EVENTS_BUTTON = "🔎 Upcoming events"
TODAY_BUTTON = "☀️ Today"
WEEK_BUTTON = "📅 This week"
WEEKEND_BUTTON = "🎉 This weekend"
FREE_BUTTON = "💚 Free events"
PAID_BUTTON = "💳 Paid events"
HACKATHONS_BUTTON = "💻 Hackathons"
OFFLINE_BUTTON = "🏢 Offline events"
SEARCH_BUTTON = "🔍 Search"
SETTINGS_BUTTON = "⚙️ Settings"
SUBSCRIBE_BUTTON = "🔔 Notifications"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=EVENTS_BUTTON), KeyboardButton(text=TODAY_BUTTON)],
            [KeyboardButton(text=WEEK_BUTTON), KeyboardButton(text=WEEKEND_BUTTON)],
            [KeyboardButton(text=FREE_BUTTON), KeyboardButton(text=PAID_BUTTON)],
            [KeyboardButton(text=HACKATHONS_BUTTON), KeyboardButton(text=OFFLINE_BUTTON)],
            [KeyboardButton(text=SEARCH_BUTTON), KeyboardButton(text=SETTINGS_BUTTON)],
            [KeyboardButton(text=SUBSCRIBE_BUTTON)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose an action or type a command",
    )


def event_keyboard(event: Event) -> InlineKeyboardMarkup:
    starts_at = event.starts_at.strftime("%Y%m%dT%H%M%SZ")
    ends_at = (event.starts_at + timedelta(hours=2)).strftime("%Y%m%dT%H%M%SZ")
    calendar_url = "https://calendar.google.com/calendar/render?" + urlencode({
        "action": "TEMPLATE",
        "text": event.title,
        "dates": f"{starts_at}/{ends_at}",
        "details": f"{event.description}\n\nRegistration: {event.url}".strip(),
        "location": event.location,
    })
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Register", url=event.url)],
        [InlineKeyboardButton(text="📅 Add to Google Calendar", url=calendar_url)],
    ])


def settings_keyboard(preferences: UserPreferences) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    selected = set(preferences.categories)
    for index, category in enumerate(Category):
        marker = "✅" if str(category) in selected else "▫️"
        builder.button(text=f"{marker} {category}", callback_data=f"category:{index}")
    builder.button(text=f"{'✅' if preferences.free_only else '▫️'} Free only", callback_data="free:toggle")
    builder.adjust(1)
    return builder.as_markup()
