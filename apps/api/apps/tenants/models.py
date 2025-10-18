"""Tenant models for multi-tenancy"""
import uuid

from django.db import models


class Tenant(models.Model):
    """Tenant (Salon or Solo Master)"""

    TYPE_CHOICES = [
        ("SALON", "Salon"),
        ("SOLO", "Solo Master"),
    ]

    STATUS_CHOICES = [
        ("TRIAL", "Trial"),
        ("ACTIVE", "Active"),
        ("GRACE", "Grace Period"),
        ("SUSPENDED", "Suspended"),
        ("CANCELLED", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True, max_length=100, db_index=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    # Subscription
    plan = models.CharField(max_length=50, default="basic")
    seats = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="TRIAL")

    # Dates
    trial_ends = models.DateTimeField(null=True, blank=True)
    grace_until = models.DateTimeField(null=True, blank=True)

    # Settings (theme, language, widget config)
    settings = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenants"
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.slug})"


class TenantDomain(models.Model):
    """Custom domains for white-label support"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="domains")
    domain = models.CharField(max_length=255, unique=True, db_index=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tenant_domains"
        verbose_name = "Tenant Domain"
        verbose_name_plural = "Tenant Domains"

    def __str__(self):
        return f"{self.domain} → {self.tenant.name}"


class Membership(models.Model):
    """User membership in a tenant with role"""

    ROLE_CHOICES = [
        ("SUPERADMIN", "Superadmin"),
        ("SALON_ADMIN", "Salon Admin"),
        ("RECEPTION", "Reception"),
        ("STAFF", "Staff"),
        ("ACCOUNTANT", "Accountant"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="memberships"
    )
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "memberships"
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"
        unique_together = [["user", "tenant"]]
        indexes = [
            models.Index(fields=["tenant", "role"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.tenant.name} ({self.role})"
