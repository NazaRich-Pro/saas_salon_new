"""Tenant views"""
from apps.notifications.email_service import EmailService
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .onboarding_service import OnboardingError, OnboardingService
from .serializers import (
    RegisterSalonSerializer,
    RegisterSoloSerializer,
    TenantSerializer,
)


class RegistrationThrottle(AnonRateThrottle):
    """Rate limit for registration: 5 per hour per IP"""

    scope = "registration"
    rate = "5/hour"


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RegistrationThrottle])
def register_salon(request):
    """
    Register new salon tenant

    Creates tenant, user, default setup, and returns auto-login URL

    Request:
        {
            "salon_name": "My Salon",
            "owner_name": "John Doe",
            "email": "owner@example.com",
            "phone": "+996700123456",
            "password": "secure_password",
            "confirm_password": "secure_password",
            "seats": 3
        }

    Response:
        {
            "message": "Salon created successfully",
            "tenant_url": "https://my-salon.saas.akylman.online/welcome?token=...",
            "tenant": {...}
        }
    """
    # Validate input
    serializer = RegisterSalonSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Extract data
    salon_name = serializer.validated_data["salon_name"]
    owner_name = serializer.validated_data["owner_name"]
    email = serializer.validated_data["email"]
    phone = serializer.validated_data["phone"]
    password = serializer.validated_data["password"]
    seats = serializer.validated_data.get("seats", 1)

    # Create salon
    onboarding_service = OnboardingService()

    try:
        result = onboarding_service.create_salon(
            salon_name=salon_name,
            owner_name=owner_name,
            email=email,
            phone=phone,
            password=password,
            seats=seats,
        )

        # Send welcome email
        email_service = EmailService(tenant=result["tenant"])

        # Determine language (default RU, can be detected from phone/country)
        language = "ru"

        email_service.send_welcome_email(
            owner_name=owner_name,
            owner_email=email,
            salon_name=salon_name,
            tenant_url=result["tenant_url"],
            language=language,
        )

        # Return response
        tenant_serializer = TenantSerializer(result["tenant"])

        return Response(
            {
                "message": "Салон успешно создан! Проверьте email.",
                "tenant_url": result["tenant_url"],
                "tenant": tenant_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    except OnboardingError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RegistrationThrottle])
def register_solo(request):
    """
    Register new solo master tenant

    Request:
        {
            "master_name": "Anna Smith",
            "email": "anna@example.com",
            "phone": "+996700123456",
            "specialty": "Nail Artist",
            "password": "secure_password",
            "confirm_password": "secure_password"
        }

    Response:
        {
            "message": "Solo master profile created successfully",
            "tenant_url": "https://anna-smith.saas.akylman.online/welcome?token=...",
            "tenant": {...}
        }
    """
    # Validate input
    serializer = RegisterSoloSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Extract data
    master_name = serializer.validated_data["master_name"]
    email = serializer.validated_data["email"]
    phone = serializer.validated_data["phone"]
    specialty = serializer.validated_data.get("specialty", "")
    password = serializer.validated_data["password"]

    # Create solo master
    onboarding_service = OnboardingService()

    try:
        result = onboarding_service.create_solo_master(
            master_name=master_name,
            email=email,
            phone=phone,
            password=password,
            specialty=specialty,
        )

        # Send welcome email
        email_service = EmailService(tenant=result["tenant"])
        language = "ru"

        email_service.send_welcome_email(
            owner_name=master_name,
            owner_email=email,
            salon_name=result["tenant"].name,
            tenant_url=result["tenant_url"],
            language=language,
        )

        # Return response
        tenant_serializer = TenantSerializer(result["tenant"])

        return Response(
            {
                "message": "Профиль мастера успешно создан! Проверьте email.",
                "tenant_url": result["tenant_url"],
                "tenant": tenant_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    except OnboardingError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def auto_login(request):
    """
    Auto-login with token from registration

    Request:
        {
            "token": "64-char-token"
        }

    Response:
        Sets auth cookies and returns user info
    """
    token = request.data.get("token")

    if not token:
        return Response(
            {"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Get token data from cache
    from django.core.cache import cache

    cache_key = f"auto_login_token:{token}"
    token_data = cache.get(cache_key)

    if not token_data:
        return Response(
            {"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Get user
    from apps.users.models import User

    try:
        user = User.objects.get(id=token_data["user_id"])
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    # Generate JWT tokens
    import uuid

    from apps.users.jwt_utils import (
        generate_access_token,
        generate_refresh_token,
        parse_device_info,
    )

    device_id = str(uuid.uuid4())
    access_token, _ = generate_access_token(user, device_id)

    device_info = parse_device_info(request)
    refresh_token_str, _ = generate_refresh_token(user, device_id, device_info)

    # Delete auto-login token (one-time use)
    cache.delete(cache_key)

    # Prepare response
    from apps.users.serializers import UserProfileSerializer

    response = Response(
        {
            "message": "Auto-login successful",
            "user": UserProfileSerializer(user).data,
            "refresh_token": refresh_token_str,
        },
        status=status.HTTP_200_OK,
    )

    # Set access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="Lax",
    )

    return response
