from io import BytesIO
from datetime import date
import json
from pathlib import Path
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from PIL import Image as PillowImage
from wagtail.images import get_image_model
from wagtail.documents import get_document_model
from wagtail.models import Collection, GroupPagePermission, Locale, Page, PageViewRestriction, Site

from home.content_snapshot import export_bundle, import_bundle
from home.models import Collaboration, ContentPage, HomePage, HomepageDesignSettings, InterfaceText, NewsIndexPage, NewsPage, PeopleIndexPage, PersonPage, ProjectPage, Publication
from home.templatetags.navigation_tags import _build_menu


class DevelopmentSnapshotTests(TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        media = self.settings(MEDIA_ROOT=self.directory / "media")
        media.enable()
        self.addCleanup(media.disable)
        self.site = Site.objects.get(is_default_site=True)
        self.site.hostname = "production.example"
        self.site.port = 443
        self.site.save()
        self.home = self.site.root_page.specific
        people = PeopleIndexPage.objects.child_of(self.home).first()
        self.profile = people.add_child(instance=PersonPage(title="Snapshot researcher", slug="snapshot-researcher", role="Researcher"))
        self.profile.save_revision().publish()
        self.parta = ProjectPage.objects.child_of(self.home).get(slug="parta")
        self.child = self.parta.add_child(instance=ContentPage(title="Parents", slug="for-parents", live=False, show_in_menus=True))
        image_bytes = BytesIO()
        PillowImage.new("RGB", (20, 20), "navy").save(image_bytes, format="JPEG")
        self.image = get_image_model().objects.create(
            title="Snapshot photo", file=SimpleUploadedFile("photo.jpg", image_bytes.getvalue(), "image/jpeg"),
        )
        self.home.hero_title = "Development title"
        self.home.hero_summary = "Development description"
        self.home.sections = []
        self.home.body = [
            ("image", {"image": self.image, "caption": "Development photo"}),
            ("button", {"page": self.parta, "label": "Project", "url": ""}),
            ("text", f'<p><a linktype="page" id="{self.parta.pk}">Project link</a></p>'),
        ]
        self.home.save_revision().publish()
        palette = HomepageDesignSettings.for_site(self.site)
        palette.background = "#123456"
        palette.save()
        self.bundle = self.directory / "bundle"
        self.data = export_bundle(self.bundle)

    def test_sync_restores_hero_menu_palette_and_keeps_accounts_and_domain(self):
        user = get_user_model().objects.create_user("editor", password="test-only-password")
        password_hash = user.password
        self.home.hero_summary = ""
        self.home.save_revision().publish()
        self.child.save_revision().publish()
        palette = HomepageDesignSettings.for_site(self.site)
        palette.background = "#000000"
        palette.save()
        call_command("seed_biglab", bundle_dir=str(self.bundle))
        self.home.refresh_from_db()
        self.child.refresh_from_db()
        self.site.refresh_from_db()
        self.assertEqual(self.home.hero_summary, "Development description")
        self.assertFalse(self.child.live)
        self.assertFalse(next(item for item in _build_menu(self.home) if item["page"].pk == self.parta.pk)["children"])
        self.assertEqual(HomepageDesignSettings.for_site(self.site).background, "#123456")
        self.assertEqual((self.site.hostname, self.site.port), ("production.example", 443))
        user.refresh_from_db()
        self.assertEqual(user.password, password_hash)
        serialized = (self.bundle / "content.json").read_text(encoding="utf-8")
        self.assertNotIn(password_hash, serialized)
        self.assertNotIn('"owner"', serialized)

    def test_cross_database_ids_are_remapped_in_fields_streams_and_rich_text(self):
        def shift_references(value):
            if isinstance(value, dict):
                return {key: item + 1000 if key == "id" and "ref" in value else shift_references(item) for key, item in value.items()}
            if isinstance(value, list):
                return [shift_references(item) for item in value]
            return value
        data = shift_references(self.data)
        data["default_root"] += 1000
        data["tree_root"] += 1000
        for group in ("pages", "assets", "snippets"):
            for item in data[group]:
                item["id"] += 1000
                if item.get("parent"):
                    item["parent"] += 1000
        home = next(item for item in data["pages"] if item["id"] == self.home.pk + 1000)
        home["fields"]["body"][0]["value"]["image"] += 1000
        home["fields"]["body"][1]["value"]["page"] += 1000
        home["fields"]["body"][2]["value"] = f'<p><a linktype="page" id="{self.parta.pk + 1000}">Project link</a></p>'
        (self.bundle / "content.json").write_text(json.dumps(data), encoding="utf-8")
        import_bundle(self.bundle)
        self.home.refresh_from_db()
        self.assertEqual(self.home.body[0].value["image"].pk, self.image.pk)
        self.assertEqual(self.home.body[1].value["page"].pk, self.parta.pk)
        self.assertIn(f'id="{self.parta.pk}"', self.home.body[2].value.source)

    def test_startup_skips_same_snapshot_and_explicit_command_resynchronizes(self):
        import_bundle(self.bundle, if_changed=True)
        self.home.hero_summary = "Later CMS edit"
        self.home.save_revision().publish()
        revision_count = self.home.revisions.count()
        self.assertTrue(import_bundle(self.bundle, if_changed=True)["unchanged"])
        self.home.refresh_from_db()
        self.assertEqual(self.home.hero_summary, "Later CMS edit")
        self.assertEqual(self.home.revisions.count(), revision_count)
        import_bundle(self.bundle)
        self.home.refresh_from_db()
        self.assertEqual(self.home.hero_summary, "Development description")

    def test_repeating_import_does_not_duplicate_assets_pages_or_revisions(self):
        import_bundle(self.bundle)
        pages = HomePage.objects.count()
        assets = get_image_model().objects.count()
        self.home.refresh_from_db()
        self.child.refresh_from_db()
        revisions = (self.home.revisions.count(), self.child.revisions.count())
        result = import_bundle(self.bundle)
        self.assertEqual(result["pages"], 0)
        self.assertEqual(HomePage.objects.count(), pages)
        self.assertEqual(get_image_model().objects.count(), assets)
        self.assertEqual((self.home.revisions.count(), self.child.revisions.count()), revisions)

    def test_existing_translation_is_reused_after_its_parent_and_slug_changed(self):
        people = self.profile.get_parent().specific
        archive = self.home.add_child(instance=PeopleIndexPage(title="Archived people", slug="archived-people"))
        self.profile.move(archive, pos="last-child")
        self.profile.refresh_from_db()
        self.profile.slug = "renamed-researcher"
        self.profile.save_revision().publish()
        original_id = self.profile.pk
        total_pages = self.home.get_descendants().count()

        import_bundle(self.bundle)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.pk, original_id)
        self.assertEqual(self.profile.get_parent().pk, people.pk)
        self.assertEqual(self.profile.slug, "snapshot-researcher")
        self.assertEqual(self.home.get_descendants().count(), total_pages)
        self.assertTrue(PeopleIndexPage.objects.filter(pk=archive.pk).exists())
        self.assertEqual(self.client.get(self.profile.url).status_code, 200)
        self.assertEqual(import_bundle(self.bundle)["pages"], 0)

    def test_unrelated_slug_collision_is_rejected_without_overwriting_content(self):
        people = self.profile.get_parent().specific
        archive = self.home.add_child(instance=PeopleIndexPage(title="Archived people", slug="archived-people"))
        self.profile.move(archive, pos="last-child")
        self.profile.refresh_from_db()
        replacement = people.add_child(instance=PersonPage(
            title="Keep this editor profile", slug=self.profile.slug, role="Editor profile",
        ))
        replacement.save_revision().publish()
        original_key = replacement.translation_key
        revisions = replacement.revisions.count()

        with self.assertRaisesMessage(CommandError, "is already in use"):
            import_bundle(self.bundle)

        self.profile.refresh_from_db()
        replacement.refresh_from_db()
        self.assertEqual(self.profile.get_parent().pk, archive.pk)
        self.assertEqual(replacement.title, "Keep this editor profile")
        self.assertEqual(replacement.translation_key, original_key)
        self.assertEqual(replacement.revisions.count(), revisions)

    def test_corrupted_asset_is_rejected_before_content_changes(self):
        self.home.hero_summary = "Keep until valid import"
        self.home.save_revision().publish()
        (self.bundle / self.data["assets"][0]["asset"]).write_bytes(b"corrupt")
        with self.assertRaises(CommandError):
            import_bundle(self.bundle)
        self.home.refresh_from_db()
        self.assertEqual(self.home.hero_summary, "Keep until valid import")

    def test_explicit_reset_restores_all_content_and_removes_test_additions(self):
        user = get_user_model().objects.create_user("reset-editor", password="test-only-password")
        password_hash = user.password
        permissions = list(GroupPagePermission.objects.filter(page__depth=1).values_list("pk", flat=True))
        home_id = self.home.pk
        snapshot_bytes = (self.bundle / "content.json").read_bytes()
        extra = self.parta.add_child(instance=ContentPage(title="Test page", slug="test-page"))
        extra.add_child(instance=ContentPage(title="Test child", slug="test-child", live=False))
        locale = self.home.locale
        Publication.objects.create(locale=locale, title="Test publication", authors="Test", year=2026)
        Collaboration.objects.create(locale=locale, name="Test collaboration")
        InterfaceText.objects.create(locale=locale, key="read_more", text="Test label")
        extra_image = get_image_model().objects.create(
            title="Test upload", file=SimpleUploadedFile("test.jpg", (self.bundle / self.data["assets"][0]["asset"]).read_bytes(), "image/jpeg"),
        )
        get_document_model().objects.create(title="Test document", file=SimpleUploadedFile("test.txt", b"Test document"))
        Collection.get_first_root_node().add_child(name="Test collection")
        Locale.objects.create(language_code="de")
        PageViewRestriction.objects.create(page=self.home, restriction_type="login")
        self.home.hero_title = "Test title"
        self.home.save_revision().publish()
        self.home.hero_summary = "Unpublished test edit"
        self.home.save_revision()
        palette = HomepageDesignSettings.for_site(self.site)
        palette.background = "#000000"
        palette.save()

        with self.captureOnCommitCallbacks(execute=True):
            call_command("seed_biglab", reset=True, bundle_dir=str(self.bundle))

        self.home.refresh_from_db()
        self.site.refresh_from_db()
        user.refresh_from_db()
        self.assertEqual(self.home.pk, home_id)
        self.assertEqual(self.home.hero_title, "Development title")
        self.assertEqual(self.home.hero_summary, "Development description")
        self.assertFalse(self.home.has_unpublished_changes)
        self.assertFalse(Page.objects.filter(slug__in=["test-page", "test-child"]).exists())
        self.assertEqual(Page.objects.filter(depth__gte=2).count(), len(self.data["pages"]))
        self.assertFalse(Publication.objects.filter(title="Test publication").exists())
        self.assertFalse(Collaboration.objects.filter(name="Test collaboration").exists())
        self.assertFalse(InterfaceText.objects.filter(text="Test label").exists())
        for model in (Publication, Collaboration, InterfaceText):
            self.assertEqual(model.objects.count(), sum(item["model"] == model._meta.label_lower for item in self.data["snippets"]))
        self.assertEqual(get_image_model().objects.count(), len(self.data["assets"]))
        self.assertEqual(get_document_model().objects.count(), 0)
        self.assertFalse(extra_image.file.storage.exists(extra_image.file.name))
        self.assertEqual(Collection.objects.count(), 1)
        self.assertFalse(Locale.objects.filter(language_code="de").exists())
        self.assertFalse(PageViewRestriction.objects.exists())
        self.assertEqual(self.home.body[0].value["image"].title, "Snapshot photo")
        self.assertEqual(self.home.body[1].value["page"].slug, "parta")
        self.assertFalse(ContentPage.objects.child_of(ProjectPage.objects.get(slug="parta")).get(slug="for-parents").live)
        self.assertEqual(HomepageDesignSettings.for_site(self.site).background, "#123456")
        self.assertEqual(user.password, password_hash)
        self.assertEqual((self.site.hostname, self.site.port), ("production.example", 443))
        self.assertEqual(list(GroupPagePermission.objects.filter(page__depth=1).values_list("pk", flat=True)), permissions)
        self.assertEqual((self.bundle / "content.json").read_bytes(), snapshot_bytes)
        self.assertEqual(self.client.get(self.home.url).status_code, 200)
        import_bundle(self.bundle, reset=True)
        self.assertEqual(Page.objects.filter(depth__gte=2).count(), len(self.data["pages"]))

    def test_ordinary_startup_preserves_added_test_content(self):
        import_bundle(self.bundle, if_changed=True)
        extra = self.parta.add_child(instance=ContentPage(title="Keep added page", slug="keep-page", live=False))
        Publication.objects.create(locale=self.home.locale, title="Keep added publication", authors="Editor", year=2026)
        self.assertTrue(import_bundle(self.bundle, if_changed=True)["unchanged"])
        import_bundle(self.bundle)
        self.assertTrue(Page.objects.filter(pk=extra.pk).exists())
        self.assertTrue(Publication.objects.filter(title="Keep added publication").exists())

    def test_reset_rejects_automatic_and_legacy_modes_before_changes(self):
        pages = list(Page.objects.values_list("pk", flat=True))
        for options in ({"if_changed": True}, {"bootstrap": True}):
            with self.assertRaisesMessage(CommandError, "--reset cannot be combined"):
                call_command("seed_biglab", reset=True, bundle_dir=str(self.bundle), **options)
        self.assertEqual(list(Page.objects.values_list("pk", flat=True)), pages)

    def test_reset_validates_assets_before_deleting_content(self):
        pages = list(Page.objects.values_list("pk", flat=True))
        (self.bundle / self.data["assets"][0]["asset"]).write_bytes(b"corrupt")
        with self.assertRaisesMessage(CommandError, "checksum mismatch"):
            import_bundle(self.bundle, reset=True)
        self.assertEqual(list(Page.objects.values_list("pk", flat=True)), pages)

    def test_failed_reset_rolls_back_existing_pages_and_media(self):
        pages = list(Page.objects.values_list("pk", flat=True))
        asset_name = self.image.file.name
        home = next(item for item in self.data["pages"] if item["id"] == self.home.pk)
        home["fields"]["body"][0]["value"]["image"] = 999999
        (self.bundle / "content.json").write_text(json.dumps(self.data), encoding="utf-8")
        with self.assertRaises(KeyError):
            import_bundle(self.bundle, reset=True)
        self.assertEqual(list(Page.objects.values_list("pk", flat=True)), pages)
        self.assertTrue(get_image_model().objects.filter(pk=self.image.pk).exists())
        self.assertTrue(self.image.file.storage.exists(asset_name))

    def test_new_news_page_is_created_with_required_date_and_image(self):
        index = NewsIndexPage.objects.child_of(self.home).first()
        news = index.add_child(instance=NewsPage(title="New development news", slug="new-story", date=date(2026, 5, 19), cover_image=self.image))
        news.save_revision().publish()
        export_bundle(self.bundle)
        news.delete()
        import_bundle(self.bundle)
        restored = NewsPage.objects.child_of(index).get(slug="new-story")
        self.assertEqual(restored.date, date(2026, 5, 19))
        self.assertEqual(restored.cover_image_id, self.image.pk)
        self.assertTrue(restored.live)

    def test_public_snapshot_refuses_restricted_content(self):
        PageViewRestriction.objects.create(page=self.home, restriction_type="login")
        with self.assertRaises(CommandError):
            export_bundle(self.directory / "private")

    def test_index_slug_change_updates_all_profile_links(self):
        index = PeopleIndexPage.objects.child_of(self.home).first()
        profiles = list(PersonPage.objects.child_of(index))
        old_slug = index.slug
        index.slug = "old-team"
        index.save_revision().publish()
        import_bundle(self.bundle)
        index.refresh_from_db()
        self.assertEqual(index.slug, old_slug)
        for profile in profiles:
            profile.refresh_from_db()
            self.assertEqual(profile.url_path, index.url_path + profile.slug + "/")
            self.assertEqual(self.client.get(profile.url).status_code, 200)

    def test_stale_profile_urls_are_repaired_when_content_is_unchanged(self):
        index = PeopleIndexPage.objects.child_of(self.home).first()
        profile = PersonPage.objects.child_of(index).first()
        PersonPage.objects.filter(pk=profile.pk).update(url_path="/home/old-team/" + profile.slug + "/")
        revisions = profile.revisions.count()
        result = import_bundle(self.bundle)
        profile.refresh_from_db()
        self.assertEqual(result["urls"], 1)
        self.assertEqual(profile.url_path, index.url_path + profile.slug + "/")
        self.assertEqual(profile.revisions.count(), revisions)
        self.assertEqual(self.client.get(profile.url).status_code, 200)
