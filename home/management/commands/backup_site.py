import json
import sqlite3
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections


class Command(BaseCommand):
    help = "Create a consistent archive containing the SQLite database and media files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            type=Path,
            default=Path(settings.BASE_DIR) / "backups",
            help="Directory in which the .tar.gz archive will be created.",
        )

    def handle(self, *args, **options):
        connection = connections["default"]
        if connection.vendor != "sqlite":
            raise CommandError("backup_site currently supports SQLite only.")

        output_dir = options["output_dir"].expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        archive_path = output_dir / f"biglab-backup-{timestamp}.tar.gz"

        with tempfile.TemporaryDirectory(prefix="biglab-backup-") as temp_dir:
            temp_path = Path(temp_dir)
            database_copy = temp_path / "db.sqlite3"
            manifest_path = temp_path / "manifest.json"

            connection.ensure_connection()
            with sqlite3.connect(database_copy) as destination:
                connection.connection.backup(destination)

            media_root = Path(settings.MEDIA_ROOT)
            media_files = (
                sum(1 for path in media_root.rglob("*") if path.is_file())
                if media_root.exists()
                else 0
            )
            manifest_path.write_text(
                json.dumps(
                    {
                        "created_at": datetime.now(UTC).isoformat(),
                        "database": "db.sqlite3",
                        "media_directory": "media",
                        "media_files": media_files,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            with tarfile.open(archive_path, "w:gz") as archive:
                archive.add(database_copy, arcname="db.sqlite3")
                archive.add(manifest_path, arcname="manifest.json")
                if media_root.exists():
                    archive.add(media_root, arcname="media")

        self.stdout.write(self.style.SUCCESS(f"Backup created: {archive_path}"))
