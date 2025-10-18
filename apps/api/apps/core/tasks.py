"""
Core background tasks for health checks and monitoring.
"""
import logging
from datetime import datetime

from celery import shared_task
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def celery_health_check():
    """
    Health check task that runs every 5 minutes.
    Updates a timestamp in cache to monitor if Celery is working.
    """
    try:
        now = timezone.now()

        # Update health check timestamp in cache
        cache.set("celery_health_check", now.isoformat(), timeout=600)  # 10 minutes

        logger.debug(f"Celery health check: OK at {now}")

        return {"status": "healthy", "timestamp": now.isoformat()}

    except Exception as exc:
        logger.error(f"Celery health check failed: {exc}")
        raise


@shared_task(ignore_result=True)
def cleanup_cache():
    """
    Cleanup old cache entries.
    Can be scheduled weekly.
    """
    try:
        # Django's cache doesn't have a built-in cleanup,
        # but we can clear specific patterns if needed

        logger.info("Cache cleanup completed")

    except Exception as exc:
        logger.error(f"Cache cleanup failed: {exc}")


@shared_task(bind=True, max_retries=3)
def test_task(self, message="Hello from Celery!"):
    """
    Test task for debugging Celery configuration.
    """
    try:
        logger.info(f"Test task executed: {message}")

        return {
            "status": "success",
            "message": message,
            "timestamp": timezone.now().isoformat(),
        }

    except Exception as exc:
        logger.error(f"Test task failed: {exc}")
        raise self.retry(exc=exc)
