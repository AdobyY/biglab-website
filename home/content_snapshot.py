"""Portable editorial content, without accounts, credentials or database IDs."""

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

from django.apps import apps
from django.core.files import File
from django.core.management.base import CommandError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from wagtail import blocks
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Collection, CollectionViewRestriction, Locale, Page, PageViewRestriction, Site
from wagtail.images import get_image_model
from wagtail.documents import get_document_model
from wagtail.contrib.redirects.models import Redirect

from home.models import Collaboration, ContactSettings, HomepageDesignSettings, InterfaceText, Publication


DEFAULT_BUNDLE = Path(__file__).resolve().parent / "seed_content"
SNIPPETS = (Publication, Collaboration, InterfaceText)
SITE_SETTINGS = (ContactSettings, HomepageDesignSettings)
PAGE_FIELDS = {"title", "draft_title", "slug", "seo_title", "search_description", "show_in_menus"}


def label(model):
    return "wagtailcore.page" if issubclass(model, Page) else model._meta.label_lower


def content_fields(obj):
    for field in obj._meta.fields:
        if field.primary_key or not field.serialize:
            continue
        if isinstance(obj, Page):
            if field.name not in PAGE_FIELDS and field.model._meta.app_label != "home":
                continue
        elif field.name in {"file", "collection", "uploaded_by_user", "created_at"}:
            continue
        yield field


def field_data(obj, field):
    if field.is_relation:
        pk = getattr(obj, field.attname)
        if pk is None:
            return None
        if field.related_model is Locale:
            return {"locale": obj.locale.language_code}
        return {"ref": label(field.related_model), "id": pk}
    value = field.value_from_object(obj)
    if isinstance(field, StreamField):
        value = field.get_prep_value(value)
    return json.loads(json.dumps(value, cls=DjangoJSONEncoder))


def record(obj):
    return {"model": obj._meta.label_lower, "id": obj.pk,
            "fields": {field.name: field_data(obj, field) for field in content_fields(obj)}}


def export_bundle(directory=DEFAULT_BUNDLE):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    asset_directory = directory / "assets"
    asset_directory.mkdir(exist_ok=True)
    if PageViewRestriction.objects.exists() or CollectionViewRestriction.objects.exists():
        raise CommandError("A public content snapshot cannot export restricted pages or asset collections.")
    site = Site.objects.get(is_default_site=True)
    pages = list(Page.objects.filter(depth__gte=2).order_by("path").specific())
    if any(page._meta.app_label != "home" for page in pages):
        raise CommandError("The snapshot supports BIG Lab page models only.")
    data = {"version": 1, "locales": list(Locale.objects.order_by("pk").values_list("language_code", flat=True)),
            "tree_root": Page.get_first_root_node().pk, "default_root": site.root_page_id, "pages": [],
            "assets": [], "snippets": [], "settings": []}
    for page in pages:
        # A live page exports its published content, never an unpublished edit.
        content = page.live_revision.as_object() if page.live and page.live_revision_id else (
            page.get_latest_revision_as_object() if not page.live and page.latest_revision_id else page
        )
        item = record(content)
        item.update(id=page.pk, parent=page.get_parent().pk if page.depth > 2 else None,
                    locale=page.locale.language_code, translation_key=str(page.translation_key), live=page.live)
        data["pages"].append(item)
    for model in (get_image_model(), get_document_model()):
        for asset in model.objects.order_by("pk"):
            with asset.file.open("rb") as source:
                payload = source.read()
            digest = hashlib.sha256(payload).hexdigest()
            filename = digest + Path(asset.file.name).suffix.lower()
            (asset_directory / filename).write_bytes(payload)
            item = record(asset)
            item.update(asset=f"assets/{filename}", sha256=digest,
                        filename=Path(asset.file.name).name, tags=list(asset.tags.names()))
            data["assets"].append(item)
    for model in SNIPPETS:
        data["snippets"].extend(record(obj) for obj in model.objects.order_by("pk"))
    for model in SITE_SETTINGS:
        item = record(model.for_site(site))
        item["fields"].pop("site", None)
        data["settings"].append(item)
    (directory / "content.json").write_text(
        json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    return data


def remap_rich_text(value, mappings):
    def replace_tag(match):
        tag = match.group(0)
        kind = re.search(r'(?:linktype|embedtype)=["\'](page|image|document)["\']', tag)
        identifier = re.search(r'\bid=["\'](\d+)["\']', tag)
        if kind and identifier:
            models = {"page": Page, "image": get_image_model(), "document": get_document_model()}
            target = mappings[(label(models[kind[1]]), int(identifier[1]))]
            tag = tag[:identifier.start(1)] + str(target.pk) + tag[identifier.end(1):]
        return tag
    return re.sub(r'<(?:a|embed)\b[^>]*>', replace_tag, value)


def remap_block(block, value, mappings):
    if value is None:
        return value
    if isinstance(block, blocks.ChooserBlock):
        return mappings[(label(block.model_class), int(value))].pk if value else value
    if isinstance(block, blocks.RichTextBlock):
        return remap_rich_text(value, mappings)
    if isinstance(block, blocks.StreamBlock):
        return [dict(item, value=remap_block(block.child_blocks[item["type"]], item["value"], mappings)) for item in value]
    if isinstance(block, blocks.StructBlock):
        return {key: remap_block(block.child_blocks[key], item, mappings) for key, item in value.items()}
    if isinstance(block, blocks.ListBlock):
        return [dict(item, value=remap_block(block.child_block, item["value"], mappings))
                if isinstance(item, dict) and item.get("type") == "item"
                else remap_block(block.child_block, item, mappings) for item in value]
    return value


def assign_fields(obj, fields, mappings):
    for name, value in fields.items():
        field = obj._meta.get_field(name)
        if field.is_relation:
            if value is None:
                setattr(obj, field.attname, None)
            elif "locale" in value:
                obj.locale = Locale.objects.get(language_code=value["locale"])
            else:
                setattr(obj, name, mappings[(value["ref"], value["id"])])
        elif isinstance(field, StreamField):
            raw = json.loads(value) if isinstance(value, str) else value
            setattr(obj, name, remap_block(field.stream_block, raw, mappings))
        elif isinstance(field, RichTextField):
            setattr(obj, name, remap_rich_text(value, mappings))
        else:
            setattr(obj, name, field.to_python(value))


def clear_editorial_content(data, site):
    """Keep the site identity and accounts, then rebuild its editorial content."""
    home = site.root_page.specific
    expected = next(item for item in data["pages"] if item["id"] == data["default_root"])
    if (Site.objects.exclude(pk=site.pk).exists() or home.depth != 2
            or home._meta.label_lower != expected["model"]
            or home.locale.language_code != expected["locale"]):
        raise CommandError("Content reset requires a single BIG Lab site with the snapshot's home page type and language.")
    # Keep the home ID so the domain, site settings and root permissions survive.
    # Treebeard also removes each selected branch's descendants.
    deleted = Page.objects.filter(depth__gte=2).exclude(pk=home.pk).count()
    Page.objects.filter(depth=2).exclude(pk=home.pk).delete()
    home.get_children().delete()
    PageViewRestriction.objects.all().delete()
    Redirect.objects.all().delete()
    for model in SNIPPETS:
        model.objects.all().delete()
    for model in (get_image_model(), get_document_model()):
        # Wagtail schedules file removal after transaction commit, so an import
        # failure rolls back the database without deleting existing media.
        model.objects.all().delete()
    CollectionViewRestriction.objects.all().delete()
    Collection.get_first_root_node().get_children().delete()
    Locale.objects.exclude(language_code__in=data["locales"]).delete()
    return deleted


def import_bundle(directory=DEFAULT_BUNDLE, *, if_changed=False, reset=False):
    if reset and if_changed:
        raise CommandError("--reset cannot be combined with --if-changed.")
    directory = Path(directory)
    manifest = directory / "content.json"
    if not manifest.exists():
        raise CommandError("Export development content with export_biglab_content first.")
    payload = manifest.read_bytes()
    # Reapply when the importer gains a repair, even for the same content.
    digest = hashlib.sha256(b"biglab-content-sync-v2\n" + payload).hexdigest()
    data = json.loads(payload)
    if data.get("version") != 1:
        raise CommandError("Unsupported content snapshot version.")
    from django.conf import settings
    marker = Path(settings.MEDIA_ROOT) / ".biglab-content-version"
    if if_changed and marker.exists() and marker.read_text(encoding="ascii").strip() == digest:
        return {"unchanged": True}
    for item in data["assets"]:
        source = (directory / item["asset"]).resolve()
        if not source.is_relative_to(directory.resolve()) or not source.is_file():
            raise CommandError("Missing or invalid snapshot asset.")
        if hashlib.sha256(source.read_bytes()).hexdigest() != item["sha256"]:
            raise CommandError("Snapshot asset checksum mismatch.")
    mappings = {(label(Page), data["tree_root"]): Page.get_first_root_node()}
    counts = {"pages": 0, "assets": 0, "snippets": 0, "settings": 0, "urls": 0}
    with transaction.atomic():
        site = Site.objects.get(is_default_site=True)
        if reset:
            counts["removed_pages"] = clear_editorial_content(data, site)
        for code in data["locales"]:
            Locale.objects.get_or_create(language_code=code)
        for item in data["assets"]:
            model = apps.get_model(item["model"])
            if model not in (get_image_model(), get_document_model()):
                raise CommandError("Unsupported snapshot asset model.")
            asset = model.objects.filter(title=item["fields"]["title"], file_hash=item["fields"].get("file_hash", "")).first()
            asset = asset or model(collection=Collection.get_first_root_node())
            assign_fields(asset, item["fields"], mappings)
            if not asset.pk or not asset.file.storage.exists(asset.file.name):
                with (directory / item["asset"]).open("rb") as source:
                    asset.file.save(item["filename"], File(source), save=False)
            asset.save()
            asset.tags.set(item["tags"])
            mappings[(label(model), item["id"])] = asset
            counts["assets"] += 1
        for item in data["snippets"]:
            model = apps.get_model(item["model"])
            if model not in SNIPPETS:
                raise CommandError("Unsupported snapshot snippet model.")
            locale = Locale.objects.get(language_code=item["fields"]["locale"]["locale"])
            key = "title" if model is Publication else "name" if model is Collaboration else "key"
            obj = model.objects.filter(locale=locale, **{key: item["fields"][key]}).first() or model()
            assign_fields(obj, item["fields"], mappings)
            obj.save()
            mappings[(label(model), item["id"])] = obj
            counts["snippets"] += 1
        siblings = defaultdict(list)
        for item in data["pages"]:
            model = apps.get_model(item["model"])
            if model._meta.app_label != "home" or not issubclass(model, Page):
                raise CommandError("Unsupported snapshot page model.")
            locale = Locale.objects.get(language_code=item["locale"])
            parent = (Page.objects.get(pk=mappings[(label(Page), item["parent"])].pk)
                      if item["parent"] else Page.get_first_root_node())
            candidates = model.objects.child_of(parent).filter(locale=locale)
            # Translation identity is unique across the entire tree. Older
            # installations may place the same page under a different parent;
            # limiting this lookup to siblings attempts to insert a duplicate.
            page = Page.objects.filter(locale=locale, translation_key=item["translation_key"]).first()
            if page is not None:
                page = page.specific
                if not isinstance(page, model):
                    raise CommandError(f"Snapshot page {item['id']} conflicts with existing page {page.pk}: different page types.")
                if page.get_parent().pk != parent.pk:
                    if parent.get_children().exclude(pk=page.pk).filter(slug=item["fields"]["slug"]).exists():
                        raise CommandError(f"Cannot move snapshot page {item['id']}: slug {item['fields']['slug']!r} is already in use under page {parent.pk}.")
                    page.move(parent, pos="last-child")
                    page.refresh_from_db()
            page = page or candidates.filter(slug=item["fields"]["slug"]).first()
            # Structural indexes are unique even when an older installation used
            # a different slug (for example "team" instead of "people").
            if page is None and model._meta.model_name in {"homepage", "sciencepage", "peopleindexpage", "newsindexpage", "projectsindexpage"}:
                page = candidates.first()
            if page is None:
                page = model(title=item["fields"]["title"], slug=item["fields"]["slug"],
                    locale=locale, translation_key=item["translation_key"], live=False)
                # Populate required scalar fields before the first database save
                # (news dates, profile roles). Page references resolve in pass two.
                scalars = {name: value for name, value in item["fields"].items()
                           if not model._meta.get_field(name).is_relation
                           and not isinstance(model._meta.get_field(name), (StreamField, RichTextField))}
                assign_fields(page, scalars, mappings)
                page = parent.add_child(instance=page)
            page.translation_key = item["translation_key"]
            page.save(update_fields=["translation_key"])
            mappings[(label(Page), item["id"])] = page
            siblings[parent.pk].append(page.pk)
        for parent_id, desired in siblings.items():
            parent = Page.objects.get(pk=parent_id)
            current = list(parent.get_children().filter(pk__in=desired).values_list("pk", flat=True))
            if current != desired:
                for pk in reversed(desired):
                    Page.objects.get(pk=pk).move(parent, pos="first-child")
        for item in data["pages"]:
            page = Page.objects.get(pk=mappings[(label(Page), item["id"])].pk).specific
            before = record(page.get_latest_revision_as_object() if not page.live and page.latest_revision_id else page)["fields"]
            assign_fields(page, item["fields"], mappings)
            page.alias_of = None
            changed = reset or before != record(page)["fields"] or page.live != item["live"] or (page.has_unpublished_changes and item["live"])
            if changed:
                if page.live and not item["live"]:
                    page.unpublish()
                page.save()
                revision = page.save_revision()
                if item["live"]:
                    revision.publish()
                counts["pages"] += 1
            mappings[(label(Page), item["id"])] = page
        # Older installations can have stale descendant URLs even when the
        # parent's slug is already correct. Repair derived paths without
        # creating editorial revisions or changing publication states.
        for item in data["pages"]:
            page = Page.objects.get(pk=mappings[(label(Page), item["id"])].pk)
            old_path = page.url_path
            page.set_url_path(page.get_parent())
            if page.url_path != old_path:
                Page.objects.filter(pk=page.pk).update(url_path=page.url_path)
                counts["urls"] += 1
        site.root_page = mappings[(label(Page), data["default_root"])]
        site.save(update_fields=["root_page"])
        for item in data["settings"]:
            model = apps.get_model(item["model"])
            if model not in SITE_SETTINGS:
                raise CommandError("Unsupported snapshot site settings.")
            obj = model.for_site(site)
            assign_fields(obj, item["fields"], mappings)
            obj.save()
            counts["settings"] += 1
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(digest + "\n", encoding="ascii")
    return counts
