"""Middleware for billing and feature access control"""
from apps.payments.billing_service import BillingService
from django.http import JsonResponse


class BillingMiddleware:
    """
    Middleware to check subscription status and block booking if needed
    """

    # Endpoints that should be blocked if subscription is suspended
    BOOKING_ENDPOINTS = [
        "/api/booking/create-appointment/",
        "/api/booking/available-slots/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip if no tenant context
        if not hasattr(request, "tenant") or request.tenant is None:
            return self.get_response(request)

        # Skip for admin/auth endpoints (always accessible)
        if request.path.startswith("/api/auth/") or request.path.startswith("/admin/"):
            return self.get_response(request)

        # Check if this is a booking endpoint
        is_booking_endpoint = any(
            request.path.startswith(endpoint) for endpoint in self.BOOKING_ENDPOINTS
        )

        if is_booking_endpoint:
            # Check billing status
            billing_service = BillingService(request.tenant)
            can_book, reason = billing_service.can_create_booking()

            if not can_book:
                return JsonResponse(
                    {
                        "error": "Онлайн запись заблокирована",
                        "reason": reason,
                        "status": billing_service.subscription.status,
                        "message": "Обратитесь в поддержку или оплатите подписку",
                    },
                    status=402,
                )  # 402 Payment Required

        # Add billing context to request
        request.billing_service = BillingService(request.tenant)

        response = self.get_response(request)
        return response
