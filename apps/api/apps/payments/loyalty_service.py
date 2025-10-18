"""Loyalty points service"""
from decimal import Decimal
from typing import Dict, Optional

from apps.booking.models import Customer
from django.db import transaction

from .models import LoyaltyRule


class LoyaltyServiceError(Exception):
    """Exception raised for loyalty operations"""

    pass


class LoyaltyService:
    """Service for loyalty points management"""

    def __init__(self, tenant):
        self.tenant = tenant
        self.loyalty_rule = self._get_loyalty_rule()

    def _get_loyalty_rule(self) -> Optional[LoyaltyRule]:
        """Get active loyalty rule for tenant"""
        try:
            return LoyaltyRule.objects.get(tenant=self.tenant, is_active=True)
        except LoyaltyRule.DoesNotExist:
            return None

    def calculate_points_earned(self, amount_spent_kgs: Decimal) -> int:
        """
        Calculate loyalty points earned from spending

        Args:
            amount_spent_kgs: Amount spent in KGS

        Returns:
            Number of points earned
        """
        if not self.loyalty_rule:
            return 0

        # Default: 1 point per 100 KGS
        points_per_hundred = self.loyalty_rule.earn_per_100_kgs
        points = int(amount_spent_kgs / 100) * points_per_hundred

        return points

    def award_points(self, customer: Customer, amount_spent_kgs: Decimal) -> int:
        """
        Award loyalty points to customer for spending

        Args:
            customer: Customer instance
            amount_spent_kgs: Amount spent

        Returns:
            Number of points awarded
        """
        points_earned = self.calculate_points_earned(amount_spent_kgs)

        if points_earned > 0:
            customer.loyalty_points += points_earned
            customer.save(update_fields=["loyalty_points"])

        return points_earned

    def calculate_discount_from_points(self, points: int) -> Decimal:
        """
        Calculate discount amount from loyalty points

        Args:
            points: Number of points to redeem

        Returns:
            Discount amount in KGS
        """
        if not self.loyalty_rule:
            return Decimal("0.00")

        # Default: 1 point = 1 KGS
        redeem_rate = self.loyalty_rule.redeem_rate
        discount = Decimal(str(points)) * redeem_rate

        return discount

    @transaction.atomic
    def redeem_points(
        self, customer: Customer, points_to_redeem: int, appointment_total: Decimal
    ) -> Dict:
        """
        Redeem loyalty points for discount

        Args:
            customer: Customer instance
            points_to_redeem: Number of points to use
            appointment_total: Total appointment price

        Returns:
            Dict with:
                - points_redeemed: Number of points used
                - discount_kgs: Discount amount
                - points_remaining: Points left after redemption

        Raises:
            LoyaltyServiceError: If redemption fails
        """
        if not self.loyalty_rule:
            raise LoyaltyServiceError(
                "Программа лояльности не активна для этого салона"
            )

        # Check minimum points
        if points_to_redeem < self.loyalty_rule.min_points_to_redeem:
            raise LoyaltyServiceError(
                f"Минимум для использования: {self.loyalty_rule.min_points_to_redeem} баллов"
            )

        # Check customer has enough points
        if customer.loyalty_points < points_to_redeem:
            raise LoyaltyServiceError(
                f"Недостаточно баллов. Доступно: {customer.loyalty_points}"
            )

        # Calculate discount
        discount = self.calculate_discount_from_points(points_to_redeem)

        # Ensure discount doesn't exceed total
        if discount > appointment_total:
            # Recalculate points needed
            points_needed = int(appointment_total / self.loyalty_rule.redeem_rate)
            discount = self.calculate_discount_from_points(points_needed)
            points_to_redeem = points_needed

        # Deduct points from customer
        customer.loyalty_points -= points_to_redeem
        customer.save(update_fields=["loyalty_points"])

        return {
            "points_redeemed": points_to_redeem,
            "discount_kgs": discount,
            "points_remaining": customer.loyalty_points,
        }

    def get_customer_points_value(self, customer: Customer) -> Decimal:
        """
        Get KGS value of customer's loyalty points

        Args:
            customer: Customer instance

        Returns:
            Value in KGS
        """
        if not self.loyalty_rule:
            return Decimal("0.00")

        return self.calculate_discount_from_points(customer.loyalty_points)

    def can_redeem_points(self, customer: Customer, points: int) -> bool:
        """
        Check if customer can redeem specified points

        Args:
            customer: Customer instance
            points: Points to check

        Returns:
            Boolean
        """
        if not self.loyalty_rule:
            return False

        if points < self.loyalty_rule.min_points_to_redeem:
            return False

        if customer.loyalty_points < points:
            return False

        return True
