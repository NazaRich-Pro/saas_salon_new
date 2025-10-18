from django.contrib import admin

from .models import Membership, Tenant, TenantDomain


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "type",
        "status",
        "seats",
        "trial_ends",
        "created_at",
    ]
    list_filter = ["type", "status", "plan"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        ("Basic Info", {"fields": ("name", "slug", "type")}),
        (
            "Subscription",
            {"fields": ("plan", "seats", "status", "trial_ends", "grace_until")},
        ),
        ("Settings", {"fields": ("settings",)}),
        ("Meta", {"fields": ("id", "created_at", "updated_at")}),
    )


@admin.register(TenantDomain)
class TenantDomainAdmin(admin.ModelAdmin):
    list_display = ["domain", "tenant", "verified_at", "created_at"]
    list_filter = ["verified_at"]
    search_fields = ["domain", "tenant__name"]
    readonly_fields = ["id", "created_at"]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "tenant", "role", "is_active", "created_at"]
    list_filter = ["role", "is_active"]
    search_fields = ["user__email", "tenant__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
