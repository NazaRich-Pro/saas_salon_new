"""Business logic for booking operations"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Appointment, AppointmentService, Customer, Location, Service, Staff
from .slot_engine import SlotGenerator


class AppointmentCreationError(Exception):
    """Exception raised when appointment creation fails"""

    pass


class AppointmentService:
    """Service for managing appointments"""

    def __init__(self, tenant):
        self.tenant = tenant
        self.slot_generator = SlotGenerator(tenant)

    @transaction.atomic
    def create_appointment(
        self,
        customer_data: Dict,
        staff_id: str,
        service_ids: List[str],
        start_at: datetime,
        location_id: Optional[str] = None,
        notes: str = "",
        source: str = "WIDGET",
    ) -> Appointment:
        """
        Create a new appointment with double-booking prevention

        Args:
            customer_data: Dict with customer info (name, phone, email)
            staff_id: Staff member UUID
            service_ids: List of service UUIDs
            start_at: Appointment start datetime
            location_id: Optional location UUID
            notes: Customer notes
            source: Booking source (WIDGET, ADMIN, etc.)

        Returns:
            Created Appointment instance

        Raises:
            AppointmentCreationError: If slot is not available or validation fails
        """
        # Validate staff
        try:
            staff = Staff.objects.get(id=staff_id, tenant=self.tenant, is_active=True)
        except Staff.DoesNotExist:
            raise AppointmentCreationError("Staff member not found")

        # Validate services
        services = Service.objects.filter(
            id__in=service_ids, tenant=self.tenant, is_active=True
        )

        if len(services) != len(service_ids):
            raise AppointmentCreationError("One or more services not found")

        # Calculate total duration and price
        total_duration = 0
        total_price = Decimal("0.00")

        service_details = []
        for idx, service in enumerate(services):
            # Check if staff can provide this service
            staff_service = service.staff_services.filter(staff=staff).first()

            if not staff_service:
                raise AppointmentCreationError(
                    f"Staff member cannot provide service: {service.name}"
                )

            # Get duration (use override if available)
            duration = staff_service.duration_override_min or service.duration_min

            # Get price (use override if available)
            price = staff_service.price_override_kgs or service.price_kgs

            # Add buffers (only for first and last service)
            if idx == 0:
                duration += service.buffer_before_min
            if idx == len(services) - 1:
                duration += service.buffer_after_min

            total_duration += duration
            total_price += price

            service_details.append(
                {
                    "service": service,
                    "order": idx + 1,
                    "duration": duration,
                    "price": price,
                }
            )

        # Calculate end time
        end_at = start_at + timedelta(minutes=total_duration)

        # Check if slot is available with advisory lock
        is_available = self.slot_generator.check_slot_available_with_lock(
            staff_id=staff_id, start_at=start_at, end_at=end_at
        )

        if not is_available:
            raise AppointmentCreationError(
                "Selected time slot is not available (double-booking prevented)"
            )

        # Get or create customer
        customer, created = Customer.objects.get_or_create(
            tenant=self.tenant,
            phone=customer_data["phone"],
            defaults={
                "name": customer_data["name"],
                "email": customer_data.get("email", ""),
                "is_active": True,
            },
        )

        # If customer exists, update name/email if provided
        if not created and customer_data.get("name"):
            customer.name = customer_data["name"]
            if customer_data.get("email"):
                customer.email = customer_data["email"]
            customer.save()

        # Get location
        location = None
        if location_id:
            try:
                location = Location.objects.get(id=location_id, tenant=self.tenant)
            except Location.DoesNotExist:
                pass

        # Create appointment
        appointment = Appointment.objects.create(
            tenant=self.tenant,
            customer=customer,
            staff=staff,
            location=location,
            start_at=start_at,
            end_at=end_at,
            status="PENDING",
            source=source,
            notes=notes,
            total_price_kgs=total_price,
            prepaid_kgs=Decimal("0.00"),
            discount_kgs=Decimal("0.00"),
        )

        # Create appointment services
        for detail in service_details:
            AppointmentService.objects.create(
                appointment=appointment,
                service=detail["service"],
                order=detail["order"],
                duration_min=detail["duration"],
                price_kgs=detail["price"],
            )

        return appointment

    def confirm_appointment(self, appointment_id: str) -> Appointment:
        """
        Confirm a pending appointment
        """
        try:
            appointment = Appointment.objects.get(id=appointment_id, tenant=self.tenant)
        except Appointment.DoesNotExist:
            raise AppointmentCreationError("Appointment not found")

        if appointment.status != "PENDING":
            raise AppointmentCreationError(
                f"Cannot confirm appointment with status: {appointment.status}"
            )

        appointment.status = "CONFIRMED"
        appointment.save(update_fields=["status", "updated_at"])

        return appointment

    def cancel_appointment(self, appointment_id: str, reason: str = "") -> Appointment:
        """
        Cancel an appointment
        """
        try:
            appointment = Appointment.objects.get(id=appointment_id, tenant=self.tenant)
        except Appointment.DoesNotExist:
            raise AppointmentCreationError("Appointment not found")

        if appointment.status in ["COMPLETED", "CANCELLED"]:
            raise AppointmentCreationError(
                f"Cannot cancel appointment with status: {appointment.status}"
            )

        appointment.status = "CANCELLED"
        if reason:
            appointment.internal_notes = (
                f"Cancelled: {reason}\n{appointment.internal_notes}"
            )
        appointment.save(update_fields=["status", "internal_notes", "updated_at"])

        return appointment

    @transaction.atomic
    def reschedule_appointment(
        self,
        appointment_id: str,
        new_start_at: datetime,
        new_staff_id: Optional[str] = None,
    ) -> Appointment:
        """
        Reschedule an appointment to a new time/staff

        Args:
            appointment_id: Appointment UUID
            new_start_at: New start datetime
            new_staff_id: Optional new staff UUID

        Returns:
            Updated Appointment instance
        """
        try:
            appointment = Appointment.objects.select_for_update().get(
                id=appointment_id, tenant=self.tenant
            )
        except Appointment.DoesNotExist:
            raise AppointmentCreationError("Appointment not found")

        if appointment.status in ["COMPLETED", "CANCELLED"]:
            raise AppointmentCreationError(
                f"Cannot reschedule appointment with status: {appointment.status}"
            )

        # Determine staff (new or keep existing)
        if new_staff_id:
            try:
                staff = Staff.objects.get(
                    id=new_staff_id, tenant=self.tenant, is_active=True
                )
            except Staff.DoesNotExist:
                raise AppointmentCreationError("Staff member not found")
        else:
            staff = appointment.staff

        # Calculate duration from existing services
        total_duration = sum(
            service.duration_min for service in appointment.services.all()
        )

        new_end_at = new_start_at + timedelta(minutes=total_duration)

        # Check availability with lock (exclude current appointment)
        is_available = self.slot_generator.check_slot_available_with_lock(
            staff_id=str(staff.id),
            start_at=new_start_at,
            end_at=new_end_at,
            exclude_appointment_id=str(appointment.id),
        )

        if not is_available:
            raise AppointmentCreationError("New time slot is not available")

        # Update appointment
        appointment.staff = staff
        appointment.start_at = new_start_at
        appointment.end_at = new_end_at
        appointment.status = "RESCHEDULED"
        appointment.save(
            update_fields=["staff", "start_at", "end_at", "status", "updated_at"]
        )

        return appointment

    def complete_appointment(self, appointment_id: str) -> Appointment:
        """
        Mark appointment as completed
        Updates customer stats (total_visits, total_spent)
        """
        try:
            appointment = Appointment.objects.select_related("customer").get(
                id=appointment_id, tenant=self.tenant
            )
        except Appointment.DoesNotExist:
            raise AppointmentCreationError("Appointment not found")

        if appointment.status != "CONFIRMED":
            raise AppointmentCreationError(
                f"Can only complete confirmed appointments (current: {appointment.status})"
            )

        with transaction.atomic():
            # Update appointment
            appointment.status = "COMPLETED"
            appointment.save(update_fields=["status", "updated_at"])

            # Update customer stats
            customer = appointment.customer
            customer.total_visits += 1
            customer.total_spent_kgs += appointment.total_price_kgs

            # Award loyalty points (1 point per 100 KGS)
            from apps.payments.models import LoyaltyRule

            try:
                loyalty_rule = LoyaltyRule.objects.get(
                    tenant=self.tenant, is_active=True
                )
                points_earned = (
                    int(appointment.total_price_kgs / 100)
                    * loyalty_rule.earn_per_100_kgs
                )
                customer.loyalty_points += points_earned
            except LoyaltyRule.DoesNotExist:
                pass

            customer.save(
                update_fields=["total_visits", "total_spent_kgs", "loyalty_points"]
            )

        return appointment

    def mark_no_show(self, appointment_id: str) -> Appointment:
        """
        Mark appointment as no-show
        """
        try:
            appointment = Appointment.objects.get(id=appointment_id, tenant=self.tenant)
        except Appointment.DoesNotExist:
            raise AppointmentCreationError("Appointment not found")

        if appointment.status not in ["PENDING", "CONFIRMED"]:
            raise AppointmentCreationError(
                f"Cannot mark as no-show (current status: {appointment.status})"
            )

        appointment.status = "NO_SHOW"
        appointment.save(update_fields=["status", "updated_at"])

        return appointment
