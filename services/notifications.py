"""Personalized notification delivery with send-once tracking."""
from __future__ import annotations

import logging
from aiogram import Bot

from bot.handlers.events import format_event
from bot.keyboards.inline import event_keyboard
from database.repository import Repository
from services.event_service import EventService

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, bot: Bot, repository: Repository, event_service: EventService) -> None:
        self.bot = bot
        self.repository = repository
        self.event_service = event_service

    async def send_daily(self) -> None:
        for preferences in await self.repository.subscribed_users():
            events = await self.event_service.upcoming(days=7, preferences=preferences, limit=5)
            for event in await self.repository.unsent(preferences.telegram_id, events):
                try:
                    await self.bot.send_message(preferences.telegram_id, format_event(event, preferences.timezone),
                                                reply_markup=event_keyboard(event), disable_web_page_preview=True)
                    if event.id is not None:
                        await self.repository.mark_sent(preferences.telegram_id, event.id)
                except Exception:
                    logger.exception("Unable to notify Telegram user %s", preferences.telegram_id)
