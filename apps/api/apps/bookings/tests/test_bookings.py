"""
Tests for booking functionality.
"""
from datetime import datetime, timedelta

import pytest
from apps.bookings.models import Appointment
from apps.customers.models import Customer
from django.urls import reverse
from django.utils import timezone
from rest_framework import status


@pytest.mark.booking
class TestAppointmentCreation:
    """Test appointment creation."""

    def test_create_appointment_success(
        self, authenticated_client, tenant, service, staff, location
    ):
        """Test successful appointment creation."""
        # Create customer
        customer = Customer.objects.create(
            tenant=tenant,
            name="Test Customer",
            phone="+996700111111",
            email="customer@example.com",
        )

        url = reverse("appointment-list")
        start_time = timezone.now() + timedelta(days=1)

        data = {
            "customer": str(customer.id),
            "staff": str(staff.id),
            "services": [str(service.id)],
            "start_at": start_time.isoformat(),
            "location": str(location.id),
            "notes": "Test booking",
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Appointment.objects.filter(customer=customer).exists()

    def test_create_appointment_in_past(
        self, authenticated_client, tenant, service, staff, location
    ):
        """Test that appointments cannot be created in the past."""
        customer = Customer.objects.create(
            tenant=tenant, name="Test Customer", phone="+996700111111"
        )

        url = reverse("appointment-list")
        start_time = timezone.now() - timedelta(days=1)  # In the past

        data = {
            "customer": str(customer.id),
            "staff": str(staff.id),
            "services": [str(service.id)],
            "start_at": start_time.isoformat(),
            "location": str(location.id),
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.booking
@pytest.mark.slow
class TestDoubleBookingPrevention:
    """Test that double bookings are prevented."""

    def test_double_booking_same_staff(
        self, authenticated_client, tenant, service, staff, location
    ):
        """Test that same staff cannot have overlapping appointments."""
        customer1 = Customer.objects.create(
            tenant=tenant, name="Customer 1", phone="+996700111111"
        )
        customer2 = Customer.objects.create(
            tenant=tenant, name="Customer 2", phone="+996700222222"
        )

        start_time = timezone.now() + timedelta(days=1)

        # Create first appointment
        Appointment.objects.create(
            tenant=tenant,
            customer=customer1,
            staff=staff,
            start_at=start_time,
            end_at=start_time + timedelta(hours=1),
            status="CONFIRMED",
        )

        # Try to create overlapping appointment
        url = reverse("appointment-list")
        data = {
            "customer": str(customer2.id),
            "staff": str(staff.id),
            "services": [str(service.id)],
            "start_at": (start_time + timedelta(minutes=30)).isoformat(),  # Overlaps
            "location": str(location.id),
        }

        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already booked" in str(response.data).lower()


@pytest.mark.booking
class TestAppointmentStatusTransitions:
    """Test appointment status transitions."""

    def test_confirm_appointment(
        self, authenticated_client, tenant, service, staff, location
    ):
        """Test confirming an appointment."""
        customer = Customer.objects.create(
            tenant=tenant, name="Test Customer", phone="+996700111111"
        )

        appointment = Appointment.objects.create(
            tenant=tenant,
            customer=customer,
            staff=staff,
            start_at=timezone.now() + timedelta(days=1),
            end_at=timezone.now() + timedelta(days=1, hours=1),
            status="PENDING",
        )

        url = reverse("appointment-confirm", args=[appointment.id])
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        appointment.refresh_from_db()
        assert appointment.status == "CONFIRMED"

    def test_cancel_appointment(
        self, authenticated_client, tenant, service, staff, location
    ):
        """Test cancelling an appointment."""
        customer = Customer.objects.create(
            tenant=tenant, name="Test Customer", phone="+996700111111"
        )

        appointment = Appointment.objects.create(
            tenant=tenant,
            customer=customer,
            staff=staff,
            start_at=timezone.now() + timedelta(days=1),
            end_at=timezone.now() + timedelta(days=1, hours=1),
            status="CONFIRMED",
        )

        url = reverse("appointment-cancel", args=[appointment.id])
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        appointment.refresh_from_db()
        assert appointment.status == "CANCELLED"


@pytest.mark.booking
class TestAvailableSlots:
    """Test available slots calculation."""

    def test_available_slots(
        self, authenticated_client, tenant, service, staff, location
    ):
        """Test getting available slots."""
        url = reverse("available_slots")
        date = (timezone.now() + timedelta(days=1)).date()

        params = {
            "service": str(service.id),
            "staff": str(staff.id),
            "date": date.isoformat(),
        }

        response = authenticated_client.get(url, params)

        assert response.status_code == status.HTTP_200_OK
        assert "slots" in response.data
        assert len(response.data["slots"]) > 0
