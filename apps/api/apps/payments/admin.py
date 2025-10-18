from django.contrib import admin

from .models import AuditLog, Coupon, GiftCard, LoyaltyRule, Payment, SaaSSubscription


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "tenant",
        "appointment",
        "type",
        "provider",
        "status",
        "amount_kgs",
        "created_at",
    ]
    list_filter = ["tenant", "type", "provider", "status", "created_at"]
    search_fields = ["id", "tenant__name", "external_ref"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "tenant",
        "kind",
        "value",
        "valid_from",
        "valid_to",
        "uses_count",
        "max_uses",
        "is_active",
    ]
    list_filter = ["tenant", "kind", "is_active", "valid_from", "valid_to"]
    search_fields = ["code", "tenant__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "tenant",
        "balance_kgs",
        "initial_balance_kgs",
        "owner_customer",
        "is_active",
        "created_at",
    ]
    list_filter = ["tenant", "is_active", "created_at"]
    search_fields = ["code", "owner_customer__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(LoyaltyRule)
class LoyaltyRuleAdmin(admin.ModelAdmin):
    list_display = [
        "tenant",
        "earn_per_100_kgs",
        "redeem_rate",
        "min_points_to_redeem",
        "is_active",
    ]
    list_filter = ["is_active"]
    search_fields = ["tenant__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(SaaSSubscription)
class SaaSSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "tenant",
        "plan",
        "seats",
        "status",
        "period_start",
        "period_end",
        "monthly_price_kgs",
    ]
    list_filter = ["plan", "status", "period_end"]
    search_fields = ["tenant__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "action",
        "entity_type",
        "entity_id",
        "user",
        "tenant",
        "ip_address",
        "created_at",
    ]
    list_filter = ["action", "entity_type", "created_at"]
    search_fields = ["entity_id", "user__email", "ip_address"]
    readonly_fields = ["id", "created_at"]
    date_hierarchy = "created_at"
