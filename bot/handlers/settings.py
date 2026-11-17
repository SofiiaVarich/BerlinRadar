"""Preference and subscription handlers."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import SETTINGS_BUTTON, SUBSCRIBE_BUTTON, settings_keyboard
from database.models import Category
from database.repository import Repository

router = Router()


@router.message(Command("settings"))
@router.message(F.text == SETTINGS_BUTTON)
async def settings_command(message: Message, repository: Repository) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    preferences = await repository.get_preferences(user_id)
    await message.answer("Choose categories and price preferences:", reply_markup=settings_keyboard(preferences))


@router.callback_query(F.data.startswith("category:"))
async def category_callback(query: CallbackQuery, repository: Repository) -> None:
    if not query.from_user or not query.data:
        return
    preferences = await repository.get_preferences(query.from_user.id)
    try:
        category = str(list(Category)[int(query.data.partition(":")[2])])
    except (ValueError, IndexError):
        await query.answer("Unknown category", show_alert=True)
        return
    if category in preferences.categories:
        preferences.categories.remove(category)
    else:
        preferences.categories.append(category)
    await repository.update_preferences(preferences)
    if query.message:
        await query.message.edit_reply_markup(reply_markup=settings_keyboard(preferences))
    await query.answer("Preferences updated")


@router.callback_query(F.data == "free:toggle")
async def free_callback(query: CallbackQuery, repository: Repository) -> None:
    preferences = await repository.get_preferences(query.from_user.id)
    preferences.free_only = not preferences.free_only
    await repository.update_preferences(preferences)
    if query.message:
        await query.message.edit_reply_markup(reply_markup=settings_keyboard(preferences))
    await query.answer("Preferences updated")


@router.message(Command("subscribe"))
@router.message(F.text == SUBSCRIBE_BUTTON)
async def subscribe_command(message: Message, repository: Repository) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    preferences = await repository.get_preferences(user_id)
    preferences.subscribed = not preferences.subscribed
    await repository.update_preferences(preferences)
    status = "enabled ✅" if preferences.subscribed else "disabled"
    await message.answer(f"Daily event recommendations are now <b>{status}</b>.")


@router.message(Command("delete_me"))
async def delete_me_command(message: Message, repository: Repository) -> None:
    user_id = message.from_user.id if message.from_user else message.chat.id
    await repository.delete_user(user_id)
    await message.answer(
        "Your preferences and notification history have been deleted. "
        "Use /start if you want to use BerlinRadar again."
    )
