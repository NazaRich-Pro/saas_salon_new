"""User views"""
import time
import uuid

from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .jwt_utils import (
    create_or_update_device_session,
    generate_access_token,
    generate_refresh_token,
    parse_device_info,
    revoke_all_user_tokens,
    rotate_refresh_token,
    terminate_device_session,
    verify_refresh_token,
)
from .models import DeviceSession, LoginAttempt, User
from .serializers import (
    ChangePasswordSerializer,
    DeviceSessionSerializer,
    LoginAttemptSerializer,
    LoginSerializer,
    LogoutSerializer,
    RefreshTokenSerializer,
    TwoFASetupSerializer,
    TwoFAVerifySerializer,
    UserProfileSerializer,
)
from .throttling import (
    EmailLoginRateThrottle,
    LoginRateThrottle,
    TwoFAThrottle,
    check_login_attempts,
    is_captcha_required,
    record_login_attempt,
)
from .totp_utils import (
    disable_2fa_for_user,
    enable_2fa_for_user,
    requires_2fa,
    setup_2fa_for_user,
    verify_totp_code,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for monitoring
    Checks database and Redis connectivity
    """
    health_status = {"status": "healthy", "timestamp": int(time.time()), "checks": {}}

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"

    # Check Redis
    try:
        cache.set("health_check", "ok", 10)
        if cache.get("health_check") == "ok":
            health_status["checks"]["redis"] = "ok"
        else:
            raise Exception("Redis get/set failed")
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = f"error: {str(e)}"

    status_code = (
        status.HTTP_200_OK
        if health_status["status"] == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return Response(health_status, status=status_code)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle, EmailLoginRateThrottle])
def login(request):
    """
    Login endpoint - returns access token in httpOnly cookie and refresh token
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data["user"]
    device_id = serializer.validated_data.get("device_id") or str(uuid.uuid4())

    # Get IP address
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(",")[0]
    else:
        ip_address = request.META.get("REMOTE_ADDR")

    # Check if 2FA is required
    if requires_2fa(user):
        # Store pending login in session
        request.session["pending_login"] = {
            "user_id": str(user.id),
            "device_id": device_id,
            "timestamp": timezone.now().timestamp(),
        }

        # Log attempt (pending 2FA)
        LoginAttempt.objects.create(
            email=user.email,
            user=user,
            success=False,
            failure_reason="Pending 2FA",
            required_2fa=True,
            passed_2fa=False,
            ip_address=ip_address,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            device_id=device_id,
        )

        return Response(
            {"requires_2fa": True, "message": "2FA verification required"},
            status=status.HTTP_200_OK,
        )

    # Generate tokens
    access_token, access_expires = generate_access_token(user, device_id)

    device_info = parse_device_info(request)
    device_info["device_id"] = device_id

    refresh_token_str, refresh_token_obj = generate_refresh_token(
        user, device_id, device_info
    )

    # Create/update device session
    create_or_update_device_session(user, device_id, device_info)

    # Update last login
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    # Log successful attempt
    LoginAttempt.objects.create(
        email=user.email,
        user=user,
        success=True,
        required_2fa=False,
        passed_2fa=False,
        ip_address=ip_address,
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        device_id=device_id,
    )

    # Record successful login for rate limiting
    record_login_attempt(user.email, ip_address, success=True)

    # Prepare response
    response = Response(
        {
            "message": "Login successful",
            "user": UserProfileSerializer(user).data,
            "refresh_token": refresh_token_str,
        },
        status=status.HTTP_200_OK,
    )

    # Set httpOnly cookie for access token
    remember_me = serializer.validated_data.get("remember_me", False)
    max_age = 30 * 24 * 60 * 60 if remember_me else None  # 30 days or session

    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=max_age,
        httponly=True,
        secure=True,  # HTTPS only
        samesite="Lax",
    )

    return response


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([TwoFAThrottle])
def verify_2fa(request):
    """
    Verify 2FA code after login
    """
    # Get pending login from session
    pending_login = request.session.get("pending_login")

    if not pending_login:
        return Response(
            {"error": "No pending login found"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Check if session is still valid (5 minutes)
    timestamp = pending_login.get("timestamp", 0)
    if timezone.now().timestamp() - timestamp > 300:
        del request.session["pending_login"]
        return Response(
            {"error": "Login session expired. Please login again."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate code
    serializer = TwoFAVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    code = serializer.validated_data["code"]
    user_id = pending_login["user_id"]
    device_id = pending_login["device_id"]

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        del request.session["pending_login"]
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Verify TOTP code
    if not verify_totp_code(user.twofa_secret, code):
        return Response(
            {"error": "Invalid 2FA code"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Clear pending login
    del request.session["pending_login"]

    # Generate tokens
    access_token, access_expires = generate_access_token(user, device_id)

    device_info = parse_device_info(request)
    device_info["device_id"] = device_id

    refresh_token_str, refresh_token_obj = generate_refresh_token(
        user, device_id, device_info
    )

    # Create/update device session
    create_or_update_device_session(user, device_id, device_info)

    # Update last login
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    # Get IP
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(",")[0]
    else:
        ip_address = request.META.get("REMOTE_ADDR")

    # Log successful attempt
    LoginAttempt.objects.create(
        email=user.email,
        user=user,
        success=True,
        required_2fa=True,
        passed_2fa=True,
        ip_address=ip_address,
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        device_id=device_id,
    )

    # Prepare response
    response = Response(
        {
            "message": "Login successful",
            "user": UserProfileSerializer(user).data,
            "refresh_token": refresh_token_str,
        },
        status=status.HTTP_200_OK,
    )

    # Set httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="Lax",
    )

    return response


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh(request):
    """
    Refresh access token using refresh token
    """
    serializer = RefreshTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    refresh_token_str = serializer.validated_data.get("refresh_token")

    if not refresh_token_str:
        return Response(
            {"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Verify and rotate refresh token
    device_info = parse_device_info(request)
    new_refresh_token_str, new_refresh_token_obj = rotate_refresh_token(
        refresh_token_str, device_info
    )

    if not new_refresh_token_obj:
        return Response(
            {"error": "Invalid or expired refresh token"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Generate new access token
    user = new_refresh_token_obj.user
    device_id = new_refresh_token_obj.device_id

    access_token, access_expires = generate_access_token(user, device_id)

    # Prepare response
    response = Response(
        {"message": "Token refreshed", "refresh_token": new_refresh_token_str},
        status=status.HTTP_200_OK,
    )

    # Set new access token in cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="Lax",
    )

    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout - revoke tokens and optionally logout all devices
    """
    serializer = LogoutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    all_devices = serializer.validated_data.get("all_devices", False)
    user = request.user
    device_id = getattr(request, "device_id", None)

    if all_devices:
        # Logout from all devices
        revoke_all_user_tokens(user)
        DeviceSession.objects.filter(user=user, is_active=True).update(is_active=False)
        message = "Logged out from all devices"
    else:
        # Logout from current device only
        if device_id:
            terminate_device_session(user, device_id)
            message = "Logged out successfully"
        else:
            message = "Logged out (no device session found)"

    # Prepare response
    response = Response({"message": message}, status=status.HTTP_200_OK)

    # Clear access token cookie
    response.delete_cookie("access_token")

    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Get current user profile
    """
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def setup_2fa(request):
    """
    Setup 2FA for user - returns QR code and backup codes
    """
    user = request.user

    # Setup 2FA
    setup_data = setup_2fa_for_user(user)

    serializer = TwoFASetupSerializer(setup_data)

    return Response(
        {
            "message": "2FA setup initiated. Scan QR code with authenticator app.",
            **serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def enable_2fa(request):
    """
    Enable 2FA after verifying setup code
    """
    serializer = TwoFAVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    code = serializer.validated_data["code"]
    user = request.user

    # Enable 2FA
    success = enable_2fa_for_user(user, code)

    if not success:
        return Response(
            {"error": "Invalid verification code"}, status=status.HTTP_400_BAD_REQUEST
        )

    return Response({"message": "2FA enabled successfully"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def disable_2fa(request):
    """
    Disable 2FA for user
    """
    user = request.user
    disable_2fa_for_user(user)

    return Response({"message": "2FA disabled successfully"}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def device_sessions(request):
    """
    List all active device sessions for user
    """
    sessions = DeviceSession.objects.filter(user=request.user, is_active=True).order_by(
        "-last_activity"
    )

    serializer = DeviceSessionSerializer(
        sessions, many=True, context={"request": request}
    )

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def terminate_session(request, session_id):
    """
    Terminate a specific device session
    """
    try:
        session = DeviceSession.objects.get(id=session_id, user=request.user)
    except DeviceSession.DoesNotExist:
        return Response(
            {"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND
        )

    terminate_device_session(request.user, session.device_id)

    return Response(
        {"message": "Session terminated successfully"}, status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password
    """
    serializer = ChangePasswordSerializer(
        data=request.data, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)

    user = request.user
    user.set_password(serializer.validated_data["new_password"])
    user.save()

    # Optionally logout all other devices
    device_id = getattr(request, "device_id", None)
    revoke_all_user_tokens(user, except_device_id=device_id)

    return Response(
        {"message": "Password changed successfully"}, status=status.HTTP_200_OK
    )
