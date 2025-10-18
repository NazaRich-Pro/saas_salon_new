from django.contrib import admin

from .models import NotificationLog, NotificationTemplate


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ["event", "kind", "lang", "tenant", "is_active", "created_at"]
    list_filter = ["kind", "event", "lang", "is_active"]
    search_fields = ["subject", "body", "tenant__name"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        ("Template Info", {"fields": ("tenant", "kind", "event", "lang", "is_active")}),
        ("Content", {"fields": ("subject", "body")}),
        ("Meta", {"fields": ("id", "created_at", "updated_at")}),
    )


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        "event",
        "kind",
        "recipient_email",
        "status",
        "sent_at",
        "retry_count",
        "created_at",
    ]
    list_filter = ["kind", "event", "status", "created_at"]
    search_fields = ["recipient_email", "recipient_phone", "subject"]
    readonly_fields = ["id", "created_at", "updated_at", "sent_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Recipient",
            {"fields": ("recipient_email", "recipient_phone", "recipient_telegram_id")},
        ),
        ("Notification", {"fields": ("kind", "event", "subject", "body", "status")}),
        ("Tracking", {"fields": ("sent_at", "retry_count", "error_message")}),
        ("Links", {"fields": ("tenant", "appointment", "customer")}),
        ("Meta", {"fields": ("id", "created_at", "updated_at")}),
    )
