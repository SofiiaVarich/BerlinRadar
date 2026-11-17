"""Inline keyboards used by event and settings messages."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Category, Event, UserPreferences


EVENTS_BUTTON = "🔎 Upcoming events"
WEEK_BUTTON = "📅 This week"
WEEKEND_BUTTON = "🎉 This weekend"
FREE_BUTTON = "💚 Free events"
SEARCH_BUTTON = "🔍 Search"
SETTINGS_BUTTON = "⚙️ Settings"
SUBSCRIBE_BUTTON = "🔔 Notifications"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=EVENTS_BUTTON), KeyboardButton(text=WEEK_BUTTON)],
            [KeyboardButton(text=WEEKEND_BUTTON), KeyboardButton(text=FREE_BUTTON)],
            [KeyboardButton(text=SEARCH_BUTTON), KeyboardButton(text=SETTINGS_BUTTON)],
            [KeyboardButton(text=SUBSCRIBE_BUTTON)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose an action or type a command",
    )


def event_keyboard(event: Event) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔗 Register", url=event.url)
    ]])


def settings_keyboard(preferences: UserPreferences) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    selected = set(preferences.categories)
    for index, category in enumerate(Category):
        marker = "✅" if str(category) in selected else "▫️"
        builder.button(text=f"{marker} {category}", callback_data=f"category:{index}")
    builder.button(text=f"{'✅' if preferences.free_only else '▫️'} Free only", callback_data="free:toggle")
    builder.adjust(1)
    return builder.as_markup()
