"""Keyword event search."""
from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bot.handlers.events import send_events
from bot.keyboards.inline import SEARCH_BUTTON
from database.repository import Repository
from services.event_service import EventService

router = Router()


@router.message(F.text == SEARCH_BUTTON)
async def search_button(message: Message) -> None:
    await message.answer("Type <code>/search</code> followed by a keyword, for example <code>/search AI</code>.")


@router.message(Command("search"))
async def search_command(message: Message, command: CommandObject, event_service: EventService,
                         repository: Repository) -> None:
    query = (command.args or "").strip()
    if not query:
        await message.answer("Usage: <code>/search AI</code>")
        return
    user_id = message.from_user.id if message.from_user else message.chat.id
    preferences = await repository.get_preferences(user_id)
    events = await event_service.upcoming(preferences=preferences, keyword=query)
    await send_events(message, events, preferences.timezone)
