"""Telegram command routers."""
from aiogram import Router

from bot.handlers import events, search, settings, start


def router() -> Router:
    root = Router()
    root.include_routers(start.router, events.router, search.router, settings.router)
    return root
