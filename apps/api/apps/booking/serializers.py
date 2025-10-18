"""Booking serializers"""
from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import (
    Appointment,
    AppointmentService,
    Customer,
    Location,
    Schedule,
    Service,
    ServiceCategory,
    Staff,
    StaffService,
)


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id",
            "name",
            "timezone",
            "address",
            "phone",
            "email",
            "latitude",
            "longitude",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ["id", "name", "description", "sort_order", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class ServiceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "description",
            "duration_min",
            "price_kgs",
            "buffer_before_min",
            "buffer_after_min",
            "allow_combo",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class StaffSerializer(serializers.ModelSerializer):
    services_count = serializers.SerializerMethodField()

    class Meta:
        model = Staff
        fields = [
            "id",
            "name",
            "title",
            "phone",
            "email",
            "bio",
            "skills",
            "photo_url",
            "commission_pct",
            "is_active",
            "services_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_services_count(self, obj):
        return obj.staff_services.count()


class StaffServiceSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    staff_name = serializers.CharField(source="staff.name", read_only=True)

    class Meta:
        model = StaffService
        fields = [
            "id",
            "staff",
            "staff_name",
            "service",
            "service_name",
            "duration_override_min",
            "price_override_kgs",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ScheduleSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source="staff.name", read_only=True)

    class Meta:
        model = Schedule
        fields = [
            "id",
            "staff",
            "staff_name",
            "rules",
            "exceptions",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "date_of_birth",
            "notes",
            "tags",
            "loyalty_points",
            "total_visits",
            "total_spent_kgs",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "loyalty_points",
            "total_visits",
            "total_spent_kgs",
            "created_at",
            "updated_at",
        ]


class AppointmentServiceSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)

    class Meta:
        model = AppointmentService
        fields = ["id", "service", "service_name", "order", "duration_min", "price_kgs"]
        read_only_fields = ["id"]


class AppointmentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)
    staff_name = serializers.CharField(source="staff.name", read_only=True)
    location_name = serializers.CharField(
        source="location.name", read_only=True, allow_null=True
    )
    services = AppointmentServiceSerializer(many=True, read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "customer",
            "customer_name",
            "customer_phone",
            "staff",
            "staff_name",
            "location",
            "location_name",
            "start_at",
            "end_at",
            "status",
            "source",
            "notes",
            "internal_notes",
            "total_price_kgs",
            "prepaid_kgs",
            "discount_kgs",
            "services",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer_name",
            "customer_phone",
            "staff_name",
            "location_name",
            "services",
            "created_at",
            "updated_at",
        ]


class AppointmentCreateSerializer(serializers.Serializer):
    """Serializer for creating appointments"""

    # Customer info
    customer_name = serializers.CharField(max_length=255)
    customer_phone = serializers.CharField(max_length=20)
    customer_email = serializers.EmailField(required=False, allow_blank=True)

    # Appointment details
    staff_id = serializers.UUIDField()
    service_ids = serializers.ListField(
        child=serializers.UUIDField(), min_length=1, max_length=10
    )
    start_at = serializers.DateTimeField()
    location_id = serializers.UUIDField(required=False, allow_null=True)

    # Notes
    notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    # Source
    source = serializers.ChoiceField(
        choices=["WIDGET", "ADMIN", "PHONE", "WALK_IN", "API"], default="WIDGET"
    )

    def validate_start_at(self, value):
        """Validate start time is in the future"""
        if value < timezone.now():
            raise serializers.ValidationError("Appointment time must be in the future")
        return value


class AvailableSlotsSerializer(serializers.Serializer):
    """Serializer for available slots query"""

    service_id = serializers.UUIDField()
    date = serializers.DateField()
    staff_id = serializers.UUIDField(required=False, allow_null=True)
    location_id = serializers.UUIDField(required=False, allow_null=True)


class SlotSerializer(serializers.Serializer):
    """Serializer for a time slot"""

    time = serializers.CharField()
    datetime = serializers.DateTimeField()
    staff_id = serializers.UUIDField()
    staff_name = serializers.CharField()
    duration_min = serializers.IntegerField()
    available = serializers.BooleanField()


class AppointmentStatusSerializer(serializers.Serializer):
    """Serializer for status updates"""

    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)


class AppointmentRescheduleSerializer(serializers.Serializer):
    """Serializer for rescheduling"""

    new_start_at = serializers.DateTimeField()
    new_staff_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_new_start_at(self, value):
        """Validate new start time is in the future"""
        if value < timezone.now():
            raise serializers.ValidationError(
                "New appointment time must be in the future"
            )
        return value
