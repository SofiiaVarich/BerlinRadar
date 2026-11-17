"""Onboarding commands."""
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.keyboards.inline import main_menu
from database.repository import Repository

router = Router()


@router.message(CommandStart())
async def start(message: Message, repository: Repository) -> None:
    if message.from_user:
        await repository.ensure_user(message.from_user.id)
    await message.answer(
        "🚀 <b>Welcome to BerlinRadar!</b>\n\n"
        "Discover Berlin tech, startup, and business events.\n\n"
        "<b>Commands</b>\n"
        "/events — upcoming events\n/today — events today\n/week — this week\n/weekend — this weekend\n"
        "/free — free events\n/paid — paid events\n/hackathons — hackathons\n"
        "/offline — in-person events\n/search AI — keyword search\n/settings — preferences\n"
        "/subscribe — toggle daily recommendations\n/help — show this guide",
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
async def help_command(message: Message, repository: Repository) -> None:
    await start(message, repository)
