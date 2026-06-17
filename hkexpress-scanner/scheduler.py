"""
HKExpress Price Scanner - Scheduler
Periodic scanning using APScheduler.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


class ScanScheduler:
    def __init__(self, scan_callback, interval_hours: int = 6,
                 jitter_minutes: int = 15):
        self.scan_callback = scan_callback
        self.interval_hours = interval_hours
        self.jitter_minutes = jitter_minutes
        self.scheduler = AsyncIOScheduler()
        self._next_run = None

    def start(self):
        """Start the periodic scheduler."""
        import random
        jitter = random.randint(0, self.jitter_minutes * 60)

        self.scheduler.add_job(
            self._run_scan,
            "interval",
            hours=self.interval_hours,
            jitter=jitter,
            id="hkexpress_scan",
            next_run_time=datetime.now() + timedelta(seconds=10)
            # Start 10 seconds after launch
        )

        self.scheduler.start()
        logger.info(
            f"Scheduler started: every {self.interval_hours}h "
            f"(±{self.jitter_minutes}m jitter)"
        )

    async def _run_scan(self):
        """Wrapper to run the async scan callback."""
        self._next_run = datetime.now() + timedelta(hours=self.interval_hours)
        logger.info("=== Scheduled scan starting ===")
        try:
            await self.scan_callback()
        except Exception as e:
            logger.error(f"Scheduled scan failed: {e}", exc_info=True)
        logger.info(f"=== Scan done, next: {self._next_run} ===")

    def stop(self):
        self.scheduler.shutdown(wait=False)

    @property
    def next_run_time(self):
        job = self.scheduler.get_job("hkexpress_scan")
        return job.next_run_time if job else None
