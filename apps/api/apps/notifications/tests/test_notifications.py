"""Tests for notification system"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from apps.booking.models import Appointment, Customer, Service, ServiceCategory, Staff
from apps.notifications.email_service import EmailService
from apps.notifications.models import NotificationLog, NotificationTemplate
from apps.notifications.telegram_service import TelegramService
from apps.notifications.template_defaults import DEFAULT_TEMPLATES
from apps.tenants.models import Tenant
from django.utils import timezone


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(
        slug="test-notifications",
        name="Test Salon",
        type="SALON",
        status="ACTIVE",
        settings={"language": "ru"},
    )


@pytest.fixture
def customer(db, tenant):
    return Customer.objects.create(
        tenant=tenant,
        name="Test Customer",
        phone="+996700111111",
        email="customer@test.com",
        date_of_birth=date.today(),
    )


@pytest.fixture
def staff(db, tenant):
    return Staff.objects.create(tenant=tenant, name="Test Master")


@pytest.fixture
def appointment(db, tenant, customer, staff):
    start_at = timezone.now() + timedelta(hours=25)

    return Appointment.objects.create(
        tenant=tenant,
        customer=customer,
        staff=staff,
        start_at=start_at,
        end_at=start_at + timedelta(hours=1),
        status="CONFIRMED",
        total_price_kgs=Decimal("500.00"),
    )


@pytest.mark.django_db
class TestEmailService:
    """Test email service"""

    def test_render_template(self, tenant):
        """Test template variable rendering"""
        service = EmailService(tenant)

        template = "Hello, %customer_name%! Your appointment is on %date_time%."
        variables = {"customer_name": "John Doe", "date_time": "15.10.2025 в 10:00"}

        rendered = service.render_template(template, variables)

        assert rendered == "Hello, John Doe! Your appointment is on 15.10.2025 в 10:00."

    def test_get_template(self, tenant):
        """Test getting notification template"""
        # Create template
        template = NotificationTemplate.objects.create(
            tenant=tenant,
            kind="EMAIL",
            event="WELCOME",
            lang="RU",
            subject="Test Subject",
            body="Test Body",
        )

        service = EmailService(tenant)
        retrieved = service.get_template("WELCOME", "ru", "EMAIL")

        assert retrieved == template
        assert retrieved.subject == "Test Subject"

    def test_fallback_to_platform_template(self, tenant):
        """Test fallback to platform default template"""
        # Create platform template (no tenant)
        platform_template = NotificationTemplate.objects.create(
            tenant=None,
            kind="EMAIL",
            event="REMINDER_24H",
            lang="RU",
            subject="Platform Reminder",
            body="Platform Body",
        )

        service = EmailService(tenant)
        retrieved = service.get_template("REMINDER_24H", "ru", "EMAIL")

        assert retrieved == platform_template

    @patch("apps.notifications.email_service.EmailMultiAlternatives")
    def test_send_email(self, mock_email, tenant):
        """Test sending email"""
        service = EmailService(tenant)

        success = service.send_email(
            to_email="test@example.com", subject="Test Subject", body="Test Body"
        )

        assert success is True
        assert mock_email.called

    @patch("apps.notifications.email_service.EmailService.send_email")
    def test_send_templated_email(self, mock_send, tenant):
        """Test sending templated email"""
        # Create template
        NotificationTemplate.objects.create(
            tenant=None,
            kind="EMAIL",
            event="WELCOME",
            lang="RU",
            subject="Welcome %owner_name%!",
            body="Hello %owner_name%, welcome to %salon_name%!",
        )

        service = EmailService(tenant)
        mock_send.return_value = True

        success = service.send_templated_email(
            to_email="owner@test.com",
            event="WELCOME",
            variables={"owner_name": "Anna", "salon_name": "My Salon"},
            language="ru",
        )

        assert success is True
        assert mock_send.called


@pytest.mark.django_db
class TestReminderTasks:
    """Test reminder Celery tasks"""

    @patch("apps.notifications.email_service.EmailService.send_appointment_reminder")
    def test_send_24h_reminders(self, mock_send, appointment):
        """Test 24h reminder task"""
        from apps.notifications.tasks import send_reminders_24h

        mock_send.return_value = True

        result = send_reminders_24h()

        # Check appointment was updated
        appointment.refresh_from_db()
        assert appointment.reminder_24h_sent is True

        assert "sent" in result.lower()

    @patch("apps.notifications.email_service.EmailService.send_appointment_reminder")
    def test_send_2h_reminders(self, mock_send, tenant, customer, staff):
        """Test 2h reminder task"""
        from apps.notifications.tasks import send_reminders_2h

        # Create appointment 2h from now
        start_at = timezone.now() + timedelta(hours=2)
        appointment = Appointment.objects.create(
            tenant=tenant,
            customer=customer,
            staff=staff,
            start_at=start_at,
            end_at=start_at + timedelta(hours=1),
            status="CONFIRMED",
            total_price_kgs=Decimal("500.00"),
        )

        mock_send.return_value = True

        result = send_reminders_2h()

        # Check appointment was updated
        appointment.refresh_from_db()
        assert appointment.reminder_2h_sent is True


@pytest.mark.django_db
class TestBirthdayNotifications:
    """Test birthday email sending"""

    @patch("apps.notifications.email_service.EmailService.send_birthday_email")
    def test_send_birthday_greetings(self, mock_send, tenant, customer):
        """Test birthday greeting task"""
        from apps.notifications.tasks import send_birthday_greetings

        # Set customer birthday to today
        customer.date_of_birth = date.today().replace(year=1990)
        customer.save()

        mock_send.return_value = True

        result = send_birthday_greetings()

        assert mock_send.called
        assert "sent" in result.lower()


@pytest.mark.django_db
class TestNotificationLog:
    """Test notification logging"""

    def test_create_notification_log(self, tenant, appointment, customer):
        """Test creating notification log"""
        log = NotificationLog.objects.create(
            tenant=tenant,
            recipient_email="test@example.com",
            kind="EMAIL",
            event="REMINDER_24H",
            subject="Test Reminder",
            body="Reminder body",
            status="SENT",
            sent_at=timezone.now(),
            appointment=appointment,
            customer=customer,
        )

        assert log.id is not None
        assert log.status == "SENT"
        assert log.appointment == appointment

    def test_track_failed_notification(self, tenant):
        """Test tracking failed notifications"""
        log = NotificationLog.objects.create(
            tenant=tenant,
            recipient_email="invalid@test.com",
            kind="EMAIL",
            event="WELCOME",
            subject="Welcome",
            body="Body",
            status="FAILED",
            error_message="SMTP error: connection refused",
            retry_count=3,
        )

        assert log.status == "FAILED"
        assert log.retry_count == 3
        assert "SMTP" in log.error_message


@pytest.mark.django_db
class TestTelegramService:
    """Test Telegram service"""

    def test_telegram_not_configured_by_default(self, tenant):
        """Test Telegram returns false when not configured"""
        service = TelegramService(tenant)

        assert service.is_configured() is False

    @patch("apps.notifications.telegram_service.requests.post")
    @patch("apps.notifications.telegram_service.settings")
    def test_send_telegram_message(self, mock_settings, mock_post, tenant):
        """Test sending Telegram message"""
        mock_settings.TELEGRAM_BOT_TOKEN = "fake-token"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        service = TelegramService(tenant)
        service.bot_token = "fake-token"
        service.api_url = "https://api.telegram.org/botfake-token"

        success = service.send_message(chat_id="123456", text="Test message")

        assert mock_post.called


@pytest.mark.django_db
class TestTemplateDefaults:
    """Test default templates"""

    def test_default_templates_exist(self):
        """Test all default templates are defined"""
        events = [
            "WELCOME",
            "REMINDER_24H",
            "REMINDER_2H",
            "FOLLOWUP",
            "BIRTHDAY",
            "DAILY_DIGEST",
        ]
        languages = ["RU", "KG"]

        for event in events:
            assert event in DEFAULT_TEMPLATES
            for lang in languages:
                assert lang in DEFAULT_TEMPLATES[event]
                assert "subject" in DEFAULT_TEMPLATES[event][lang]
                assert "body" in DEFAULT_TEMPLATES[event][lang]

    def test_templates_have_variables(self):
        """Test templates contain expected variables"""
        welcome_ru = DEFAULT_TEMPLATES["WELCOME"]["RU"]["body"]

        # Check for common variables
        assert "%owner_name%" in welcome_ru
        assert "%salon_name%" in welcome_ru
        assert "%tenant_url%" in welcome_ru

        reminder_ru = DEFAULT_TEMPLATES["REMINDER_24H"]["RU"]["body"]

        assert "%customer_name%" in reminder_ru
        assert "%date_time%" in reminder_ru
        assert "%service%" in reminder_ru
        assert "%staff_name%" in reminder_ru
