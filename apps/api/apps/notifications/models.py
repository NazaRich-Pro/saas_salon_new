"""Notification models"""
import uuid

from django.db import models


class NotificationTemplate(models.Model):
    """Email/Telegram notification templates"""

    KIND_CHOICES = [
        ("EMAIL", "Email"),
        ("TELEGRAM", "Telegram"),
        ("SMS", "SMS"),
    ]

    EVENT_CHOICES = [
        ("WELCOME", "Welcome"),
        ("REMINDER_24H", "Reminder 24h"),
        ("REMINDER_2H", "Reminder 2h"),
        ("FOLLOWUP", "Follow-up"),
        ("BIRTHDAY", "Birthday"),
        ("DAILY_DIGEST", "Daily Digest"),
    ]

    LANG_CHOICES = [
        ("RU", "Russian"),
        ("KG", "Kyrgyz"),
        ("EN", "English"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notification_templates",
    )

    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    event = models.CharField(max_length=50, choices=EVENT_CHOICES)
    lang = models.CharField(max_length=2, choices=LANG_CHOICES)

    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()

    # Metadata
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_templates"
        unique_together = [["tenant", "kind", "event", "lang"]]
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"

    def __str__(self):
        tenant_name = self.tenant.name if self.tenant else "Platform"
        return f"{self.event} - {self.lang} ({self.kind}) [{tenant_name}]"


class NotificationLog(models.Model):
    """Log of sent notifications"""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SENT", "Sent"),
        ("FAILED", "Failed"),
        ("BOUNCED", "Bounced"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notification_logs",
    )

    # Recipient
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    recipient_telegram_id = models.CharField(max_length=100, blank=True)

    # Notification details
    kind = models.CharField(max_length=20)  # EMAIL, TELEGRAM, SMS
    event = models.CharField(max_length=50)  # WELCOME, REMINDER_24H, etc

    # Content
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PENDING", db_index=True
    )

    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)

    # Links
    appointment = models.ForeignKey(
        "booking.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_logs",
    )
    customer = models.ForeignKey(
        "booking.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_logs",
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification_logs"
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"
        indexes = [
            models.Index(fields=["tenant", "status", "created_at"]),
            models.Index(fields=["recipient_email", "created_at"]),
            models.Index(fields=["event", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event} to {self.recipient_email or self.recipient_phone} - {self.status}"
