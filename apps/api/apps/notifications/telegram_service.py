"""Telegram notification service (optional)"""
import logging
from typing import Dict, Optional

import requests
from django.conf import settings

from .models import NotificationTemplate

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for sending Telegram messages"""

    def __init__(self, tenant=None):
        self.tenant = tenant
        self.bot_token = settings.TELEGRAM_BOT_TOKEN or None
        self.api_url = (
            f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        )

    def is_configured(self) -> bool:
        """Check if Telegram is configured"""
        return bool(self.bot_token)

    def render_template(self, template_body: str, variables: Dict) -> str:
        """
        Render Telegram message template
        Uses same variable system as email
        """
        rendered = template_body

        for key, value in variables.items():
            placeholder = f"%{key}%"
            rendered = rendered.replace(placeholder, str(value))

        return rendered

    def get_template(
        self, event: str, language: str = "ru"
    ) -> Optional[NotificationTemplate]:
        """Get Telegram template"""
        if self.tenant:
            template = NotificationTemplate.objects.filter(
                tenant=self.tenant, kind="TELEGRAM", event=event, lang=language.upper()
            ).first()

            if template:
                return template

        # Platform default
        template = NotificationTemplate.objects.filter(
            tenant__isnull=True, kind="TELEGRAM", event=event, lang=language.upper()
        ).first()

        return template

    def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
        """
        Send Telegram message

        Args:
            chat_id: Telegram chat ID or username
            text: Message text
            parse_mode: Parse mode (HTML, Markdown, None)

        Returns:
            Boolean - success
        """
        if not self.is_configured():
            logger.warning("Telegram not configured (no BOT_TOKEN)")
            return False

        try:
            url = f"{self.api_url}/sendMessage"
            data = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}

            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()

            logger.info(f"Telegram message sent to {chat_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {str(e)}")
            return False

    def send_templated_message(
        self, chat_id: str, event: str, variables: Dict, language: str = "ru"
    ) -> bool:
        """
        Send Telegram message using stored template

        Args:
            chat_id: Telegram chat ID
            event: Event type
            variables: Template variables
            language: Language code

        Returns:
            Boolean - success
        """
        template = self.get_template(event, language)

        if not template:
            logger.error(f"Telegram template not found: {event}/{language}")
            return False

        # Render message
        text = self.render_template(template.body, variables)

        return self.send_message(chat_id, text)

    def send_appointment_reminder(
        self, chat_id: str, appointment, hours_before: int = 24, language: str = "ru"
    ) -> bool:
        """
        Send appointment reminder via Telegram

        Args:
            chat_id: Customer's Telegram chat ID
            appointment: Appointment instance
            hours_before: Hours before (24 or 2)
            language: Language code

        Returns:
            Boolean - success
        """
        event = "REMINDER_24H" if hours_before == 24 else "REMINDER_2H"

        appt_datetime = appointment.start_at.strftime("%d.%m.%Y в %H:%M")

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
        }

        return self.send_templated_message(chat_id, event, variables, language)
