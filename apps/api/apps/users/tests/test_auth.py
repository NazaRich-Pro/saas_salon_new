"""Tests for authentication"""
from datetime import timedelta

import pytest
from apps.users.jwt_utils import generate_access_token, generate_refresh_token
from apps.users.models import DeviceSession, LoginAttempt, RefreshToken, User
from apps.users.totp_utils import setup_2fa_for_user, verify_totp_code
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user(db):
    user = User.objects.create_user(email="test@example.com", password="testpass123")
    return user


@pytest.fixture
def test_superadmin(db):
    user = User.objects.create_superuser(
        email="admin@example.com", password="adminpass123"
    )
    return user


@pytest.mark.django_db
class TestLogin:
    """Test login endpoint"""

    def test_successful_login(self, api_client, test_user):
        """Test successful login without 2FA"""
        url = reverse("login")
        data = {"email": "test@example.com", "password": "testpass123"}

        response = api_client.post(url, data)

        assert response.status_code == 200
        assert "user" in response.data
        assert "refresh_token" in response.data
        assert "access_token" in response.cookies

        # Check refresh token was created
        assert RefreshToken.objects.filter(user=test_user).exists()

        # Check login attempt was logged
        assert LoginAttempt.objects.filter(
            email="test@example.com", success=True
        ).exists()

    def test_login_invalid_credentials(self, api_client, test_user):
        """Test login with wrong password"""
        url = reverse("login")
        data = {"email": "test@example.com", "password": "wrongpassword"}

        response = api_client.post(url, data)

        assert response.status_code == 400

        # Check failed login was recorded
        test_user.refresh_from_db()
        assert test_user.failed_login_attempts == 1

    def test_login_nonexistent_user(self, api_client):
        """Test login with non-existent email"""
        url = reverse("login")
        data = {"email": "nonexistent@example.com", "password": "somepassword"}

        response = api_client.post(url, data)

        assert response.status_code == 400

    def test_login_locked_account(self, api_client, test_user):
        """Test login with locked account"""
        # Lock the account
        test_user.failed_login_attempts = 5
        test_user.locked_until = timezone.now() + timedelta(minutes=15)
        test_user.save()

        url = reverse("login")
        data = {"email": "test@example.com", "password": "testpass123"}

        response = api_client.post(url, data)

        assert response.status_code == 400
        assert "locked" in response.data["non_field_errors"][0].lower()

    def test_login_requires_2fa(self, api_client, test_superadmin):
        """Test login with 2FA required"""
        # Setup 2FA for superadmin
        setup_data = setup_2fa_for_user(test_superadmin)
        test_superadmin.twofa_enabled = True
        test_superadmin.save()

        url = reverse("login")
        data = {"email": "admin@example.com", "password": "adminpass123"}

        response = api_client.post(url, data)

        assert response.status_code == 200
        assert response.data["requires_2fa"] is True
        assert "access_token" not in response.cookies


@pytest.mark.django_db
class TestRefreshToken:
    """Test refresh token endpoint"""

    def test_refresh_token_success(self, api_client, test_user):
        """Test successful token refresh"""
        # Generate refresh token
        device_id = "test-device-123"
        device_info = {
            "device_name": "Test Device",
            "user_agent": "Mozilla/5.0",
            "ip_address": "127.0.0.1",
        }

        refresh_token_str, refresh_token_obj = generate_refresh_token(
            test_user, device_id, device_info
        )

        url = reverse("refresh")
        data = {"refresh_token": refresh_token_str}

        response = api_client.post(url, data)

        assert response.status_code == 200
        assert "refresh_token" in response.data
        assert "access_token" in response.cookies

        # Old token should be revoked
        refresh_token_obj.refresh_from_db()
        assert refresh_token_obj.is_revoked is True

        # New token should exist
        new_token = RefreshToken.objects.filter(
            user=test_user, device_id=device_id, is_revoked=False
        ).first()
        assert new_token is not None

    def test_refresh_invalid_token(self, api_client):
        """Test refresh with invalid token"""
        url = reverse("refresh")
        data = {"refresh_token": "invalid-token-123"}

        response = api_client.post(url, data)

        assert response.status_code == 401


@pytest.mark.django_db
class TestLogout:
    """Test logout endpoint"""

    def test_logout_current_device(self, api_client, test_user):
        """Test logout from current device"""
        # Login first
        access_token, _ = generate_access_token(test_user, "device-123")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        url = reverse("logout")
        data = {"all_devices": False}

        response = api_client.post(url, data)

        assert response.status_code == 200
        assert "access_token" not in response.cookies

    def test_logout_all_devices(self, api_client, test_user):
        """Test logout from all devices"""
        # Create multiple sessions
        for i in range(3):
            generate_refresh_token(
                test_user,
                f"device-{i}",
                {
                    "device_name": f"Device {i}",
                    "user_agent": "Mozilla/5.0",
                    "ip_address": "127.0.0.1",
                },
            )

        assert (
            RefreshToken.objects.filter(user=test_user, is_revoked=False).count() == 3
        )

        # Login and logout all
        access_token, _ = generate_access_token(test_user, "device-0")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        url = reverse("logout")
        data = {"all_devices": True}

        response = api_client.post(url, data)

        assert response.status_code == 200

        # All tokens should be revoked
        assert (
            RefreshToken.objects.filter(user=test_user, is_revoked=False).count() == 0
        )


@pytest.mark.django_db
class Test2FA:
    """Test 2FA functionality"""

    def test_2fa_setup(self, api_client, test_user):
        """Test 2FA setup"""
        access_token, _ = generate_access_token(test_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        url = reverse("setup_2fa")
        response = api_client.post(url)

        assert response.status_code == 200
        assert "secret" in response.data
        assert "qr_code" in response.data
        assert "backup_codes" in response.data

        # User should have secret but not enabled
        test_user.refresh_from_db()
        assert test_user.twofa_secret is not None
        assert test_user.twofa_enabled is False

    def test_2fa_enable(self, api_client, test_user):
        """Test enabling 2FA"""
        # Setup 2FA first
        setup_data = setup_2fa_for_user(test_user)
        secret = setup_data["secret"]

        # Generate valid TOTP code
        import pyotp

        totp = pyotp.TOTP(secret)
        code = totp.now()

        access_token, _ = generate_access_token(test_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        url = reverse("enable_2fa")
        data = {"code": code}
        response = api_client.post(url, data)

        assert response.status_code == 200

        # 2FA should be enabled
        test_user.refresh_from_db()
        assert test_user.twofa_enabled is True

    def test_2fa_disable(self, api_client, test_user):
        """Test disabling 2FA"""
        # Enable 2FA first
        test_user.twofa_enabled = True
        test_user.twofa_secret = "TESTSECRET123456"
        test_user.save()

        access_token, _ = generate_access_token(test_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        url = reverse("disable_2fa")
        response = api_client.post(url)

        assert response.status_code == 200

        # 2FA should be disabled
        test_user.refresh_from_db()
        assert test_user.twofa_enabled is False
        assert test_user.twofa_secret is None


@pytest.mark.django_db
class TestProfile:
    """Test profile endpoints"""

    def test_get_profile(self, api_client, test_user):
        """Test getting user profile"""
        access_token, _ = generate_access_token(test_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        url = reverse("profile")
        response = api_client.get(url)

        assert response.status_code == 200
        assert response.data["email"] == "test@example.com"
        assert "id" in response.data

    def test_change_password(self, api_client, test_user):
        """Test password change"""
        access_token, _ = generate_access_token(test_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        url = reverse("change_password")
        data = {
            "current_password": "testpass123",
            "new_password": "newpass456",
            "confirm_password": "newpass456",
        }

        response = api_client.post(url, data)

        assert response.status_code == 200

        # Verify new password works
        test_user.refresh_from_db()
        assert test_user.check_password("newpass456")


@pytest.mark.django_db
class TestDeviceSessions:
    """Test device session management"""

    def test_list_device_sessions(self, api_client, test_user):
        """Test listing device sessions"""
        # Create sessions
        for i in range(3):
            DeviceSession.objects.create(
                user=test_user,
                device_id=f"device-{i}",
                device_name=f"Device {i}",
                device_type="desktop",
                expires_at=timezone.now() + timedelta(days=7),
                is_active=True,
            )

        access_token, _ = generate_access_token(test_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        url = reverse("device_sessions")
        response = api_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 3

    def test_terminate_session(self, api_client, test_user):
        """Test terminating a device session"""
        session = DeviceSession.objects.create(
            user=test_user,
            device_id="device-to-terminate",
            device_name="Test Device",
            device_type="mobile",
            expires_at=timezone.now() + timedelta(days=7),
            is_active=True,
        )

        access_token, _ = generate_access_token(test_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        url = reverse("terminate_session", kwargs={"session_id": session.id})
        response = api_client.delete(url)

        assert response.status_code == 200

        # Session should be terminated
        session.refresh_from_db()
        assert session.is_active is False


@pytest.mark.django_db
class TestAccountLocking:
    """Test account locking after failed attempts"""

    def test_account_locks_after_5_failures(self, api_client, test_user):
        """Test account locks after 5 failed login attempts"""
        url = reverse("login")

        # Make 5 failed attempts
        for i in range(5):
            data = {"email": "test@example.com", "password": "wrongpassword"}
            response = api_client.post(url, data)
            assert response.status_code == 400

        # Account should be locked
        test_user.refresh_from_db()
        assert test_user.is_locked() is True
        assert test_user.failed_login_attempts == 5

        # Next attempt should fail with locked message
        response = api_client.post(url, data)
        assert response.status_code == 400
        assert "locked" in str(response.data).lower()

    def test_successful_login_resets_counter(self, api_client, test_user):
        """Test successful login resets failed attempt counter"""
        # Record some failed attempts
        test_user.failed_login_attempts = 3
        test_user.save()

        url = reverse("login")
        data = {"email": "test@example.com", "password": "testpass123"}

        response = api_client.post(url, data)

        assert response.status_code == 200

        # Counter should be reset
        test_user.refresh_from_db()
        assert test_user.failed_login_attempts == 0
