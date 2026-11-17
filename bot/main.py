"""Application entry point: ``python -m bot.main``."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
import httpx

from bot.handlers import router
from collectors.eventbrite import EventbriteCollector
from collectors.meetup import MeetupCollector
from collectors.websites import WebsiteCollector
from config import settings
from database.repository import Repository
from scheduler.jobs import create_scheduler
from services.event_service import EventService
from services.notifications import NotificationService


async def main() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required; copy .env.example to .env and configure it")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    repository = Repository(settings.database_path)
    await repository.initialize()

    bot = Bot(settings.telegram_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    dispatcher.include_router(router())
    dispatcher["repository"] = repository

    async with httpx.AsyncClient(timeout=20, headers={"User-Agent": "BerlinRadar/1.0"}) as client:
        collectors = [
            EventbriteCollector(client, settings.eventbrite_token),
            MeetupCollector(client, settings.meetup_access_token),
            WebsiteCollector(client, settings.event_feed_urls),
        ]
        event_service = EventService(repository, collectors, settings.timezone, settings.default_city)
        notifications = NotificationService(bot, repository, event_service)
        dispatcher["event_service"] = event_service
        scheduler = create_scheduler(event_service, notifications, settings.event_update_interval_hours,
                                     settings.notification_hour, settings.timezone)
        scheduler.start()
        try:
            await bot.set_my_commands([
                BotCommand(command="start", description="Start BerlinRadar"),
                BotCommand(command="events", description="Upcoming events"),
                BotCommand(command="week", description="Events this week"),
                BotCommand(command="weekend", description="Events this weekend"),
                BotCommand(command="free", description="Free events"),
                BotCommand(command="search", description="Search by keyword"),
                BotCommand(command="settings", description="Event preferences"),
                BotCommand(command="subscribe", description="Toggle notifications"),
                BotCommand(command="delete_me", description="Delete my stored data"),
            ])
            await event_service.collect()
            await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
        finally:
            scheduler.shutdown(wait=False)
            await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
