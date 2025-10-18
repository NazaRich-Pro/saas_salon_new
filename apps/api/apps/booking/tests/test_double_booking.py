"""Tests for double-booking prevention"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from apps.booking.models import (
    Appointment,
    Customer,
    Schedule,
    Service,
    ServiceCategory,
    Staff,
    StaffService,
)
from apps.booking.services import AppointmentCreationError, AppointmentService
from apps.booking.slot_engine import SlotGenerator
from apps.tenants.models import Tenant
from django.utils import timezone


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(
        slug="test-salon", name="Test Salon", type="SALON", status="ACTIVE"
    )


@pytest.fixture
def service_category(db, tenant):
    return ServiceCategory.objects.create(
        tenant=tenant, name="Test Category", is_active=True
    )


@pytest.fixture
def service(db, tenant, service_category):
    return Service.objects.create(
        tenant=tenant,
        category=service_category,
        name="Test Service",
        duration_min=60,
        price_kgs=Decimal("100.00"),
        buffer_before_min=5,
        buffer_after_min=5,
        is_active=True,
    )


@pytest.fixture
def staff(db, tenant):
    return Staff.objects.create(tenant=tenant, name="Test Master", is_active=True)


@pytest.fixture
def staff_service(db, staff, service):
    return StaffService.objects.create(staff=staff, service=service)


@pytest.fixture
def schedule(db, tenant, staff):
    return Schedule.objects.create(
        tenant=tenant,
        staff=staff,
        rules={
            "monday": {"enabled": True, "slots": [{"start": "09:00", "end": "18:00"}]},
            "tuesday": {"enabled": True, "slots": [{"start": "09:00", "end": "18:00"}]},
            "wednesday": {
                "enabled": True,
                "slots": [{"start": "09:00", "end": "18:00"}],
            },
            "thursday": {
                "enabled": True,
                "slots": [{"start": "09:00", "end": "18:00"}],
            },
            "friday": {"enabled": True, "slots": [{"start": "09:00", "end": "18:00"}]},
            "saturday": {
                "enabled": True,
                "slots": [{"start": "10:00", "end": "16:00"}],
            },
            "sunday": {"enabled": False, "slots": []},
        },
        is_active=True,
    )


@pytest.mark.django_db
class TestDoubleBookingPrevention:
    """Test double-booking prevention with advisory locks"""

    def test_prevent_overlapping_appointments(
        self, tenant, staff, service, staff_service, schedule
    ):
        """Test that overlapping appointments are prevented"""
        appointment_service = AppointmentService(tenant)

        # Create first appointment
        start_time = timezone.now().replace(
            hour=10, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

        customer_data = {
            "name": "Customer 1",
            "phone": "+996700111111",
            "email": "customer1@example.com",
        }

        appointment1 = appointment_service.create_appointment(
            customer_data=customer_data,
            staff_id=str(staff.id),
            service_ids=[str(service.id)],
            start_at=start_time,
            notes="First appointment",
        )

        assert appointment1 is not None
        assert appointment1.status == "PENDING"

        # Try to create overlapping appointment (should fail)
        customer_data2 = {"name": "Customer 2", "phone": "+996700222222"}

        # Same time, same staff
        with pytest.raises(AppointmentCreationError) as exc:
            appointment_service.create_appointment(
                customer_data=customer_data2,
                staff_id=str(staff.id),
                service_ids=[str(service.id)],
                start_at=start_time,
                notes="Should fail",
            )

        assert "not available" in str(exc.value).lower()

    def test_allow_non_overlapping_appointments(
        self, tenant, staff, service, staff_service, schedule
    ):
        """Test that non-overlapping appointments are allowed"""
        appointment_service = AppointmentService(tenant)

        # Create first appointment at 10:00
        start_time1 = timezone.now().replace(
            hour=10, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

        customer_data1 = {"name": "Customer 1", "phone": "+996700111111"}

        appointment1 = appointment_service.create_appointment(
            customer_data=customer_data1,
            staff_id=str(staff.id),
            service_ids=[str(service.id)],
            start_at=start_time1,
        )

        # Service is 60 min + 5 min buffer before + 5 min after = 70 min total
        # First appointment: 10:00 - 11:10

        # Create second appointment at 11:15 (after first ends)
        start_time2 = start_time1 + timedelta(minutes=75)

        customer_data2 = {"name": "Customer 2", "phone": "+996700222222"}

        appointment2 = appointment_service.create_appointment(
            customer_data=customer_data2,
            staff_id=str(staff.id),
            service_ids=[str(service.id)],
            start_at=start_time2,
        )

        assert appointment2 is not None
        assert appointment2.id != appointment1.id

    @pytest.mark.slow
    def test_concurrent_booking_prevention(
        self, tenant, staff, service, staff_service, schedule
    ):
        """Test that concurrent booking requests don't create double-booking"""
        appointment_service = AppointmentService(tenant)

        start_time = timezone.now().replace(
            hour=14, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

        def create_appointment_attempt(customer_num):
            """Attempt to create appointment"""
            customer_data = {
                "name": f"Customer {customer_num}",
                "phone": f"+99670000000{customer_num}",
            }

            try:
                return appointment_service.create_appointment(
                    customer_data=customer_data,
                    staff_id=str(staff.id),
                    service_ids=[str(service.id)],
                    start_at=start_time,
                    notes=f"Concurrent attempt {customer_num}",
                )
            except AppointmentCreationError:
                return None

        # Try to create 5 appointments concurrently for the same slot
        successful_appointments = []
        failed_attempts = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_appointment_attempt, i) for i in range(5)]

            for future in as_completed(futures):
                result = future.result()
                if result:
                    successful_appointments.append(result)
                else:
                    failed_attempts += 1

        # Only ONE appointment should succeed
        assert (
            len(successful_appointments) == 1
        ), f"Expected 1 successful booking, got {len(successful_appointments)}"
        assert failed_attempts == 4, f"Expected 4 failures, got {failed_attempts}"


@pytest.mark.django_db
class TestSlotGeneration:
    """Test slot generation engine"""

    def test_generate_slots_for_working_day(
        self, tenant, staff, service, staff_service, schedule
    ):
        """Test slot generation for a working day"""
        generator = SlotGenerator(tenant)

        # Get slots for tomorrow (assuming it's a weekday)
        tomorrow = timezone.now().date() + timedelta(days=1)

        # Skip if tomorrow is Sunday (not working)
        if tomorrow.strftime("%A").lower() == "sunday":
            tomorrow = tomorrow + timedelta(days=1)

        slots = generator.get_available_slots(
            service_id=str(service.id), date=tomorrow, staff_id=str(staff.id)
        )

        # Should have multiple slots (9:00-18:00 in 15-min increments)
        assert len(slots) > 0

        # First slot should be at 09:00
        assert slots[0]["time"] == "09:00"

        # All slots should have staff info
        for slot in slots:
            assert slot["staff_id"] == str(staff.id)
            assert slot["staff_name"] == staff.name
            assert slot["available"] is True

    def test_no_slots_for_non_working_day(
        self, tenant, staff, service, staff_service, schedule
    ):
        """Test no slots generated for non-working days (Sunday)"""
        generator = SlotGenerator(tenant)

        # Find next Sunday
        today = timezone.now().date()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        next_sunday = today + timedelta(days=days_until_sunday)

        slots = generator.get_available_slots(
            service_id=str(service.id), date=next_sunday, staff_id=str(staff.id)
        )

        # Sunday is disabled, should have no slots
        assert len(slots) == 0

    def test_slots_exclude_existing_appointments(
        self, tenant, staff, service, staff_service, schedule
    ):
        """Test that existing appointments are excluded from available slots"""
        # Create an appointment at 10:00
        tomorrow = timezone.now().replace(
            hour=10, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

        customer = Customer.objects.create(
            tenant=tenant, name="Existing Customer", phone="+996700999999"
        )

        Appointment.objects.create(
            tenant=tenant,
            customer=customer,
            staff=staff,
            start_at=tomorrow,
            end_at=tomorrow + timedelta(minutes=70),  # 60 + 10 buffers
            status="CONFIRMED",
            total_price_kgs=Decimal("100.00"),
        )

        # Generate slots
        generator = SlotGenerator(tenant)
        slots = generator.get_available_slots(
            service_id=str(service.id), date=tomorrow.date(), staff_id=str(staff.id)
        )

        # 10:00 slot should not be available
        slot_times = [slot["time"] for slot in slots]
        assert "10:00" not in slot_times


@pytest.mark.django_db
class TestAppointmentLifecycle:
    """Test appointment status transitions"""

    def test_create_pending_appointment(
        self, tenant, staff, service, staff_service, schedule
    ):
        """Test creating appointment in PENDING status"""
        appointment_service = AppointmentService(tenant)

        start_time = timezone.now().replace(hour=11, minute=0) + timedelta(days=1)

        customer_data = {
            "name": "Test Customer",
            "phone": "+996700111111",
            "email": "test@example.com",
        }

        appointment = appointment_service.create_appointment(
            customer_data=customer_data,
            staff_id=str(staff.id),
            service_ids=[str(service.id)],
            start_at=start_time,
        )

        assert appointment.status == "PENDING"
        assert appointment.customer.name == "Test Customer"
        assert appointment.staff == staff
        assert appointment.total_price_kgs == Decimal("100.00")

    def test_confirm_appointment(self, tenant, staff, service, staff_service, schedule):
        """Test confirming a pending appointment"""
        appointment_service = AppointmentService(tenant)

        # Create appointment
        start_time = timezone.now().replace(hour=12, minute=0) + timedelta(days=1)

        appointment = appointment_service.create_appointment(
            customer_data={"name": "Customer", "phone": "+996700111111"},
            staff_id=str(staff.id),
            service_ids=[str(service.id)],
            start_at=start_time,
        )

        assert appointment.status == "PENDING"

        # Confirm it
        confirmed = appointment_service.confirm_appointment(str(appointment.id))

        assert confirmed.status == "CONFIRMED"
        assert confirmed.id == appointment.id

    def test_complete_appointment_updates_customer_stats(
        self, tenant, staff, service, staff_service, schedule
    ):
        """Test completing appointment updates customer statistics"""
        appointment_service = AppointmentService(tenant)

        # Create and confirm appointment
        start_time = timezone.now().replace(hour=13, minute=0) + timedelta(days=1)

        customer_data = {"name": "Stat Customer", "phone": "+996700333333"}

        appointment = appointment_service.create_appointment(
            customer_data=customer_data,
            staff_id=str(staff.id),
            service_ids=[str(service.id)],
            start_at=start_time,
        )

        # Confirm first
        appointment_service.confirm_appointment(str(appointment.id))

        # Get customer initial stats
        customer = Customer.objects.get(tenant=tenant, phone="+996700333333")
        initial_visits = customer.total_visits
        initial_spent = customer.total_spent_kgs

        # Complete appointment
        completed = appointment_service.complete_appointment(str(appointment.id))

        assert completed.status == "COMPLETED"

        # Check customer stats updated
        customer.refresh_from_db()
        assert customer.total_visits == initial_visits + 1
        assert customer.total_spent_kgs == initial_spent + Decimal("100.00")

    def test_cancel_appointment(self, tenant, staff, service, staff_service, schedule):
        """Test cancelling an appointment"""
        appointment_service = AppointmentService(tenant)

        # Create appointment
        start_time = timezone.now().replace(hour=15, minute=0) + timedelta(days=1)

        appointment = appointment_service.create_appointment(
            customer_data={"name": "Cancel Test", "phone": "+996700444444"},
            staff_id=str(staff.id),
            service_ids=[str(service.id)],
            start_at=start_time,
        )

        # Cancel it
        cancelled = appointment_service.cancel_appointment(
            str(appointment.id), reason="Customer requested"
        )

        assert cancelled.status == "CANCELLED"
        assert "Customer requested" in cancelled.internal_notes

    def test_reschedule_appointment(
        self, tenant, staff, service, staff_service, schedule
    ):
        """Test rescheduling an appointment"""
        appointment_service = AppointmentService(tenant)

        # Create appointment at 10:00
        start_time1 = timezone.now().replace(hour=10, minute=0) + timedelta(days=1)

        appointment = appointment_service.create_appointment(
            customer_data={"name": "Reschedule Test", "phone": "+996700555555"},
            staff_id=str(staff.id),
            service_ids=[str(service.id)],
            start_at=start_time1,
        )

        # Reschedule to 14:00
        start_time2 = timezone.now().replace(hour=14, minute=0) + timedelta(days=1)

        rescheduled = appointment_service.reschedule_appointment(
            str(appointment.id), new_start_at=start_time2
        )

        assert rescheduled.status == "RESCHEDULED"
        assert rescheduled.start_at == start_time2

    def test_mark_no_show(self, tenant, staff, service, staff_service, schedule):
        """Test marking appointment as no-show"""
        appointment_service = AppointmentService(tenant)

        # Create and confirm appointment
        start_time = timezone.now().replace(hour=16, minute=0) + timedelta(days=1)

        appointment = appointment_service.create_appointment(
            customer_data={"name": "NoShow Test", "phone": "+996700666666"},
            staff_id=str(staff.id),
            service_ids=[str(service.id)],
            start_at=start_time,
        )

        appointment_service.confirm_appointment(str(appointment.id))

        # Mark as no-show
        no_show = appointment_service.mark_no_show(str(appointment.id))

        assert no_show.status == "NO_SHOW"


@pytest.mark.django_db
class TestMultipleServices:
    """Test appointments with multiple services"""

    def test_create_appointment_with_multiple_services(
        self, tenant, staff, service_category, staff_service, schedule
    ):
        """Test creating appointment with combo services"""
        # Create second service
        service2 = Service.objects.create(
            tenant=tenant,
            category=service_category,
            name="Second Service",
            duration_min=30,
            price_kgs=Decimal("50.00"),
            is_active=True,
        )

        StaffService.objects.create(staff=staff, service=service2)

        # Get first service from fixture
        service1 = staff.staff_services.first().service

        appointment_service = AppointmentService(tenant)

        start_time = timezone.now().replace(hour=11, minute=0) + timedelta(days=1)

        appointment = appointment_service.create_appointment(
            customer_data={"name": "Combo Customer", "phone": "+996700777777"},
            staff_id=str(staff.id),
            service_ids=[str(service1.id), str(service2.id)],
            start_at=start_time,
        )

        # Total duration should be sum of both services + buffers
        # Service 1: 60 min, Service 2: 30 min
        # Buffer before (first): 5 min, Buffer after (last): 5 min
        # Total: 5 + 60 + 30 + 5 = 100 min

        duration_min = (appointment.end_at - appointment.start_at).total_seconds() / 60
        assert duration_min == 100

        # Total price should be sum of both
        assert appointment.total_price_kgs == Decimal("150.00")

        # Should have 2 service records
        assert appointment.services.count() == 2


@pytest.mark.django_db
class TestScheduleRules:
    """Test schedule rules and exceptions"""

    def test_respect_working_hours(
        self, tenant, staff, service, staff_service, schedule
    ):
        """Test slots are only generated during working hours"""
        generator = SlotGenerator(tenant)

        tomorrow = timezone.now().date() + timedelta(days=1)

        # Skip Sunday
        if tomorrow.strftime("%A").lower() == "sunday":
            tomorrow = tomorrow + timedelta(days=1)

        slots = generator.get_available_slots(
            service_id=str(service.id), date=tomorrow, staff_id=str(staff.id)
        )

        # All slots should be within working hours (09:00-18:00 for weekdays)
        for slot in slots:
            hour = int(slot["time"].split(":")[0])
            assert 9 <= hour < 18

    def test_schedule_exception_day_off(
        self, tenant, staff, service, staff_service, schedule
    ):
        """Test schedule exception for day off"""
        # Add exception for tomorrow
        tomorrow = timezone.now().date() + timedelta(days=1)

        schedule.exceptions = [
            {"date": tomorrow.strftime("%Y-%m-%d"), "type": "off", "reason": "Holiday"}
        ]
        schedule.save()

        generator = SlotGenerator(tenant)

        slots = generator.get_available_slots(
            service_id=str(service.id), date=tomorrow, staff_id=str(staff.id)
        )

        # Should have no slots (day off)
        assert len(slots) == 0

    def test_schedule_exception_custom_hours(
        self, tenant, staff, service, staff_service, schedule
    ):
        """Test schedule exception with custom hours"""
        # Add exception for tomorrow with custom hours
        tomorrow = timezone.now().date() + timedelta(days=1)

        schedule.exceptions = [
            {
                "date": tomorrow.strftime("%Y-%m-%d"),
                "type": "custom",
                "slots": [{"start": "12:00", "end": "15:00"}],
            }
        ]
        schedule.save()

        generator = SlotGenerator(tenant)

        slots = generator.get_available_slots(
            service_id=str(service.id), date=tomorrow, staff_id=str(staff.id)
        )

        # Should only have slots between 12:00-15:00
        for slot in slots:
            hour = int(slot["time"].split(":")[0])
            assert 12 <= hour < 15
