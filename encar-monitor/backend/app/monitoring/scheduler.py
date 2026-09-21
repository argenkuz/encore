from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.monitoring.monitor import EncarMonitor
from app.telegram.notifications import TelegramNotifier


class MonitorScheduler:

    def __init__(
        self,
        bot: Bot,
    ):
        notifier = TelegramNotifier(bot)

        self.monitor = EncarMonitor(
            notifier=notifier,
        )

        self.scheduler = AsyncIOScheduler()

    def start(self):
        self.scheduler.add_job(
            self.monitor.check_all_filters,
            "interval",
            minutes=settings.monitor_interval_minutes,
            id="encar_monitor",
            replace_existing=True,
            max_instances=1,
        )

        self.scheduler.start()

        print(
            "Monitor scheduler started "
            f"({settings.monitor_interval_minutes} min)."
        )

    def update_interval(
        self,
        minutes: int,
    ):
        job = self.scheduler.get_job(
            "encar_monitor"
        )

        if job is None:
            raise RuntimeError(
                "Monitor scheduler is not running."
            )

        self.scheduler.reschedule_job(
            "encar_monitor",
            trigger="interval",
            minutes=minutes,
        )

        settings.monitor_interval_minutes = minutes

        print(
            f"Monitor interval changed to "
            f"{minutes} minutes."
        )

    async def stop(self):
        self.scheduler.shutdown(
            wait=False,
        )

        await self.monitor.close()

        print(
            "Monitor scheduler stopped."
        )