"""
Rate limiting middleware using Redis.
"""
import logging

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Rate limiting middleware to prevent abuse.
    Uses Redis for distributed rate limiting.
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Rate limits by endpoint pattern
        self.rate_limits = {
            "/api/auth/login": {"requests": 5, "window": 300},  # 5 per 5 min
            "/api/auth/register": {"requests": 3, "window": 3600},  # 3 per hour
            "/api/onboarding/": {"requests": 5, "window": 3600},  # 5 per hour
            "/api/public/": {"requests": 100, "window": 60},  # 100 per minute
        }

    def __call__(self, request):
        # Skip rate limiting for health checks
        if request.path == "/health/":
            return self.get_response(request)

        # Check rate limit
        if self.is_rate_limited(request):
            return JsonResponse(
                {
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": 60,
                },
                status=429,
            )

        response = self.get_response(request)
        return response

    def is_rate_limited(self, request):
        """Check if request should be rate limited."""
        # Get client identifier (IP or user ID)
        client_id = self.get_client_id(request)

        # Find matching rate limit rule
        limit_config = None
        for pattern, config in self.rate_limits.items():
            if request.path.startswith(pattern):
                limit_config = config
                break

        if not limit_config:
            return False  # No rate limit for this endpoint

        # Check rate limit in Redis
        cache_key = f"ratelimit:{request.path}:{client_id}"

        try:
            count = cache.get(cache_key, 0)

            if count >= limit_config["requests"]:
                logger.warning(f"Rate limit exceeded for {client_id} on {request.path}")
                return True

            # Increment counter
            cache.set(cache_key, count + 1, timeout=limit_config["window"])

            return False

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return False  # Fail open

    def get_client_id(self, request):
        """Get unique client identifier."""
        # Use user ID if authenticated
        if hasattr(request, "user") and request.user.is_authenticated:
            return f"user:{request.user.id}"

        # Otherwise use IP address
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")

        return f"ip:{ip}"
