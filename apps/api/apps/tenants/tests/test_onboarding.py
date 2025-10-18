"""Tests for auto onboarding"""
import pytest
from apps.booking.models import Location, Service, Staff
from apps.payments.models import LoyaltyRule, SaaSSubscription
from apps.tenants.models import Membership, Tenant
from apps.tenants.onboarding_service import OnboardingService
from apps.users.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestOnboardingService:
    """Test onboarding service"""

    def test_generate_unique_slug(self):
        """Test slug generation"""
        service = OnboardingService()

        slug = service.generate_unique_slug("My Salon")
        assert slug == "my-salon"

        # Create tenant with this slug
        Tenant.objects.create(
            slug="my-salon", name="My Salon", type="SALON", status="ACTIVE"
        )

        # Next slug should be different
        slug2 = service.generate_unique_slug("My Salon")
        assert slug2 == "my-salon-1"

    def test_transliterate_cyrillic(self):
        """Test Cyrillic transliteration"""
        service = OnboardingService()

        slug = service.generate_unique_slug("Мой Салон")
        assert "moy" in slug or "salon" in slug

        slug2 = service.generate_unique_slug("Красота")
        assert slug2  # Should generate something

    def test_auto_login_token_generation(self):
        """Test auto-login token generation"""
        token = OnboardingService.generate_auto_login_token()

        assert len(token) == 64
        assert token.isalnum()

    def test_create_salon_full_setup(self):
        """Test complete salon creation"""
        service = OnboardingService()

        result = service.create_salon(
            salon_name="Test Salon",
            owner_name="Test Owner",
            email="owner@test.com",
            phone="+996700123456",
            password="testpass123",
            seats=3,
        )

        assert result["tenant"] is not None
        assert result["user"] is not None
        assert result["tenant_url"].startswith("https://")
        assert len(result["auto_login_token"]) == 64

        # Check tenant created
        tenant = result["tenant"]
        assert tenant.slug is not None
        assert tenant.name == "Test Salon"
        assert tenant.type == "SALON"
        assert tenant.seats == 3
        assert tenant.status == "TRIAL"

        # Check user created
        user = result["user"]
        assert user.email == "owner@test.com"
        assert user.check_password("testpass123")

        # Check membership created
        assert Membership.objects.filter(
            user=user, tenant=tenant, role="SALON_ADMIN"
        ).exists()

        # Check defaults created
        assert Location.objects.filter(tenant=tenant).exists()
        assert Service.objects.filter(tenant=tenant).count() >= 2
        assert LoyaltyRule.objects.filter(tenant=tenant).exists()
        assert SaaSSubscription.objects.filter(tenant=tenant).exists()

    def test_create_solo_master_full_setup(self):
        """Test complete solo master creation"""
        service = OnboardingService()

        result = service.create_solo_master(
            master_name="Anna Smith",
            email="anna@test.com",
            phone="+996700999999",
            password="testpass123",
            specialty="Nail Artist",
        )

        assert result["tenant"] is not None
        assert result["user"] is not None

        # Check tenant
        tenant = result["tenant"]
        assert tenant.type == "SOLO"
        assert tenant.seats == 1

        # Check staff profile created
        assert Staff.objects.filter(tenant=tenant, user=result["user"]).exists()

        # Check schedule created
        from apps.booking.models import Schedule

        assert Schedule.objects.filter(tenant=tenant).exists()


@pytest.mark.django_db
class TestRegisterSalonAPI:
    """Test salon registration API"""

    def test_register_salon_success(self, api_client):
        """Test successful salon registration"""
        url = "/api/register-salon/register-salon/"
        data = {
            "salon_name": "Beautiful Salon",
            "owner_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+996700111111",
            "password": "securepass123",
            "confirm_password": "securepass123",
            "seats": 2,
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == 201
        assert "tenant_url" in response.data
        assert "tenant" in response.data

        # Check tenant was created
        tenant_slug = response.data["tenant"]["slug"]
        assert Tenant.objects.filter(slug=tenant_slug).exists()

        # Check user was created
        assert User.objects.filter(email="jane@example.com").exists()

        # Check URL format
        assert "saas.akylman.online/welcome?token=" in response.data["tenant_url"]

    def test_register_salon_duplicate_email(self, api_client):
        """Test registration fails with duplicate email"""
        # Create existing user
        User.objects.create_user(email="existing@example.com", password="pass123")

        url = "/api/register-salon/register-salon/"
        data = {
            "salon_name": "New Salon",
            "owner_name": "John Doe",
            "email": "existing@example.com",  # Duplicate
            "phone": "+996700222222",
            "password": "securepass123",
            "confirm_password": "securepass123",
            "seats": 1,
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == 400
        assert "email" in str(response.data).lower()

    def test_register_salon_password_mismatch(self, api_client):
        """Test registration fails with password mismatch"""
        url = "/api/register-salon/register-salon/"
        data = {
            "salon_name": "Test Salon",
            "owner_name": "Test Owner",
            "email": "test@example.com",
            "phone": "+996700333333",
            "password": "pass123456",
            "confirm_password": "different123",  # Mismatch
            "seats": 1,
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == 400

    def test_register_salon_weak_password(self, api_client):
        """Test registration fails with weak password"""
        url = "/api/register-salon/register-salon/"
        data = {
            "salon_name": "Test Salon",
            "owner_name": "Test Owner",
            "email": "test@example.com",
            "phone": "+996700444444",
            "password": "123",  # Too weak
            "confirm_password": "123",
            "seats": 1,
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == 400


@pytest.mark.django_db
class TestRegisterSoloAPI:
    """Test solo master registration API"""

    def test_register_solo_success(self, api_client):
        """Test successful solo master registration"""
        url = "/api/register-solo/register-solo/"
        data = {
            "master_name": "Maria Rodriguez",
            "email": "maria@example.com",
            "phone": "+996700555555",
            "specialty": "Hair Stylist",
            "password": "securepass123",
            "confirm_password": "securepass123",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == 201
        assert "tenant_url" in response.data

        # Check tenant created
        tenant_slug = response.data["tenant"]["slug"]
        tenant = Tenant.objects.get(slug=tenant_slug)

        assert tenant.type == "SOLO"
        assert tenant.seats == 1

        # Check staff profile created
        assert Staff.objects.filter(tenant=tenant).exists()


@pytest.mark.django_db
class TestAutoLogin:
    """Test auto-login with token"""

    def test_auto_login_with_valid_token(self, api_client):
        """Test auto-login with valid token"""
        # Create user and tenant
        service = OnboardingService()
        result = service.create_salon(
            salon_name="Auto Login Test",
            owner_name="Test Owner",
            email="autologin@test.com",
            phone="+996700666666",
            password="testpass123",
            seats=1,
        )

        token = result["auto_login_token"]

        # Attempt auto-login
        url = "/api/tenants/auto-login/"
        response = api_client.post(url, {"token": token}, format="json")

        assert response.status_code == 200
        assert "user" in response.data
        assert "access_token" in response.cookies

    def test_auto_login_invalid_token(self, api_client):
        """Test auto-login fails with invalid token"""
        url = "/api/tenants/auto-login/"
        response = api_client.post(url, {"token": "invalid-token-123"}, format="json")

        assert response.status_code == 400

    def test_auto_login_token_expires(self, api_client):
        """Test auto-login token is one-time use"""
        service = OnboardingService()
        result = service.create_salon(
            salon_name="Expire Test",
            owner_name="Test",
            email="expire@test.com",
            phone="+996700777777",
            password="testpass123",
            seats=1,
        )

        token = result["auto_login_token"]
        url = "/api/tenants/auto-login/"

        # First use - should work
        response1 = api_client.post(url, {"token": token}, format="json")
        assert response1.status_code == 200

        # Second use - should fail (token deleted after first use)
        response2 = api_client.post(url, {"token": token}, format="json")
        assert response2.status_code == 400


@pytest.mark.django_db
class TestDefaultsCreation:
    """Test default resources are created"""

    def test_salon_defaults(self):
        """Test salon gets default resources"""
        service = OnboardingService()

        result = service.create_salon(
            salon_name="Defaults Test Salon",
            owner_name="Owner",
            email="defaults@test.com",
            phone="+996700888888",
            password="testpass123",
            seats=2,
        )

        tenant = result["tenant"]

        # Check location
        locations = Location.objects.filter(tenant=tenant)
        assert locations.count() >= 1

        # Check services
        services = Service.objects.filter(tenant=tenant)
        assert services.count() >= 2

        # Check service categories
        from apps.booking.models import ServiceCategory

        categories = ServiceCategory.objects.filter(tenant=tenant)
        assert categories.count() >= 2

        # Check loyalty rule
        loyalty = LoyaltyRule.objects.filter(tenant=tenant).first()
        assert loyalty is not None
        assert loyalty.earn_per_100_kgs == 1

        # Check subscription
        subscription = SaaSSubscription.objects.filter(tenant=tenant).first()
        assert subscription is not None
        assert subscription.plan == "SALON"
        assert subscription.seats == 2
        assert subscription.status == "TRIAL"

    def test_solo_defaults(self):
        """Test solo master gets appropriate defaults"""
        service = OnboardingService()

        result = service.create_solo_master(
            master_name="Solo Test",
            email="solo@test.com",
            phone="+996700999999",
            password="testpass123",
            specialty="Test Specialist",
        )

        tenant = result["tenant"]

        # Check staff profile
        staff = Staff.objects.filter(tenant=tenant).first()
        assert staff is not None
        assert staff.name == "Solo Test"
        assert staff.title == "Test Specialist"

        # Check schedule
        from apps.booking.models import Schedule

        schedule = Schedule.objects.filter(tenant=tenant, staff=staff).first()
        assert schedule is not None
        assert "monday" in schedule.rules

        # Check subscription
        subscription = SaaSSubscription.objects.filter(tenant=tenant).first()
        assert subscription.plan == "SOLO"
        assert subscription.seats == 1


@pytest.mark.django_db
class TestRateLimiting:
    """Test rate limiting on registration"""

    def test_registration_rate_limited(self, api_client):
        """Test registration is rate limited"""
        url = "/api/register-salon/register-salon/"

        # Try to register 6 times (limit is 5/hour)
        for i in range(6):
            data = {
                "salon_name": f"Salon {i}",
                "owner_name": f"Owner {i}",
                "email": f"owner{i}@test.com",
                "phone": f"+99670000000{i}",
                "password": "testpass123",
                "confirm_password": "testpass123",
                "seats": 1,
            }

            response = api_client.post(url, data, format="json")

            if i < 5:
                # First 5 should succeed or fail for other reasons
                assert response.status_code in [201, 400]
            else:
                # 6th should be rate limited
                assert response.status_code == 429
