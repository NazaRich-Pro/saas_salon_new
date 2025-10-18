"""
Background tasks for booking management.
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from apps.tenants.models import Membership, Tenant
from celery import shared_task
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from .models import Appointment

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)  # 5 minutes
def archive_old_appointments(self):
    """
    Archive appointments older than 60 days that are completed.
    Updates status to ARCHIVED for historical records.
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=60)

        # Find old completed appointments
        old_appointments = Appointment.objects.filter(
            status="COMPLETED",
            end_at__lt=cutoff_date,
            archived_at__isnull=True,  # Not already archived
        )

        archived_count = 0

        for appointment in old_appointments:
            appointment.archived_at = timezone.now()
            appointment.save(update_fields=["archived_at"])
            archived_count += 1

        logger.info(
            f"Archived {archived_count} old appointments (older than {cutoff_date})"
        )

        return {
            "status": "success",
            "archived_count": archived_count,
            "cutoff_date": cutoff_date.isoformat(),
        }

    except Exception as exc:
        logger.error(f"Error archiving old appointments: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_daily_digest(self):
    """
    Send daily digest email to salon admins with yesterday's KPIs.
    Includes: revenue, appointments, no-shows, top staff, etc.
    """
    from apps.notifications.services import EmailService

    try:
        yesterday = timezone.now().date() - timedelta(days=1)

        # Get all active tenants
        tenants = Tenant.objects.filter(status="ACTIVE")

        digests_sent = 0

        for tenant in tenants:
            try:
                # Get yesterday's appointments for this tenant
                appointments = Appointment.objects.filter(
                    tenant=tenant, start_at__date=yesterday
                )

                if not appointments.exists():
                    # Skip if no appointments yesterday
                    continue

                # Calculate KPIs
                total_appointments = appointments.count()
                completed = appointments.filter(status="COMPLETED").count()
                no_shows = appointments.filter(status="NO_SHOW").count()
                cancelled = appointments.filter(status="CANCELLED").count()

                completion_rate = (
                    (completed / total_appointments * 100)
                    if total_appointments > 0
                    else 0
                )
                no_show_rate = (
                    (no_shows / total_appointments * 100)
                    if total_appointments > 0
                    else 0
                )

                # Revenue
                revenue = appointments.filter(status="COMPLETED").aggregate(
                    total=Sum("total_price_kgs")
                )["total"] or Decimal("0.00")

                # Top staff
                top_staff = (
                    appointments.filter(status="COMPLETED")
                    .values("staff__name")
                    .annotate(revenue=Sum("total_price_kgs"), count=Count("id"))
                    .order_by("-revenue")[:3]
                )

                # Get salon admins
                admins = Membership.objects.filter(
                    tenant=tenant, role=Membership.ROLE_SALON_ADMIN
                ).select_related("user")

                # Prepare email context
                context = {
                    "tenant_name": tenant.name,
                    "date": yesterday.strftime("%d.%m.%Y"),
                    "total_appointments": total_appointments,
                    "completed": completed,
                    "no_shows": no_shows,
                    "cancelled": cancelled,
                    "completion_rate": round(completion_rate, 1),
                    "no_show_rate": round(no_show_rate, 1),
                    "total_revenue": float(revenue),
                    "top_staff": [
                        {
                            "name": item["staff__name"],
                            "revenue": float(item["revenue"]),
                            "count": item["count"],
                        }
                        for item in top_staff
                    ],
                    "dashboard_url": f"https://{tenant.slug}.saas.akylman.online/dashboard",
                }

                # Send to each admin
                email_service = EmailService()

                for membership in admins:
                    if membership.user.email:
                        email_service.send_daily_digest(
                            to_email=membership.user.email,
                            tenant=tenant,
                            context=context,
                        )
                        digests_sent += 1

                logger.info(
                    f"Sent daily digest to {admins.count()} admins for tenant {tenant.slug}"
                )

            except Exception as e:
                logger.error(f"Error sending digest for tenant {tenant.slug}: {e}")
                continue

        logger.info(
            f"Daily digest task completed. Sent {digests_sent} emails to admins."
        )

        return {
            "status": "success",
            "digests_sent": digests_sent,
            "date": yesterday.isoformat(),
        }

    except Exception as exc:
        logger.error(f"Error in send_daily_digest: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True)
def generate_report_async(self, tenant_id, report_type, params):
    """
    Generate a report asynchronously for large datasets.
    Used for PDF reports or complex analytics.
    """
    try:
        from apps.tenants.models import Tenant

        tenant = Tenant.objects.get(id=tenant_id)

        logger.info(f"Generating {report_type} report for tenant {tenant.slug}")

        # Here would be actual report generation logic
        # For now, just a placeholder

        return {
            "status": "success",
            "tenant_id": str(tenant_id),
            "report_type": report_type,
            "generated_at": timezone.now().isoformat(),
        }

    except Exception as exc:
        logger.error(f"Error generating report: {exc}")
        raise self.retry(exc=exc, max_retries=1)


@shared_task(ignore_result=True)
def update_appointment_stats(appointment_id):
    """
    Update statistics for an appointment after changes.
    Can be used for analytics aggregation.
    """
    try:
        appointment = Appointment.objects.get(id=appointment_id)

        # Here would be logic to update aggregated stats
        # For example, updating tenant's daily stats cache

        logger.debug(f"Updated stats for appointment {appointment_id}")

    except Appointment.DoesNotExist:
        logger.warning(f"Appointment {appointment_id} not found for stats update")
    except Exception as exc:
        logger.error(f"Error updating appointment stats: {exc}")
