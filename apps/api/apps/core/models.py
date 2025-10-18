"""
Core models including audit log.
"""
import uuid

from django.db import models


class AuditLog(models.Model):
    """
    Audit log for tracking critical actions across the platform.
    Implements OWASP A09:2021 – Security Logging and Monitoring Failures.
    """

    ACTION_CREATE = "CREATE"
    ACTION_UPDATE = "UPDATE"
    ACTION_DELETE = "DELETE"
    ACTION_LOGIN = "LOGIN"
    ACTION_LOGOUT = "LOGOUT"
    ACTION_PASSWORD_CHANGE = "PASSWORD_CHANGE"
    ACTION_2FA_ENABLE = "2FA_ENABLE"
    ACTION_2FA_DISABLE = "2FA_DISABLE"
    ACTION_PERMISSION_CHANGE = "PERMISSION_CHANGE"
    ACTION_PAYMENT = "PAYMENT"
    ACTION_REFUND = "REFUND"
    ACTION_EXPORT = "EXPORT"
    ACTION_IMPERSONATE = "IMPERSONATE"

    ACTION_CHOICES = [
        (ACTION_CREATE, "Create"),
        (ACTION_UPDATE, "Update"),
        (ACTION_DELETE, "Delete"),
        (ACTION_LOGIN, "Login"),
        (ACTION_LOGOUT, "Logout"),
        (ACTION_PASSWORD_CHANGE, "Password Change"),
        (ACTION_2FA_ENABLE, "2FA Enable"),
        (ACTION_2FA_DISABLE, "2FA Disable"),
        (ACTION_PERMISSION_CHANGE, "Permission Change"),
        (ACTION_PAYMENT, "Payment"),
        (ACTION_REFUND, "Refund"),
        (ACTION_EXPORT, "Export"),
        (ACTION_IMPERSONATE, "Impersonate"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Tenant context (nullable for platform-wide actions)
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    # User who performed the action (nullable for system actions)
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    # Action details
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    entity_type = models.CharField(
        max_length=100
    )  # e.g., 'Appointment', 'User', 'Payment'
    entity_id = models.UUIDField(null=True, blank=True)  # ID of affected entity

    # Additional context (JSON)
    metadata = models.JSONField(default=dict, blank=True)

    # Request details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_logs"
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else "System"
        return f"{self.action} by {user_str} on {self.entity_type} at {self.created_at}"
