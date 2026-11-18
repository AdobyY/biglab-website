import uuid
from itertools import groupby

from django.db import migrations, models
from wagtail.models import Page as TreePage

from home.legacy_homepage import ENGLISH_TAGLINE, OLD_TAGLINES, SUPPLIED_CONTACT, about_sections, standalone_contact


def migrate_pages(apps, schema_editor):
    Home = apps.get_model("home", "HomePage")
    Content = apps.get_model("home", "ContentPage")
    Page = apps.get_model("wagtailcore", "Page")
    Revision = apps.get_model("wagtailcore", "Revision")
    ContentType = apps.get_model("contenttypes", "ContentType")
    content_type, _ = ContentType.objects.get_or_create(app_label="home", model="contentpage")
    homes = Home.objects.select_related("locale").order_by("translation_key", "locale_id")
    for home_key, translations in groupby(homes, key=lambda home: home.translation_key):
        family = []
        for home in translations:
            children = Page.objects.filter(depth=home.depth + 1, path__startswith=home.path)
            family.append((home, children))
        # An existing translated page can have an editor-chosen slug.
        contact_keys = {key for _, children in family for key in
                        children.filter(slug__in=("contact", "kontakt")).values_list("translation_key", flat=True)}
        contact_keys.add(SUPPLIED_CONTACT)
        existing = [children.filter(translation_key__in=contact_keys).first() for _, children in family]
        translation_key = next((page.translation_key for page in existing if page), uuid.uuid5(home_key, "contact"))
        for (home, children), page in zip(family, existing):
            raw = home._meta.get_field("sections").get_prep_value(home.sections)
            if page:
                Page.objects.filter(pk=page.pk).update(show_in_menus=True)
                for rev in Revision.objects.filter(pk__in=[page.latest_revision_id, page.live_revision_id]):
                    if not rev.content.get("show_in_menus"):
                        Revision.objects.filter(pk=rev.pk).update(content={**rev.content, "show_in_menus": True})
            else:
                contact, visible = standalone_contact(raw, home.show_contact_section, translation_key, home.locale.language_code)
                last_path = children.order_by("path").values_list("path", flat=True).last()
                position = TreePage._str2int(last_path[-TreePage.steplen:]) + 1 if last_path else 1
                Content.objects.create(
                    **contact, locale_id=home.locale_id,
                    translation_key=translation_key, content_type=content_type,
                    path=TreePage._get_path(home.path, home.depth + 1, position), depth=home.depth + 1,
                    url_path=home.url_path + "contact/", live=visible,
                )
                Page.objects.filter(pk=home.pk).update(numchild=models.F("numchild") + 1)
            converted = about_sections(raw)
            if converted != raw:
                Home.objects.filter(pk=home.pk).update(sections=models.Value(converted, output_field=models.JSONField()))
            for rev in Revision.objects.filter(pk__in=[home.latest_revision_id, home.live_revision_id]):
                if "sections" in rev.content:
                    converted = about_sections(rev.content["sections"])
                    if converted != rev.content["sections"]:
                        Revision.objects.filter(pk=rev.pk).update(content={**rev.content, "sections": converted})

    apps.get_model("home", "ContactSettings").objects.filter(tagline__in=OLD_TAGLINES).update(tagline=ENGLISH_TAGLINE)
    apps.get_model("home", "InterfaceText").objects.filter(key="footer_tagline", text__in=OLD_TAGLINES).update(text=ENGLISH_TAGLINE)


class Migration(migrations.Migration):
    dependencies = [("home", "0026_document_research_structure")]
    operations = [migrations.RunPython(migrate_pages, migrations.RunPython.noop)]
