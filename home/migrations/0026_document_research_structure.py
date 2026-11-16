"""Update approved interface labels without replacing editorial content or page IDs."""
import json
from copy import deepcopy
from django.db import migrations


def rename_sections(value):
    as_string = isinstance(value, str)
    sections = json.loads(value) if as_string else deepcopy(value or [])
    changed = False
    for section in sections:
        data = section.get("value", {})
        if not isinstance(data, dict):
            continue
        if section.get("type") == "research":
            for key, old, new in (("title", "Science", "Research"), ("link_label", "All science", "All research")):
                if data.get(key) == old:
                    data[key] = new
                    changed = True
        if section.get("type") == "page_links":
            for item in data.get("pages", []):
                item = item.get("value", item)
                if item.get("label") == "Science":
                    item["label"] = "Research"
                    changed = True
    return (json.dumps(sections, ensure_ascii=False) if as_string else sections), changed


def update_research_labels(apps, schema_editor):
    Page = apps.get_model("wagtailcore", "Page")
    Locale = apps.get_model("wagtailcore", "Locale")
    Revision = apps.get_model("wagtailcore", "Revision")
    InterfaceText = apps.get_model("home", "InterfaceText")
    locale_ids = list(Locale.objects.filter(language_code="en").values_list("pk", flat=True))
    for key, old, new in (("science", "Science", "Research"), ("all_science", "All science", "All research"),
                          ("explore_science", "Explore our science", "Explore our research"),
                          ("collaborations", "Collaborations", "Collaboration")):
        InterfaceText.objects.filter(locale_id__in=locale_ids, key=key, text=old).update(text=new)
    for model_name in ("HomePage", "SciencePage", "ContentPage", "ProjectPage"):
        Model = apps.get_model("home", model_name)
        for instance in Model.objects.filter(locale_id__in=locale_ids):
            updates = {}
            if model_name == "SciencePage" and instance.title == "Science":
                Page.objects.filter(pk=instance.pk, title="Science").update(title="Research")
                Page.objects.filter(pk=instance.pk, draft_title="Science").update(draft_title="Research")
            field = Model._meta.get_field("sections")
            data, changed = rename_sections(field.get_prep_value(instance.sections))
            if changed:
                updates["sections"] = field.to_python(data)
            if updates:
                Model.objects.filter(pk=instance.pk).update(**updates)
            revision_ids = {instance.latest_revision_id, instance.live_revision_id} - {None}
            for revision in Revision.objects.filter(pk__in=revision_ids):
                content = deepcopy(revision.content)
                touched = False
                if model_name == "SciencePage":
                    for name in ("title", "draft_title"):
                        if content.get(name) == "Science":
                            content[name] = "Research"
                            touched = True
                if "sections" in content:
                    content["sections"], section_change = rename_sections(content["sections"])
                    touched = touched or section_change
                if touched:
                    Revision.objects.filter(pk=revision.pk).update(content=content)


class Migration(migrations.Migration):
    dependencies = [("home", "0025_research_interface_labels")]
    operations = [migrations.RunPython(update_research_labels, migrations.RunPython.noop)]
