"""JWT Authentication for DRF"""
import logging

from django.conf import settings
from rest_framework import authentication, exceptions

from .jwt_utils import verify_access_token
from .models import User

logger = logging.getLogger(__name__)


class JWTAuthentication(authentication.BaseAuthentication):
    """
    JWT token authentication using httpOnly cookies
    """

    def authenticate(self, request):
        """
        Authenticate the request using JWT from cookies

        Returns: (user, auth_token) tuple or None
        """
        # Get token from httpOnly cookie
        access_token = request.COOKIES.get("access_token")

        if not access_token:
            # Also check Authorization header as fallback
            auth_header = request.META.get("HTTP_AUTHORIZATION", "")
            if auth_header.startswith("Bearer "):
                access_token = auth_header[7:]
            else:
                return None

        # Verify token
        payload = verify_access_token(access_token)

        if not payload:
            return None

        # Get user
        try:
            user = User.objects.get(id=payload["user_id"], is_active=True)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("User not found or inactive")

        # Store device_id in request for later use
        request.device_id = payload.get("device_id")

        return (user, access_token)

    def authenticate_header(self, request):
        """
        Return WWW-Authenticate header for 401 responses
        """
        return 'Bearer realm="api"'
