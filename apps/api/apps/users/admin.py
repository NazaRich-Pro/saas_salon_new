from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import DeviceSession, LoginAttempt, RefreshToken, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "email",
        "is_superadmin",
        "is_active",
        "twofa_enabled",
        "failed_login_attempts",
        "created_at",
    ]
    list_filter = ["is_superadmin", "is_active", "twofa_enabled"]
    search_fields = ["email", "phone"]
    ordering = ["-created_at"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("phone",)}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superadmin",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("2FA", {"fields": ("twofa_enabled", "twofa_secret")}),
        (
            "Security",
            {"fields": ("failed_login_attempts", "last_failed_login", "locked_until")},
        ),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )

    readonly_fields = ["created_at", "updated_at", "last_failed_login"]

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "device_name",
        "device_id",
        "is_revoked",
        "expires_at",
        "last_used_at",
        "created_at",
    ]
    list_filter = ["is_revoked", "created_at", "expires_at"]
    search_fields = ["user__email", "device_id", "device_name", "ip_address"]
    readonly_fields = ["id", "token", "created_at", "last_used_at", "revoked_at"]
    date_hierarchy = "created_at"

    actions = ["revoke_tokens"]

    def revoke_tokens(self, request, queryset):
        for token in queryset:
            token.revoke()
        self.message_user(request, f"Revoked {queryset.count()} tokens")

    revoke_tokens.short_description = "Revoke selected tokens"


@admin.register(DeviceSession)
class DeviceSessionAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "device_name",
        "device_type",
        "os",
        "browser",
        "ip_address",
        "is_active",
        "last_activity",
    ]
    list_filter = ["is_active", "device_type", "created_at"]
    search_fields = ["user__email", "device_id", "device_name", "ip_address"]
    readonly_fields = ["id", "created_at", "last_activity"]
    date_hierarchy = "created_at"

    actions = ["terminate_sessions"]

    def terminate_sessions(self, request, queryset):
        for session in queryset:
            session.terminate()
        self.message_user(request, f"Terminated {queryset.count()} sessions")

    terminate_sessions.short_description = "Terminate selected sessions"


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "success",
        "failure_reason",
        "required_2fa",
        "passed_2fa",
        "ip_address",
        "attempted_at",
    ]
    list_filter = ["success", "required_2fa", "passed_2fa", "attempted_at"]
    search_fields = ["email", "user__email", "ip_address"]
    readonly_fields = ["id", "attempted_at"]
    date_hierarchy = "attempted_at"
