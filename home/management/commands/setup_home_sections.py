from django.core.management.base import BaseCommand

from home.home_sections import ensure_home_sections
from home.models import HomePage


class Command(BaseCommand):
    help = "Populate empty homepage section builders without replacing editor changes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Replace existing homepage sections with the defaults.",
        )

    def handle(self, *args, **options):
        updated = 0
        for home in HomePage.objects.all().specific():
            updated += ensure_home_sections(home, force=options["force"])
        self.stdout.write(self.style.SUCCESS(f"Homepage sections ready ({updated} updated)."))
