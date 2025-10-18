"""Tenant serializers"""
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from rest_framework import serializers

from .models import Membership, Tenant, TenantDomain


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model"""

    class Meta:
        model = Tenant
        fields = [
            "id",
            "slug",
            "name",
            "type",
            "plan",
            "seats",
            "status",
            "trial_ends",
            "settings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class RegisterSalonSerializer(serializers.Serializer):
    """Serializer for salon registration"""

    salon_name = serializers.CharField(max_length=255)
    owner_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    seats = serializers.IntegerField(min_value=1, max_value=50, default=1)

    def validate_email(self, value):
        """Check email is not already used"""
        from apps.users.models import User

        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Этот email уже используется")

        return value.lower()

    def validate_password(self, value):
        """Validate password strength"""
        try:
            validate_password(value)
        except django_exceptions.ValidationError as e:
            raise serializers.ValidationError(list(e.messages))

        return value

    def validate(self, attrs):
        """Validate passwords match"""
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Пароли не совпадают"}
            )

        return attrs


class RegisterSoloSerializer(serializers.Serializer):
    """Serializer for solo master registration"""

    master_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    specialty = serializers.CharField(max_length=100, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    confirm_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    def validate_email(self, value):
        """Check email is not already used"""
        from apps.users.models import User

        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Этот email уже используется")

        return value.lower()

    def validate_password(self, value):
        """Validate password strength"""
        try:
            validate_password(value)
        except django_exceptions.ValidationError as e:
            raise serializers.ValidationError(list(e.messages))

        return value

    def validate(self, attrs):
        """Validate passwords match"""
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Пароли не совпадают"}
            )

        return attrs


class MembershipSerializer(serializers.ModelSerializer):
    """Serializer for Membership model"""

    user_email = serializers.CharField(source="user.email", read_only=True)
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)

    class Meta:
        model = Membership
        fields = [
            "id",
            "user",
            "user_email",
            "tenant",
            "tenant_name",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TenantDomainSerializer(serializers.ModelSerializer):
    """Serializer for custom domains"""

    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    is_verified = serializers.SerializerMethodField()

    class Meta:
        model = TenantDomain
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "domain",
            "verified_at",
            "is_verified",
            "created_at",
        ]
        read_only_fields = ["id", "verified_at", "created_at"]

    def get_is_verified(self, obj):
        return obj.verified_at is not None
