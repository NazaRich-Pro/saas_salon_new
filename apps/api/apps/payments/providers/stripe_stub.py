"""Stripe payment provider (stub for future implementation)"""
import uuid
from decimal import Decimal
from typing import Dict, Optional

from .base import PaymentProvider


class StripeStubProvider(PaymentProvider):
    """
    Stripe payment provider stub
    This is a placeholder for future Stripe integration
    """

    @property
    def name(self) -> str:
        return "STRIPE"

    @property
    def display_name(self) -> str:
        return "Stripe (Card Payments)"

    def process_payment(
        self, amount: Decimal, currency: str = "KGS", metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Process Stripe payment (stub)

        In production, this would:
        1. Create Stripe PaymentIntent
        2. Return client_secret for frontend
        3. Handle 3D Secure if required
        4. Process the payment

        For now, returns a stub response
        """
        if not self.validate_amount(amount):
            return {
                "status": "FAILED",
                "transaction_id": None,
                "message": "Invalid amount",
                "extra": {},
            }

        # Generate stub payment intent ID
        payment_intent_id = f"pi_stub_{uuid.uuid4().hex[:24]}"
        client_secret = f"{payment_intent_id}_secret_{uuid.uuid4().hex[:16]}"

        return {
            "status": "PENDING",
            "transaction_id": payment_intent_id,
            "message": "Stripe PaymentIntent created (stub)",
            "extra": {
                "client_secret": client_secret,
                "payment_intent_id": payment_intent_id,
                "amount": int(amount * 100),  # Stripe uses cents
                "currency": currency.lower(),
                "stub": True,
                "note": "This is a stub. Real Stripe integration pending.",
            },
        }

    def refund_payment(
        self, transaction_id: str, amount: Optional[Decimal] = None
    ) -> Dict:
        """
        Refund Stripe payment (stub)

        In production, would call Stripe Refunds API
        """
        refund_id = f"re_stub_{uuid.uuid4().hex[:24]}"

        return {
            "status": "SUCCEEDED",
            "refund_id": refund_id,
            "original_transaction_id": transaction_id,
            "amount": str(amount) if amount else "full",
            "message": "Stripe refund created (stub)",
            "extra": {
                "stub": True,
                "note": "This is a stub. Real Stripe integration pending.",
            },
        }

    def get_payment_status(self, transaction_id: str) -> Dict:
        """
        Get Stripe payment status (stub)

        In production, would call Stripe API to get PaymentIntent status
        """
        return {
            "transaction_id": transaction_id,
            "status": "PENDING",
            "payment_method": "card",
            "stub": True,
            "note": "This is a stub. Real Stripe integration pending.",
        }

    def supports_currency(self, currency: str) -> bool:
        """
        Check if Stripe supports currency

        Stripe supports many currencies, but not all
        For KGS (Kyrgyzstan Som), check Stripe documentation
        """
        # For now, allow all currencies (stub)
        return True

    def create_payment_intent(
        self, amount: Decimal, currency: str = "KGS", metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create Stripe PaymentIntent (stub)

        This is a convenience method for creating payment intents
        In production, would call Stripe API

        Returns:
            Dict with client_secret and payment_intent_id
        """
        result = self.process_payment(amount, currency, metadata)
        return result["extra"]
