"""Tenant onboarding service"""
import secrets
import string
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict

from apps.booking.models import Location, Schedule, Service, ServiceCategory, Staff
from apps.payments.models import LoyaltyRule, SaaSSubscription
from apps.users.models import User
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from .models import Membership, Tenant


class OnboardingError(Exception):
    """Exception raised during onboarding"""

    pass


class OnboardingService:
    """Service for automated tenant onboarding"""

    @staticmethod
    def generate_unique_slug(base_name: str) -> str:
        """
        Generate unique slug for tenant

        Args:
            base_name: Base name for slug

        Returns:
            Unique slug string
        """
        # Create base slug
        base_slug = slugify(base_name, allow_unicode=False)

        # Transliterate Cyrillic if needed
        base_slug = OnboardingService._transliterate(base_slug)

        # Ensure it's valid (alphanumeric and hyphens only)
        base_slug = "".join(c for c in base_slug if c.isalnum() or c == "-")
        base_slug = base_slug[:50]  # Max 50 chars

        # Check uniqueness
        slug = base_slug
        counter = 1

        while Tenant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    @staticmethod
    def _transliterate(text: str) -> str:
        """
        Simple transliteration for Cyrillic to Latin
        """
        cyrillic_to_latin = {
            "а": "a",
            "б": "b",
            "в": "v",
            "г": "g",
            "д": "d",
            "е": "e",
            "ё": "yo",
            "ж": "zh",
            "з": "z",
            "и": "i",
            "й": "y",
            "к": "k",
            "л": "l",
            "м": "m",
            "н": "n",
            "о": "o",
            "п": "p",
            "р": "r",
            "с": "s",
            "т": "t",
            "у": "u",
            "ф": "f",
            "х": "h",
            "ц": "ts",
            "ч": "ch",
            "ш": "sh",
            "щ": "sch",
            "ъ": "",
            "ы": "y",
            "ь": "",
            "э": "e",
            "ю": "yu",
            "я": "ya",
        }

        result = []
        for char in text.lower():
            result.append(cyrillic_to_latin.get(char, char))

        return "".join(result)

    @staticmethod
    def generate_auto_login_token() -> str:
        """
        Generate secure auto-login token

        Returns:
            Token string (64 characters)
        """
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(64))

    @transaction.atomic
    def create_salon(
        self,
        salon_name: str,
        owner_name: str,
        email: str,
        phone: str,
        password: str,
        seats: int = 1,
    ) -> Dict:
        """
        Create new salon tenant with full setup

        Args:
            salon_name: Salon name
            owner_name: Owner's name
            email: Owner's email
            phone: Owner's phone
            password: Owner's password
            seats: Number of seats (masters)

        Returns:
            Dict with:
                - tenant: Tenant instance
                - user: User instance
                - tenant_url: URL with auto-login token
                - auto_login_token: Token for auto-login

        Raises:
            OnboardingError: If creation fails
        """
        # Validate email uniqueness
        if User.objects.filter(email=email).exists():
            raise OnboardingError("Email уже используется")

        # Generate slug
        slug = self.generate_unique_slug(salon_name)

        # Create tenant
        tenant = Tenant.objects.create(
            slug=slug,
            name=salon_name,
            type="SALON",
            plan="basic",
            seats=seats,
            status="TRIAL",
            trial_ends=timezone.now().date() + timedelta(days=14),
            settings={
                "theme": {"primary_color": "#3B82F6", "secondary_color": "#10B981"},
                "language": "ru",
                "timezone": "Asia/Bishkek",
            },
        )

        # Create user
        user = User.objects.create_user(email=email, password=password)
        user.phone = phone
        user.save()

        # Create membership (owner is SALON_ADMIN)
        Membership.objects.create(
            user=user, tenant=tenant, role="SALON_ADMIN", is_active=True
        )

        # Create subscription
        SaaSSubscription.objects.create(
            tenant=tenant,
            plan="SALON",
            seats=seats,
            status="TRIAL",
            period_start=date.today(),
            period_end=date.today() + timedelta(days=30),
            monthly_price_kgs=Decimal(str(500 * seats)),
        )

        # Create default location
        Location.objects.create(
            tenant=tenant,
            name="Главный офис",
            timezone="Asia/Bishkek",
            address="",
            is_active=True,
        )

        # Create loyalty rule
        LoyaltyRule.objects.create(
            tenant=tenant,
            earn_per_100_kgs=1,
            redeem_rate=Decimal("1.00"),
            min_points_to_redeem=100,
            is_active=True,
        )

        # Create sample service categories
        category_hair = ServiceCategory.objects.create(
            tenant=tenant, name="Стрижки", sort_order=1
        )

        category_color = ServiceCategory.objects.create(
            tenant=tenant, name="Окрашивание", sort_order=2
        )

        # Create sample services
        Service.objects.create(
            tenant=tenant,
            category=category_hair,
            name="Женская стрижка",
            duration_min=60,
            price_kgs=Decimal("800.00"),
            buffer_before_min=5,
            buffer_after_min=5,
        )

        Service.objects.create(
            tenant=tenant,
            category=category_hair,
            name="Мужская стрижка",
            duration_min=30,
            price_kgs=Decimal("500.00"),
            buffer_before_min=5,
            buffer_after_min=5,
        )

        # Generate auto-login token
        auto_login_token = self.generate_auto_login_token()

        # Store token in cache (valid for 1 hour)
        from django.core.cache import cache

        cache_key = f"auto_login_token:{auto_login_token}"
        cache.set(
            cache_key, {"user_id": str(user.id), "tenant_id": str(tenant.id)}, 3600
        )  # 1 hour

        # Build tenant URL
        tenant_url = (
            f"https://{slug}.saas.akylman.online/welcome?token={auto_login_token}"
        )

        return {
            "tenant": tenant,
            "user": user,
            "tenant_url": tenant_url,
            "auto_login_token": auto_login_token,
        }

    @transaction.atomic
    def create_solo_master(
        self,
        master_name: str,
        email: str,
        phone: str,
        password: str,
        specialty: str = "",
    ) -> Dict:
        """
        Create new solo master tenant

        Args:
            master_name: Master's name
            email: Master's email
            phone: Master's phone
            password: Master's password
            specialty: Master's specialty

        Returns:
            Dict with tenant, user, tenant_url, auto_login_token

        Raises:
            OnboardingError: If creation fails
        """
        # Validate email uniqueness
        if User.objects.filter(email=email).exists():
            raise OnboardingError("Email уже используется")

        # Generate slug
        slug = self.generate_unique_slug(master_name)

        # Create tenant
        tenant = Tenant.objects.create(
            slug=slug,
            name=f"Мастер {master_name}",
            type="SOLO",
            plan="basic",
            seats=1,
            status="TRIAL",
            trial_ends=timezone.now().date() + timedelta(days=14),
            settings={
                "theme": {"primary_color": "#8B5CF6", "secondary_color": "#EC4899"},
                "language": "ru",
                "timezone": "Asia/Bishkek",
            },
        )

        # Create user
        user = User.objects.create_user(email=email, password=password)
        user.phone = phone
        user.save()

        # Create membership (solo master is also admin)
        Membership.objects.create(
            user=user, tenant=tenant, role="SALON_ADMIN", is_active=True
        )

        # Create subscription
        SaaSSubscription.objects.create(
            tenant=tenant,
            plan="SOLO",
            seats=1,
            status="TRIAL",
            period_start=date.today(),
            period_end=date.today() + timedelta(days=30),
            monthly_price_kgs=Decimal("500.00"),
        )

        # Create location (master's studio)
        Location.objects.create(
            tenant=tenant,
            name="Домашняя студия",
            timezone="Asia/Bishkek",
            is_active=True,
        )

        # Create loyalty rule
        LoyaltyRule.objects.create(
            tenant=tenant,
            earn_per_100_kgs=1,
            redeem_rate=Decimal("1.00"),
            min_points_to_redeem=100,
            is_active=True,
        )

        # Create service category
        category = ServiceCategory.objects.create(
            tenant=tenant, name="Мои услуги", sort_order=1
        )

        # Create sample service
        Service.objects.create(
            tenant=tenant,
            category=category,
            name="Консультация",
            duration_min=30,
            price_kgs=Decimal("500.00"),
            buffer_before_min=10,
            buffer_after_min=10,
        )

        # Create staff profile for the master
        staff = Staff.objects.create(
            tenant=tenant,
            user=user,
            name=master_name,
            title=specialty or "Мастер",
            phone=phone,
            email=email,
            is_active=True,
        )

        # Create default schedule
        Schedule.objects.create(
            tenant=tenant,
            staff=staff,
            rules={
                "monday": {
                    "enabled": True,
                    "slots": [{"start": "10:00", "end": "19:00"}],
                },
                "tuesday": {
                    "enabled": True,
                    "slots": [{"start": "10:00", "end": "19:00"}],
                },
                "wednesday": {
                    "enabled": True,
                    "slots": [{"start": "10:00", "end": "19:00"}],
                },
                "thursday": {
                    "enabled": True,
                    "slots": [{"start": "10:00", "end": "19:00"}],
                },
                "friday": {
                    "enabled": True,
                    "slots": [{"start": "10:00", "end": "20:00"}],
                },
                "saturday": {
                    "enabled": True,
                    "slots": [{"start": "11:00", "end": "18:00"}],
                },
                "sunday": {"enabled": False, "slots": []},
            },
            is_active=True,
        )

        # Generate auto-login token
        auto_login_token = self.generate_auto_login_token()

        # Store token in cache
        from django.core.cache import cache

        cache_key = f"auto_login_token:{auto_login_token}"
        cache.set(
            cache_key, {"user_id": str(user.id), "tenant_id": str(tenant.id)}, 3600
        )

        # Build tenant URL
        tenant_url = (
            f"https://{slug}.saas.akylman.online/welcome?token={auto_login_token}"
        )

        return {
            "tenant": tenant,
            "user": user,
            "tenant_url": tenant_url,
            "auto_login_token": auto_login_token,
        }
