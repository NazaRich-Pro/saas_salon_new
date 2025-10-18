"""Celery tasks for user management"""
from celery import shared_task
from django.utils import timezone

from .jwt_utils import cleanup_expired_tokens


@shared_task
def cleanup_expired_tokens_task():
    """
    Cleanup expired refresh tokens and device sessions
    Runs daily via Celery beat
    """
    cleanup_expired_tokens()
    return "Expired tokens cleaned up"


@shared_task
def cleanup_old_login_attempts():
    """
    Delete old login attempts (older than 90 days)
    """
    from datetime import timedelta

    from .models import LoginAttempt

    cutoff_date = timezone.now() - timedelta(days=90)
    deleted_count, _ = LoginAttempt.objects.filter(
        attempted_at__lt=cutoff_date
    ).delete()

    return f"Deleted {deleted_count} old login attempts"


@shared_task
def unlock_locked_accounts():
    """
    Unlock accounts that have passed their lock period
    """
    from .models import User

    locked_users = User.objects.filter(
        locked_until__isnull=False, locked_until__lt=timezone.now()
    )

    unlocked_count = 0
    for user in locked_users:
        user.reset_failed_login()
        unlocked_count += 1

    return f"Unlocked {unlocked_count} accounts"
