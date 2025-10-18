"""Payment serializers"""
from decimal import Decimal

from rest_framework import serializers

from .models import Coupon, GiftCard, LoyaltyRule, Payment, SaaSSubscription


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""

    appointment_info = serializers.SerializerMethodField()
    processed_by_name = serializers.CharField(
        source="processed_by.email", read_only=True, allow_null=True
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "appointment",
            "appointment_info",
            "type",
            "provider",
            "status",
            "amount_kgs",
            "external_ref",
            "metadata",
            "processed_by",
            "processed_by_name",
            "processed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "processed_at"]

    def get_appointment_info(self, obj):
        if not obj.appointment:
            return None

        return {
            "id": str(obj.appointment.id),
            "customer_name": obj.appointment.customer.name,
            "start_at": obj.appointment.start_at,
            "total_price_kgs": str(obj.appointment.total_price_kgs),
        }


class MarkCashPaidSerializer(serializers.Serializer):
    """Serializer for marking appointment as cash paid"""

    appointment_id = serializers.UUIDField()
    amount_kgs = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.01")
    )
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_amount_kgs(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value


class StripePaymentIntentSerializer(serializers.Serializer):
    """Serializer for creating Stripe payment intent"""

    amount_kgs = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.01")
    )
    appointment_id = serializers.UUIDField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False, default=dict)


class PaymentRefundSerializer(serializers.Serializer):
    """Serializer for payment refunds"""

    payment_id = serializers.UUIDField()
    amount_kgs = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Partial refund amount (leave empty for full refund)",
    )
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)


class CouponSerializer(serializers.ModelSerializer):
    """Serializer for Coupon model"""

    is_valid = serializers.SerializerMethodField()
    uses_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = [
            "id",
            "code",
            "kind",
            "value",
            "valid_from",
            "valid_to",
            "max_uses",
            "uses_count",
            "uses_remaining",
            "max_uses_per_customer",
            "rules",
            "is_active",
            "is_valid",
            "created_at",
        ]
        read_only_fields = ["id", "uses_count", "created_at"]

    def get_is_valid(self, obj):
        """Check if coupon is currently valid"""
        from django.utils import timezone

        now = timezone.now()

        if not obj.is_active:
            return False

        if now < obj.valid_from or now > obj.valid_to:
            return False

        if obj.max_uses and obj.uses_count >= obj.max_uses:
            return False

        return True

    def get_uses_remaining(self, obj):
        """Get remaining uses"""
        if not obj.max_uses:
            return None
        return max(0, obj.max_uses - obj.uses_count)


class CouponValidateSerializer(serializers.Serializer):
    """Serializer for validating a coupon code"""

    code = serializers.CharField(max_length=50)
    appointment_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    service_ids = serializers.ListField(child=serializers.UUIDField(), required=False)


class GiftCardSerializer(serializers.ModelSerializer):
    """Serializer for Gift Card model"""

    owner_name = serializers.CharField(
        source="owner_customer.name", read_only=True, allow_null=True
    )

    class Meta:
        model = GiftCard
        fields = [
            "id",
            "code",
            "balance_kgs",
            "initial_balance_kgs",
            "owner_customer",
            "owner_name",
            "valid_from",
            "valid_to",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class LoyaltyRuleSerializer(serializers.ModelSerializer):
    """Serializer for Loyalty Rule model"""

    class Meta:
        model = LoyaltyRule
        fields = [
            "id",
            "earn_per_100_kgs",
            "redeem_rate",
            "min_points_to_redeem",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SaaSSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for SaaS Subscription model"""

    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    days_until_expiry = serializers.SerializerMethodField()

    class Meta:
        model = SaaSSubscription
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "plan",
            "seats",
            "status",
            "period_start",
            "period_end",
            "grace_until",
            "monthly_price_kgs",
            "last_payment_date",
            "next_payment_date",
            "days_until_expiry",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_days_until_expiry(self, obj):
        """Calculate days until subscription expires"""
        from datetime import date

        from django.utils import timezone

        if obj.status == "CANCELLED":
            return 0

        today = date.today()

        if obj.grace_until and obj.grace_until >= today:
            return (obj.grace_until - today).days
        elif obj.period_end >= today:
            return (obj.period_end - today).days
        else:
            return 0
