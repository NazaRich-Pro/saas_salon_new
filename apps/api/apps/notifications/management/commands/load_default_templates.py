"""
Management command to load default notification templates
Usage: python manage.py load_default_templates
"""
from apps.notifications.models import NotificationTemplate
from apps.notifications.template_defaults import DEFAULT_TEMPLATES
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load default notification templates (RU/KG) into database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite existing templates",
        )

    def handle(self, *args, **options):
        overwrite = options["overwrite"]

        self.stdout.write(
            self.style.SUCCESS("Loading default notification templates...")
        )

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for event, languages in DEFAULT_TEMPLATES.items():
            for lang, template_data in languages.items():
                # Check if template exists
                existing = NotificationTemplate.objects.filter(
                    tenant__isnull=True,  # Platform defaults
                    kind="EMAIL",
                    event=event,
                    lang=lang.upper(),
                ).first()

                if existing:
                    if overwrite:
                        existing.subject = template_data["subject"]
                        existing.body = template_data["body"]
                        existing.save()
                        updated_count += 1
                        self.stdout.write(f"  ↻ Updated: {event} / {lang}")
                    else:
                        skipped_count += 1
                        self.stdout.write(
                            f"  - Skipped: {event} / {lang} (already exists)"
                        )
                else:
                    # Create new template
                    NotificationTemplate.objects.create(
                        tenant=None,  # Platform default
                        kind="EMAIL",
                        event=event,
                        lang=lang.upper(),
                        subject=template_data["subject"],
                        body=template_data["body"],
                        is_active=True,
                    )
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Created: {event} / {lang}")
                    )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Summary:"))
        self.stdout.write(f"  • Created: {created_count}")
        self.stdout.write(f"  • Updated: {updated_count}")
        self.stdout.write(f"  • Skipped: {skipped_count}")
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("✓ Default templates loaded successfully!")
        )

        # Show template list
        self.stdout.write("\nAvailable templates:")
        all_templates = NotificationTemplate.objects.filter(tenant__isnull=True)
        for template in all_templates:
            self.stdout.write(f"  • {template}")
