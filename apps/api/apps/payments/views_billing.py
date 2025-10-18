"""Views for billing and subscription management"""
from apps.tenants.permissions import IsSuperAdmin, IsTenantAdmin
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .billing_service import BillingError, BillingService
from .serializers import SaaSSubscriptionSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsTenantAdmin])
def get_subscription(request):
    """
    Get current subscription information

    Response:
        {
            "subscription": {...},
            "billing_status": {...},
            "features": {...}
        }
    """
    billing_service = BillingService(request.tenant)

    # Get subscription
    subscription_serializer = SaaSSubscriptionSerializer(billing_service.subscription)

    # Get billing status
    billing_status = billing_service.get_billing_status()

    # Get available features
    features = billing_service.get_features()

    return Response(
        {
            "subscription": subscription_serializer.data,
            "billing_status": billing_status,
            "features": features,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsTenantAdmin])
def update_seats(request):
    """
    Update number of seats

    Request:
        {
            "seats": 5
        }

    Response:
        {
            "message": "Seats updated",
            "subscription": {...}
        }
    """
    new_seats = request.data.get("seats")

    if not new_seats:
        return Response(
            {"error": "seats is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        new_seats = int(new_seats)
    except (ValueError, TypeError):
        return Response(
            {"error": "seats must be an integer"}, status=status.HTTP_400_BAD_REQUEST
        )

    billing_service = BillingService(request.tenant)

    try:
        subscription = billing_service.update_seats(new_seats)

        serializer = SaaSSubscriptionSerializer(subscription)

        return Response(
            {
                "message": f"Количество мест обновлено до {new_seats}",
                "subscription": serializer.data,
                "new_monthly_price": str(subscription.monthly_price_kgs),
            },
            status=status.HTTP_200_OK,
        )

    except BillingError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def billing_status(request):
    """
    Get billing status flags

    Response:
        {
            "status": "TRIAL",
            "is_trial": true,
            "booking_blocked": false,
            "admin_access": true,
            "days_remaining": 10,
            ...
        }
    """
    if not hasattr(request, "tenant") or request.tenant is None:
        return Response(
            {"error": "Tenant context required"}, status=status.HTTP_400_BAD_REQUEST
        )

    billing_service = BillingService(request.tenant)
    billing_status = billing_service.get_billing_status()

    return Response(billing_status, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def mark_invoice_paid_endpoint(request):
    """
    Mark invoice as paid (superadmin only)

    Request:
        {
            "tenant_id": "uuid",
            "payment_date": "2025-10-11"  // optional
        }

    Response:
        {
            "message": "Invoice marked as paid",
            "subscription": {...}
        }
    """
    tenant_id = request.data.get("tenant_id")
    payment_date_str = request.data.get("payment_date")

    if not tenant_id:
        return Response(
            {"error": "tenant_id is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Get tenant
    from apps.tenants.models import Tenant

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return Response({"error": "Tenant not found"}, status=status.HTTP_404_NOT_FOUND)

    # Parse payment date
    payment_date = None
    if payment_date_str:
        from datetime import datetime

        try:
            payment_date = datetime.strptime(payment_date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format (use YYYY-MM-DD)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Mark as paid
    billing_service = BillingService(tenant)
    subscription = billing_service.mark_invoice_paid(payment_date)

    serializer = SaaSSubscriptionSerializer(subscription)

    return Response(
        {
            "message": "Счет отмечен как оплаченный, подписка продлена",
            "subscription": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsTenantAdmin])
def current_invoice(request):
    """
    Get current invoice data

    Response:
        {
            "invoice_number": "INV-my-salon-202510",
            "amount_kgs": "1500.00",
            "period_start": "2025-10-01",
            "period_end": "2025-10-31",
            "due_date": "2025-10-31",
            "status": "TRIAL",
            ...
        }
    """
    billing_service = BillingService(request.tenant)
    invoice_data = billing_service.generate_invoice_data()

    return Response(invoice_data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def features(request):
    """
    Get available features for current plan

    Response:
        {
            "plan": "SALON",
            "seats": 3,
            "max_seats": 50,
            "max_bookings_per_day": 200,
            "sms_enabled": true,
            "telegram_enabled": true,
            "white_label": true,
            "api_access": true,
            "priority_support": true
        }
    """
    if not hasattr(request, "tenant") or request.tenant is None:
        return Response(
            {"error": "Tenant context required"}, status=status.HTTP_400_BAD_REQUEST
        )

    billing_service = BillingService(request.tenant)
    features = billing_service.get_features()

    return Response(features, status=status.HTTP_200_OK)
