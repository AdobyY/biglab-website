from django.db import migrations


def create_initial_locale_and_settings(apps, schema_editor):
    Locale = apps.get_model("wagtailcore", "Locale")
    Site = apps.get_model("wagtailcore", "Site")
    ContactSettings = apps.get_model("home", "ContactSettings")
    HomePage = apps.get_model("home", "HomePage")

    Locale.objects.get_or_create(language_code="cs")
    for site in Site.objects.all():
        ContactSettings.objects.get_or_create(site=site)
    HomePage.objects.filter(depth=2).update(title="About BIG Lab")


class Migration(migrations.Migration):
    dependencies = [("home", "0003_contentpage_newsindexpage_peopleindexpage_and_more")]

    operations = [migrations.RunPython(create_initial_locale_and_settings, migrations.RunPython.noop)]
