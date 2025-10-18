from django.contrib import admin

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


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "timezone", "phone", "is_active", "created_at"]
    list_filter = ["tenant", "is_active", "timezone"]
    search_fields = ["name", "address", "phone"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "sort_order", "is_active", "created_at"]
    list_filter = ["tenant", "is_active"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["tenant", "sort_order", "name"]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "tenant",
        "category",
        "duration_min",
        "price_kgs",
        "is_active",
    ]
    list_filter = ["tenant", "category", "is_active"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "tenant",
        "title",
        "phone",
        "email",
        "commission_pct",
        "is_active",
    ]
    list_filter = ["tenant", "is_active"]
    search_fields = ["name", "phone", "email"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(StaffService)
class StaffServiceAdmin(admin.ModelAdmin):
    list_display = [
        "staff",
        "service",
        "duration_override_min",
        "price_override_kgs",
        "created_at",
    ]
    list_filter = ["staff__tenant"]
    search_fields = ["staff__name", "service__name"]
    readonly_fields = ["id", "created_at"]


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ["staff", "tenant", "is_active", "created_at"]
    list_filter = ["tenant", "is_active"]
    search_fields = ["staff__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "tenant",
        "phone",
        "email",
        "total_visits",
        "total_spent_kgs",
        "loyalty_points",
        "is_active",
    ]
    list_filter = ["tenant", "is_active", "created_at"]
    search_fields = ["name", "phone", "email"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "tenant",
        "customer",
        "staff",
        "start_at",
        "status",
        "total_price_kgs",
        "created_at",
    ]
    list_filter = ["tenant", "status", "source", "created_at"]
    search_fields = ["id", "customer__name", "staff__name", "notes"]
    readonly_fields = ["id", "created_at", "updated_at"]
    date_hierarchy = "start_at"


@admin.register(AppointmentService)
class AppointmentServiceAdmin(admin.ModelAdmin):
    list_display = [
        "appointment",
        "service",
        "order",
        "duration_min",
        "price_kgs",
        "created_at",
    ]
    list_filter = ["appointment__tenant"]
    search_fields = ["appointment__id", "service__name"]
    readonly_fields = ["id", "created_at"]
    ordering = ["appointment", "order"]
