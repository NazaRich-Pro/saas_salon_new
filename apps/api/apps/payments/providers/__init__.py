"""Payment providers package"""
from .base import PaymentProvider
from .manual_cash import ManualCashProvider
from .stripe_stub import StripeStubProvider

# Provider registry
PAYMENT_PROVIDERS = {
    "MANUAL_CASH": ManualCashProvider,
    "STRIPE": StripeStubProvider,
}


def get_provider(provider_name: str) -> PaymentProvider:
    """
    Get payment provider instance by name

    Args:
        provider_name: Provider name (MANUAL_CASH, STRIPE)

    Returns:
        PaymentProvider instance

    Raises:
        ValueError: If provider not found
    """
    provider_class = PAYMENT_PROVIDERS.get(provider_name)

    if not provider_class:
        raise ValueError(f"Payment provider '{provider_name}' not found")

    return provider_class()


__all__ = [
    "PaymentProvider",
    "ManualCashProvider",
    "StripeStubProvider",
    "get_provider",
]
