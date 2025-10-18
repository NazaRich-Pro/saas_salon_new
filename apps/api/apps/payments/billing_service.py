"""SaaS billing service"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Optional

from apps.tenants.models import Tenant
from django.db import transaction
from django.utils import timezone

from .models import SaaSSubscription


class BillingError(Exception):
    """Exception for billing operations"""

    pass


class BillingService:
    """Service for SaaS billing and subscription management"""

    # Plan definitions
    PLANS = {
        "SOLO": {
            "name": "Solo Master",
            "base_price": Decimal("500.00"),
            "features": {
                "max_seats": 1,
                "max_bookings_per_day": 20,
                "sms_enabled": False,
                "telegram_enabled": False,
                "white_label": False,
                "api_access": False,
                "priority_support": False,
            },
        },
        "SALON": {
            "name": "Salon",
            "base_price": Decimal("500.00"),  # Per seat
            "features": {
                "max_seats": 50,
                "max_bookings_per_day": 200,
                "sms_enabled": True,
                "telegram_enabled": True,
                "white_label": True,
                "api_access": True,
                "priority_support": True,
            },
        },
    }

    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self.subscription = self._get_or_create_subscription()

    def _get_or_create_subscription(self) -> SaaSSubscription:
        """Get or create subscription for tenant"""
        subscription, created = SaaSSubscription.objects.get_or_create(
            tenant=self.tenant,
            defaults={
                "plan": "SOLO" if self.tenant.type == "SOLO" else "SALON",
                "seats": self.tenant.seats,
                "status": "TRIAL",
                "period_start": date.today(),
                "period_end": date.today() + timedelta(days=30),
                "monthly_price_kgs": self.calculate_monthly_price(
                    "SOLO" if self.tenant.type == "SOLO" else "SALON", self.tenant.seats
                ),
            },
        )

        return subscription

    @classmethod
    def calculate_monthly_price(cls, plan: str, seats: int) -> Decimal:
        """
        Calculate monthly price for plan and seats

        Args:
            plan: SOLO or SALON
            seats: Number of seats

        Returns:
            Monthly price in KGS
        """
        base_price = cls.PLANS[plan]["base_price"]

        if plan == "SOLO":
            return base_price  # Fixed 500 KGS
        else:  # SALON
            return base_price * seats  # 500 × seats

    def get_billing_status(self) -> Dict:
        """
        Get current billing status

        Returns:
            Dict with status flags and info
        """
        subscription = self.subscription
        today = date.today()

        # Determine status flags
        is_trial = subscription.status == "TRIAL"
        is_grace = subscription.status == "GRACE"
        is_active = subscription.status == "ACTIVE"
        is_suspended = subscription.status == "SUSPENDED"

        # Calculate days remaining
        if is_trial:
            days_remaining = (subscription.period_end - today).days
        elif is_grace and subscription.grace_until:
            days_remaining = (subscription.grace_until - today).days
        else:
            days_remaining = 0

        # Determine if booking should be blocked
        booking_blocked = is_suspended or (
            is_grace and subscription.grace_until and subscription.grace_until < today
        )

        return {
            "status": subscription.status,
            "plan": subscription.plan,
            "seats": subscription.seats,
            "monthly_price_kgs": str(subscription.monthly_price_kgs),
            "is_trial": is_trial,
            "is_grace": is_grace,
            "is_active": is_active,
            "is_suspended": is_suspended,
            "booking_blocked": booking_blocked,
            "admin_access": True,  # Always allow admin access
            "days_remaining": max(0, days_remaining),
            "period_start": subscription.period_start,
            "period_end": subscription.period_end,
            "grace_until": subscription.grace_until,
            "next_payment_date": subscription.next_payment_date,
            "last_payment_date": subscription.last_payment_date,
        }

    def get_features(self) -> Dict:
        """
        Get features available for current plan

        Returns:
            Dict with feature flags
        """
        plan = self.subscription.plan
        features = self.PLANS.get(plan, {}).get("features", {})

        return {**features, "plan": plan, "seats": self.subscription.seats}

    def check_feature(self, feature_name: str) -> bool:
        """
        Check if feature is enabled for tenant

        Args:
            feature_name: Feature name (e.g., 'sms_enabled')

        Returns:
            Boolean
        """
        features = self.get_features()
        return features.get(feature_name, False)

    @transaction.atomic
    def update_seats(self, new_seats: int) -> SaaSSubscription:
        """
        Update number of seats

        Args:
            new_seats: New seat count

        Returns:
            Updated subscription

        Raises:
            BillingError: If validation fails
        """
        plan = self.subscription.plan
        max_seats = self.PLANS[plan]["features"]["max_seats"]

        if new_seats < 1:
            raise BillingError("Минимум 1 место")

        if new_seats > max_seats:
            raise BillingError(f"Максимум {max_seats} мест для плана {plan}")

        # Update subscription
        self.subscription.seats = new_seats
        self.subscription.monthly_price_kgs = self.calculate_monthly_price(
            plan, new_seats
        )
        self.subscription.save(
            update_fields=["seats", "monthly_price_kgs", "updated_at"]
        )

        # Update tenant
        self.tenant.seats = new_seats
        self.tenant.save(update_fields=["seats"])

        return self.subscription

    @transaction.atomic
    def mark_invoice_paid(
        self, payment_date: Optional[date] = None
    ) -> SaaSSubscription:
        """
        Mark invoice as paid (manual by superadmin)
        Extends subscription period

        Args:
            payment_date: Date of payment (default: today)

        Returns:
            Updated subscription
        """
        if not payment_date:
            payment_date = date.today()

        subscription = self.subscription

        # Update payment dates
        subscription.last_payment_date = payment_date

        # Extend period by 30 days
        if subscription.status in ["GRACE", "SUSPENDED"]:
            # Restart from today
            subscription.period_start = payment_date
            subscription.period_end = payment_date + timedelta(days=30)
        else:
            # Extend from current period_end
            subscription.period_start = subscription.period_end + timedelta(days=1)
            subscription.period_end = subscription.period_start + timedelta(days=30)

        subscription.next_payment_date = subscription.period_end
        subscription.status = "ACTIVE"
        subscription.grace_until = None

        subscription.save()

        # Update tenant status
        self.tenant.status = "ACTIVE"
        self.tenant.save(update_fields=["status"])

        return subscription

    def generate_invoice_data(self) -> Dict:
        """
        Generate invoice data for current period

        Returns:
            Dict with invoice information
        """
        subscription = self.subscription

        # Calculate amount
        amount = subscription.monthly_price_kgs

        # Invoice period
        period_start = subscription.period_start
        period_end = subscription.period_end

        return {
            "tenant_name": self.tenant.name,
            "tenant_slug": self.tenant.slug,
            "plan": subscription.plan,
            "seats": subscription.seats,
            "amount_kgs": str(amount),
            "currency": "KGS",
            "period_start": period_start,
            "period_end": period_end,
            "due_date": period_end,
            "status": subscription.status,
            "invoice_number": f"INV-{self.tenant.slug}-{period_start.strftime('%Y%m')}",
        }

    def can_create_booking(self) -> tuple[bool, Optional[str]]:
        """
        Check if tenant can create new bookings

        Returns:
            (allowed: bool, reason: Optional[str])
        """
        status = self.subscription.status

        if status == "ACTIVE":
            return True, None

        if status == "TRIAL":
            if self.subscription.period_end >= date.today():
                return True, None
            else:
                return False, "Пробный период истек"

        if status == "GRACE":
            if (
                self.subscription.grace_until
                and self.subscription.grace_until >= date.today()
            ):
                return True, "Льготный период - оплатите в течение {days} дней"
            else:
                return False, "Льготный период истек - онлайн запись заблокирована"

        if status == "SUSPENDED":
            return False, "Подписка приостановлена - обратитесь в поддержку"

        if status == "CANCELLED":
            return False, "Подписка отменена"

        return False, "Неизвестный статус подписки"

    def can_access_feature(self, feature_name: str) -> bool:
        """
        Check if tenant can access a feature based on plan and status

        Args:
            feature_name: Feature name

        Returns:
            Boolean
        """
        # Admin access always allowed
        if feature_name == "admin_access":
            return True

        # During trial/grace, all features available
        if self.subscription.status in ["TRIAL", "GRACE", "ACTIVE"]:
            return self.check_feature(feature_name)

        # Suspended: only admin access
        return False
