"""Manual cash payment provider"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

from .base import PaymentProvider


class ManualCashProvider(PaymentProvider):
    """
    Manual cash payment provider
    Used when reception/admin marks payment as received in cash
    """

    @property
    def name(self) -> str:
        return "MANUAL_CASH"

    @property
    def display_name(self) -> str:
        return "Manual Cash Payment"

    def process_payment(
        self, amount: Decimal, currency: str = "KGS", metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Process manual cash payment

        For manual cash, we immediately mark as succeeded since
        the reception/admin is confirming they received the cash

        Args:
            amount: Payment amount
            currency: Currency code
            metadata: Additional info (processed_by, appointment_id, etc.)

        Returns:
            Dict with payment result
        """
        if not self.validate_amount(amount):
            return {
                "status": "FAILED",
                "transaction_id": None,
                "message": "Invalid amount",
                "extra": {},
            }

        # Generate internal transaction ID
        transaction_id = f"CASH-{uuid.uuid4().hex[:12].upper()}"

        metadata = metadata or {}

        return {
            "status": "SUCCEEDED",
            "transaction_id": transaction_id,
            "message": f"Cash payment of {amount} {currency} marked as received",
            "extra": {
                "payment_method": "cash",
                "received_at": datetime.utcnow().isoformat(),
                "processed_by": metadata.get("processed_by"),
                "appointment_id": metadata.get("appointment_id"),
                "notes": metadata.get("notes", ""),
            },
        }

    def refund_payment(
        self, transaction_id: str, amount: Optional[Decimal] = None
    ) -> Dict:
        """
        Refund manual cash payment

        For manual cash, this just creates a record of the refund
        The actual cash must be returned manually

        Args:
            transaction_id: Original payment transaction ID
            amount: Refund amount (None = full refund)

        Returns:
            Dict with refund result
        """
        refund_id = f"REFUND-{uuid.uuid4().hex[:12].upper()}"

        return {
            "status": "SUCCEEDED",
            "refund_id": refund_id,
            "original_transaction_id": transaction_id,
            "amount": str(amount) if amount else "full",
            "message": "Cash refund recorded (manual action required)",
            "extra": {
                "refunded_at": datetime.utcnow().isoformat(),
                "manual_refund": True,
            },
        }

    def get_payment_status(self, transaction_id: str) -> Dict:
        """
        Get payment status

        For manual cash, all payments are immediately succeeded

        Args:
            transaction_id: Transaction ID

        Returns:
            Dict with payment status
        """
        # In manual cash, we don't have external tracking
        # All payments marked as succeeded
        return {
            "transaction_id": transaction_id,
            "status": "SUCCEEDED",
            "payment_method": "cash",
        }

    def supports_currency(self, currency: str) -> bool:
        """Manual cash supports all currencies"""
        return True
