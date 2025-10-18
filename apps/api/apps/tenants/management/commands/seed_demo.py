"""
Management command to seed demo data
Usage: python manage.py seed_demo
"""
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from apps.booking.models import (
    Appointment,
    AppointmentService,
    Customer,
    Location,
    Schedule,
    Service,
    ServiceCategory,
    Staff,
    StaffService,
)
from apps.notifications.models import NotificationTemplate
from apps.payments.models import Coupon, LoyaltyRule, SaaSSubscription
from apps.tenants.models import Membership, Tenant, TenantDomain
from apps.users.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Seed demo data for BeautyHub SaaS"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing demo data before seeding",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting demo data seeding..."))

        if options["flush"]:
            self.stdout.write("Flushing existing demo data...")
            self._flush_demo_data()

        # Create superadmin
        superadmin = self._create_superadmin()

        # Create demo salon tenant
        demo_salon = self._create_demo_salon()

        # Create demo solo master
        demo_solo = self._create_demo_solo()

        self.stdout.write(self.style.SUCCESS("\n✅ Demo data seeding completed!"))
        self.stdout.write(self.style.SUCCESS("\nAccess Points:"))
        self.stdout.write(f"  • Main Platform: https://saas.akylman.online")
        self.stdout.write(f"  • Demo Salon: https://demo-salon.saas.akylman.online")
        self.stdout.write(f"  • Demo Solo: https://demo-solo.saas.akylman.online")
        self.stdout.write(f"\nSuperadmin: admin@saas.akylman.online / admin123")
        self.stdout.write(f"Demo Salon Admin: salon@demo.com / demo123")
        self.stdout.write(f"Demo Solo Master: solo@demo.com / demo123")

    def _flush_demo_data(self):
        """Delete demo data"""
        Tenant.objects.filter(slug__in=["demo-salon", "demo-solo"]).delete()
        User.objects.filter(
            email__in=["admin@saas.akylman.online", "salon@demo.com", "solo@demo.com"]
        ).delete()

    def _create_superadmin(self):
        """Create platform superadmin"""
        self.stdout.write("Creating superadmin...")

        superadmin, created = User.objects.get_or_create(
            email="admin@saas.akylman.online",
            defaults={
                "is_superadmin": True,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            superadmin.set_password("admin123")
            superadmin.save()
            self.stdout.write(self.style.SUCCESS("  ✓ Superadmin created"))
        else:
            self.stdout.write("  ℹ Superadmin already exists")

        return superadmin

    def _create_demo_salon(self):
        """Create demo salon with full setup"""
        self.stdout.write("\nCreating demo salon...")

        # Create tenant
        salon, created = Tenant.objects.get_or_create(
            slug="demo-salon",
            defaults={
                "name": "Демо Салон Красоты",
                "type": "SALON",
                "plan": "basic",
                "seats": 3,
                "status": "TRIAL",
                "trial_ends": (timezone.now() + timedelta(days=14)).date(),
                "settings": {
                    "theme": {"primary_color": "#FF6B6B", "secondary_color": "#4ECDC4"},
                    "language": "ru",
                    "timezone": "Asia/Bishkek",
                },
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS("  ✓ Salon tenant created"))

        # Create salon admin user
        admin_user, user_created = User.objects.get_or_create(
            email="salon@demo.com", defaults={}
        )

        if user_created:
            admin_user.set_password("demo123")
            admin_user.save()

        # Create membership
        Membership.objects.get_or_create(
            user=admin_user,
            tenant=salon,
            defaults={"role": "SALON_ADMIN", "is_active": True},
        )

        # Create subscription
        SaaSSubscription.objects.get_or_create(
            tenant=salon,
            defaults={
                "plan": "SALON",
                "seats": 3,
                "status": "TRIAL",
                "period_start": date.today(),
                "period_end": (date.today() + timedelta(days=30)),
                "monthly_price_kgs": Decimal("1500.00"),
            },
        )

        # Create loyalty rule
        LoyaltyRule.objects.get_or_create(
            tenant=salon,
            defaults={
                "earn_per_100_kgs": 1,
                "redeem_rate": Decimal("1.00"),
                "min_points_to_redeem": 100,
                "is_active": True,
            },
        )

        # Create location
        location, _ = Location.objects.get_or_create(
            tenant=salon,
            name="Главный офис",
            defaults={
                "timezone": "Asia/Bishkek",
                "address": "ул. Чуй 123, Бишкек, Кыргызстан",
                "phone": "+996700123456",
                "email": "info@demo-salon.com",
                "is_active": True,
            },
        )

        # Create service categories
        category_haircut, _ = ServiceCategory.objects.get_or_create(
            tenant=salon, name="Стрижки", defaults={"sort_order": 1, "is_active": True}
        )

        category_coloring, _ = ServiceCategory.objects.get_or_create(
            tenant=salon,
            name="Окрашивание",
            defaults={"sort_order": 2, "is_active": True},
        )

        category_nails, _ = ServiceCategory.objects.get_or_create(
            tenant=salon,
            name="Маникюр/Педикюр",
            defaults={"sort_order": 3, "is_active": True},
        )

        # Create services
        services = [
            ("Женская стрижка", category_haircut, 60, 800),
            ("Мужская стрижка", category_haircut, 30, 500),
            ("Детская стрижка", category_haircut, 30, 400),
            ("Окрашивание волос", category_coloring, 120, 2500),
            ("Мелирование", category_coloring, 180, 3500),
            ("Маникюр", category_nails, 60, 600),
            ("Педикюр", category_nails, 90, 800),
            ("Наращивание ногтей", category_nails, 120, 1200),
        ]

        service_objects = []
        for name, category, duration, price in services:
            service, _ = Service.objects.get_or_create(
                tenant=salon,
                name=name,
                defaults={
                    "category": category,
                    "duration_min": duration,
                    "price_kgs": Decimal(str(price)),
                    "buffer_before_min": 5,
                    "buffer_after_min": 5,
                    "allow_combo": True,
                    "is_active": True,
                },
            )
            service_objects.append(service)

        self.stdout.write(f"  ✓ Created {len(service_objects)} services")

        # Create staff
        staff_list = [
            ("Анна Иванова", "Старший стилист", "+996700111111", "anna@demo.com", 30),
            ("Елена Петрова", "Колорист", "+996700222222", "elena@demo.com", 25),
            (
                "Мария Сидорова",
                "Мастер маникюра",
                "+996700333333",
                "maria@demo.com",
                20,
            ),
        ]

        staff_objects = []
        for name, title, phone, email, commission in staff_list:
            staff, _ = Staff.objects.get_or_create(
                tenant=salon,
                name=name,
                defaults={
                    "title": title,
                    "phone": phone,
                    "email": email,
                    "bio": f"Опытный мастер с 5+ летним стажем",
                    "commission_pct": Decimal(str(commission)),
                    "is_active": True,
                },
            )
            staff_objects.append(staff)

            # Link staff to services
            for service in service_objects[:5]:  # Link first 5 services
                StaffService.objects.get_or_create(staff=staff, service=service)

        self.stdout.write(f"  ✓ Created {len(staff_objects)} staff members")

        # Create schedules for staff
        default_schedule = {
            "monday": {"enabled": True, "slots": [{"start": "09:00", "end": "18:00"}]},
            "tuesday": {"enabled": True, "slots": [{"start": "09:00", "end": "18:00"}]},
            "wednesday": {
                "enabled": True,
                "slots": [{"start": "09:00", "end": "18:00"}],
            },
            "thursday": {
                "enabled": True,
                "slots": [{"start": "09:00", "end": "18:00"}],
            },
            "friday": {"enabled": True, "slots": [{"start": "09:00", "end": "20:00"}]},
            "saturday": {
                "enabled": True,
                "slots": [{"start": "10:00", "end": "18:00"}],
            },
            "sunday": {"enabled": False, "slots": []},
        }

        for staff in staff_objects:
            Schedule.objects.get_or_create(
                tenant=salon,
                staff=staff,
                defaults={
                    "rules": default_schedule,
                    "exceptions": [],
                    "is_active": True,
                },
            )

        # Create demo customers
        customers = [
            ("Айгуль Асанова", "+996555111111", "aigul@example.com", date(1990, 3, 15)),
            ("Бакыт Токтомов", "+996555222222", "bakyt@example.com", date(1985, 7, 20)),
            (
                "Гульмира Жумабаева",
                "+996555333333",
                "gulmira@example.com",
                date(1995, 11, 5),
            ),
            (
                "Дастан Эрматов",
                "+996555444444",
                "dastan@example.com",
                date(1992, 1, 10),
            ),
        ]

        customer_objects = []
        for name, phone, email, dob in customers:
            customer, _ = Customer.objects.get_or_create(
                tenant=salon,
                phone=phone,
                defaults={
                    "name": name,
                    "email": email,
                    "date_of_birth": dob,
                    "loyalty_points": 150,
                    "total_visits": 5,
                    "total_spent_kgs": Decimal("3500.00"),
                    "is_active": True,
                },
            )
            customer_objects.append(customer)

        self.stdout.write(f"  ✓ Created {len(customer_objects)} demo customers")

        # Create sample appointments
        tomorrow = timezone.now() + timedelta(days=1)
        tomorrow_10am = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

        appointment, _ = Appointment.objects.get_or_create(
            tenant=salon,
            customer=customer_objects[0],
            staff=staff_objects[0],
            start_at=tomorrow_10am,
            defaults={
                "end_at": tomorrow_10am + timedelta(hours=1),
                "location": location,
                "status": "CONFIRMED",
                "source": "WIDGET",
                "notes": "Хочу модную стрижку",
                "total_price_kgs": Decimal("800.00"),
                "prepaid_kgs": Decimal("0.00"),
                "discount_kgs": Decimal("0.00"),
            },
        )

        if appointment:
            AppointmentService.objects.get_or_create(
                appointment=appointment,
                service=service_objects[0],  # Женская стрижка
                defaults={
                    "order": 1,
                    "duration_min": 60,
                    "price_kgs": Decimal("800.00"),
                },
            )

        self.stdout.write("  ✓ Created sample appointment")

        # Create demo coupon
        Coupon.objects.get_or_create(
            tenant=salon,
            code="DEMO50",
            defaults={
                "kind": "PERCENT",
                "value": Decimal("50.00"),
                "valid_from": timezone.now(),
                "valid_to": timezone.now() + timedelta(days=30),
                "max_uses": 100,
                "max_uses_per_customer": 1,
                "rules": {"min_amount": 500},
                "is_active": True,
            },
        )

        # Create notification templates (RU)
        templates = [
            (
                "WELCOME",
                "EMAIL",
                "RU",
                "Добро пожаловать в %salon_name%!",
                "Здравствуйте, %owner_name%!\nВаш салон успешно создан: %tenant_url%\nЛогин: %email%",
            ),
            (
                "REMINDER_24H",
                "EMAIL",
                "RU",
                "Напоминание о записи",
                "Здравствуйте, %customer_name%!\nНапоминаем о вашей записи завтра в %time% к мастеру %staff_name%.",
            ),
            (
                "REMINDER_2H",
                "EMAIL",
                "RU",
                "Напоминание о записи через 2 часа",
                "Здравствуйте, %customer_name%!\nНапоминаем о вашей записи через 2 часа к мастеру %staff_name%.",
            ),
        ]

        for event, kind, lang, subject, body in templates:
            NotificationTemplate.objects.get_or_create(
                tenant=salon,
                kind=kind,
                event=event,
                lang=lang,
                defaults={"subject": subject, "body": body},
            )

        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Demo salon "{salon.name}" created successfully!')
        )
        return salon

    def _create_demo_solo(self):
        """Create demo solo master"""
        self.stdout.write("\nCreating demo solo master...")

        # Create tenant
        solo, created = Tenant.objects.get_or_create(
            slug="demo-solo",
            defaults={
                "name": "Мастер Алия",
                "type": "SOLO",
                "plan": "basic",
                "seats": 1,
                "status": "TRIAL",
                "trial_ends": (timezone.now() + timedelta(days=14)).date(),
                "settings": {
                    "theme": {"primary_color": "#9B59B6", "secondary_color": "#E74C3C"},
                    "language": "ru",
                    "timezone": "Asia/Bishkek",
                },
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS("  ✓ Solo master tenant created"))

        # Create solo master user
        solo_user, user_created = User.objects.get_or_create(
            email="solo@demo.com", defaults={}
        )

        if user_created:
            solo_user.set_password("demo123")
            solo_user.save()

        # Create membership
        Membership.objects.get_or_create(
            user=solo_user,
            tenant=solo,
            defaults={"role": "SALON_ADMIN", "is_active": True},
        )

        # Create subscription
        SaaSSubscription.objects.get_or_create(
            tenant=solo,
            defaults={
                "plan": "SOLO",
                "seats": 1,
                "status": "TRIAL",
                "period_start": date.today(),
                "period_end": (date.today() + timedelta(days=30)),
                "monthly_price_kgs": Decimal("500.00"),
            },
        )

        # Create location
        location, _ = Location.objects.get_or_create(
            tenant=solo,
            name="Домашняя студия",
            defaults={
                "timezone": "Asia/Bishkek",
                "address": "ул. Гоголя 45, кв. 12, Бишкек",
                "phone": "+996700999999",
                "is_active": True,
            },
        )

        # Create service category
        category, _ = ServiceCategory.objects.get_or_create(
            tenant=solo, name="Услуги", defaults={"sort_order": 1, "is_active": True}
        )

        # Create services
        services = [
            ("Маникюр", 60, 500),
            ("Педикюр", 90, 700),
            ("Маникюр + педикюр", 120, 1100),
            ("Наращивание ногтей", 120, 1000),
        ]

        for name, duration, price in services:
            Service.objects.get_or_create(
                tenant=solo,
                name=name,
                defaults={
                    "category": category,
                    "duration_min": duration,
                    "price_kgs": Decimal(str(price)),
                    "buffer_before_min": 10,
                    "buffer_after_min": 10,
                    "is_active": True,
                },
            )

        # Create staff (the solo master herself)
        staff, _ = Staff.objects.get_or_create(
            tenant=solo,
            name="Алия Нурбекова",
            defaults={
                "user": solo_user,
                "title": "Мастер маникюра",
                "phone": "+996700999999",
                "email": "solo@demo.com",
                "bio": "Профессиональный мастер маникюра и педикюра с опытом 7 лет",
                "is_active": True,
            },
        )

        # Create schedule
        Schedule.objects.get_or_create(
            tenant=solo,
            staff=staff,
            defaults={
                "rules": {
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
                "exceptions": [],
                "is_active": True,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Demo solo master "{solo.name}" created successfully!'
            )
        )
        return solo
