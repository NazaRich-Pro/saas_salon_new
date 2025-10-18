"""Coupon application and validation service"""
from decimal import Decimal
from typing import Dict, List, Optional

from apps.booking.models import Customer
from django.db.models import Q
from django.utils import timezone

from .models import Coupon


class CouponApplicationError(Exception):
    """Exception raised when coupon cannot be applied"""

    pass


class CouponService:
    """Service for coupon validation and application"""

    def __init__(self, tenant):
        self.tenant = tenant

    def validate_and_apply(
        self,
        code: str,
        appointment_total: Decimal,
        customer: Optional[Customer] = None,
        service_ids: Optional[List[str]] = None,
        appointment_datetime: Optional[timezone.datetime] = None,
    ) -> Dict:
        """
        Validate coupon and calculate discount

        Args:
            code: Coupon code
            appointment_total: Total appointment price
            customer: Customer instance (for usage limit checking)
            service_ids: List of service UUIDs
            appointment_datetime: Appointment datetime (for day/time rules)

        Returns:
            Dict with:
                - coupon: Coupon instance
                - discount_kgs: Discount amount
                - final_amount_kgs: Final price after discount
                - applied: Boolean

        Raises:
            CouponApplicationError: If coupon is invalid
        """
        # Get coupon
        try:
            coupon = Coupon.objects.get(
                tenant=self.tenant, code=code.upper().strip(), is_active=True
            )
        except Coupon.DoesNotExist:
            raise CouponApplicationError("Купон не найден")

        # Check validity period
        now = timezone.now()
        if now < coupon.valid_from:
            raise CouponApplicationError("Купон еще не действует")

        if now > coupon.valid_to:
            raise CouponApplicationError("Купон истек")

        # Check usage limits
        if coupon.max_uses and coupon.uses_count >= coupon.max_uses:
            raise CouponApplicationError("Лимит использования купона исчерпан")

        # Check per-customer usage limit
        if customer and coupon.max_uses_per_customer:
            from apps.booking.models import Appointment

            customer_uses = Appointment.objects.filter(
                tenant=self.tenant,
                customer=customer,
                discount_kgs__gt=0,
                internal_notes__icontains=code,
            ).count()

            if customer_uses >= coupon.max_uses_per_customer:
                raise CouponApplicationError(
                    f"Вы уже использовали этот купон {coupon.max_uses_per_customer} раз(а)"
                )

        # Check rules
        if not self._check_rules(
            coupon, appointment_total, service_ids, appointment_datetime
        ):
            raise CouponApplicationError("Купон не применим к этой записи")

        # Calculate discount
        if coupon.kind == "PERCENT":
            discount = (appointment_total * coupon.value) / 100
        else:  # FIXED
            discount = coupon.value

        # Ensure discount doesn't exceed total
        discount = min(discount, appointment_total)
        final_amount = max(Decimal("0.00"), appointment_total - discount)

        return {
            "coupon": coupon,
            "discount_kgs": discount,
            "final_amount_kgs": final_amount,
            "applied": True,
        }

    def _check_rules(
        self,
        coupon: Coupon,
        appointment_total: Decimal,
        service_ids: Optional[List[str]],
        appointment_datetime: Optional[timezone.datetime],
    ) -> bool:
        """
        Check if coupon rules allow application

        Rules can include:
        - min_amount: Minimum purchase amount
        - services: List of service UUIDs
        - categories: List of category UUIDs
        - days: List of day names
        - time_from: Minimum time (HH:MM)
        - time_to: Maximum time (HH:MM)
        """
        rules = coupon.rules

        if not rules:
            return True

        # Check minimum amount
        min_amount = rules.get("min_amount")
        if min_amount and appointment_total < Decimal(str(min_amount)):
            return False

        # Check services
        allowed_services = rules.get("services", [])
        if allowed_services and service_ids:
            if not any(sid in allowed_services for sid in service_ids):
                return False

        # Check categories
        allowed_categories = rules.get("categories", [])
        if allowed_categories and service_ids:
            from apps.booking.models import Service

            service_categories = Service.objects.filter(
                id__in=service_ids, tenant=self.tenant
            ).values_list("category_id", flat=True)

            if not any(
                str(cat_id) in allowed_categories for cat_id in service_categories
            ):
                return False

        # Check day of week
        allowed_days = rules.get("days", [])
        if allowed_days and appointment_datetime:
            day_name = appointment_datetime.strftime("%A").lower()
            if day_name not in [d.lower() for d in allowed_days]:
                return False

        # Check time range
        time_from = rules.get("time_from")
        time_to = rules.get("time_to")

        if (time_from or time_to) and appointment_datetime:
            appt_time = appointment_datetime.time()

            if time_from:
                from datetime import datetime

                min_time = datetime.strptime(time_from, "%H:%M").time()
                if appt_time < min_time:
                    return False

            if time_to:
                from datetime import datetime

                max_time = datetime.strptime(time_to, "%H:%M").time()
                if appt_time > max_time:
                    return False

        return True

    def apply_coupon_to_appointment(self, appointment, code: str) -> Decimal:
        """
        Apply coupon to an appointment

        Args:
            appointment: Appointment instance
            code: Coupon code

        Returns:
            Discount amount in KGS

        Raises:
            CouponApplicationError: If coupon cannot be applied
        """
        # Get service IDs
        service_ids = [str(aps.service_id) for aps in appointment.services.all()]

        # Validate and calculate
        result = self.validate_and_apply(
            code=code,
            appointment_total=appointment.total_price_kgs,
            customer=appointment.customer,
            service_ids=service_ids,
            appointment_datetime=appointment.start_at,
        )

        # Apply discount to appointment
        appointment.discount_kgs = result["discount_kgs"]
        appointment.internal_notes = (
            f"Купон {code} применен\n{appointment.internal_notes}"
        )
        appointment.save(update_fields=["discount_kgs", "internal_notes", "updated_at"])

        # Increment coupon usage
        coupon = result["coupon"]
        coupon.uses_count += 1
        coupon.save(update_fields=["uses_count", "updated_at"])

        return result["discount_kgs"]

    def remove_coupon_from_appointment(self, appointment) -> None:
        """
        Remove coupon discount from appointment
        """
        appointment.discount_kgs = Decimal("0.00")
        appointment.save(update_fields=["discount_kgs", "updated_at"])
