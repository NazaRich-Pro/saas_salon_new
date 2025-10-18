"""User models for authentication"""
import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superadmin", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)

    # 2FA
    twofa_secret = models.CharField(max_length=32, blank=True, null=True)
    twofa_enabled = models.BooleanField(default=False)

    # Login attempts tracking
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    locked_until = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    def is_locked(self):
        """Check if user account is locked"""
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def record_failed_login(self):
        """Record a failed login attempt"""
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()

        # Lock account after 5 failed attempts for 15 minutes
        if self.failed_login_attempts >= 5:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=15)

        self.save(
            update_fields=["failed_login_attempts", "last_failed_login", "locked_until"]
        )

    def reset_failed_login(self):
        """Reset failed login counter"""
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.locked_until = None
        self.save(
            update_fields=["failed_login_attempts", "last_failed_login", "locked_until"]
        )


class RefreshToken(models.Model):
    """Refresh token for JWT authentication with rotation"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="refresh_tokens"
    )
    token = models.CharField(max_length=255, unique=True, db_index=True)

    # Device info
    device_id = models.CharField(
        max_length=255, db_index=True, help_text="Unique device identifier"
    )
    device_name = models.CharField(
        max_length=255, blank=True, help_text="User-friendly device name"
    )
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Token lifecycle
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)

    # Rotation tracking
    previous_token = models.CharField(
        max_length=255, blank=True, help_text="Previous token in rotation chain"
    )
    is_revoked = models.BooleanField(default=False, db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "refresh_tokens"
        verbose_name = "Refresh Token"
        verbose_name_plural = "Refresh Tokens"
        indexes = [
            models.Index(fields=["user", "device_id", "is_revoked"]),
            models.Index(fields=["token", "is_revoked"]),
            models.Index(fields=["expires_at", "is_revoked"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.device_name}"

    def is_valid(self):
        """Check if token is valid (not expired and not revoked)"""
        return not self.is_revoked and self.expires_at > timezone.now()

    def revoke(self):
        """Revoke this token"""
        self.is_revoked = True
        self.revoked_at = timezone.now()
        self.save(update_fields=["is_revoked", "revoked_at"])


class DeviceSession(models.Model):
    """Active device session tracking"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="device_sessions"
    )
    device_id = models.CharField(max_length=255, db_index=True)

    # Device information
    device_name = models.CharField(max_length=255, blank=True)
    device_type = models.CharField(
        max_length=50, blank=True, help_text="mobile, desktop, tablet"
    )
    os = models.CharField(max_length=100, blank=True)
    browser = models.CharField(max_length=100, blank=True)

    # Location
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)

    # Session lifecycle
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "device_sessions"
        verbose_name = "Device Session"
        verbose_name_plural = "Device Sessions"
        unique_together = [["user", "device_id"]]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["device_id", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.device_name} ({self.device_type})"

    def is_expired(self):
        """Check if session is expired"""
        return self.expires_at < timezone.now()

    def terminate(self):
        """Terminate this session"""
        self.is_active = False
        self.save(update_fields=["is_active"])


class LoginAttempt(models.Model):
    """Login attempt logging for security monitoring"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="login_attempts",
    )

    # Attempt result
    success = models.BooleanField(default=False, db_index=True)
    failure_reason = models.CharField(max_length=100, blank=True)

    # Request info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_id = models.CharField(max_length=255, blank=True)

    # 2FA
    required_2fa = models.BooleanField(default=False)
    passed_2fa = models.BooleanField(default=False)

    attempted_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "login_attempts"
        verbose_name = "Login Attempt"
        verbose_name_plural = "Login Attempts"
        indexes = [
            models.Index(fields=["email", "attempted_at"]),
            models.Index(fields=["ip_address", "attempted_at"]),
            models.Index(fields=["user", "success", "attempted_at"]),
        ]
        ordering = ["-attempted_at"]

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.email} - {status} at {self.attempted_at}"
