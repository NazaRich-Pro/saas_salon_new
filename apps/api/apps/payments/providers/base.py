"""Base payment provider interface"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Optional


class PaymentProvider(ABC):
    """
    Abstract base class for payment providers
    All payment providers must implement this interface
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name"""
        pass

    @abstractmethod
    def process_payment(
        self, amount: Decimal, currency: str, metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Process a payment

        Args:
            amount: Payment amount
            currency: Currency code (e.g., 'KGS')
            metadata: Additional payment metadata

        Returns:
            Dict with:
                - status: 'SUCCEEDED' | 'FAILED' | 'PENDING'
                - transaction_id: External transaction ID
                - message: Success/error message
                - extra: Provider-specific data
        """
        pass

    @abstractmethod
    def refund_payment(
        self, transaction_id: str, amount: Optional[Decimal] = None
    ) -> Dict:
        """
        Refund a payment

        Args:
            transaction_id: Original transaction ID
            amount: Refund amount (None = full refund)

        Returns:
            Dict with refund status and details
        """
        pass

    @abstractmethod
    def get_payment_status(self, transaction_id: str) -> Dict:
        """
        Get payment status

        Args:
            transaction_id: Transaction ID to check

        Returns:
            Dict with current payment status
        """
        pass

    def validate_amount(self, amount: Decimal) -> bool:
        """
        Validate payment amount

        Args:
            amount: Amount to validate

        Returns:
            Boolean - True if valid
        """
        return amount > 0

    def supports_currency(self, currency: str) -> bool:
        """
        Check if provider supports currency

        Args:
            currency: Currency code

        Returns:
            Boolean - True if supported
        """
        # Override in subclass if provider has currency restrictions
        return True
