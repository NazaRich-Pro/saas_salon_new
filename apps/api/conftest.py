"""
Pytest configuration and shared fixtures.
"""
import pytest
from apps.bookings.models import Location, Service, ServiceCategory, Staff
from apps.payments.models_billing import SaaSSubscription
from apps.tenants.models import Membership, Tenant
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """API client for making requests."""
    return APIClient()


@pytest.fixture
def tenant(db):
    """Create a test tenant."""
    tenant = Tenant.objects.create(
        slug="test-salon", name="Test Salon", type="SALON", seats=3, status="ACTIVE"
    )

    # Create subscription
    SaaSSubscription.objects.create(
        tenant=tenant, plan_type="SALON", seats=3, status="ACTIVE"
    )

    return tenant


@pytest.fixture
def another_tenant(db):
    """Create another tenant for isolation testing."""
    tenant = Tenant.objects.create(
        slug="another-salon",
        name="Another Salon",
        type="SALON",
        seats=2,
        status="ACTIVE",
    )

    SaaSSubscription.objects.create(
        tenant=tenant, plan_type="SALON", seats=2, status="ACTIVE"
    )

    return tenant


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        email="test@example.com", password="testpass123", phone="+996700111111"
    )


@pytest.fixture
def admin_user(db, tenant):
    """Create an admin user with membership."""
    user = User.objects.create_user(email="admin@example.com", password="adminpass123")

    Membership.objects.create(
        user=user, tenant=tenant, role=Membership.ROLE_SALON_ADMIN
    )

    return user


@pytest.fixture
def staff_user(db, tenant):
    """Create a staff user with membership."""
    user = User.objects.create_user(email="staff@example.com", password="staffpass123")

    Membership.objects.create(user=user, tenant=tenant, role=Membership.ROLE_STAFF)

    return user


@pytest.fixture
def authenticated_client(api_client, admin_user, tenant):
    """Authenticated API client with tenant context."""
    api_client.force_authenticate(user=admin_user)
    api_client.tenant = tenant
    return api_client


@pytest.fixture
def location(db, tenant):
    """Create a test location."""
    return Location.objects.create(
        tenant=tenant,
        name="Main Location",
        timezone="Asia/Bishkek",
        address="Test Address",
    )


@pytest.fixture
def service_category(db, tenant):
    """Create a test service category."""
    return ServiceCategory.objects.create(
        tenant=tenant, name="Hair Services", sort_order=1
    )


@pytest.fixture
def service(db, tenant, service_category):
    """Create a test service."""
    return Service.objects.create(
        tenant=tenant,
        category=service_category,
        name="Haircut",
        duration_minutes=60,
        price_kgs=1000,
        buffer_before_minutes=0,
        buffer_after_minutes=0,
        allow_combo=True,
    )


@pytest.fixture
def staff(db, tenant, user):
    """Create a test staff member."""
    return Staff.objects.create(
        tenant=tenant,
        user=user,
        name="John Barber",
        skills={"specialization": "haircuts"},
        commission_percent=50,
    )
