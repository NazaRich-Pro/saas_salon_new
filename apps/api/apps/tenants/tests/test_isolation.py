"""
Tests for tenant isolation.
Critical security tests to ensure data doesn't leak between tenants.
"""
from datetime import timedelta

import pytest
from apps.bookings.models import Appointment
from apps.customers.models import Customer
from apps.payments.models import Payment
from apps.users.models import Staff
from django.urls import reverse
from django.utils import timezone
from rest_framework import status


@pytest.mark.tenant_isolation
class TestTenantDataIsolation:
    """Test that tenant data is properly isolated."""

    def test_cannot_access_other_tenant_appointments(
        self, api_client, admin_user, tenant, another_tenant, staff, location
    ):
        """Test that admin cannot see another tenant's appointments."""
        # Create appointment in another tenant
        other_customer = Customer.objects.create(
            tenant=another_tenant, name="Other Customer", phone="+996700111111"
        )

        other_appointment = Appointment.objects.create(
            tenant=another_tenant,
            customer=other_customer,
            staff=staff,
            start_at=timezone.now() + timedelta(days=1),
            end_at=timezone.now() + timedelta(days=1, hours=1),
        )

        # Authenticate as admin of first tenant
        api_client.force_authenticate(user=admin_user)
        api_client.tenant = tenant

        # Try to access other tenant's appointment
        url = reverse("appointment-detail", args=[other_appointment.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_list_other_tenant_data(
        self, api_client, admin_user, tenant, another_tenant
    ):
        """Test that listing endpoints only show own tenant data."""
        # Create customers in both tenants
        Customer.objects.create(
            tenant=tenant, name="My Customer", phone="+996700111111"
        )
        Customer.objects.create(
            tenant=another_tenant, name="Other Customer", phone="+996700222222"
        )

        # Authenticate as admin of first tenant
        api_client.force_authenticate(user=admin_user)
        api_client.tenant = tenant

        # List customers
        url = reverse("customer-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "My Customer"

    def test_cannot_modify_other_tenant_data(
        self, api_client, admin_user, tenant, another_tenant
    ):
        """Test that admin cannot modify another tenant's data."""
        # Create customer in another tenant
        other_customer = Customer.objects.create(
            tenant=another_tenant, name="Other Customer", phone="+996700111111"
        )

        # Authenticate as admin of first tenant
        api_client.force_authenticate(user=admin_user)
        api_client.tenant = tenant

        # Try to update other tenant's customer
        url = reverse("customer-detail", args=[other_customer.id])
        data = {"name": "Hacked Name"}
        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Verify data wasn't changed
        other_customer.refresh_from_db()
        assert other_customer.name == "Other Customer"

    def test_cannot_delete_other_tenant_data(
        self, api_client, admin_user, tenant, another_tenant
    ):
        """Test that admin cannot delete another tenant's data."""
        # Create customer in another tenant
        other_customer = Customer.objects.create(
            tenant=another_tenant, name="Other Customer", phone="+996700111111"
        )

        # Authenticate as admin of first tenant
        api_client.force_authenticate(user=admin_user)
        api_client.tenant = tenant

        # Try to delete other tenant's customer
        url = reverse("customer-detail", args=[other_customer.id])
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Customer.objects.filter(id=other_customer.id).exists()


@pytest.mark.tenant_isolation
class TestCrossTenantAttacks:
    """Test protection against cross-tenant attacks."""

    def test_cannot_create_appointment_with_other_tenant_staff(
        self, authenticated_client, tenant, another_tenant, service, location
    ):
        """Test that we cannot book with staff from another tenant."""
        # Create staff in another tenant
        other_staff = Staff.objects.create(
            tenant=another_tenant, name="Other Staff", commission_percent=50
        )

        # Create customer in our tenant
        customer = Customer.objects.create(
            tenant=tenant, name="My Customer", phone="+996700111111"
        )

        # Try to create appointment with other tenant's staff
        url = reverse("appointment-list")
        data = {
            "customer": str(customer.id),
            "staff": str(other_staff.id),  # Cross-tenant!
            "services": [str(service.id)],
            "start_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "location": str(location.id),
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
