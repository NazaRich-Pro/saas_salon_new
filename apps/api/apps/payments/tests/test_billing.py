"""Tests for billing system"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from apps.payments.billing_service import BillingError, BillingService
from apps.payments.models import SaaSSubscription
from apps.tenants.models import Tenant


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(
        slug="test-billing", name="Test Salon", type="SALON", status="TRIAL", seats=3
    )


@pytest.fixture
def subscription(db, tenant):
    return SaaSSubscription.objects.create(
        tenant=tenant,
        plan="SALON",
        seats=3,
        status="TRIAL",
        period_start=date.today(),
        period_end=date.today() + timedelta(days=14),
        monthly_price_kgs=Decimal("1500.00"),
    )


@pytest.mark.django_db
class TestBillingService:
    """Test billing service"""

    def test_calculate_monthly_price_solo(self):
        """Test monthly price calculation for solo"""
        price = BillingService.calculate_monthly_price("SOLO", 1)
        assert price == Decimal("500.00")

    def test_calculate_monthly_price_salon(self):
        """Test monthly price calculation for salon"""
        price = BillingService.calculate_monthly_price("SALON", 3)
        assert price == Decimal("1500.00")  # 500 × 3

        price = BillingService.calculate_monthly_price("SALON", 5)
        assert price == Decimal("2500.00")  # 500 × 5

    def test_get_billing_status_trial(self, tenant, subscription):
        """Test billing status during trial"""
        service = BillingService(tenant)
        status = service.get_billing_status()

        assert status["status"] == "TRIAL"
        assert status["is_trial"] is True
        assert status["booking_blocked"] is False
        assert status["admin_access"] is True

    def test_get_billing_status_grace(self, tenant, subscription):
        """Test billing status during grace period"""
        # Move to grace
        subscription.status = "GRACE"
        subscription.grace_until = date.today() + timedelta(days=5)
        subscription.save()

        service = BillingService(tenant)
        status = service.get_billing_status()

        assert status["status"] == "GRACE"
        assert status["is_grace"] is True
        assert status["booking_blocked"] is False  # Still within grace
        assert status["admin_access"] is True

    def test_get_billing_status_suspended(self, tenant, subscription):
        """Test billing status when suspended"""
        subscription.status = "SUSPENDED"
        subscription.save()

        service = BillingService(tenant)
        status = service.get_billing_status()

        assert status["status"] == "SUSPENDED"
        assert status["is_suspended"] is True
        assert status["booking_blocked"] is True  # Booking blocked
        assert status["admin_access"] is True  # Admin still accessible

    def test_update_seats(self, tenant, subscription):
        """Test updating seat count"""
        service = BillingService(tenant)

        # Update from 3 to 5 seats
        updated = service.update_seats(5)

        assert updated.seats == 5
        assert updated.monthly_price_kgs == Decimal("2500.00")  # 500 × 5

        # Check tenant updated too
        tenant.refresh_from_db()
        assert tenant.seats == 5

    def test_cannot_exceed_max_seats(self, tenant, subscription):
        """Test cannot set seats above plan limit"""
        service = BillingService(tenant)

        # SALON max is 50
        with pytest.raises(BillingError):
            service.update_seats(51)

    def test_cannot_set_zero_seats(self, tenant, subscription):
        """Test cannot set seats to 0"""
        service = BillingService(tenant)

        with pytest.raises(BillingError):
            service.update_seats(0)

    def test_mark_invoice_paid(self, tenant, subscription):
        """Test marking invoice as paid"""
        service = BillingService(tenant)

        # Mark as paid
        updated = service.mark_invoice_paid()

        assert updated.status == "ACTIVE"
        assert updated.last_payment_date is not None
        assert updated.grace_until is None

        # Period should be extended
        assert updated.period_end > subscription.period_end

        # Tenant status updated
        tenant.refresh_from_db()
        assert tenant.status == "ACTIVE"


@pytest.mark.django_db
class TestFeatureFlags:
    """Test feature flags per plan"""

    def test_solo_features(self):
        """Test features for SOLO plan"""
        features = BillingService.PLANS["SOLO"]["features"]

        assert features["max_seats"] == 1
        assert features["max_bookings_per_day"] == 20
        assert features["sms_enabled"] is False
        assert features["telegram_enabled"] is False
        assert features["white_label"] is False

    def test_salon_features(self):
        """Test features for SALON plan"""
        features = BillingService.PLANS["SALON"]["features"]

        assert features["max_seats"] == 50
        assert features["max_bookings_per_day"] == 200
        assert features["sms_enabled"] is True
        assert features["telegram_enabled"] is True
        assert features["white_label"] is True
        assert features["api_access"] is True

    def test_get_features_for_tenant(self, tenant, subscription):
        """Test getting features for specific tenant"""
        service = BillingService(tenant)
        features = service.get_features()

        assert features["plan"] == "SALON"
        assert features["seats"] == 3
        assert features["sms_enabled"] is True

    def test_check_feature(self, tenant, subscription):
        """Test checking individual feature"""
        service = BillingService(tenant)

        assert service.check_feature("sms_enabled") is True
        assert service.check_feature("white_label") is True


@pytest.mark.django_db
class TestBookingBlocking:
    """Test booking blocking logic"""

    def test_can_book_during_trial(self, tenant, subscription):
        """Test bookings allowed during trial"""
        service = BillingService(tenant)

        can_book, reason = service.can_create_booking()

        assert can_book is True
        assert reason is None

    def test_can_book_when_active(self, tenant, subscription):
        """Test bookings allowed when active"""
        subscription.status = "ACTIVE"
        subscription.save()

        service = BillingService(tenant)
        can_book, reason = service.can_create_booking()

        assert can_book is True

    def test_cannot_book_when_suspended(self, tenant, subscription):
        """Test bookings blocked when suspended"""
        subscription.status = "SUSPENDED"
        subscription.save()

        service = BillingService(tenant)
        can_book, reason = service.can_create_booking()

        assert can_book is False
        assert "приостановлена" in reason.lower()

    def test_admin_access_always_allowed(self, tenant, subscription):
        """Test admin access never blocked"""
        # Even when suspended
        subscription.status = "SUSPENDED"
        subscription.save()

        service = BillingService(tenant)

        # Admin access check
        assert service.can_access_feature("admin_access") is True


@pytest.mark.django_db
class TestInvoiceGeneration:
    """Test invoice data generation"""

    def test_generate_invoice_data(self, tenant, subscription):
        """Test invoice data generation"""
        service = BillingService(tenant)
        invoice = service.generate_invoice_data()

        assert invoice["tenant_name"] == "Test Salon"
        assert invoice["plan"] == "SALON"
        assert invoice["seats"] == 3
        assert invoice["amount_kgs"] == "1500.00"
        assert invoice["currency"] == "KGS"
        assert "invoice_number" in invoice
        assert invoice["invoice_number"].startswith("INV-")


@pytest.mark.django_db
class TestSubscriptionLifecycle:
    """Test subscription lifecycle"""

    def test_trial_to_grace_transition(self, tenant, subscription):
        """Test trial expiry moves to grace"""
        # Expire trial
        subscription.period_end = date.today() - timedelta(days=1)
        subscription.save()

        # In real system, Celery task would do this
        subscription.status = "GRACE"
        subscription.grace_until = date.today() + timedelta(days=7)
        subscription.save()

        service = BillingService(tenant)
        status_info = service.get_billing_status()

        assert status_info["is_grace"] is True
        assert status_info["days_remaining"] == 7

    def test_grace_to_suspended_transition(self, tenant, subscription):
        """Test grace expiry leads to suspension"""
        subscription.status = "GRACE"
        subscription.grace_until = date.today() - timedelta(days=1)  # Expired
        subscription.save()

        service = BillingService(tenant)
        status_info = service.get_billing_status()

        # Booking should be blocked
        assert status_info["booking_blocked"] is True

    def test_reactivation_after_payment(self, tenant, subscription):
        """Test reactivation after payment"""
        # Start from suspended
        subscription.status = "SUSPENDED"
        subscription.save()

        tenant.status = "SUSPENDED"
        tenant.save()

        # Mark as paid
        service = BillingService(tenant)
        updated = service.mark_invoice_paid()

        # Should be active again
        assert updated.status == "ACTIVE"

        tenant.refresh_from_db()
        assert tenant.status == "ACTIVE"

        # Booking should work
        can_book, _ = service.can_create_booking()
        assert can_book is True
