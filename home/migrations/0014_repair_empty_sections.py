from importlib import import_module

from django.db import migrations


def repair_empty_sections(apps, schema_editor):
    # Reuse the frozen defaults, not the runtime editor helper. This also
    # repairs installations where 0013 ran before its SQL filter was corrected.
    migration = import_module("home.migrations.0013_visible_default_sections")
    migration.populate_empty_sections(apps, schema_editor)


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ("home", "0013_visible_default_sections"),
    ]

    operations = [
        migrations.RunPython(repair_empty_sections, migrations.RunPython.noop),
    ]
