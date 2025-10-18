"""
Tests for authentication functionality.
"""
import pytest
from apps.users.models import DeviceSession, User
from django.urls import reverse
from rest_framework import status


@pytest.mark.auth
class TestAuthentication:
    """Test authentication flows."""

    def test_register_user(self, api_client):
        """Test user registration."""
        url = reverse("register")
        data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "phone": "+996700111111",
        }

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email="newuser@example.com").exists()

    def test_login_success(self, api_client, user):
        """Test successful login."""
        url = reverse("login")
        data = {"email": "test@example.com", "password": "testpass123"}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data
        assert "refresh_token" in response.data

    def test_login_invalid_credentials(self, api_client, user):
        """Test login with invalid credentials."""
        url = reverse("login")
        data = {"email": "test@example.com", "password": "wrongpassword"}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token(self, api_client, user):
        """Test token refresh."""
        # Login first
        login_url = reverse("login")
        login_data = {"email": "test@example.com", "password": "testpass123"}
        login_response = api_client.post(login_url, login_data)
        refresh_token = login_response.data["refresh_token"]

        # Refresh
        refresh_url = reverse("refresh")
        refresh_data = {"refresh_token": refresh_token}

        response = api_client.post(refresh_url, refresh_data)

        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.data

    def test_logout(self, api_client, user):
        """Test logout."""
        # Login first
        api_client.force_authenticate(user=user)

        url = reverse("logout")
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK

    def test_device_session_created(self, api_client, user):
        """Test that device session is created on login."""
        url = reverse("login")
        data = {"email": "test@example.com", "password": "testpass123"}

        api_client.post(url, data)

        assert DeviceSession.objects.filter(user=user).exists()


@pytest.mark.auth
class TestPasswordChange:
    """Test password change functionality."""

    def test_change_password_success(self, api_client, user):
        """Test successful password change."""
        api_client.force_authenticate(user=user)

        url = reverse("change_password")
        data = {"old_password": "testpass123", "new_password": "NewSecurePass123!"}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_200_OK

        # Verify new password works
        user.refresh_from_db()
        assert user.check_password("NewSecurePass123!")

    def test_change_password_wrong_old_password(self, api_client, user):
        """Test password change with wrong old password."""
        api_client.force_authenticate(user=user)

        url = reverse("change_password")
        data = {"old_password": "wrongpassword", "new_password": "NewSecurePass123!"}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.auth
class TestRateLimiting:
    """Test rate limiting on auth endpoints."""

    def test_login_rate_limit(self, api_client, user):
        """Test that login is rate limited after too many attempts."""
        url = reverse("login")
        data = {"email": "test@example.com", "password": "wrongpassword"}

        # Make 6 attempts (limit is 5)
        for i in range(6):
            response = api_client.post(url, data)

        # 6th attempt should be rate limited
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
