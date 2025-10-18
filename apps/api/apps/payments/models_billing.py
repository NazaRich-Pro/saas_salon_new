"""Additional billing models"""
import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone


class Invoice(models.Model):
    """Invoice for SaaS subscription"""

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("OVERDUE", "Overdue"),
        ("CANCELLED", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="invoices"
    )
    subscription = models.ForeignKey(
        "SaaSSubscription", on_delete=models.CASCADE, related_name="invoices"
    )

    # Invoice details
    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    amount_kgs = models.DecimalField(max_digits=10, decimal_places=2)

    # Period
    period_start = models.DateField()
    period_end = models.DateField()

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PENDING", db_index=True
    )

    # Payment
    paid_at = models.DateTimeField(null=True, blank=True)
    paid_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_invoices",
    )
    payment = models.ForeignKey(
        "Payment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoice",
    )

    # Dates
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()

    # Notes
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoices"
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["status", "due_date"]),
            models.Index(fields=["invoice_number"]),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.tenant.name} ({self.status})"

    def is_overdue(self) -> bool:
        """Check if invoice is overdue"""
        if self.status == "PAID":
            return False

        from datetime import date

        return self.due_date < date.today()

    def mark_as_paid(self, paid_by=None):
        """Mark invoice as paid"""
        self.status = "PAID"
        self.paid_at = timezone.now()
        self.paid_by = paid_by
        self.save(update_fields=["status", "paid_at", "paid_by", "updated_at"])


class FeatureUsage(models.Model):
    """Track feature usage for billing and analytics"""

    FEATURE_CHOICES = [
        ("BOOKING", "Booking"),
        ("SMS", "SMS"),
        ("TELEGRAM", "Telegram"),
        ("API", "API Call"),
        ("WHITE_LABEL", "White Label"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="feature_usage"
    )

    feature = models.CharField(max_length=20, choices=FEATURE_CHOICES, db_index=True)
    count = models.IntegerField(default=0)

    # Date tracking
    date = models.DateField(db_index=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "feature_usage"
        verbose_name = "Feature Usage"
        verbose_name_plural = "Feature Usage"
        unique_together = [["tenant", "feature", "date"]]
        indexes = [
            models.Index(fields=["tenant", "date"]),
            models.Index(fields=["feature", "date"]),
        ]

    def __str__(self):
        return f"{self.tenant.name} - {self.feature} - {self.date}: {self.count}"
