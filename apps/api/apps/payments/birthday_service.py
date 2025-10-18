"""Birthday campaign service"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List

from apps.booking.models import Customer
from django.utils import timezone

from .models import Coupon


class BirthdayService:
    """Service for birthday campaigns"""

    def __init__(self, tenant):
        self.tenant = tenant

    def get_todays_birthdays(self) -> List[Customer]:
        """
        Get customers with birthday today

        Returns:
            List of Customer instances
        """
        today = date.today()

        # Get customers with birthday today (matching month and day)
        customers = Customer.objects.filter(
            tenant=self.tenant,
            date_of_birth__month=today.month,
            date_of_birth__day=today.day,
            is_active=True,
            email__isnull=False,  # Must have email
        ).exclude(email="")

        return list(customers)

    def create_birthday_coupon(
        self,
        customer: Customer,
        discount_percent: Decimal = Decimal("20.00"),
        validity_days: int = 30,
    ) -> Coupon:
        """
        Create birthday coupon for customer

        Args:
            customer: Customer instance
            discount_percent: Discount percentage (default 20%)
            validity_days: How many days coupon is valid (default 30)

        Returns:
            Created Coupon instance
        """
        # Generate unique code
        code = f"BIRTHDAY-{customer.phone[-4:]}-{date.today().year}"

        # Check if coupon already exists
        existing = Coupon.objects.filter(tenant=self.tenant, code=code).first()

        if existing:
            return existing

        # Create coupon
        valid_from = timezone.now()
        valid_to = valid_from + timedelta(days=validity_days)

        coupon = Coupon.objects.create(
            tenant=self.tenant,
            code=code,
            kind="PERCENT",
            value=discount_percent,
            valid_from=valid_from,
            valid_to=valid_to,
            max_uses=1,  # Can only be used once
            max_uses_per_customer=1,
            rules={"birthday_coupon": True, "customer_phone": customer.phone},
            is_active=True,
        )

        return coupon

    def prepare_birthday_greeting(self, customer: Customer, coupon: Coupon) -> Dict:
        """
        Prepare birthday greeting data for email

        Args:
            customer: Customer instance
            coupon: Birthday coupon

        Returns:
            Dict with greeting data
        """
        return {
            "customer_name": customer.name,
            "customer_email": customer.email,
            "coupon_code": coupon.code,
            "discount_percent": str(coupon.value),
            "valid_until": coupon.valid_to.strftime("%d.%m.%Y"),
            "tenant_name": self.tenant.name,
            "tenant_url": f"https://{self.tenant.slug}.saas.akylman.online",
            "language": self.tenant.settings.get("language", "ru"),
        }

    def process_birthday_campaigns(self) -> Dict:
        """
        Process birthday campaigns for today

        Returns:
            Dict with campaign statistics
        """
        customers = self.get_todays_birthdays()

        sent_count = 0
        coupon_count = 0
        errors = []

        for customer in customers:
            try:
                # Create birthday coupon
                coupon = self.create_birthday_coupon(customer)
                coupon_count += 1

                # Prepare greeting (will be sent by notification service)
                greeting_data = self.prepare_birthday_greeting(customer, coupon)

                # Queue email (will be implemented in Stage 8)
                # For now, just prepare the data
                from apps.notifications.tasks import send_birthday_email

                send_birthday_email.delay(greeting_data)

                sent_count += 1

            except Exception as e:
                errors.append(f"{customer.email}: {str(e)}")

        return {
            "total_birthdays": len(customers),
            "coupons_created": coupon_count,
            "greetings_sent": sent_count,
            "errors": errors,
        }

    def get_upcoming_birthdays(self, days_ahead: int = 7) -> List[Customer]:
        """
        Get customers with upcoming birthdays

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of customers with birthdays in next N days
        """
        today = date.today()
        upcoming = []

        for day_offset in range(1, days_ahead + 1):
            check_date = today + timedelta(days=day_offset)

            customers = Customer.objects.filter(
                tenant=self.tenant,
                date_of_birth__month=check_date.month,
                date_of_birth__day=check_date.day,
                is_active=True,
            )

            upcoming.extend(customers)

        return upcoming
