"""
Reports and analytics views for booking data.
Provides revenue reports, no-show statistics, and CSV exports.
"""
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List

from apps.payments.models import Payment
from apps.tenants.permissions import IsTenantAdmin, IsTenantMember
from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Appointment


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsTenantMember])
def revenue_report(request):
    """
    Revenue report with grouping by day/week/month/staff/service.

    Query params:
    - from: Start date (YYYY-MM-DD)
    - to: End date (YYYY-MM-DD)
    - group_by: 'day'|'week'|'month'|'staff'|'service' (default: 'day')
    """
    tenant = request.tenant

    # Parse date range
    try:
        from_date = datetime.strptime(request.GET.get("from", ""), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        from_date = date.today() - timedelta(days=30)

    try:
        to_date = datetime.strptime(request.GET.get("to", ""), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        to_date = date.today()

    group_by = request.GET.get("group_by", "day")

    # Base queryset: completed appointments in date range
    appointments = Appointment.objects.filter(
        tenant=tenant,
        status="COMPLETED",
        start_at__date__gte=from_date,
        start_at__date__lte=to_date,
    )

    # Group and aggregate based on group_by parameter
    if group_by == "day":
        data = (
            appointments.annotate(group_key=TruncDate("start_at"))
            .values("group_key")
            .annotate(
                count=Count("id"),
                total_revenue=Sum("total_price_kgs"),
                avg_revenue=Avg("total_price_kgs"),
            )
            .order_by("group_key")
        )

        result = [
            {
                "date": item["group_key"].isoformat(),
                "appointments_count": item["count"],
                "total_revenue": float(item["total_revenue"] or 0),
                "avg_revenue": float(item["avg_revenue"] or 0),
            }
            for item in data
        ]

    elif group_by == "week":
        data = (
            appointments.annotate(group_key=TruncWeek("start_at"))
            .values("group_key")
            .annotate(count=Count("id"), total_revenue=Sum("total_price_kgs"))
            .order_by("group_key")
        )

        result = [
            {
                "week": item["group_key"].isoformat(),
                "appointments_count": item["count"],
                "total_revenue": float(item["total_revenue"] or 0),
            }
            for item in data
        ]

    elif group_by == "month":
        data = (
            appointments.annotate(group_key=TruncMonth("start_at"))
            .values("group_key")
            .annotate(count=Count("id"), total_revenue=Sum("total_price_kgs"))
            .order_by("group_key")
        )

        result = [
            {
                "month": item["group_key"].isoformat(),
                "appointments_count": item["count"],
                "total_revenue": float(item["total_revenue"] or 0),
            }
            for item in data
        ]

    elif group_by == "staff":
        data = (
            appointments.values("staff__id", "staff__name")
            .annotate(
                count=Count("id"),
                total_revenue=Sum("total_price_kgs"),
                avg_revenue=Avg("total_price_kgs"),
            )
            .order_by("-total_revenue")
        )

        result = [
            {
                "staff_id": str(item["staff__id"]),
                "staff_name": item["staff__name"],
                "appointments_count": item["count"],
                "total_revenue": float(item["total_revenue"] or 0),
                "avg_revenue": float(item["avg_revenue"] or 0),
            }
            for item in data
        ]

    elif group_by == "service":
        # Get services through appointment_services relationship
        from apps.bookings.models import AppointmentService

        services_data = (
            AppointmentService.objects.filter(
                appointment__tenant=tenant,
                appointment__status="COMPLETED",
                appointment__start_at__date__gte=from_date,
                appointment__start_at__date__lte=to_date,
            )
            .values("service__id", "service__name")
            .annotate(count=Count("id"), total_revenue=Sum("price_kgs"))
            .order_by("-total_revenue")
        )

        result = [
            {
                "service_id": str(item["service__id"]),
                "service_name": item["service__name"],
                "bookings_count": item["count"],
                "total_revenue": float(item["total_revenue"] or 0),
            }
            for item in services_data
        ]

    else:
        return Response(
            {
                "error": "Invalid group_by parameter. Use: day, week, month, staff, or service."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Calculate summary
    summary = appointments.aggregate(
        total_appointments=Count("id"),
        total_revenue=Sum("total_price_kgs"),
        avg_revenue=Avg("total_price_kgs"),
    )

    return Response(
        {
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "group_by": group_by,
            "summary": {
                "total_appointments": summary["total_appointments"] or 0,
                "total_revenue": float(summary["total_revenue"] or 0),
                "avg_revenue": float(summary["avg_revenue"] or 0),
            },
            "data": result,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsTenantMember])
def no_show_report(request):
    """
    No-show statistics report.

    Query params:
    - from: Start date (YYYY-MM-DD)
    - to: End date (YYYY-MM-DD)
    """
    tenant = request.tenant

    # Parse date range
    try:
        from_date = datetime.strptime(request.GET.get("from", ""), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        from_date = date.today() - timedelta(days=30)

    try:
        to_date = datetime.strptime(request.GET.get("to", ""), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        to_date = date.today()

    # Get appointments in date range
    appointments = Appointment.objects.filter(
        tenant=tenant, start_at__date__gte=from_date, start_at__date__lte=to_date
    )

    # Count by status
    total = appointments.count()
    no_shows = appointments.filter(status="NO_SHOW").count()
    completed = appointments.filter(status="COMPLETED").count()
    cancelled = appointments.filter(status="CANCELLED").count()

    no_show_rate = (no_shows / total * 100) if total > 0 else 0
    completion_rate = (completed / total * 100) if total > 0 else 0

    # No-shows by staff
    no_shows_by_staff = (
        appointments.filter(status="NO_SHOW")
        .values("staff__id", "staff__name")
        .annotate(no_show_count=Count("id"))
        .order_by("-no_show_count")
    )

    # No-shows by day
    no_shows_by_day = (
        appointments.filter(status="NO_SHOW")
        .annotate(day=TruncDate("start_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    # Calculate lost revenue from no-shows
    lost_revenue = appointments.filter(status="NO_SHOW").aggregate(
        total=Sum("total_price_kgs")
    )["total"] or Decimal("0.00")

    return Response(
        {
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "summary": {
                "total_appointments": total,
                "completed": completed,
                "no_shows": no_shows,
                "cancelled": cancelled,
                "no_show_rate": round(no_show_rate, 2),
                "completion_rate": round(completion_rate, 2),
                "lost_revenue": float(lost_revenue),
            },
            "no_shows_by_staff": [
                {
                    "staff_id": str(item["staff__id"]),
                    "staff_name": item["staff__name"],
                    "no_show_count": item["no_show_count"],
                }
                for item in no_shows_by_staff
            ],
            "no_shows_by_day": [
                {"date": item["day"].isoformat(), "count": item["count"]}
                for item in no_shows_by_day
            ],
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsTenantMember])
def kpi_report(request):
    """
    Key Performance Indicators report.

    Query params:
    - from: Start date (YYYY-MM-DD)
    - to: End date (YYYY-MM-DD)
    """
    tenant = request.tenant

    # Parse date range
    try:
        from_date = datetime.strptime(request.GET.get("from", ""), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        from_date = date.today() - timedelta(days=30)

    try:
        to_date = datetime.strptime(request.GET.get("to", ""), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        to_date = date.today()

    # Get appointments in date range
    appointments = Appointment.objects.filter(
        tenant=tenant, start_at__date__gte=from_date, start_at__date__lte=to_date
    )

    # Calculate KPIs
    total_appointments = appointments.count()
    completed = appointments.filter(status="COMPLETED").count()
    no_shows = appointments.filter(status="NO_SHOW").count()
    cancelled = appointments.filter(status="CANCELLED").count()
    pending = appointments.filter(status="PENDING").count()

    completion_rate = (
        (completed / total_appointments * 100) if total_appointments > 0 else 0
    )
    no_show_rate = (
        (no_shows / total_appointments * 100) if total_appointments > 0 else 0
    )
    cancellation_rate = (
        (cancelled / total_appointments * 100) if total_appointments > 0 else 0
    )

    # Revenue metrics
    revenue_data = appointments.filter(status="COMPLETED").aggregate(
        total_revenue=Sum("total_price_kgs"), avg_revenue=Avg("total_price_kgs")
    )

    # Payment metrics
    payments = Payment.objects.filter(
        tenant=tenant,
        created_at__date__gte=from_date,
        created_at__date__lte=to_date,
        status="SUCCEEDED",
    )

    cash_revenue = payments.filter(type="CASH").aggregate(Sum("amount_kgs"))[
        "amount_kgs__sum"
    ] or Decimal("0.00")
    card_revenue = payments.filter(type="CARD").aggregate(Sum("amount_kgs"))[
        "amount_kgs__sum"
    ] or Decimal("0.00")
    online_revenue = payments.filter(type="ONLINE").aggregate(Sum("amount_kgs"))[
        "amount_kgs__sum"
    ] or Decimal("0.00")

    # Customer metrics
    unique_customers = appointments.values("customer").distinct().count()
    repeat_customers = (
        appointments.values("customer")
        .annotate(visit_count=Count("id"))
        .filter(visit_count__gt=1)
        .count()
    )

    repeat_rate = (
        (repeat_customers / unique_customers * 100) if unique_customers > 0 else 0
    )

    # Average booking window (days between created and start)
    avg_booking_window = appointments.annotate(
        booking_window=F("start_at") - F("created_at")
    ).aggregate(avg=Avg("booking_window"))["avg"]

    avg_booking_days = avg_booking_window.days if avg_booking_window else 0

    return Response(
        {
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "kpis": {
                "appointments": {
                    "total": total_appointments,
                    "completed": completed,
                    "pending": pending,
                    "no_shows": no_shows,
                    "cancelled": cancelled,
                    "completion_rate": round(completion_rate, 2),
                    "no_show_rate": round(no_show_rate, 2),
                    "cancellation_rate": round(cancellation_rate, 2),
                },
                "revenue": {
                    "total": float(revenue_data["total_revenue"] or 0),
                    "average_per_appointment": float(revenue_data["avg_revenue"] or 0),
                    "cash": float(cash_revenue),
                    "card": float(card_revenue),
                    "online": float(online_revenue),
                },
                "customers": {
                    "unique": unique_customers,
                    "repeat": repeat_customers,
                    "repeat_rate": round(repeat_rate, 2),
                    "avg_booking_window_days": avg_booking_days,
                },
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsTenantMember])
def export_csv(request):
    """
    Export appointments data to CSV.

    Query params:
    - from: Start date (YYYY-MM-DD)
    - to: End date (YYYY-MM-DD)
    - status: Filter by status (optional)
    """
    tenant = request.tenant

    # Parse date range
    try:
        from_date = datetime.strptime(request.GET.get("from", ""), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        from_date = date.today() - timedelta(days=30)

    try:
        to_date = datetime.strptime(request.GET.get("to", ""), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        to_date = date.today()

    # Get appointments
    appointments = (
        Appointment.objects.filter(
            tenant=tenant, start_at__date__gte=from_date, start_at__date__lte=to_date
        )
        .select_related("customer", "staff")
        .order_by("start_at")
    )

    # Filter by status if provided
    status_filter = request.GET.get("status")
    if status_filter:
        appointments = appointments.filter(status=status_filter)

    # Create CSV response
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response[
        "Content-Disposition"
    ] = f'attachment; filename="appointments_{from_date}_{to_date}.csv"'

    # Add BOM for Excel UTF-8 support
    response.write("\ufeff")

    writer = csv.writer(response)

    # Header row
    writer.writerow(
        [
            "ID",
            "Дата",
            "Время начала",
            "Время окончания",
            "Клиент",
            "Телефон",
            "Мастер",
            "Услуги",
            "Длительность (мин)",
            "Сумма (KGS)",
            "Предоплата (KGS)",
            "Статус",
            "Источник",
            "Заметки",
        ]
    )

    # Data rows
    for apt in appointments:
        # Get services for this appointment
        services = apt.services.all()
        services_str = ", ".join([s.name for s in services])

        writer.writerow(
            [
                str(apt.id),
                apt.start_at.date().isoformat(),
                apt.start_at.strftime("%H:%M"),
                apt.end_at.strftime("%H:%M"),
                apt.customer.name,
                apt.customer.phone or "",
                apt.staff.name,
                services_str,
                int((apt.end_at - apt.start_at).total_seconds() / 60),
                float(apt.total_price_kgs),
                float(apt.prepaid_kgs or 0),
                apt.status,
                apt.source or "",
                apt.notes or "",
            ]
        )

    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsTenantMember])
def payments_export_csv(request):
    """
    Export payments data to CSV.

    Query params:
    - from: Start date (YYYY-MM-DD)
    - to: End date (YYYY-MM-DD)
    """
    tenant = request.tenant

    # Parse date range
    try:
        from_date = datetime.strptime(request.GET.get("from", ""), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        from_date = date.today() - timedelta(days=30)

    try:
        to_date = datetime.strptime(request.GET.get("to", ""), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        to_date = date.today()

    # Get payments
    payments = (
        Payment.objects.filter(
            tenant=tenant,
            created_at__date__gte=from_date,
            created_at__date__lte=to_date,
        )
        .select_related("appointment", "appointment__customer")
        .order_by("created_at")
    )

    # Create CSV response
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response[
        "Content-Disposition"
    ] = f'attachment; filename="payments_{from_date}_{to_date}.csv"'

    # Add BOM for Excel UTF-8 support
    response.write("\ufeff")

    writer = csv.writer(response)

    # Header row
    writer.writerow(
        [
            "ID",
            "Дата",
            "Время",
            "Запись ID",
            "Клиент",
            "Сумма (KGS)",
            "Тип",
            "Провайдер",
            "Статус",
            "Внешний ID",
        ]
    )

    # Data rows
    for payment in payments:
        customer_name = (
            payment.appointment.customer.name if payment.appointment else "N/A"
        )
        appointment_id = str(payment.appointment.id) if payment.appointment else ""

        writer.writerow(
            [
                str(payment.id),
                payment.created_at.date().isoformat(),
                payment.created_at.strftime("%H:%M:%S"),
                appointment_id,
                customer_name,
                float(payment.amount_kgs),
                payment.type,
                payment.provider,
                payment.status,
                payment.external_ref or "",
            ]
        )

    return response
