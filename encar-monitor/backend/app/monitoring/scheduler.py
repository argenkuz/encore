from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.monitoring.monitor import EncarMonitor
from app.telegram.notifications import TelegramNotifier


class MonitorScheduler:

    def __init__(self, bot: Bot):
        notifier = TelegramNotifier(bot)

        self.monitor = EncarMonitor(
            notifier=notifier,
        )

        self.scheduler = AsyncIOScheduler()

    def start(self):
        self.scheduler.add_job(
            self.monitor.check_due_users,
            "interval",
            minutes=1,
            id="encar_monitor_tick",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30,
        )

        self.scheduler.start()

        print("Monitor scheduler started (1 minute tick).")

    async def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

        await self.monitor.close()

        print("Monitor scheduler stopped.")
