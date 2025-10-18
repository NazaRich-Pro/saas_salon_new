"""
Celery configuration for BeautyHub SaaS.
Includes beat schedule for all periodic tasks.
"""
import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("beautyhub")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    # === Appointment Reminders ===
    "send-24h-reminders": {
        "task": "apps.notifications.tasks.send_appointment_reminders_24h",
        "schedule": crontab(hour=9, minute=0),  # 9 AM daily
        "options": {
            "expires": 3600,  # Task expires after 1 hour if not executed
        },
    },
    "send-2h-reminders": {
        "task": "apps.notifications.tasks.send_appointment_reminders_2h",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
        "options": {
            "expires": 1800,
        },
    },
    # === Follow-up Messages ===
    "send-followups": {
        "task": "apps.notifications.tasks.send_followup_messages",
        "schedule": crontab(hour=10, minute=0),  # 10 AM daily
        "options": {
            "expires": 3600,
        },
    },
    # === Birthday Campaigns ===
    "run-birthday-campaigns": {
        "task": "apps.payments.tasks.run_daily_birthday_campaigns",
        "schedule": crontab(hour=8, minute=0),  # 8 AM daily
        "options": {
            "expires": 3600,
        },
    },
    # === Daily Digest ===
    "send-daily-digest": {
        "task": "apps.bookings.tasks.send_daily_digest",
        "schedule": crontab(hour=20, minute=0),  # 8 PM daily
        "options": {
            "expires": 3600,
        },
    },
    # === Cleanup Tasks ===
    "cleanup-expired-tokens": {
        "task": "apps.auth.tasks.cleanup_expired_tokens",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
    },
    "cleanup-expired-coupons": {
        "task": "apps.payments.tasks.cleanup_expired_coupons",
        "schedule": crontab(hour=3, minute=0),  # 3 AM daily
    },
    "cleanup-old-login-attempts": {
        "task": "apps.auth.tasks.cleanup_old_login_attempts",
        "schedule": crontab(hour=3, minute=30),  # 3:30 AM daily
    },
    # === Auto-archive ===
    "archive-old-appointments": {
        "task": "apps.bookings.tasks.archive_old_appointments",
        "schedule": crontab(hour=4, minute=0),  # 4 AM daily
    },
    # === Loyalty Points ===
    "award-loyalty-points": {
        "task": "apps.payments.tasks.award_loyalty_points_for_completed",
        "schedule": crontab(hour=23, minute=0),  # 11 PM daily
    },
    # === Trial Lifecycle (already exists from Stage 9) ===
    "check-trial-expiring": {
        "task": "apps.onboarding.tasks.check_trial_expiring",
        "schedule": crontab(hour=9, minute=30),  # 9:30 AM daily
    },
    "check-trial-expired": {
        "task": "apps.onboarding.tasks.check_trial_expired",
        "schedule": crontab(hour=10, minute=0),  # 10 AM daily
    },
    "cleanup-inactive-trials": {
        "task": "apps.onboarding.tasks.cleanup_inactive_trials",
        "schedule": crontab(hour=5, minute=0),  # 5 AM daily
    },
    # === Monitoring ===
    "celery-health-check": {
        "task": "apps.core.tasks.celery_health_check",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
}

# Celery Task Configuration
app.conf.update(
    # Task retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Result backend
    result_backend="redis://redis:6379/1",
    result_expires=3600,  # Results expire after 1 hour
    # Task routing
    task_routes={
        "apps.notifications.tasks.*": {"queue": "notifications"},
        "apps.payments.tasks.*": {"queue": "payments"},
        "apps.bookings.tasks.*": {"queue": "bookings"},
        "apps.onboarding.tasks.*": {"queue": "onboarding"},
    },
    # Time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit
    # Prefetch
    worker_prefetch_multiplier=4,
    # Timezone
    timezone="UTC",
    enable_utc=True,
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f"Request: {self.request!r}")
