"""ICS calendar export for appointments"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional


def generate_ics(appointment) -> str:
    """
    Generate ICS calendar file content for an appointment

    Args:
        appointment: Appointment instance

    Returns:
        ICS file content as string
    """
    # Format datetimes for ICS (UTC, format: YYYYMMDDTHHmmssZ)
    start_utc = appointment.start_at.astimezone(datetime.timezone.utc)
    end_utc = appointment.end_at.astimezone(datetime.timezone.utc)

    dtstart = start_utc.strftime("%Y%m%dT%H%M%SZ")
    dtend = end_utc.strftime("%Y%m%dT%H%M%SZ")
    dtstamp = datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # Generate unique ID
    uid = f"{appointment.id}@beautyhub"

    # Build service list
    service_names = ", ".join([svc.service.name for svc in appointment.services.all()])

    # Build description
    description = f"Услуги: {service_names}"
    if appointment.notes:
        description += f"\\n\\nЗаметки: {appointment.notes}"

    # Build location string
    location_str = ""
    if appointment.location:
        location_str = f"{appointment.location.name}"
        if appointment.location.address:
            location_str += f", {appointment.location.address}"

    # Contact info
    organizer = f"ORGANIZER;CN={appointment.staff.name}"
    if appointment.staff.email:
        organizer += f":mailto:{appointment.staff.email}"

    attendee = f"ATTENDEE;CN={appointment.customer.name};RSVP=TRUE"
    if appointment.customer.email:
        attendee += f":mailto:{appointment.customer.email}"

    # Build ICS content
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//BeautyHub//Booking//EN
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:Запись к мастеру {appointment.staff.name}
DESCRIPTION:{description}
LOCATION:{location_str}
{organizer}
{attendee}
STATUS:CONFIRMED
SEQUENCE:0
BEGIN:VALARM
TRIGGER:-PT24H
ACTION:DISPLAY
DESCRIPTION:Reminder: Appointment tomorrow
END:VALARM
BEGIN:VALARM
TRIGGER:-PT2H
ACTION:DISPLAY
DESCRIPTION:Reminder: Appointment in 2 hours
END:VALARM
END:VEVENT
END:VCALENDAR"""

    return ics_content


def generate_ics_filename(appointment) -> str:
    """
    Generate filename for ICS file

    Args:
        appointment: Appointment instance

    Returns:
        Filename string
    """
    # Format: appointment_{date}_{customer}.ics
    date_str = appointment.start_at.strftime("%Y%m%d")
    customer_slug = appointment.customer.name.lower().replace(" ", "_")[:20]

    return f"appointment_{date_str}_{customer_slug}.ics"


def generate_ics_url(appointment, domain: str) -> str:
    """
    Generate webcal URL for appointment

    Args:
        appointment: Appointment instance
        domain: Base domain (e.g., tenant.saas.akylman.online)

    Returns:
        webcal:// URL
    """
    # This would typically point to an ICS feed endpoint
    # For now, return a placeholder
    return f"webcal://{domain}/api/booking/appointments/{appointment.id}/calendar.ics"


def create_reminder_ics(appointment, hours_before: int = 24) -> str:
    """
    Create ICS reminder for appointment

    Args:
        appointment: Appointment instance
        hours_before: Hours before appointment to remind

    Returns:
        ICS content with reminder
    """
    reminder_time = appointment.start_at - timedelta(hours=hours_before)

    # Similar to generate_ics but focused on reminder
    start_utc = reminder_time.astimezone(datetime.timezone.utc)
    dtstamp = datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    service_names = ", ".join([svc.service.name for svc in appointment.services.all()])

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//BeautyHub//Reminder//EN
METHOD:REQUEST
BEGIN:VEVENT
UID:{appointment.id}-reminder-{hours_before}h@beautyhub
DTSTAMP:{dtstamp}
DTSTART:{start_utc.strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:Напоминание: запись к {appointment.staff.name}
DESCRIPTION:Через {hours_before} часов у вас запись\\nУслуги: {service_names}\\nМастер: {appointment.staff.name}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""

    return ics_content
