"""Celery tasks for payments and loyalty"""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def process_daily_birthday_campaigns():
    """
    Process birthday campaigns - run daily at 9 AM
    Creates birthday coupons and sends greetings
    """
    from apps.tenants.models import Tenant

    from .birthday_service import BirthdayService

    total_processed = 0
    total_sent = 0

    # Process for all active tenants
    tenants = Tenant.objects.filter(status__in=["TRIAL", "ACTIVE", "GRACE"])

    for tenant in tenants:
        try:
            service = BirthdayService(tenant)
            result = service.process_birthday_campaigns()

            total_processed += result["total_birthdays"]
            total_sent += result["greetings_sent"]

            if result["total_birthdays"] > 0:
                logger.info(
                    f"Birthday campaigns for {tenant.name}: "
                    f"{result['greetings_sent']}/{result['total_birthdays']} sent"
                )

            if result["errors"]:
                logger.warning(
                    f"Birthday campaign errors for {tenant.name}: {result['errors']}"
                )

        except Exception as e:
            logger.error(f"Error processing birthdays for {tenant.name}: {str(e)}")

    logger.info(
        f"Birthday campaigns complete: {total_sent}/{total_processed} greetings sent"
    )

    return f"Processed {total_processed} birthdays, sent {total_sent} greetings"


@shared_task
def cleanup_expired_coupons():
    """
    Cleanup expired coupons - deactivate them
    Run daily at 2 AM
    """
    from .models import Coupon

    expired_count = Coupon.objects.filter(
        is_active=True, valid_to__lt=timezone.now()
    ).update(is_active=False)

    logger.info(f"Deactivated {expired_count} expired coupons")

    return f"Deactivated {expired_count} expired coupons"


@shared_task
def send_birthday_email(greeting_data: dict):
    """
    Send birthday greeting email

    This is a placeholder - will be fully implemented in Stage 8

    Args:
        greeting_data: Dict with customer info and coupon
    """
    # Will be implemented in Stage 8 with actual email sending
    logger.info(
        f"Birthday email queued for {greeting_data['customer_email']} "
        f"with coupon {greeting_data['coupon_code']}"
    )

    return f"Birthday email sent to {greeting_data['customer_email']}"


@shared_task
def award_loyalty_points_for_completed_appointments():
    """
    Award loyalty points for recently completed appointments
    Run every hour as a safety net (points should be awarded on completion)
    """
    from datetime import timedelta

    from apps.booking.models import Appointment

    # Find completed appointments from last hour without loyalty points awarded
    one_hour_ago = timezone.now() - timedelta(hours=1)

    appointments = Appointment.objects.filter(
        status="COMPLETED",
        updated_at__gte=one_hour_ago,
        internal_notes__icontains="loyalty_points_awarded",
    ).select_related("customer", "tenant")

    # This is a safety net - points should already be awarded in completion logic
    # Just log if we find any

    if appointments.exists():
        logger.warning(
            f"Found {appointments.count()} completed appointments needing loyalty points"
        )

    return f"Checked loyalty points for {appointments.count()} appointments"
