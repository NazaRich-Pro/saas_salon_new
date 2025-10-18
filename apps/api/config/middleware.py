"""
Security middleware for BeautyHub SaaS.
Implements OWASP best practices.
"""
from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses.
    Implements OWASP security headers recommendations.
    """

    def process_response(self, request, response):
        # Prevent clickjacking
        response["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response["X-Content-Type-Options"] = "nosniff"

        # Enable XSS protection
        response["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        # HSTS (if using HTTPS)
        if request.is_secure():
            response[
                "Strict-Transport-Security"
            ] = "max-age=31536000; includeSubDomains; preload"

        # Permissions Policy (formerly Feature-Policy)
        response["Permissions-Policy"] = (
            "geolocation=(), " "microphone=(), " "camera=(), " "payment=()"
        )

        return response
