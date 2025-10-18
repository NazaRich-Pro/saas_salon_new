"""JWT utilities for token generation and validation"""
import uuid
from datetime import timedelta

import jwt
from django.conf import settings
from django.utils import timezone

from .models import DeviceSession, RefreshToken


def generate_access_token(user, device_id=None):
    """
    Generate JWT access token

    Returns: (token_string, expires_at)
    """
    expires_at = timezone.now() + timedelta(seconds=settings.JWT_ACCESS_TOKEN_LIFETIME)

    payload = {
        "user_id": str(user.id),
        "email": user.email,
        "is_superadmin": user.is_superadmin,
        "device_id": device_id or str(uuid.uuid4()),
        "exp": expires_at.timestamp(),
        "iat": timezone.now().timestamp(),
        "type": "access",
    }

    token = jwt.encode(payload, settings.JWT_ACCESS_SECRET, algorithm="HS256")
    return token, expires_at


def generate_refresh_token(user, device_id, device_info=None):
    """
    Generate refresh token and store in database

    Args:
        user: User instance
        device_id: Unique device identifier
        device_info: Dict with device_name, user_agent, ip_address

    Returns: (token_string, RefreshToken instance)
    """
    expires_at = timezone.now() + timedelta(seconds=settings.JWT_REFRESH_TOKEN_LIFETIME)

    # Generate unique token
    token_string = str(uuid.uuid4())

    # Create refresh token in database
    device_info = device_info or {}
    refresh_token = RefreshToken.objects.create(
        user=user,
        token=token_string,
        device_id=device_id,
        device_name=device_info.get("device_name", "Unknown Device"),
        user_agent=device_info.get("user_agent", ""),
        ip_address=device_info.get("ip_address"),
        expires_at=expires_at,
    )

    return token_string, refresh_token


def rotate_refresh_token(old_token_string, device_info=None):
    """
    Rotate refresh token - create new one and revoke old one

    Args:
        old_token_string: Current refresh token
        device_info: Updated device info

    Returns: (new_token_string, RefreshToken instance) or (None, None) if invalid
    """
    try:
        old_token = RefreshToken.objects.get(token=old_token_string, is_revoked=False)

        # Check if expired
        if not old_token.is_valid():
            old_token.revoke()
            return None, None

        # Generate new token
        device_info = device_info or {}
        device_info.setdefault("device_name", old_token.device_name)
        device_info.setdefault("user_agent", old_token.user_agent)
        device_info.setdefault("ip_address", old_token.ip_address)

        new_token_string, new_token = generate_refresh_token(
            old_token.user, old_token.device_id, device_info
        )

        # Store reference to old token
        new_token.previous_token = old_token_string
        new_token.save(update_fields=["previous_token"])

        # Revoke old token
        old_token.revoke()

        return new_token_string, new_token

    except RefreshToken.DoesNotExist:
        return None, None


def verify_access_token(token_string):
    """
    Verify and decode access token

    Returns: payload dict or None if invalid
    """
    try:
        payload = jwt.decode(
            token_string, settings.JWT_ACCESS_SECRET, algorithms=["HS256"]
        )

        # Check token type
        if payload.get("type") != "access":
            return None

        return payload

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_refresh_token(token_string):
    """
    Verify refresh token from database

    Returns: RefreshToken instance or None if invalid
    """
    try:
        refresh_token = RefreshToken.objects.select_related("user").get(
            token=token_string, is_revoked=False
        )

        if not refresh_token.is_valid():
            refresh_token.revoke()
            return None

        return refresh_token

    except RefreshToken.DoesNotExist:
        return None


def revoke_all_user_tokens(user, except_device_id=None):
    """
    Revoke all refresh tokens for a user (logout all devices)

    Args:
        user: User instance
        except_device_id: Optional device_id to keep active
    """
    tokens_query = RefreshToken.objects.filter(user=user, is_revoked=False)

    if except_device_id:
        tokens_query = tokens_query.exclude(device_id=except_device_id)

    for token in tokens_query:
        token.revoke()


def revoke_device_tokens(user, device_id):
    """
    Revoke all tokens for a specific device

    Args:
        user: User instance
        device_id: Device identifier to revoke
    """
    tokens = RefreshToken.objects.filter(
        user=user, device_id=device_id, is_revoked=False
    )

    for token in tokens:
        token.revoke()


def create_or_update_device_session(user, device_id, device_info):
    """
    Create or update device session

    Args:
        user: User instance
        device_id: Unique device identifier
        device_info: Dict with device details

    Returns: DeviceSession instance
    """
    expires_at = timezone.now() + timedelta(seconds=settings.JWT_REFRESH_TOKEN_LIFETIME)

    session, created = DeviceSession.objects.update_or_create(
        user=user,
        device_id=device_id,
        defaults={
            "device_name": device_info.get("device_name", "Unknown Device"),
            "device_type": device_info.get("device_type", "unknown"),
            "os": device_info.get("os", ""),
            "browser": device_info.get("browser", ""),
            "ip_address": device_info.get("ip_address"),
            "country": device_info.get("country", ""),
            "city": device_info.get("city", ""),
            "expires_at": expires_at,
            "is_active": True,
        },
    )

    return session


def terminate_device_session(user, device_id):
    """
    Terminate device session and revoke tokens

    Args:
        user: User instance
        device_id: Device identifier
    """
    # Revoke tokens
    revoke_device_tokens(user, device_id)

    # Terminate session
    try:
        session = DeviceSession.objects.get(user=user, device_id=device_id)
        session.terminate()
    except DeviceSession.DoesNotExist:
        pass


def cleanup_expired_tokens():
    """
    Cleanup expired refresh tokens and sessions
    Should be run periodically via Celery beat
    """
    # Delete expired refresh tokens
    RefreshToken.objects.filter(expires_at__lt=timezone.now()).delete()

    # Terminate expired sessions
    expired_sessions = DeviceSession.objects.filter(
        expires_at__lt=timezone.now(), is_active=True
    )
    for session in expired_sessions:
        session.terminate()


def parse_device_info(request):
    """
    Parse device information from request

    Args:
        request: Django request object

    Returns: Dict with device info
    """
    from user_agents import parse

    user_agent_string = request.META.get("HTTP_USER_AGENT", "")
    user_agent = parse(user_agent_string)

    # Get IP address
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(",")[0]
    else:
        ip_address = request.META.get("REMOTE_ADDR")

    # Determine device type
    if user_agent.is_mobile:
        device_type = "mobile"
    elif user_agent.is_tablet:
        device_type = "tablet"
    elif user_agent.is_pc:
        device_type = "desktop"
    else:
        device_type = "unknown"

    # Generate device name
    device_name = f"{user_agent.browser.family} on {user_agent.os.family}"
    if user_agent.device.family != "Other":
        device_name = f"{user_agent.device.family} - {device_name}"

    return {
        "device_name": device_name,
        "device_type": device_type,
        "os": f"{user_agent.os.family} {user_agent.os.version_string}",
        "browser": f"{user_agent.browser.family} {user_agent.browser.version_string}",
        "user_agent": user_agent_string,
        "ip_address": ip_address,
    }
