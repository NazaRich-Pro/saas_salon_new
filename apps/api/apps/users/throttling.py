"""Rate limiting for authentication endpoints"""
from django.core.cache import cache
from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """
    Rate limit for login attempts
    5 per minute per IP
    """

    scope = "login"
    rate = "5/min"

    def get_cache_key(self, request, view):
        """
        Use IP address as identifier
        """
        ident = self.get_ident(request)
        return f"throttle_{self.scope}_{ident}"


class EmailLoginRateThrottle(SimpleRateThrottle):
    """
    Rate limit per email address
    10 attempts per hour per email
    """

    scope = "email_login"
    rate = "10/hour"

    def get_cache_key(self, request, view):
        """
        Use email address as identifier
        """
        email = request.data.get("email", "")
        if not email:
            return None

        return f"throttle_{self.scope}_{email.lower()}"


class TwoFAThrottle(SimpleRateThrottle):
    """
    Rate limit for 2FA verification
    5 attempts per 5 minutes per user
    """

    scope = "2fa"
    rate = "5/5min"

    def get_cache_key(self, request, view):
        """
        Use user ID or session ID as identifier
        """
        if request.user and request.user.is_authenticated:
            ident = str(request.user.id)
        else:
            ident = request.session.session_key or self.get_ident(request)

        return f"throttle_{self.scope}_{ident}"


class PasswordResetThrottle(AnonRateThrottle):
    """
    Rate limit for password reset requests
    3 per hour per IP
    """

    scope = "password_reset"
    rate = "3/hour"


def check_login_attempts(email, ip_address):
    """
    Check if login attempts for email/IP are within limits

    Returns: (allowed: bool, attempts: int, wait_seconds: int)
    """
    # Check email-based attempts
    email_key = f"login_attempts_email_{email.lower()}"
    email_attempts = cache.get(email_key, 0)

    # Check IP-based attempts
    ip_key = f"login_attempts_ip_{ip_address}"
    ip_attempts = cache.get(ip_key, 0)

    # Limits
    EMAIL_LIMIT = 10  # per hour
    IP_LIMIT = 20  # per hour
    LOCKOUT_TIME = 3600  # 1 hour

    if email_attempts >= EMAIL_LIMIT:
        ttl = cache.ttl(email_key)
        return False, email_attempts, ttl

    if ip_attempts >= IP_LIMIT:
        ttl = cache.ttl(ip_key)
        return False, ip_attempts, ttl

    return True, max(email_attempts, ip_attempts), 0


def record_login_attempt(email, ip_address, success=False):
    """
    Record a login attempt

    Args:
        email: Email address
        ip_address: IP address
        success: Whether login was successful
    """
    timeout = 3600  # 1 hour

    email_key = f"login_attempts_email_{email.lower()}"
    ip_key = f"login_attempts_ip_{ip_address}"

    if success:
        # Clear counters on successful login
        cache.delete(email_key)
        cache.delete(ip_key)
    else:
        # Increment counters on failed login
        email_attempts = cache.get(email_key, 0)
        ip_attempts = cache.get(ip_key, 0)

        cache.set(email_key, email_attempts + 1, timeout)
        cache.set(ip_key, ip_attempts + 1, timeout)


def is_captcha_required(email, ip_address):
    """
    Check if CAPTCHA is required for login
    CAPTCHA required after 5 failed attempts

    Args:
        email: Email address
        ip_address: IP address

    Returns: Boolean
    """
    email_key = f"login_attempts_email_{email.lower()}"
    ip_key = f"login_attempts_ip_{ip_address}"

    email_attempts = cache.get(email_key, 0)
    ip_attempts = cache.get(ip_key, 0)

    return email_attempts >= 5 or ip_attempts >= 5
