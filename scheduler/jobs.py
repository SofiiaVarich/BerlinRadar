"""APScheduler setup for collection and daily notifications."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from services.event_service import EventService
from services.notifications import NotificationService


def create_scheduler(event_service: EventService, notifications: NotificationService,
                     interval_hours: int, notification_hour: int, timezone: str) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=timezone)
    scheduler.add_job(event_service.collect, "interval", hours=interval_hours, id="collect-events",
                      replace_existing=True, max_instances=1, coalesce=True)
    scheduler.add_job(notifications.send_daily, "cron", hour=notification_hour, minute=0,
                      id="daily-notifications", replace_existing=True, max_instances=1)
    return scheduler
