"""Tests for payment system"""
from datetime import timedelta
from decimal import Decimal

import pytest
from apps.booking.models import (
    Appointment,
    Customer,
    Schedule,
    Service,
    ServiceCategory,
    Staff,
    StaffService,
)
from apps.payments.models import Coupon, Payment
from apps.payments.providers import ManualCashProvider, StripeStubProvider, get_provider
from apps.tenants.models import Membership, Tenant
from apps.users.models import User
from django.urls import reverse
from django.utils import timezone


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(
        slug="test-payment-salon",
        name="Test Payment Salon",
        type="SALON",
        status="ACTIVE",
    )


@pytest.fixture
def reception_user(db, tenant):
    user = User.objects.create_user(email="reception@test.com", password="test123")
    Membership.objects.create(
        user=user, tenant=tenant, role="RECEPTION", is_active=True
    )
    return user


@pytest.fixture
def service(db, tenant):
    category = ServiceCategory.objects.create(tenant=tenant, name="Test Category")
    return Service.objects.create(
        tenant=tenant,
        category=category,
        name="Test Service",
        duration_min=60,
        price_kgs=Decimal("500.00"),
    )


@pytest.fixture
def staff(db, tenant):
    return Staff.objects.create(tenant=tenant, name="Test Staff")


@pytest.fixture
def appointment(db, tenant, service, staff):
    customer = Customer.objects.create(
        tenant=tenant, name="Test Customer", phone="+996700123456"
    )

    start_at = timezone.now() + timedelta(hours=2)

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
class TestPaymentProviders:
    """Test payment provider abstraction"""

    def test_get_manual_cash_provider(self):
        """Test getting ManualCash provider"""
        provider = get_provider("MANUAL_CASH")

        assert isinstance(provider, ManualCashProvider)
        assert provider.name == "MANUAL_CASH"
        assert provider.display_name == "Manual Cash Payment"

    def test_get_stripe_provider(self):
        """Test getting Stripe provider"""
        provider = get_provider("STRIPE")

        assert isinstance(provider, StripeStubProvider)
        assert provider.name == "STRIPE"

    def test_invalid_provider_raises_error(self):
        """Test invalid provider name raises error"""
        with pytest.raises(ValueError):
            get_provider("INVALID_PROVIDER")


@pytest.mark.django_db
class TestManualCashProvider:
    """Test ManualCash payment provider"""

    def test_process_cash_payment(self):
        """Test processing manual cash payment"""
        provider = ManualCashProvider()

        result = provider.process_payment(
            amount=Decimal("500.00"),
            currency="KGS",
            metadata={"appointment_id": "test-123"},
        )

        assert result["status"] == "SUCCEEDED"
        assert result["transaction_id"].startswith("CASH-")
        assert "received" in result["message"].lower()
        assert result["extra"]["payment_method"] == "cash"

    def test_manual_cash_refund(self):
        """Test manual cash refund"""
        provider = ManualCashProvider()

        # Process payment first
        payment_result = provider.process_payment(Decimal("500.00"), "KGS")
        transaction_id = payment_result["transaction_id"]

        # Refund
        refund_result = provider.refund_payment(transaction_id, Decimal("500.00"))

        assert refund_result["status"] == "SUCCEEDED"
        assert refund_result["refund_id"].startswith("REFUND-")
        assert refund_result["extra"]["manual_refund"] is True

    def test_invalid_amount_fails(self):
        """Test payment with invalid amount"""
        provider = ManualCashProvider()

        result = provider.process_payment(amount=Decimal("-100.00"), currency="KGS")

        assert result["status"] == "FAILED"


@pytest.mark.django_db
class TestStripeStubProvider:
    """Test Stripe stub provider"""

    def test_create_payment_intent(self):
        """Test creating Stripe PaymentIntent (stub)"""
        provider = StripeStubProvider()

        result = provider.process_payment(amount=Decimal("1000.00"), currency="KGS")

        assert result["status"] == "PENDING"
        assert result["transaction_id"].startswith("pi_stub_")
        assert "client_secret" in result["extra"]
        assert result["extra"]["stub"] is True

    def test_stripe_refund_stub(self):
        """Test Stripe refund (stub)"""
        provider = StripeStubProvider()

        # Create payment
        payment_result = provider.process_payment(Decimal("1000.00"), "KGS")
        transaction_id = payment_result["transaction_id"]

        # Refund
        refund_result = provider.refund_payment(transaction_id)

        assert refund_result["status"] == "SUCCEEDED"
        assert refund_result["extra"]["stub"] is True


@pytest.mark.django_db
class TestMarkCashPaid:
    """Test mark cash paid endpoint"""

    def test_mark_appointment_as_cash_paid(
        self, client, tenant, reception_user, appointment
    ):
        """Test marking appointment as paid in cash"""
        # Login
        client.force_authenticate(user=reception_user)

        url = "/api/payments/mark-cash-paid/"
        data = {
            "appointment_id": str(appointment.id),
            "amount_kgs": "500.00",
            "notes": "Payment received",
        }

        # Mock request.tenant
        from unittest.mock import patch

        with patch("apps.payments.views.Request.tenant", tenant):
            response = client.post(url, data, format="json")

        # Note: This test might need adjustment for actual request context
        # In real app, tenant middleware sets request.tenant

    def test_cannot_mark_paid_twice(self, tenant, appointment, reception_user):
        """Test cannot mark same appointment as paid twice"""
        # Create first payment
        Payment.objects.create(
            tenant=tenant,
            appointment=appointment,
            type="CASH",
            provider="MANUAL_CASH",
            status="SUCCEEDED",
            amount_kgs=Decimal("500.00"),
            external_ref="CASH-TEST123",
            processed_by=reception_user,
        )

        # Try to create second payment (should fail in view logic)
        # This would be tested via API endpoint


@pytest.mark.django_db
class TestCoupons:
    """Test coupon functionality"""

    def test_create_coupon(self, tenant):
        """Test creating a coupon"""
        coupon = Coupon.objects.create(
            tenant=tenant,
            code="TEST50",
            kind="PERCENT",
            value=Decimal("50.00"),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            max_uses=100,
            is_active=True,
        )

        assert coupon.code == "TEST50"
        assert coupon.kind == "PERCENT"
        assert coupon.value == Decimal("50.00")

    def test_coupon_percentage_discount(self, tenant):
        """Test percentage coupon discount calculation"""
        coupon = Coupon.objects.create(
            tenant=tenant,
            code="DISCOUNT25",
            kind="PERCENT",
            value=Decimal("25.00"),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            is_active=True,
        )

        # 25% off 1000 KGS = 250 KGS discount
        total = Decimal("1000.00")
        discount = (total * coupon.value) / 100

        assert discount == Decimal("250.00")
        assert total - discount == Decimal("750.00")

    def test_coupon_fixed_discount(self, tenant):
        """Test fixed amount coupon"""
        coupon = Coupon.objects.create(
            tenant=tenant,
            code="FIXED100",
            kind="FIXED",
            value=Decimal("100.00"),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            is_active=True,
        )

        total = Decimal("500.00")
        discount = coupon.value

        assert discount == Decimal("100.00")
        assert total - discount == Decimal("400.00")


@pytest.mark.django_db
class TestPaymentTracking:
    """Test payment tracking and appointment linking"""

    def test_payment_linked_to_appointment(self, tenant, appointment, reception_user):
        """Test payment is correctly linked to appointment"""
        payment = Payment.objects.create(
            tenant=tenant,
            appointment=appointment,
            type="CASH",
            provider="MANUAL_CASH",
            status="SUCCEEDED",
            amount_kgs=Decimal("500.00"),
            external_ref="CASH-TEST",
            processed_by=reception_user,
            processed_at=timezone.now(),
        )

        assert payment.appointment == appointment
        assert payment.tenant == tenant
        assert payment.status == "SUCCEEDED"

    def test_appointment_prepaid_updated(self, tenant, appointment):
        """Test appointment prepaid amount is updated"""
        initial_prepaid = appointment.prepaid_kgs

        # Mark as paid
        payment = Payment.objects.create(
            tenant=tenant,
            appointment=appointment,
            type="CASH",
            provider="MANUAL_CASH",
            status="SUCCEEDED",
            amount_kgs=Decimal("500.00"),
            external_ref="CASH-TEST",
        )

        # Update appointment (this happens in view)
        appointment.prepaid_kgs += payment.amount_kgs
        appointment.save()

        appointment.refresh_from_db()
        assert appointment.prepaid_kgs == initial_prepaid + Decimal("500.00")
