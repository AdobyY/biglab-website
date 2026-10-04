from django.core.management.base import BaseCommand

from home.content_snapshot import DEFAULT_BUNDLE, export_bundle


class Command(BaseCommand):
    help = "Export current development editorial content and originals for seed_biglab; excludes accounts and secrets."

    def add_arguments(self, parser):
        parser.add_argument("--output-dir", default=str(DEFAULT_BUNDLE))

    def handle(self, *args, **options):
        data = export_bundle(options["output_dir"])
        self.stdout.write(f"Exported {len(data['pages'])} pages, {len(data['assets'])} assets and {len(data['snippets'])} snippets.")
