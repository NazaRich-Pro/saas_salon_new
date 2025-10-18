"""Email notification service"""
import logging
from typing import Dict, List, Optional

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Context, Template

from .models import NotificationTemplate

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""

    def __init__(self, tenant=None):
        self.tenant = tenant
        self.from_email = settings.DEFAULT_FROM_EMAIL

    def render_template(self, template_body: str, variables: Dict) -> str:
        """
        Render email template with variables

        Variables supported:
        - %customer_name% → variables['customer_name']
        - %date_time% → variables['date_time']
        - %service% → variables['service']
        - %salon_name% → variables['salon_name']
        - %tenant_url% → variables['tenant_url']
        - And more...

        Args:
            template_body: Template string with %variables%
            variables: Dict with variable values

        Returns:
            Rendered string
        """
        rendered = template_body

        for key, value in variables.items():
            placeholder = f"%{key}%"
            rendered = rendered.replace(placeholder, str(value))

        return rendered

    def get_template(
        self, event: str, language: str = "ru", kind: str = "EMAIL"
    ) -> Optional[NotificationTemplate]:
        """
        Get notification template

        Args:
            event: Event type (WELCOME, REMINDER_24H, etc.)
            language: Language code (ru, kg, en)
            kind: Notification kind (EMAIL, TELEGRAM, SMS)

        Returns:
            NotificationTemplate instance or None
        """
        # Try tenant-specific template first
        if self.tenant:
            template = NotificationTemplate.objects.filter(
                tenant=self.tenant, kind=kind, event=event, lang=language.upper()
            ).first()

            if template:
                return template

        # Fall back to platform default (tenant=None)
        template = NotificationTemplate.objects.filter(
            tenant__isnull=True, kind=kind, event=event, lang=language.upper()
        ).first()

        return template

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        reply_to: Optional[List[str]] = None,
    ) -> bool:
        """
        Send email via SMTP

        Args:
            to_email: Recipient email
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            reply_to: Optional reply-to addresses

        Returns:
            Boolean - True if sent successfully
        """
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=self.from_email,
                to=[to_email],
                reply_to=reply_to or [],
            )

            if html_body:
                msg.attach_alternative(html_body, "text/html")

            msg.send(fail_silently=False)

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_templated_email(
        self, to_email: str, event: str, variables: Dict, language: str = "ru"
    ) -> bool:
        """
        Send email using stored template

        Args:
            to_email: Recipient email
            event: Event type (WELCOME, REMINDER_24H, etc.)
            variables: Template variables
            language: Language code

        Returns:
            Boolean - True if sent successfully
        """
        # Get template
        template = self.get_template(event, language, "EMAIL")

        if not template:
            logger.error(f"Email template not found: {event}/{language}")
            return False

        # Render subject and body
        subject = self.render_template(template.subject, variables)
        body = self.render_template(template.body, variables)

        # Create HTML version (simple)
        html_body = body.replace("\n", "<br>")
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            {html_body}
        </body>
        </html>
        """

        # Send email
        return self.send_email(to_email, subject, body, html_body)

    def send_welcome_email(
        self,
        owner_name: str,
        owner_email: str,
        salon_name: str,
        tenant_url: str,
        language: str = "ru",
    ) -> bool:
        """
        Send welcome email after tenant registration

        Args:
            owner_name: Owner's name
            owner_email: Owner's email
            salon_name: Salon name
            tenant_url: Tenant subdomain URL
            language: Language code

        Returns:
            Boolean - success
        """
        variables = {
            "owner_name": owner_name,
            "email": owner_email,
            "salon_name": salon_name,
            "tenant_url": tenant_url,
            "support_email": "support@saas.akylman.online",
        }

        return self.send_templated_email(
            to_email=owner_email,
            event="WELCOME",
            variables=variables,
            language=language,
        )

    def send_appointment_reminder(
        self, appointment, hours_before: int = 24, language: str = "ru"
    ) -> bool:
        """
        Send appointment reminder

        Args:
            appointment: Appointment instance
            hours_before: Hours before appointment (24 or 2)
            language: Language code

        Returns:
            Boolean - success
        """
        if not appointment.customer.email:
            logger.warning(f"Customer {appointment.customer.name} has no email")
            return False

        # Determine event type
        event = "REMINDER_24H" if hours_before == 24 else "REMINDER_2H"

        # Prepare variables
        from datetime import datetime

        # Format date time in local timezone
        appt_datetime = appointment.start_at.strftime("%d.%m.%Y в %H:%M")

        # Get services list
        services = ", ".join([aps.service.name for aps in appointment.services.all()])

        variables = {
            "customer_name": appointment.customer.name,
            "date_time": appt_datetime,
            "service": services,
            "salon_name": self.tenant.name if self.tenant else "BeautyHub",
            "staff_name": appointment.staff.name,
            "tenant_url": f"https://{self.tenant.slug}.saas.akylman.online"
            if self.tenant
            else "",
            "location": appointment.location.address if appointment.location else "",
        }

        return self.send_templated_email(
            to_email=appointment.customer.email,
            event=event,
            variables=variables,
            language=language,
        )

    def send_followup_email(self, appointment, language: str = "ru") -> bool:
        """
        Send follow-up email after appointment

        Args:
            appointment: Completed appointment
            language: Language code

        Returns:
            Boolean - success
        """
        if not appointment.customer.email:
            return False

        variables = {
            "customer_name": appointment.customer.name,
            "salon_name": self.tenant.name if self.tenant else "BeautyHub",
            "tenant_url": f"https://{self.tenant.slug}.saas.akylman.online"
            if self.tenant
            else "",
            "staff_name": appointment.staff.name,
            "loyalty_points": appointment.customer.loyalty_points,
        }

        return self.send_templated_email(
            to_email=appointment.customer.email,
            event="FOLLOWUP",
            variables=variables,
            language=language,
        )

    def send_birthday_email(
        self,
        customer_name: str,
        customer_email: str,
        coupon_code: str,
        discount_percent: str,
        valid_until: str,
        language: str = "ru",
    ) -> bool:
        """
        Send birthday greeting email

        Args:
            customer_name: Customer's name
            customer_email: Customer's email
            coupon_code: Birthday coupon code
            discount_percent: Discount percentage
            valid_until: Coupon expiry date
            language: Language code

        Returns:
            Boolean - success
        """
        variables = {
            "customer_name": customer_name,
            "coupon_code": coupon_code,
            "discount_percent": discount_percent,
            "valid_until": valid_until,
            "salon_name": self.tenant.name if self.tenant else "BeautyHub",
            "tenant_url": f"https://{self.tenant.slug}.saas.akylman.online"
            if self.tenant
            else "",
        }

        return self.send_templated_email(
            to_email=customer_email,
            event="BIRTHDAY",
            variables=variables,
            language=language,
        )
