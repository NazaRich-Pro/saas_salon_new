"""Authentication serializers"""
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers

from .models import DeviceSession, LoginAttempt, User
from .totp_utils import requires_2fa, verify_totp_code


class LoginSerializer(serializers.Serializer):
    """Serializer for login"""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    device_id = serializers.CharField(required=False)
    remember_me = serializers.BooleanField(default=False)

    def validate(self, attrs):
        email = attrs.get("email", "").lower()
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError("Email and password are required")

        # Try to get user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        # Check if account is locked
        if user.is_locked():
            minutes_left = int(
                (user.locked_until - timezone.now()).total_seconds() / 60
            )
            raise serializers.ValidationError(
                f"Account is temporarily locked. Try again in {minutes_left} minutes."
            )

        # Check password
        if not user.check_password(password):
            user.record_failed_login()
            raise serializers.ValidationError("Invalid credentials")

        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError("Account is inactive")

        # Reset failed login attempts
        user.reset_failed_login()

        attrs["user"] = user
        return attrs


class TwoFAVerifySerializer(serializers.Serializer):
    """Serializer for 2FA verification"""

    code = serializers.CharField(min_length=6, max_length=6)

    def validate_code(self, value):
        # Must be 6 digits
        if not value.isdigit():
            raise serializers.ValidationError("Code must be 6 digits")
        return value


class TwoFASetupSerializer(serializers.Serializer):
    """Serializer for 2FA setup response"""

    secret = serializers.CharField(read_only=True)
    qr_code = serializers.CharField(read_only=True)
    backup_codes = serializers.ListField(child=serializers.CharField(), read_only=True)


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer for refresh token"""

    refresh_token = serializers.CharField(required=False)


class LogoutSerializer(serializers.Serializer):
    """Serializer for logout"""

    all_devices = serializers.BooleanField(default=False)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "phone",
            "is_superadmin",
            "twofa_enabled",
            "created_at",
            "last_login",
        ]
        read_only_fields = ["id", "email", "is_superadmin", "created_at", "last_login"]


class DeviceSessionSerializer(serializers.ModelSerializer):
    """Serializer for device sessions"""

    is_current = serializers.SerializerMethodField()

    class Meta:
        model = DeviceSession
        fields = [
            "id",
            "device_id",
            "device_name",
            "device_type",
            "os",
            "browser",
            "ip_address",
            "country",
            "city",
            "is_current",
            "is_active",
            "created_at",
            "last_activity",
            "expires_at",
        ]
        read_only_fields = fields

    def get_is_current(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "device_id"):
            return obj.device_id == request.device_id
        return False


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""

    current_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    confirm_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match"}
            )

        if len(attrs["new_password"]) < 8:
            raise serializers.ValidationError(
                {"new_password": "Password must be at least 8 characters"}
            )

        return attrs

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value


class LoginAttemptSerializer(serializers.ModelSerializer):
    """Serializer for login attempts"""

    class Meta:
        model = LoginAttempt
        fields = [
            "id",
            "email",
            "success",
            "failure_reason",
            "required_2fa",
            "passed_2fa",
            "ip_address",
            "device_id",
            "attempted_at",
        ]
        read_only_fields = fields
