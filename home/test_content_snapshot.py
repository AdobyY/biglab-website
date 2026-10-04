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
from wagtail.models import PageViewRestriction, Site

from home.content_snapshot import export_bundle, import_bundle
from home.models import ContentPage, HomePage, HomepageDesignSettings, NewsIndexPage, NewsPage, ProjectPage
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

    def test_corrupted_asset_is_rejected_before_content_changes(self):
        self.home.hero_summary = "Keep until valid import"
        self.home.save_revision().publish()
        (self.bundle / self.data["assets"][0]["asset"]).write_bytes(b"corrupt")
        with self.assertRaises(CommandError):
            import_bundle(self.bundle)
        self.home.refresh_from_db()
        self.assertEqual(self.home.hero_summary, "Keep until valid import")

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
