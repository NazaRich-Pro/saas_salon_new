"""Booking domain models"""
import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Location(models.Model):
    """Physical location for salon (multiple locations support)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="locations"
    )

    name = models.CharField(max_length=255)
    timezone = models.CharField(max_length=50, default="UTC")
    address = models.TextField(blank=True)

    # Contact info
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    # Coordinates for maps
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "locations"
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class ServiceCategory(models.Model):
    """Category for services (e.g., Haircut, Coloring, Nails)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="service_categories"
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "service_categories"
        verbose_name = "Service Category"
        verbose_name_plural = "Service Categories"
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class Service(models.Model):
    """Service offered by salon/master"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="services"
    )
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="services",
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Pricing and timing
    duration_min = models.IntegerField(help_text="Duration in minutes")
    price_kgs = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Price in KGS"
    )

    # Buffer times
    buffer_before_min = models.IntegerField(
        default=0, help_text="Buffer before appointment in minutes"
    )
    buffer_after_min = models.IntegerField(
        default=0, help_text="Buffer after appointment in minutes"
    )

    # Settings
    allow_combo = models.BooleanField(
        default=True, help_text="Allow combining with other services"
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "services"
        verbose_name = "Service"
        verbose_name_plural = "Services"
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["tenant", "category"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.price_kgs} KGS ({self.tenant.name})"


class Staff(models.Model):
    """Staff member (master) who provides services"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="staff"
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_profiles",
    )

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    # Professional info
    title = models.CharField(
        max_length=100, blank=True, help_text="e.g., Senior Stylist"
    )
    bio = models.TextField(blank=True)
    skills = models.JSONField(
        default=list, blank=True, help_text="List of skills/specializations"
    )

    # Photo
    photo_url = models.URLField(blank=True)

    # Commission
    commission_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Commission percentage",
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "staff"
        verbose_name = "Staff Member"
        verbose_name_plural = "Staff Members"
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class StaffService(models.Model):
    """Link between staff and services they can provide"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(
        Staff, on_delete=models.CASCADE, related_name="staff_services"
    )
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="staff_services"
    )

    # Overrides (optional)
    duration_override_min = models.IntegerField(
        null=True, blank=True, help_text="Override service duration"
    )
    price_override_kgs = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Override service price",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "staff_services"
        verbose_name = "Staff Service"
        verbose_name_plural = "Staff Services"
        unique_together = [["staff", "service"]]
        indexes = [
            models.Index(fields=["staff", "service"]),
        ]

    def __str__(self):
        return f"{self.staff.name} - {self.service.name}"


class Schedule(models.Model):
    """Staff member's schedule (working hours, breaks, exceptions)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="schedules")

    # Rules stored as JSON:
    # {
    #   "monday": {"enabled": true, "slots": [{"start": "09:00", "end": "18:00"}]},
    #   "tuesday": {"enabled": true, "slots": [{"start": "09:00", "end": "18:00"}]},
    #   ...
    # }
    rules = models.JSONField(default=dict, help_text="Weekly schedule rules")

    # Exceptions stored as JSON:
    # [
    #   {"date": "2025-12-25", "type": "off", "reason": "Christmas"},
    #   {"date": "2025-10-15", "type": "custom", "slots": [{"start": "10:00", "end": "14:00"}]}
    # ]
    exceptions = models.JSONField(
        default=list, blank=True, help_text="Date-specific exceptions"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "schedules"
        verbose_name = "Schedule"
        verbose_name_plural = "Schedules"
        indexes = [
            models.Index(fields=["tenant", "staff", "is_active"]),
        ]

    def __str__(self):
        return f"Schedule for {self.staff.name}"


class Customer(models.Model):
    """Customer/client of the salon"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="customers"
    )

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True, db_index=True)

    # Additional info
    date_of_birth = models.DateField(
        null=True, blank=True, help_text="For birthday campaigns"
    )
    notes = models.TextField(blank=True, help_text="Internal notes about customer")
    tags = models.JSONField(default=list, blank=True, help_text="Customer tags/labels")

    # Loyalty
    loyalty_points = models.IntegerField(default=0)

    # Stats
    total_visits = models.IntegerField(default=0)
    total_spent_kgs = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers"
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        indexes = [
            models.Index(fields=["tenant", "phone"]),
            models.Index(fields=["tenant", "email"]),
            models.Index(fields=["tenant", "created_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.phone})"


class Appointment(models.Model):
    """Booking/appointment"""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
        ("NO_SHOW", "No Show"),
        ("RESCHEDULED", "Rescheduled"),
    ]

    SOURCE_CHOICES = [
        ("WIDGET", "Widget"),
        ("ADMIN", "Admin Panel"),
        ("PHONE", "Phone"),
        ("WALK_IN", "Walk-in"),
        ("API", "API"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="appointments"
    )
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="appointments"
    )
    staff = models.ForeignKey(
        Staff, on_delete=models.CASCADE, related_name="appointments"
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )

    # Time
    start_at = models.DateTimeField(db_index=True)
    end_at = models.DateTimeField(db_index=True)

    # Status
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PENDING", db_index=True
    )
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="WIDGET")

    # Notes
    notes = models.TextField(blank=True, help_text="Customer notes/requests")
    internal_notes = models.TextField(blank=True, help_text="Internal staff notes")

    # Pricing
    total_price_kgs = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prepaid_kgs = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_kgs = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Reminders sent
    reminder_24h_sent = models.BooleanField(default=False)
    reminder_2h_sent = models.BooleanField(default=False)
    followup_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "appointments"
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"
        indexes = [
            models.Index(fields=["tenant", "start_at"]),
            models.Index(fields=["tenant", "status", "start_at"]),
            models.Index(fields=["tenant", "customer"]),
            models.Index(fields=["tenant", "staff", "start_at"]),
            models.Index(
                fields=["staff", "start_at", "end_at"]
            ),  # For double-booking prevention
        ]

    def __str__(self):
        return f"{self.customer.name} with {self.staff.name} at {self.start_at}"


class AppointmentService(models.Model):
    """Services in an appointment (many-to-many with order)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, related_name="services"
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE)

    order = models.IntegerField(default=0, help_text="Order of service in appointment")
    duration_min = models.IntegerField(help_text="Actual duration for this appointment")
    price_kgs = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Actual price for this appointment"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "appointment_services"
        verbose_name = "Appointment Service"
        verbose_name_plural = "Appointment Services"
        ordering = ["order"]
        indexes = [
            models.Index(fields=["appointment", "order"]),
        ]

    def __str__(self):
        return f"{self.service.name} for {self.appointment.id}"
