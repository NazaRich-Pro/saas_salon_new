from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views, views_billing, views_loyalty

router = DefaultRouter()
router.register(r"payments", views.PaymentViewSet, basename="payment")
router.register(r"coupons", views.CouponViewSet, basename="coupon")
router.register(r"gift-cards", views.GiftCardViewSet, basename="gift-card")
router.register(r"loyalty-rules", views.LoyaltyRuleViewSet, basename="loyalty-rule")
router.register(
    r"subscriptions", views.SaaSSubscriptionViewSet, basename="subscription"
)

urlpatterns = [
    # Cash payments
    path("mark-cash-paid/", views.mark_cash_paid, name="mark_cash_paid"),
    # Stripe (stub)
    path(
        "stripe/create-intent/", views.create_stripe_intent, name="stripe_create_intent"
    ),
    # Refunds
    path("refund/", views.refund_payment, name="refund_payment"),
    # Coupons
    path("apply-coupon/", views_loyalty.apply_coupon, name="apply_coupon"),
    path("remove-coupon/", views_loyalty.remove_coupon, name="remove_coupon"),
    # Loyalty points
    path(
        "redeem-points/",
        views_loyalty.redeem_loyalty_points,
        name="redeem_loyalty_points",
    ),
    path(
        "customer/<uuid:customer_id>/loyalty/",
        views_loyalty.customer_loyalty_info,
        name="customer_loyalty_info",
    ),
    # Birthday campaigns
    path("birthdays/today/", views_loyalty.todays_birthdays, name="todays_birthdays"),
    path(
        "birthdays/upcoming/",
        views_loyalty.upcoming_birthdays,
        name="upcoming_birthdays",
    ),
    # Billing
    path(
        "billing/subscription/",
        views_billing.get_subscription,
        name="billing_subscription",
    ),
    path(
        "billing/subscription/update-seats/",
        views_billing.update_seats,
        name="billing_update_seats",
    ),
    path("billing/status/", views_billing.billing_status, name="billing_status"),
    path("billing/invoice/", views_billing.current_invoice, name="current_invoice"),
    path("billing/features/", views_billing.features, name="billing_features"),
    path(
        "billing/mark-invoice-paid/",
        views_billing.mark_invoice_paid_endpoint,
        name="billing_mark_paid",
    ),
    # Include router URLs
    path("", include(router.urls)),
]
