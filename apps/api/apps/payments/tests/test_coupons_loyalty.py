"""Tests for coupons and loyalty system"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from apps.booking.models import Appointment, Customer, Service, ServiceCategory, Staff
from apps.payments.birthday_service import BirthdayService
from apps.payments.coupon_service import CouponApplicationError, CouponService
from apps.payments.loyalty_service import LoyaltyService, LoyaltyServiceError
from apps.payments.models import Coupon, LoyaltyRule
from apps.tenants.models import Tenant
from django.utils import timezone


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(
        slug="test-loyalty", name="Test Salon", type="SALON", status="ACTIVE"
    )


@pytest.fixture
def customer(db, tenant):
    return Customer.objects.create(
        tenant=tenant,
        name="Test Customer",
        phone="+996700111111",
        email="customer@test.com",
        loyalty_points=200,
    )


@pytest.fixture
def service(db, tenant):
    category = ServiceCategory.objects.create(tenant=tenant, name="Test Category")
    return Service.objects.create(
        tenant=tenant,
        category=category,
        name="Test Service",
        duration_min=60,
        price_kgs=Decimal("1000.00"),
    )


@pytest.fixture
def loyalty_rule(db, tenant):
    return LoyaltyRule.objects.create(
        tenant=tenant,
        earn_per_100_kgs=1,
        redeem_rate=Decimal("1.00"),
        min_points_to_redeem=100,
        is_active=True,
    )


@pytest.mark.django_db
class TestCouponService:
    """Test coupon validation and application"""

    def test_validate_percentage_coupon(self, tenant):
        """Test percentage coupon validation"""
        coupon = Coupon.objects.create(
            tenant=tenant,
            code="TEST20",
            kind="PERCENT",
            value=Decimal("20.00"),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            is_active=True,
        )

        service = CouponService(tenant)
        result = service.validate_and_apply(
            code="TEST20", appointment_total=Decimal("1000.00")
        )

        assert result["applied"] is True
        assert result["discount_kgs"] == Decimal("200.00")  # 20% of 1000
        assert result["final_amount_kgs"] == Decimal("800.00")

    def test_validate_fixed_coupon(self, tenant):
        """Test fixed amount coupon"""
        Coupon.objects.create(
            tenant=tenant,
            code="FIXED500",
            kind="FIXED",
            value=Decimal("500.00"),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            is_active=True,
        )

        service = CouponService(tenant)
        result = service.validate_and_apply(
            code="FIXED500", appointment_total=Decimal("2000.00")
        )

        assert result["discount_kgs"] == Decimal("500.00")
        assert result["final_amount_kgs"] == Decimal("1500.00")

    def test_expired_coupon_fails(self, tenant):
        """Test expired coupon is rejected"""
        Coupon.objects.create(
            tenant=tenant,
            code="EXPIRED",
            kind="PERCENT",
            value=Decimal("50.00"),
            valid_from=timezone.now() - timedelta(days=60),
            valid_to=timezone.now() - timedelta(days=30),  # Expired
            is_active=True,
        )

        service = CouponService(tenant)

        with pytest.raises(CouponApplicationError) as exc:
            service.validate_and_apply(
                code="EXPIRED", appointment_total=Decimal("1000.00")
            )

        assert "истек" in str(exc.value).lower()

    def test_usage_limit_enforced(self, tenant):
        """Test coupon usage limit is enforced"""
        coupon = Coupon.objects.create(
            tenant=tenant,
            code="LIMITED",
            kind="PERCENT",
            value=Decimal("10.00"),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            max_uses=5,
            uses_count=5,  # Already used 5 times
            is_active=True,
        )

        service = CouponService(tenant)

        with pytest.raises(CouponApplicationError) as exc:
            service.validate_and_apply(
                code="LIMITED", appointment_total=Decimal("1000.00")
            )

        assert "лимит" in str(exc.value).lower()

    def test_minimum_amount_rule(self, tenant):
        """Test coupon with minimum amount rule"""
        Coupon.objects.create(
            tenant=tenant,
            code="MIN1000",
            kind="PERCENT",
            value=Decimal("15.00"),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            rules={"min_amount": 1000},
            is_active=True,
        )

        service = CouponService(tenant)

        # Below minimum - should fail
        with pytest.raises(CouponApplicationError):
            service.validate_and_apply(
                code="MIN1000", appointment_total=Decimal("500.00")
            )

        # Above minimum - should succeed
        result = service.validate_and_apply(
            code="MIN1000", appointment_total=Decimal("1500.00")
        )

        assert result["applied"] is True


@pytest.mark.django_db
class TestLoyaltyService:
    """Test loyalty points system"""

    def test_calculate_points_earned(self, tenant, loyalty_rule):
        """Test loyalty points calculation"""
        service = LoyaltyService(tenant)

        # 500 KGS = 5 points (1 per 100)
        points = service.calculate_points_earned(Decimal("500.00"))
        assert points == 5

        # 1234 KGS = 12 points (floor division)
        points = service.calculate_points_earned(Decimal("1234.00"))
        assert points == 12

        # 50 KGS = 0 points (below 100)
        points = service.calculate_points_earned(Decimal("50.00"))
        assert points == 0

    def test_award_points(self, tenant, customer, loyalty_rule):
        """Test awarding points to customer"""
        initial_points = customer.loyalty_points

        service = LoyaltyService(tenant)
        points_awarded = service.award_points(customer, Decimal("1000.00"))

        assert points_awarded == 10

        customer.refresh_from_db()
        assert customer.loyalty_points == initial_points + 10

    def test_calculate_discount_from_points(self, tenant, loyalty_rule):
        """Test calculating discount from points"""
        service = LoyaltyService(tenant)

        # 100 points = 100 KGS (1:1 rate)
        discount = service.calculate_discount_from_points(100)
        assert discount == Decimal("100.00")

        # 250 points = 250 KGS
        discount = service.calculate_discount_from_points(250)
        assert discount == Decimal("250.00")

    def test_redeem_points(self, tenant, customer, loyalty_rule):
        """Test redeeming loyalty points"""
        service = LoyaltyService(tenant)

        # Customer has 200 points, redeem 150
        result = service.redeem_points(
            customer=customer,
            points_to_redeem=150,
            appointment_total=Decimal("2000.00"),
        )

        assert result["points_redeemed"] == 150
        assert result["discount_kgs"] == Decimal("150.00")
        assert result["points_remaining"] == 50

        # Check customer points updated
        customer.refresh_from_db()
        assert customer.loyalty_points == 50

    def test_cannot_redeem_below_minimum(self, tenant, customer, loyalty_rule):
        """Test cannot redeem below minimum points"""
        service = LoyaltyService(tenant)

        # Minimum is 100, trying to redeem 50
        with pytest.raises(LoyaltyServiceError) as exc:
            service.redeem_points(
                customer=customer,
                points_to_redeem=50,
                appointment_total=Decimal("1000.00"),
            )

        assert "минимум" in str(exc.value).lower()

    def test_cannot_redeem_more_than_available(self, tenant, customer, loyalty_rule):
        """Test cannot redeem more points than customer has"""
        service = LoyaltyService(tenant)

        # Customer has 200, trying to redeem 300
        with pytest.raises(LoyaltyServiceError) as exc:
            service.redeem_points(
                customer=customer,
                points_to_redeem=300,
                appointment_total=Decimal("5000.00"),
            )

        assert "недостаточно" in str(exc.value).lower()

    def test_discount_capped_at_total(self, tenant, customer, loyalty_rule):
        """Test discount doesn't exceed appointment total"""
        service = LoyaltyService(tenant)

        # Customer wants to use 200 points (= 200 KGS discount)
        # But appointment is only 150 KGS
        result = service.redeem_points(
            customer=customer, points_to_redeem=200, appointment_total=Decimal("150.00")
        )

        # Should only redeem 150 points (matching the total)
        assert result["points_redeemed"] == 150
        assert result["discount_kgs"] == Decimal("150.00")


@pytest.mark.django_db
class TestBirthdayService:
    """Test birthday campaign system"""

    def test_get_todays_birthdays(self, tenant):
        """Test finding customers with birthday today"""
        today = date.today()

        # Customer with birthday today
        Customer.objects.create(
            tenant=tenant,
            name="Birthday Customer",
            phone="+996700999991",
            email="birthday@test.com",
            date_of_birth=date(1990, today.month, today.day),
        )

        # Customer with different birthday
        Customer.objects.create(
            tenant=tenant,
            name="Other Customer",
            phone="+996700999992",
            email="other@test.com",
            date_of_birth=date(1990, 1, 1),
        )

        service = BirthdayService(tenant)
        birthdays = service.get_todays_birthdays()

        assert len(birthdays) == 1
        assert birthdays[0].name == "Birthday Customer"

    def test_create_birthday_coupon(self, tenant):
        """Test creating birthday coupon"""
        customer = Customer.objects.create(
            tenant=tenant,
            name="Birthday Customer",
            phone="+996700123456",
            email="birthday@test.com",
            date_of_birth=date(1990, 10, 12),
        )

        service = BirthdayService(tenant)
        coupon = service.create_birthday_coupon(customer)

        assert coupon is not None
        assert coupon.code.startswith("BIRTHDAY-")
        assert coupon.kind == "PERCENT"
        assert coupon.value == Decimal("20.00")  # Default 20%
        assert coupon.max_uses == 1
        assert coupon.max_uses_per_customer == 1

    def test_prepare_birthday_greeting(self, tenant, customer):
        """Test preparing birthday greeting data"""
        coupon = Coupon.objects.create(
            tenant=tenant,
            code="BIRTHDAY-TEST",
            kind="PERCENT",
            value=Decimal("20.00"),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            is_active=True,
        )

        service = BirthdayService(tenant)
        greeting = service.prepare_birthday_greeting(customer, coupon)

        assert greeting["customer_name"] == customer.name
        assert greeting["customer_email"] == customer.email
        assert greeting["coupon_code"] == "BIRTHDAY-TEST"
        assert greeting["discount_percent"] == "20.00"
        assert "valid_until" in greeting
        assert "tenant_url" in greeting

    def test_upcoming_birthdays(self, tenant):
        """Test getting upcoming birthdays"""
        today = date.today()
        in_3_days = today + timedelta(days=3)
        in_5_days = today + timedelta(days=5)

        # Customer with birthday in 3 days
        Customer.objects.create(
            tenant=tenant,
            name="Soon Birthday 1",
            phone="+996700111111",
            email="soon1@test.com",
            date_of_birth=date(1990, in_3_days.month, in_3_days.day),
        )

        # Customer with birthday in 5 days
        Customer.objects.create(
            tenant=tenant,
            name="Soon Birthday 2",
            phone="+996700222222",
            email="soon2@test.com",
            date_of_birth=date(1985, in_5_days.month, in_5_days.day),
        )

        service = BirthdayService(tenant)
        upcoming = service.get_upcoming_birthdays(days_ahead=7)

        assert len(upcoming) == 2


@pytest.mark.django_db
class TestCouponRules:
    """Test coupon rule evaluation"""

    def test_day_of_week_rule(self, tenant):
        """Test coupon restricted to specific days"""
        # Coupon only valid on Monday and Tuesday
        coupon = Coupon.objects.create(
            tenant=tenant,
            code="WEEKDAY",
            kind="PERCENT",
            value=Decimal("10.00"),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=365),
            rules={"days": ["monday", "tuesday"]},
            is_active=True,
        )

        service = CouponService(tenant)

        # Find next Monday
        today = timezone.now()
        days_ahead = (0 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        next_monday = today + timedelta(days=days_ahead)

        # Should work on Monday
        result = service.validate_and_apply(
            code="WEEKDAY",
            appointment_total=Decimal("1000.00"),
            appointment_datetime=next_monday,
        )

        assert result["applied"] is True

        # Find next Friday (should fail)
        days_to_friday = (4 - today.weekday()) % 7
        if days_to_friday == 0:
            days_to_friday = 7
        next_friday = today + timedelta(days=days_to_friday)

        with pytest.raises(CouponApplicationError):
            service.validate_and_apply(
                code="WEEKDAY",
                appointment_total=Decimal("1000.00"),
                appointment_datetime=next_friday,
            )

    def test_time_range_rule(self, tenant):
        """Test coupon restricted to time range"""
        # Coupon only valid 09:00-12:00
        Coupon.objects.create(
            tenant=tenant,
            code="MORNING",
            kind="PERCENT",
            value=Decimal("15.00"),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            rules={"time_from": "09:00", "time_to": "12:00"},
            is_active=True,
        )

        service = CouponService(tenant)

        # 10:00 - should work
        morning_time = timezone.now().replace(hour=10, minute=0)
        result = service.validate_and_apply(
            code="MORNING",
            appointment_total=Decimal("1000.00"),
            appointment_datetime=morning_time,
        )

        assert result["applied"] is True

        # 14:00 - should fail
        afternoon_time = timezone.now().replace(hour=14, minute=0)

        with pytest.raises(CouponApplicationError):
            service.validate_and_apply(
                code="MORNING",
                appointment_total=Decimal("1000.00"),
                appointment_datetime=afternoon_time,
            )


@pytest.mark.django_db
class TestLoyaltyIntegration:
    """Test loyalty points integration with appointments"""

    def test_points_earned_on_completion(self, tenant, customer, loyalty_rule):
        """Test points are earned when appointment is completed"""
        # Customer completes appointment worth 1500 KGS
        service = LoyaltyService(tenant)

        initial_points = customer.loyalty_points
        points_earned = service.award_points(customer, Decimal("1500.00"))

        # Should earn 15 points (1 per 100 KGS)
        assert points_earned == 15

        customer.refresh_from_db()
        assert customer.loyalty_points == initial_points + 15

    def test_full_loyalty_cycle(self, tenant, customer, loyalty_rule):
        """Test full cycle: earn points → redeem for discount"""
        service = LoyaltyService(tenant)

        # 1. Customer spends 2000 KGS, earns points
        points_earned = service.award_points(customer, Decimal("2000.00"))
        assert points_earned == 20

        customer.refresh_from_db()
        # Initial 200 + 20 = 220 points
        assert customer.loyalty_points == 220

        # 2. Customer redeems 150 points for discount
        result = service.redeem_points(
            customer=customer,
            points_to_redeem=150,
            appointment_total=Decimal("1000.00"),
        )

        assert result["discount_kgs"] == Decimal("150.00")

        customer.refresh_from_db()
        # 220 - 150 = 70 points remaining
        assert customer.loyalty_points == 70


@pytest.mark.django_db
class TestCombinedDiscounts:
    """Test combining coupons and loyalty points"""

    def test_both_coupon_and_points(self, tenant, customer, loyalty_rule):
        """Test applying both coupon and loyalty points"""
        # Create appointment
        staff = Staff.objects.create(tenant=tenant, name="Staff")

        start_at = timezone.now() + timedelta(hours=2)
        appointment = Appointment.objects.create(
            tenant=tenant,
            customer=customer,
            staff=staff,
            start_at=start_at,
            end_at=start_at + timedelta(hours=1),
            total_price_kgs=Decimal("2000.00"),
            status="CONFIRMED",
        )

        # Apply coupon (20% off 2000 = 400 KGS discount)
        Coupon.objects.create(
            tenant=tenant,
            code="COMBO20",
            kind="PERCENT",
            value=Decimal("20.00"),
            valid_from=timezone.now(),
            valid_to=timezone.now() + timedelta(days=30),
            is_active=True,
        )

        coupon_service = CouponService(tenant)
        coupon_discount = coupon_service.apply_coupon_to_appointment(
            appointment, "COMBO20"
        )

        assert coupon_discount == Decimal("400.00")

        appointment.refresh_from_db()
        assert appointment.discount_kgs == Decimal("400.00")

        # New total after coupon: 2000 - 400 = 1600 KGS
        # Now redeem 100 loyalty points
        loyalty_service = LoyaltyService(tenant)
        result = loyalty_service.redeem_points(
            customer=customer,
            points_to_redeem=100,
            appointment_total=Decimal("1600.00"),
        )

        # Additional discount of 100 KGS
        appointment.discount_kgs += result["discount_kgs"]
        appointment.save()

        # Total discount: 400 (coupon) + 100 (loyalty) = 500 KGS
        assert appointment.discount_kgs == Decimal("500.00")

        # Final price: 2000 - 500 = 1500 KGS
        final_price = appointment.total_price_kgs - appointment.discount_kgs
        assert final_price == Decimal("1500.00")
