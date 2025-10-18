"""Payment models"""
import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Payment(models.Model):
    """Payment transaction"""

    TYPE_CHOICES = [
        ("CASH", "Cash"),
        ("CARD", "Card"),
        ("ONLINE", "Online"),
    ]

    PROVIDER_CHOICES = [
        ("MANUAL_CASH", "Manual Cash"),
        ("STRIPE", "Stripe"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCEEDED", "Succeeded"),
        ("FAILED", "Failed"),
        ("REFUNDED", "Refunded"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="payments"
    )
    appointment = models.ForeignKey(
        "booking.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )

    # Payment info
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PENDING", db_index=True
    )

    # Amount
    amount_kgs = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )

    # External reference (from payment gateway)
    external_ref = models.CharField(
        max_length=255, blank=True, help_text="External payment ID from gateway"
    )

    # Metadata
    metadata = models.JSONField(
        default=dict, blank=True, help_text="Additional payment metadata"
    )

    # Audit
    processed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_payments",
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        indexes = [
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["appointment"]),
        ]

    def __str__(self):
        return f"Payment {self.id} - {self.amount_kgs} KGS ({self.status})"


class Coupon(models.Model):
    """Discount coupon"""

    KIND_CHOICES = [
        ("PERCENT", "Percentage"),
        ("FIXED", "Fixed Amount"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="coupons"
    )

    code = models.CharField(max_length=50, db_index=True)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Percentage (0-100) or fixed amount in KGS",
    )

    # Validity
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    # Usage limits
    max_uses = models.IntegerField(
        null=True, blank=True, help_text="Maximum number of uses (null = unlimited)"
    )
    uses_count = models.IntegerField(default=0)
    max_uses_per_customer = models.IntegerField(
        default=1, help_text="Max uses per customer"
    )

    # Rules (JSON):
    # {
    #   "min_amount": 1000,
    #   "services": ["uuid1", "uuid2"],
    #   "categories": ["uuid3"],
    #   "days": ["monday", "tuesday"],
    #   "time_from": "09:00",
    #   "time_to": "12:00"
    # }
    rules = models.JSONField(
        default=dict, blank=True, help_text="Coupon application rules"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "coupons"
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        unique_together = [["tenant", "code"]]
        indexes = [
            models.Index(fields=["tenant", "code", "is_active"]),
            models.Index(fields=["tenant", "valid_from", "valid_to"]),
        ]

    def __str__(self):
        return f"{self.code} ({self.tenant.name})"


class GiftCard(models.Model):
    """Gift card"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="gift_cards"
    )

    code = models.CharField(max_length=50, unique=True, db_index=True)
    balance_kgs = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    initial_balance_kgs = models.DecimalField(max_digits=10, decimal_places=2)

    # Owner (optional)
    owner_customer = models.ForeignKey(
        "booking.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gift_cards",
    )

    # Validity
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "gift_cards"
        verbose_name = "Gift Card"
        verbose_name_plural = "Gift Cards"
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["code", "is_active"]),
        ]

    def __str__(self):
        return f"Gift Card {self.code} - {self.balance_kgs} KGS"


class LoyaltyRule(models.Model):
    """Loyalty program rules for tenant"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="loyalty_rule"
    )

    # Earning rules
    earn_per_100_kgs = models.IntegerField(
        default=1, help_text="Points earned per 100 KGS spent"
    )

    # Redemption rules
    redeem_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        help_text="1 point = X KGS discount",
    )
    min_points_to_redeem = models.IntegerField(
        default=100, help_text="Minimum points to redeem"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "loyalty_rules"
        verbose_name = "Loyalty Rule"
        verbose_name_plural = "Loyalty Rules"

    def __str__(self):
        return f"Loyalty Rule for {self.tenant.name}"


class SaaSSubscription(models.Model):
    """SaaS subscription for tenant"""

    PLAN_CHOICES = [
        ("SOLO", "Solo Master"),
        ("SALON", "Salon"),
    ]

    STATUS_CHOICES = [
        ("TRIAL", "Trial"),
        ("ACTIVE", "Active"),
        ("GRACE", "Grace Period"),
        ("SUSPENDED", "Suspended"),
        ("CANCELLED", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="subscription"
    )

    plan = models.CharField(max_length=10, choices=PLAN_CHOICES)
    seats = models.IntegerField(default=1, help_text="Number of active seats (masters)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="TRIAL")

    # Billing periods
    period_start = models.DateField()
    period_end = models.DateField()
    grace_until = models.DateField(null=True, blank=True)

    # Pricing
    monthly_price_kgs = models.DecimalField(
        max_digits=10, decimal_places=2, default=500
    )

    # Payment status
    last_payment_date = models.DateField(null=True, blank=True)
    next_payment_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "saas_subscriptions"
        verbose_name = "SaaS Subscription"
        verbose_name_plural = "SaaS Subscriptions"
        indexes = [
            models.Index(fields=["status", "period_end"]),
            models.Index(fields=["next_payment_date"]),
        ]

    def __str__(self):
        return f"{self.tenant.name} - {self.plan} ({self.status})"


class AuditLog(models.Model):
    """Audit log for important actions"""

    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("PAYMENT", "Payment"),
        ("BOOKING", "Booking"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="audit_logs",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True)
    entity_type = models.CharField(max_length=50, help_text="Model name")
    entity_id = models.CharField(max_length=255, help_text="Object ID")

    # Metadata (what changed, etc.)
    metadata = models.JSONField(default=dict, blank=True)

    # IP and user agent
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_logs"
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        indexes = [
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} on {self.entity_type} by {self.user}"
