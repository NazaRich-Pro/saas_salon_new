"""Celery tasks for tenant management"""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def archive_inactive_trial_tenants():
    """
    Archive trial tenants that are inactive after 14 days
    Runs daily at 3:00 AM
    """
    from .models import Tenant

    # Find trial tenants that expired
    cutoff_date = timezone.now().date()

    expired_trials = Tenant.objects.filter(status="TRIAL", trial_ends__lt=cutoff_date)

    archived_count = 0

    for tenant in expired_trials:
        # Check if tenant has any activity
        from apps.booking.models import Appointment

        has_appointments = Appointment.objects.filter(tenant=tenant).exists()

        if not has_appointments:
            # No activity, suspend the tenant
            tenant.status = "SUSPENDED"
            tenant.save(update_fields=["status"])
            archived_count += 1

            logger.info(
                f"Archived inactive trial tenant: {tenant.name} (slug: {tenant.slug})"
            )

    logger.info(f"Archived {archived_count} inactive trial tenants")
    return f"Archived {archived_count} inactive trial tenants"


@shared_task
def check_trial_expiry():
    """
    Check trial period expiry and move to grace period
    Runs daily at 4:00 AM
    """
    from apps.payments.models import SaaSSubscription

    from .models import Tenant

    today = timezone.now().date()

    # Find trials expiring today
    expiring_trials = Tenant.objects.filter(status="TRIAL", trial_ends=today)

    moved_count = 0

    for tenant in expiring_trials:
        # Move to grace period (7 days)
        tenant.status = "GRACE"
        tenant.grace_until = today + timedelta(days=7)
        tenant.save(update_fields=["status", "grace_until"])

        # Update subscription
        try:
            subscription = SaaSSubscription.objects.get(tenant=tenant)
            subscription.status = "GRACE"
            subscription.grace_until = tenant.grace_until
            subscription.save(update_fields=["status", "grace_until"])
        except SaaSSubscription.DoesNotExist:
            pass

        moved_count += 1
        logger.info(f"Trial expired for {tenant.name}, moved to grace period")

    return f"Moved {moved_count} tenants to grace period"


@shared_task
def suspend_expired_grace_tenants():
    """
    Suspend tenants whose grace period has expired
    Runs daily at 5:00 AM
    """
    from .models import Tenant

    today = timezone.now().date()

    expired_grace = Tenant.objects.filter(status="GRACE", grace_until__lt=today)

    suspended_count = 0

    for tenant in expired_grace:
        tenant.status = "SUSPENDED"
        tenant.save(update_fields=["status"])

        suspended_count += 1
        logger.warning(f"Grace period expired, suspended tenant: {tenant.name}")

    return f"Suspended {suspended_count} tenants"
