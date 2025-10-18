"""Payment views"""
from decimal import Decimal

from apps.booking.models import Appointment
from apps.tenants.mixins import TenantViewSetMixin
from apps.tenants.permissions import IsReception, IsSuperAdmin, IsTenantAdmin
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .birthday_service import BirthdayService
from .coupon_service import CouponApplicationError, CouponService
from .loyalty_service import LoyaltyService, LoyaltyServiceError
from .models import Coupon, GiftCard, LoyaltyRule, Payment, SaaSSubscription
from .providers import get_provider
from .serializers import (
    CouponSerializer,
    CouponValidateSerializer,
    GiftCardSerializer,
    LoyaltyRuleSerializer,
    MarkCashPaidSerializer,
    PaymentRefundSerializer,
    PaymentSerializer,
    SaaSSubscriptionSerializer,
    StripePaymentIntentSerializer,
)


class PaymentViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for payments"""

    queryset = Payment.objects.select_related("appointment", "processed_by").all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsReception]

    def get_queryset(self):
        qs = super().get_queryset()

        # Filter by appointment
        appointment_id = self.request.query_params.get("appointment")
        if appointment_id:
            qs = qs.filter(appointment_id=appointment_id)

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Filter by type
        type_filter = self.request.query_params.get("type")
        if type_filter:
            qs = qs.filter(type=type_filter)

        return qs.order_by("-created_at")


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsReception])
def mark_cash_paid(request):
    """
    Mark appointment as paid in cash
    Creates a Payment record with MANUAL_CASH provider
    """
    serializer = MarkCashPaidSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    appointment_id = serializer.validated_data["appointment_id"]
    amount_kgs = serializer.validated_data["amount_kgs"]
    notes = serializer.validated_data.get("notes", "")

    # Get appointment
    try:
        appointment = Appointment.objects.get(id=appointment_id, tenant=request.tenant)
    except Appointment.DoesNotExist:
        return Response(
            {"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND
        )

    # Check if already paid
    existing_payment = Payment.objects.filter(
        appointment=appointment, status="SUCCEEDED"
    ).first()

    if existing_payment:
        return Response(
            {"error": "Appointment already has a successful payment"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Process payment via ManualCash provider
    provider = get_provider("MANUAL_CASH")

    result = provider.process_payment(
        amount=amount_kgs,
        currency="KGS",
        metadata={
            "processed_by": str(request.user.id),
            "appointment_id": str(appointment_id),
            "notes": notes,
        },
    )

    # Create Payment record
    payment = Payment.objects.create(
        tenant=request.tenant,
        appointment=appointment,
        type="CASH",
        provider="MANUAL_CASH",
        status=result["status"],
        amount_kgs=amount_kgs,
        external_ref=result["transaction_id"],
        metadata=result["extra"],
        processed_by=request.user,
        processed_at=timezone.now(),
    )

    # Update appointment prepaid amount
    appointment.prepaid_kgs += amount_kgs
    appointment.save(update_fields=["prepaid_kgs", "updated_at"])

    # Serialize response
    payment_serializer = PaymentSerializer(payment)

    return Response(
        {"message": "Payment marked as received", "payment": payment_serializer.data},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_stripe_intent(request):
    """
    Create Stripe PaymentIntent (stub)

    This endpoint will be used by frontend to initialize Stripe payment
    Currently returns a stub response
    """
    serializer = StripePaymentIntentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    amount_kgs = serializer.validated_data["amount_kgs"]
    appointment_id = serializer.validated_data.get("appointment_id")
    metadata = serializer.validated_data.get("metadata", {})

    # Get Stripe provider
    provider = get_provider("STRIPE")

    # Create payment intent
    result = provider.process_payment(
        amount=amount_kgs, currency="KGS", metadata=metadata
    )

    # Create Payment record in PENDING status
    payment_data = {
        "tenant": request.tenant,
        "type": "ONLINE",
        "provider": "STRIPE",
        "status": "PENDING",
        "amount_kgs": amount_kgs,
        "external_ref": result["transaction_id"],
        "metadata": result["extra"],
    }

    if appointment_id:
        try:
            appointment = Appointment.objects.get(
                id=appointment_id, tenant=request.tenant
            )
            payment_data["appointment"] = appointment
        except Appointment.DoesNotExist:
            pass

    payment = Payment.objects.create(**payment_data)

    return Response(
        {
            "payment_id": str(payment.id),
            "client_secret": result["extra"]["client_secret"],
            "payment_intent_id": result["transaction_id"],
            "amount": result["extra"]["amount"],
            "currency": result["extra"]["currency"],
            "note": "This is a stub. Real Stripe integration pending.",
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsReception])
def refund_payment(request):
    """
    Refund a payment (full or partial)
    """
    serializer = PaymentRefundSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    payment_id = serializer.validated_data["payment_id"]
    amount_kgs = serializer.validated_data.get("amount_kgs")
    reason = serializer.validated_data.get("reason", "")

    # Get payment
    try:
        payment = Payment.objects.get(id=payment_id, tenant=request.tenant)
    except Payment.DoesNotExist:
        return Response(
            {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
        )

    # Check if payment can be refunded
    if payment.status != "SUCCEEDED":
        return Response(
            {"error": f"Cannot refund payment with status: {payment.status}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Process refund via provider
    provider = get_provider(payment.provider)

    refund_result = provider.refund_payment(
        transaction_id=payment.external_ref, amount=amount_kgs
    )

    # Update payment status
    payment.status = "REFUNDED"
    payment.metadata["refund"] = refund_result
    payment.metadata["refund_reason"] = reason
    payment.save(update_fields=["status", "metadata", "updated_at"])

    # Update appointment prepaid if applicable
    if payment.appointment:
        refund_amount = amount_kgs or payment.amount_kgs
        payment.appointment.prepaid_kgs -= refund_amount
        payment.appointment.save(update_fields=["prepaid_kgs", "updated_at"])

    return Response(
        {
            "message": "Payment refunded",
            "refund_id": refund_result.get("refund_id"),
            "amount_refunded": str(amount_kgs or payment.amount_kgs),
        },
        status=status.HTTP_200_OK,
    )


class CouponViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for coupons"""

    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def get_queryset(self):
        qs = super().get_queryset()

        # Filter active only
        if self.action == "list":
            active_only = self.request.query_params.get("active_only", "false")
            if active_only.lower() == "true":
                qs = qs.filter(is_active=True)

        return qs.order_by("-created_at")

    @action(detail=False, methods=["post"], url_path="validate")
    def validate_coupon(self, request):
        """Validate a coupon code"""
        serializer = CouponValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]
        appointment_total = serializer.validated_data["appointment_total"]

        try:
            coupon = Coupon.objects.get(
                tenant=request.tenant, code=code.upper(), is_active=True
            )
        except Coupon.DoesNotExist:
            return Response(
                {"error": "Invalid coupon code"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check validity
        now = timezone.now()
        if now < coupon.valid_from or now > coupon.valid_to:
            return Response(
                {"error": "Coupon has expired or not yet valid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check usage limits
        if coupon.max_uses and coupon.uses_count >= coupon.max_uses:
            return Response(
                {"error": "Coupon usage limit reached"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate discount
        if coupon.kind == "PERCENT":
            discount = (appointment_total * coupon.value) / 100
        else:  # FIXED
            discount = coupon.value

        # Ensure discount doesn't exceed total
        discount = min(discount, appointment_total)

        return Response(
            {
                "valid": True,
                "coupon": CouponSerializer(coupon).data,
                "discount_kgs": str(discount),
                "final_amount_kgs": str(appointment_total - discount),
            },
            status=status.HTTP_200_OK,
        )


class GiftCardViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for gift cards"""

    queryset = GiftCard.objects.all()
    serializer_class = GiftCardSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]


class LoyaltyRuleViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """ViewSet for loyalty rules"""

    queryset = LoyaltyRule.objects.all()
    serializer_class = LoyaltyRuleSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]


class SaaSSubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for SaaS subscriptions (Superadmin only)"""

    queryset = SaaSSubscription.objects.select_related("tenant").all()
    serializer_class = SaaSSubscriptionSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        """Mark subscription invoice as paid (manual)"""
        subscription = self.get_object()

        # Extend period
        from datetime import timedelta

        subscription.last_payment_date = timezone.now().date()
        subscription.next_payment_date = subscription.period_end + timedelta(days=1)
        subscription.period_start = subscription.period_end + timedelta(days=1)
        subscription.period_end = subscription.period_start + timedelta(days=30)
        subscription.status = "ACTIVE"
        subscription.grace_until = None

        subscription.save()

        return Response(
            {
                "message": "Subscription marked as paid and extended",
                "next_payment_date": subscription.next_payment_date,
            },
            status=status.HTTP_200_OK,
        )
