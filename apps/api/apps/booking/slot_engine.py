"""
Slot generation engine for booking system
Computes available time slots based on staff schedules, existing appointments, and buffers
"""
from datetime import datetime
from datetime import time as datetime_time
from datetime import timedelta
from typing import Dict, List, Optional

import pytz
from django.db.models import Q
from django.utils import timezone

from .models import Appointment, Schedule, Service, Staff, StaffService


class SlotGenerator:
    """Generate available booking slots"""

    def __init__(self, tenant):
        self.tenant = tenant

    def get_available_slots(
        self,
        service_id: str,
        date: datetime.date,
        staff_id: Optional[str] = None,
        location_id: Optional[str] = None,
        duration_override: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get available time slots for a service on a specific date

        Args:
            service_id: UUID of the service
            date: Date to check availability
            staff_id: Optional specific staff member
            location_id: Optional specific location
            duration_override: Optional duration override in minutes

        Returns:
            List of dicts with slot information:
            [
                {
                    'time': '10:00',
                    'datetime': datetime object,
                    'staff_id': 'uuid',
                    'staff_name': 'Name',
                    'available': True
                },
                ...
            ]
        """
        try:
            service = Service.objects.get(
                id=service_id, tenant=self.tenant, is_active=True
            )
        except Service.DoesNotExist:
            return []

        # Get staff who can provide this service
        if staff_id:
            staff_list = Staff.objects.filter(
                id=staff_id, tenant=self.tenant, is_active=True
            )
        else:
            # Get all staff who can provide this service
            staff_list = Staff.objects.filter(
                tenant=self.tenant, is_active=True, staff_services__service=service
            ).distinct()

        all_slots = []

        for staff in staff_list:
            slots = self._get_staff_slots(staff, service, date, duration_override)
            all_slots.extend(slots)

        # Sort by datetime
        all_slots.sort(key=lambda x: x["datetime"])

        return all_slots

    def _get_staff_slots(
        self,
        staff: Staff,
        service: Service,
        date: datetime.date,
        duration_override: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get available slots for a specific staff member
        """
        # Get staff schedule
        try:
            schedule = Schedule.objects.get(
                tenant=self.tenant, staff=staff, is_active=True
            )
        except Schedule.DoesNotExist:
            return []

        # Get working hours for this day
        day_name = date.strftime("%A").lower()
        day_rules = schedule.rules.get(day_name, {})

        if not day_rules.get("enabled", False):
            # Staff doesn't work on this day
            return []

        # Check for exceptions on this date
        date_str = date.strftime("%Y-%m-%d")
        exception = next(
            (exc for exc in schedule.exceptions if exc.get("date") == date_str), None
        )

        if exception:
            if exception.get("type") == "off":
                # Staff is off on this date
                return []
            elif exception.get("type") == "custom":
                # Use custom slots for this date
                day_rules = {"enabled": True, "slots": exception.get("slots", [])}

        # Get working slots for the day
        working_slots = day_rules.get("slots", [])

        if not working_slots:
            return []

        # Get service duration (with possible override)
        staff_service = StaffService.objects.filter(
            staff=staff, service=service
        ).first()

        if duration_override:
            duration_min = duration_override
        elif staff_service and staff_service.duration_override_min:
            duration_min = staff_service.duration_override_min
        else:
            duration_min = service.duration_min

        # Calculate total duration with buffers
        total_duration = (
            service.buffer_before_min + duration_min + service.buffer_after_min
        )

        # Get existing appointments for this staff on this date
        start_of_day = timezone.make_aware(datetime.combine(date, datetime_time.min))
        end_of_day = timezone.make_aware(datetime.combine(date, datetime_time.max))

        existing_appointments = Appointment.objects.filter(
            tenant=self.tenant,
            staff=staff,
            start_at__gte=start_of_day,
            end_at__lte=end_of_day,
            status__in=["PENDING", "CONFIRMED"],  # Only consider active appointments
        ).order_by("start_at")

        # Generate slots
        available_slots = []

        for slot_range in working_slots:
            start_time_str = slot_range.get("start", "09:00")
            end_time_str = slot_range.get("end", "18:00")

            # Parse times
            start_hour, start_min = map(int, start_time_str.split(":"))
            end_hour, end_min = map(int, end_time_str.split(":"))

            slot_start = timezone.make_aware(
                datetime.combine(date, datetime_time(start_hour, start_min))
            )
            slot_end = timezone.make_aware(
                datetime.combine(date, datetime_time(end_hour, end_min))
            )

            # Generate slots in 15-minute increments
            current_time = slot_start
            while current_time + timedelta(minutes=total_duration) <= slot_end:
                slot_end_time = current_time + timedelta(minutes=total_duration)

                # Check if slot is available (no overlap with existing appointments)
                is_available = self._is_slot_available(
                    current_time, slot_end_time, existing_appointments
                )

                if is_available:
                    available_slots.append(
                        {
                            "time": current_time.strftime("%H:%M"),
                            "datetime": current_time,
                            "staff_id": str(staff.id),
                            "staff_name": staff.name,
                            "duration_min": duration_min,
                            "available": True,
                        }
                    )

                # Move to next slot (15-minute increments)
                current_time += timedelta(minutes=15)

        return available_slots

    def _is_slot_available(
        self, slot_start: datetime, slot_end: datetime, existing_appointments
    ) -> bool:
        """
        Check if a time slot is available (no overlap with existing appointments)

        Args:
            slot_start: Slot start datetime
            slot_end: Slot end datetime
            existing_appointments: QuerySet of existing appointments

        Returns:
            Boolean - True if available, False if overlaps
        """
        for appointment in existing_appointments:
            # Check for overlap
            if slot_start < appointment.end_at and slot_end > appointment.start_at:
                return False

        return True

    def check_slot_available_with_lock(
        self,
        staff_id: str,
        start_at: datetime,
        end_at: datetime,
        exclude_appointment_id: Optional[str] = None,
    ) -> bool:
        """
        Check if slot is available with database-level locking
        Used during appointment creation to prevent double-booking

        Args:
            staff_id: Staff member ID
            start_at: Appointment start time
            end_at: Appointment end time
            exclude_appointment_id: Appointment ID to exclude (for rescheduling)

        Returns:
            Boolean - True if available
        """
        from django.db import transaction

        # Use select_for_update to lock rows
        with transaction.atomic():
            overlapping = Appointment.objects.select_for_update().filter(
                tenant=self.tenant,
                staff_id=staff_id,
                status__in=["PENDING", "CONFIRMED"],
                start_at__lt=end_at,
                end_at__gt=start_at,
            )

            if exclude_appointment_id:
                overlapping = overlapping.exclude(id=exclude_appointment_id)

            return not overlapping.exists()


class ScheduleValidator:
    """Validate schedule rules and exceptions"""

    @staticmethod
    def validate_schedule_rules(rules: dict) -> tuple[bool, Optional[str]]:
        """
        Validate schedule rules JSON structure

        Returns:
            (is_valid, error_message)
        """
        required_days = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]

        for day in required_days:
            if day not in rules:
                return False, f"Missing day: {day}"

            day_rule = rules[day]

            if "enabled" not in day_rule:
                return False, f"Missing 'enabled' for {day}"

            if day_rule["enabled"]:
                if "slots" not in day_rule or not isinstance(day_rule["slots"], list):
                    return False, f"Missing or invalid 'slots' for {day}"

                for slot in day_rule["slots"]:
                    if "start" not in slot or "end" not in slot:
                        return False, f"Slot missing start or end time for {day}"

                    # Validate time format
                    try:
                        datetime.strptime(slot["start"], "%H:%M")
                        datetime.strptime(slot["end"], "%H:%M")
                    except ValueError:
                        return False, f"Invalid time format in {day} slot"

        return True, None

    @staticmethod
    def validate_exceptions(exceptions: list) -> tuple[bool, Optional[str]]:
        """
        Validate schedule exceptions JSON structure

        Returns:
            (is_valid, error_message)
        """
        for exc in exceptions:
            if "date" not in exc or "type" not in exc:
                return False, "Exception missing date or type"

            # Validate date format
            try:
                datetime.strptime(exc["date"], "%Y-%m-%d")
            except ValueError:
                return False, f"Invalid date format: {exc['date']}"

            if exc["type"] not in ["off", "custom"]:
                return False, f"Invalid exception type: {exc['type']}"

            if exc["type"] == "custom":
                if "slots" not in exc:
                    return False, "Custom exception missing slots"

        return True, None


def get_next_available_slot(
    tenant,
    service_id: str,
    staff_id: Optional[str] = None,
    after_datetime: Optional[datetime] = None,
) -> Optional[Dict]:
    """
    Get the next available slot for a service

    Args:
        tenant: Tenant instance
        service_id: Service UUID
        staff_id: Optional staff UUID
        after_datetime: Optional datetime to start search from

    Returns:
        Dict with slot info or None if no slots available
    """
    generator = SlotGenerator(tenant)

    # Start from today or specified datetime
    if after_datetime:
        search_date = after_datetime.date()
    else:
        search_date = timezone.now().date()

    # Search up to 30 days ahead
    for day_offset in range(30):
        check_date = search_date + timedelta(days=day_offset)

        slots = generator.get_available_slots(
            service_id=service_id, date=check_date, staff_id=staff_id
        )

        if slots:
            # Filter out past slots if checking today
            if check_date == timezone.now().date():
                now = timezone.now()
                slots = [s for s in slots if s["datetime"] > now]

            if slots:
                return slots[0]

    return None
