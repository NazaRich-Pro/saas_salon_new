"""
Background tasks for notifications (reminders, follow-ups, etc.).
Enhanced with retry logic and exponential backoff.
"""
import logging
from datetime import datetime, timedelta

from apps.bookings.models import Appointment
from celery import shared_task
from django.utils import timezone

from .services import EmailService, TelegramService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,  # 1 minute base delay
    autoretry_for=(Exception,),
    retry_backoff=True,  # Exponential backoff
    retry_backoff_max=3600,  # Max 1 hour
    retry_jitter=True,  # Add randomness to prevent thundering herd
)
def send_appointment_reminders_24h(self):
    """
    Send 24-hour appointment reminders.
    Runs daily at 9 AM.
    """
    try:
        now = timezone.now()
        tomorrow = now + timedelta(hours=24)

        # Find appointments in 24-26 hours (2-hour window)
        window_start = now + timedelta(hours=24)
        window_end = now + timedelta(hours=26)

        appointments = Appointment.objects.filter(
            start_at__gte=window_start,
            start_at__lt=window_end,
            status__in=["PENDING", "CONFIRMED"],
        ).select_related("customer", "staff", "tenant")

        email_service = EmailService()
        reminders_sent = 0

        for appointment in appointments:
            try:
                if appointment.customer.email:
                    email_service.send_reminder_24h(
                        appointment=appointment, to_email=appointment.customer.email
                    )
                    reminders_sent += 1

                    logger.info(f"Sent 24h reminder for appointment {appointment.id}")

            except Exception as e:
                logger.error(
                    f"Failed to send 24h reminder for appointment {appointment.id}: {e}"
                )
                continue

        logger.info(f"Sent {reminders_sent} 24-hour reminders")

        return {
            "status": "success",
            "reminders_sent": reminders_sent,
            "appointments_checked": appointments.count(),
        }

    except Exception as exc:
        logger.error(f"Error in send_appointment_reminders_24h: {exc}")
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=1800,
    retry_jitter=True,
)
def send_appointment_reminders_2h(self):
    """
    Send 2-hour appointment reminders.
    Runs every 30 minutes.
    """
    try:
        now = timezone.now()

        # Find appointments in 2-2.5 hours
        window_start = now + timedelta(hours=2)
        window_end = now + timedelta(hours=2, minutes=30)

        appointments = Appointment.objects.filter(
            start_at__gte=window_start,
            start_at__lt=window_end,
            status__in=["PENDING", "CONFIRMED"],
        ).select_related("customer", "staff", "tenant")

        email_service = EmailService()
        telegram_service = TelegramService()
        reminders_sent = 0

        for appointment in appointments:
            try:
                # Send email
                if appointment.customer.email:
                    email_service.send_reminder_2h(
                        appointment=appointment, to_email=appointment.customer.email
                    )
                    reminders_sent += 1

                # Send Telegram if available
                if appointment.customer.telegram_chat_id:
                    telegram_service.send_reminder_2h(
                        appointment=appointment,
                        chat_id=appointment.customer.telegram_chat_id,
                    )

                logger.info(f"Sent 2h reminder for appointment {appointment.id}")

            except Exception as e:
                logger.error(
                    f"Failed to send 2h reminder for appointment {appointment.id}: {e}"
                )
                continue

        logger.info(f"Sent {reminders_sent} 2-hour reminders")

        return {
            "status": "success",
            "reminders_sent": reminders_sent,
            "appointments_checked": appointments.count(),
        }

    except Exception as exc:
        logger.error(f"Error in send_appointment_reminders_2h: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300, retry_backoff=True)
def send_followup_messages(self):
    """
    Send follow-up messages to customers after completed appointments.
    Runs daily at 10 AM, sends to appointments completed 1 day ago.
    """
    try:
        yesterday = timezone.now().date() - timedelta(days=1)

        # Find completed appointments from yesterday
        appointments = Appointment.objects.filter(
            status="COMPLETED", end_at__date=yesterday
        ).select_related("customer", "staff", "tenant")

        email_service = EmailService()
        followups_sent = 0

        for appointment in appointments:
            try:
                if appointment.customer.email:
                    email_service.send_followup(
                        appointment=appointment, to_email=appointment.customer.email
                    )
                    followups_sent += 1

                    logger.info(f"Sent follow-up for appointment {appointment.id}")

            except Exception as e:
                logger.error(
                    f"Failed to send follow-up for appointment {appointment.id}: {e}"
                )
                continue

        logger.info(f"Sent {followups_sent} follow-up messages")

        return {
            "status": "success",
            "followups_sent": followups_sent,
            "date": yesterday.isoformat(),
        }

    except Exception as exc:
        logger.error(f"Error in send_followup_messages: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_email(self, to_email, subject, body, tenant_id=None):
    """
    Generic task to send an email notification.
    Used for one-off notifications.
    """
    try:
        from apps.tenants.models import Tenant

        tenant = None
        if tenant_id:
            tenant = Tenant.objects.get(id=tenant_id)

        email_service = EmailService()
        email_service.send_email(
            to_email=to_email, subject=subject, body=body, tenant=tenant
        )

        logger.info(f"Sent notification email to {to_email}")

        return {"status": "success", "to_email": to_email}

    except Exception as exc:
        logger.error(f"Error sending notification email to {to_email}: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_telegram_notification(self, chat_id, message):
    """
    Generic task to send a Telegram notification.
    """
    try:
        telegram_service = TelegramService()
        telegram_service.send_message(chat_id=chat_id, message=message)

        logger.info(f"Sent Telegram notification to chat {chat_id}")

        return {"status": "success", "chat_id": chat_id}

    except Exception as exc:
        logger.error(f"Error sending Telegram notification to {chat_id}: {exc}")
        raise self.retry(exc=exc)
