"""Deployment regressions; subprocesses never use the editor's database or media."""

import os
from io import StringIO
from pathlib import Path
import subprocess
import sys
import tempfile

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from unittest.mock import Mock

from home.management.commands.seed_biglab import Command, PROJECT_BODIES_CS
from home.home_sections import default_home_sections
from home.management.commands.upgrade_biglab_content import MISSION, PARTA_BODY, PARTA_INTRO, PLACEHOLDER_INTROS, PROJECT_BODIES_EN
from home.models import Collaboration, ContentPage, HomePage, ProjectPage
from wagtail.models import Locale, Page
from wagtail.rich_text import RichText


ROOT = Path(__file__).resolve().parent.parent


class SeedPreservationTests(SimpleTestCase):
    def test_existing_empty_child_is_not_reseeded_or_republished(self):
        command = Command()
        parent = Mock()
        existing = Mock(live=False, intro="")
        parent.get_children.return_value.filter.return_value.specific.return_value.first.return_value = existing
        result = command._child(parent, Mock(), "timeline", publish=False, title="Timeline")
        self.assertIs(result, existing)
        existing.save_revision.assert_not_called()
        parent.add_child.assert_not_called()

    def test_editor_revision_protects_intentionally_empty_content(self):
        command = Command()
        page = Mock(intro="", body=[], hero_summary="")
        page.revisions.exists.return_value = True
        command._seed_existing(page, intro="replacement")
        self.assertEqual(page.intro, "")
        page.save_revision.assert_not_called()

    def test_financing_marker_protects_intentionally_empty_content(self):
        command = Command()
        home = Mock(about_financing="", has_unpublished_changes=False)
        home.revisions.filter.return_value.exists.return_value = True
        command._seed_financing(home)
        self.assertEqual(home.about_financing, "")
        home.save.assert_not_called()
        home.save_revision.assert_not_called()

    def test_new_placeholder_saves_draft_without_publishing(self):
        command = Command()
        page = Mock()
        command._publish(page, publish=False)
        page.save_revision.assert_called_once_with()
        page.save_revision.return_value.publish.assert_not_called()

    def test_supplied_project_bodies_have_czech_initial_translations(self):
        self.assertEqual(len(PROJECT_BODIES_CS), 3)
        self.assertIn("Segregace uvnitř škol", PROJECT_BODIES_CS["rethinking-segregation-within-schools"])
        self.assertIn("osobních zkušeností", PROJECT_BODIES_CS["behavior-dynamics"])
        self.assertIn("sebepoškozování", PROJECT_BODIES_CS["selfharm-screening"])


class LegacyContentUpgradeTests(TestCase):
    def setUp(self):
        self.home = HomePage.objects.get(depth=2, locale__language_code="en")
        self.home.hero_title = "About BIG Lab"
        self.home.hero_summary = ""
        self.home.intro = ""
        self.home.body = []
        self.home.about_financing = ""
        self.home.sections = [
            ("about", {"title": MISSION["en"]["heading"], "anchor": "about", "intro": "", "text": "", "theme": "paper", "is_visible": True}),
            ("about", {"title": "Editor's other section", "anchor": "custom", "intro": "", "text": "<p>Keep this content</p>", "theme": "coral", "is_visible": True}),
        ]
        self.home.save_revision().publish()
        # Simulate legacy revisions written before the financing field existed.
        self.remove_financing_marker(self.home)
        self.parta = ProjectPage.objects.child_of(self.home).get(slug="parta")
        self.placeholder = ContentPage(
            title="Timeline", slug="timeline", live=False,
            intro=PLACEHOLDER_INTROS["en"], body=[], sections=[], after_body=[],
        )
        self.parta.add_child(instance=self.placeholder)
        self.placeholder.save_revision().publish()
        self.cs = Locale.objects.get(language_code="cs")
        self.home_cs = self.home.copy_for_translation(self.cs)
        self.home_cs.hero_title = "O BIG Lab"
        self.home_cs.sections[0].value["title"] = MISSION["cs"]["heading"]
        self.home_cs.save_revision().publish()
        self.remove_financing_marker(self.home_cs)
        self.project = ProjectPage(
            title="Dynamika chování", slug="behavior-dynamics", live=False,
            intro="<p>Keep this intro</p>", body=[("text", PROJECT_BODIES_EN["behavior-dynamics"])],
        )
        self.home_cs.add_child(instance=self.project)
        self.project.save_revision().publish()
        self.collaboration = Collaboration.objects.create(
            locale=self.cs, name="University of Oxford", description="International collaboration",
        )
        self.home.refresh_from_db()
        self.home_cs.refresh_from_db()
        self.project.refresh_from_db()
        self.placeholder.refresh_from_db()

    def remove_financing_marker(self, home):
        for revision in home.revisions.all():
            revision.content.pop("about_financing", None)
            revision.save(update_fields=["content"])

    def upgrade(self, **options):
        output = StringIO()
        call_command("upgrade_biglab_content", stdout=output, **options)
        return output.getvalue()

    def test_default_dry_run_and_explicit_dry_run_write_nothing(self):
        pages = list(Page.objects.order_by("pk").values())
        homes = list(HomePage.objects.order_by("pk").values())
        projects = list(ProjectPage.objects.order_by("pk").values())
        revisions = list(self.home.revisions.order_by("pk").values())
        for options in ({}, {"dry_run": True}):
            output = self.upgrade(**options)
            self.assertIn("Dry run", output)
            self.assertIn("home_mission: 2", output)
            self.assertIn("parta_placeholders: 1", output)
            self.assertIn("czech_project_bodies: 1", output)
            self.assertNotIn("Oxford", output)
            self.assertEqual(pages, list(Page.objects.order_by("pk").values()))
            self.assertEqual(homes, list(HomePage.objects.order_by("pk").values()))
            self.assertEqual(projects, list(ProjectPage.objects.order_by("pk").values()))
            self.assertEqual(revisions, list(self.home.revisions.order_by("pk").values()))
            self.collaboration.refresh_from_db()
            self.assertEqual(self.collaboration.description, "International collaboration")

    def test_apply_repairs_scaffold_preserves_ids_and_is_idempotent(self):
        field = self.home._meta.get_field("sections")
        # Compare canonical StructBlock values including Wagtail's optional defaults.
        for block in self.home.sections:
            block.value
        before = field.get_prep_value(self.home.sections)
        body_id = self.project.body[0].id
        output = self.upgrade(apply=True)
        self.assertIn("home_financing: 2", output)
        self.home.refresh_from_db()
        self.home_cs.refresh_from_db()
        for block in self.home.sections:
            block.value
        after = field.get_prep_value(self.home.sections)
        self.assertEqual([block["id"] for block in before], [block["id"] for block in after])
        self.assertEqual(before[1], after[1])
        self.assertEqual(self.home.title, "About BIG Lab")
        self.assertEqual(self.home.hero_title, MISSION["en"]["hero_title"])
        self.assertEqual(str(self.home.sections[0].value["intro"]), MISSION["en"]["intro"])
        self.assertEqual(str(self.home_cs.sections[0].value["text"]), MISSION["cs"]["text"])
        self.assertTrue(self.home.about_financing)
        self.assertFalse(self.home.has_unpublished_changes)
        self.placeholder.refresh_from_db()
        self.assertFalse(self.placeholder.live)
        self.assertEqual(str(self.placeholder.intro), PLACEHOLDER_INTROS["en"])
        self.project.refresh_from_db()
        self.assertEqual(str(self.project.body[0].value), PROJECT_BODIES_CS["behavior-dynamics"])
        self.assertEqual(self.project.body[0].id, body_id)
        self.assertEqual(str(self.project.intro), "<p>Keep this intro</p>")
        self.collaboration.refresh_from_db()
        self.assertEqual(self.collaboration.description, "Mezinárodní spolupráce")
        self.assertIn("total_actions: 0", self.upgrade(apply=True))

    def test_edited_placeholder_supporting_content_is_not_unpublished(self):
        self.placeholder.after_body = [("text", "<p>Confirmed materials</p>")]
        self.placeholder.save_revision().publish()
        self.upgrade(apply=True)
        self.placeholder.refresh_from_db()
        self.assertTrue(self.placeholder.live)
        self.assertIn("Confirmed materials", str(self.placeholder.after_body))

    def test_edited_placeholder_intro_body_and_sections_are_preserved(self):
        changes = (
            ("for-parents", {"intro": "<p>Confirmed parent information</p>"}),
            ("for-schools", {"body": [("text", "<p>Confirmed school information</p>")]}),
            ("results", {"sections": [("about", {"title": "Confirmed results", "text": "<p>Supplied results</p>", "intro": "", "anchor": "results", "theme": "paper", "is_visible": True})]}),
        )
        for slug, fields in changes:
            with self.subTest(slug=slug):
                child = ContentPage(title=slug, slug=slug, live=False, intro=PLACEHOLDER_INTROS["en"], **{key: value for key, value in fields.items() if key != "intro"})
                if "intro" in fields:
                    child.intro = fields["intro"]
                self.parta.add_child(instance=child)
                child.save_revision().publish()
                self.upgrade(apply=True)
                child.refresh_from_db()
                self.assertTrue(child.live)

    def test_exact_czech_placeholder_is_unpublished_without_erasing_copy(self):
        parta_cs = self.parta.copy_for_translation(self.cs)
        parta_cs.save_revision().publish()
        child = ContentPage(title="Výsledky", slug="results", live=False, intro=PLACEHOLDER_INTROS["cs"])
        parta_cs.add_child(instance=child)
        child.save_revision().publish()
        self.upgrade(apply=True)
        child.refresh_from_db()
        self.assertFalse(child.live)
        self.assertEqual(child.title, "Výsledky")
        self.assertEqual(str(child.intro), PLACEHOLDER_INTROS["cs"])
        self.assertTrue(child.revisions.exists())

    def test_unpublished_changes_are_never_published_or_discarded(self):
        for page in (self.home, self.placeholder, self.project):
            page.intro = "<p>Editor draft</p>"
            page.save_revision()
        self.upgrade(apply=True)
        for page in (self.home, self.placeholder, self.project):
            page.refresh_from_db()
            self.assertTrue(page.has_unpublished_changes)
            self.assertTrue(page.live)
            self.assertEqual(str(page.get_latest_revision_as_object().intro), "<p>Editor draft</p>")
        self.assertEqual(self.home.hero_title, "About BIG Lab")
        self.assertEqual(str(self.project.body[0].value), PROJECT_BODIES_EN["behavior-dynamics"])

    def test_custom_about_heading_and_custom_translation_are_preserved(self):
        self.home.sections[0].value["title"] = "Custom editorial heading"
        self.home.save_revision().publish()
        self.project.body = [("text", "<p>Vlastní český text</p>")]
        self.project.save_revision().publish()
        self.collaboration.description = "Vlastní popis spolupráce"
        self.collaboration.save()
        self.upgrade(apply=True)
        self.home.refresh_from_db()
        self.project.refresh_from_db()
        self.collaboration.refresh_from_db()
        self.assertFalse(self.home.hero_summary)
        self.assertEqual(str(self.project.body[0].value), "<p>Vlastní český text</p>")
        self.assertEqual(self.collaboration.description, "Vlastní popis spolupráce")

    def test_intentionally_cleared_home_content_is_not_restored(self):
        self.home.intro = "<p>Earlier real content</p>"
        self.home.save_revision().publish()
        self.home.intro = ""
        self.home.save_revision().publish()
        self.upgrade(apply=True)
        self.home.refresh_from_db()
        self.assertFalse(self.home.intro)
        self.assertFalse(self.home.hero_summary)

    def test_empty_financing_marker_is_respected_while_mission_is_repaired(self):
        self.home.save_revision().publish()
        self.upgrade(apply=True)
        self.home.refresh_from_db()
        self.assertTrue(self.home.hero_summary)
        self.assertFalse(self.home.about_financing)

    def inherited_czech_home(self):
        self.parta.intro = PARTA_INTRO["en"]
        self.parta.body = PARTA_BODY["en"]
        self.parta.save_revision().publish()
        parta_cs = self.parta.copy_for_translation(self.cs)
        parta_cs.save_revision().publish()
        self.home_cs.hero_title = MISSION["cs"]["hero_title"]
        self.home_cs.hero_summary = MISSION["cs"]["hero_summary"]
        self.home_cs.intro = MISSION["en"]["intro"]
        self.home_cs.body = [("heading", MISSION["en"]["heading"]), ("text", MISSION["en"]["text"])]
        self.home_cs.sections = default_home_sections(self.home)
        self.home_cs.sections[0].value.update(intro=RichText(MISSION["en"]["intro"]), text=RichText(MISSION["en"]["text"]))
        self.home_cs.sections.append(("about", {"title": "Custom heading", "text": "<p>Keep custom copy</p>", "intro": "", "anchor": "custom", "theme": "coral"}))
        self.home_cs.save_revision().publish()
        self.remove_financing_marker(self.home_cs)
        self.home_cs.refresh_from_db()
        parta_cs.refresh_from_db()
        return parta_cs

    def test_inherited_czech_sections_and_parta_are_translated_idempotently(self):
        parta_cs = self.inherited_czech_home()
        section_ids = [block.id for block in self.home_cs.sections]
        body_ids = [block.id for block in self.home_cs.body]
        parta_body_ids = [block.id for block in parta_cs.body]
        revisions = self.home_cs.revisions.count()
        output = self.upgrade(dry_run=True)
        self.assertIn("czech_home_section_fields: 9", output)
        self.assertIn("czech_featured_project_links: 1", output)
        self.assertIn("czech_parta_intro: 1", output)
        self.assertIn("czech_parta_body: 1", output)
        self.assertEqual(self.home_cs.revisions.count(), revisions)
        self.home_cs.refresh_from_db()
        parta_cs.refresh_from_db()
        self.assertEqual(self.home_cs.sections[1].value["title"], "Research areas")
        self.assertEqual(str(parta_cs.intro), PARTA_INTRO["en"])
        self.upgrade(apply=True)
        self.home_cs.refresh_from_db()
        parta_cs.refresh_from_db()
        self.assertEqual([block.id for block in self.home_cs.sections], section_ids)
        self.assertEqual([block.id for block in self.home_cs.body], body_ids)
        self.assertEqual([block.id for block in parta_cs.body], parta_body_ids)
        expected = dict(default_home_sections(self.home_cs))
        for block in self.home_cs.sections[:5]:
            for key in ("title", "link_label", "label", "button_label"):
                if key in expected[block.block_type]:
                    self.assertEqual(block.value[key], expected[block.block_type][key])
        self.assertEqual(str(self.home_cs.sections[0].value["intro"]), MISSION["cs"]["intro"])
        self.assertEqual(str(self.home_cs.sections[0].value["text"]), MISSION["cs"]["text"])
        self.assertEqual(self.home_cs.sections[3].value["project"].pk, parta_cs.pk)
        self.assertEqual(str(self.home_cs.intro), MISSION["cs"]["intro"])
        self.assertEqual(str(self.home_cs.body[1].value), MISSION["cs"]["text"])
        self.assertEqual(self.home_cs.hero_summary, MISSION["cs"]["hero_summary"])
        self.assertTrue(self.home_cs.about_financing)
        self.assertEqual(str(self.home_cs.sections[5].value["text"]), "<p>Keep custom copy</p>")
        self.assertEqual(str(parta_cs.intro), PARTA_INTRO["cs"])
        self.assertEqual([(block.block_type, str(block.value)) for block in parta_cs.body], PARTA_BODY["cs"])
        self.assertIn("total_actions: 0", self.upgrade(apply=True))

    def test_czech_editor_labels_copy_and_project_selection_are_preserved(self):
        parta_cs = self.inherited_czech_home()
        self.home_cs.sections[0].value.update(title="Vlastní nadpis", intro=RichText("<p>Vlastní úvod</p>"), text=RichText("<p>Vlastní popis</p>"))
        self.home_cs.sections[1].value.update(title="Vlastní výzkum", link_label="Vlastní odkaz")
        self.home_cs.sections[2].value.update(title="Vlastní tým", link_label="Naši kolegové")
        self.home_cs.sections[3].value.update(label="Vlastní značka", button_label="Vlastní tlačítko", project=self.project)
        self.home_cs.sections[4].value["title"] = "Vlastní novinky"
        self.home_cs.intro = "<p>Vlastní kořenový úvod</p>"
        self.home_cs.body = [("text", "<p>Vlastní kořenový text</p>")]
        self.home_cs.save_revision().publish()
        parta_cs.intro = "<p>Potvrzený popis Party</p>"
        parta_cs.body = [("text", "<p>Potvrzené informace</p>")]
        parta_cs.save_revision().publish()
        self.home_cs.refresh_from_db()
        field = self.home_cs._meta.get_field("sections")
        before = field.get_prep_value(self.home_cs.sections)
        self.upgrade(apply=True)
        self.home_cs.refresh_from_db()
        parta_cs.refresh_from_db()
        self.assertEqual(field.get_prep_value(self.home_cs.sections), before)
        self.assertEqual(str(self.home_cs.intro), "<p>Vlastní kořenový úvod</p>")
        self.assertEqual(str(self.home_cs.body[0].value), "<p>Vlastní kořenový text</p>")
        self.assertEqual(str(parta_cs.intro), "<p>Potvrzený popis Party</p>")
        self.assertEqual(str(parta_cs.body[0].value), "<p>Potvrzené informace</p>")

    def test_czech_inherited_defaults_with_unpublished_changes_are_skipped(self):
        parta_cs = self.inherited_czech_home()
        self.home_cs.intro = "<p>New homepage draft</p>"
        self.home_cs.save_revision()
        parta_cs.intro = "<p>New project draft</p>"
        parta_cs.save_revision()
        self.upgrade(apply=True)
        self.home_cs.refresh_from_db()
        parta_cs.refresh_from_db()
        self.assertEqual(self.home_cs.sections[1].value["title"], "Research areas")
        self.assertEqual(str(parta_cs.intro), PARTA_INTRO["en"])
        self.assertTrue(self.home_cs.has_unpublished_changes)
        self.assertTrue(parta_cs.has_unpublished_changes)
        self.assertEqual(str(self.home_cs.get_latest_revision_as_object().intro), "<p>New homepage draft</p>")
        self.assertEqual(str(parta_cs.get_latest_revision_as_object().intro), "<p>New project draft</p>")

    def test_populated_czech_mission_keeps_empty_financing_marker(self):
        self.inherited_czech_home()
        self.home_cs.save_revision().publish()
        self.upgrade(apply=True)
        self.home_cs.refresh_from_db()
        self.assertEqual(self.home_cs.sections[1].value["title"], "Oblasti výzkumu")
        self.assertFalse(self.home_cs.about_financing)

    def test_populated_czech_mission_keeps_previously_cleared_financing_empty(self):
        self.inherited_czech_home()
        self.home_cs.about_financing = "<p>Earlier funding copy</p>"
        self.home_cs.save_revision().publish()
        self.home_cs.about_financing = ""
        self.home_cs.save_revision().publish()
        self.upgrade(apply=True)
        self.home_cs.refresh_from_db()
        self.assertFalse(self.home_cs.about_financing)

    def test_previously_populated_financing_is_not_restored_after_clearing(self):
        self.home.about_financing = "<p>Previous funding statement</p>"
        self.home.save_revision().publish()
        self.home.about_financing = ""
        self.home.save_revision().publish()
        self.upgrade(apply=True)
        self.home.refresh_from_db()
        self.assertFalse(self.home.about_financing)


class DeploymentSettingsTests(SimpleTestCase):
    def environment(self, module):
        env = os.environ.copy()
        for name in (
            "DJANGO_SECRET_KEY", "DJANGO_ALLOWED_HOSTS", "DJANGO_CSRF_TRUSTED_ORIGINS",
            "WAGTAILADMIN_BASE_URL", "SQLITE_PATH", "MEDIA_ROOT", "STATIC_ROOT",
        ):
            env.pop(name, None)
        env["DJANGO_SETTINGS_MODULE"] = module
        return env

    def run_python(self, *arguments, env):
        return subprocess.run(
            [sys.executable, *arguments], cwd=ROOT, env=env,
            capture_output=True, text=True, timeout=120,
        )

    def test_collectstatic_build_requires_no_runtime_credentials(self):
        env = self.environment("config.settings.build")
        with tempfile.TemporaryDirectory() as directory:
            env["STATIC_ROOT"] = directory
            result = self.run_python(
                "manage.py", "collectstatic", "--noinput", "--clear", "--verbosity=0", env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(directory) / "wagtailadmin" / "css" / "core.css").exists())

    def test_production_still_requires_a_runtime_secret(self):
        result = self.run_python(
            "-c", "from django.conf import settings; print(settings.SECRET_KEY)",
            env=self.environment("config.settings.production"),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY environment variable is required", result.stderr)

    def test_build_and_runtime_use_matching_storage(self):
        env = self.environment("config.settings.production")
        env.update(
            DJANGO_SECRET_KEY="test-runtime-key-not-a-deployment-secret",
            DJANGO_ALLOWED_HOSTS="example.invalid",
            WAGTAILADMIN_BASE_URL="https://example.invalid",
        )
        result = self.run_python(
            "-c",
            "from config.settings import build, production; "
            "assert build.STORAGES['staticfiles'] == production.STORAGES['staticfiles']; "
            "assert production.SECRET_KEY != build.SECRET_KEY; "
            "assert not production.DEBUG; "
            "assert production.SESSION_COOKIE_SECURE; "
            "assert production.SECURE_SSL_REDIRECT",
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_initial_seed_is_safe_in_an_isolated_installation(self):
        script = '''
import django
from django.core.management import call_command

django.setup()
call_command("migrate", verbosity=0)
call_command("seed_biglab", bootstrap=True, verbosity=0)
from home.models import HomePage, ProjectPage, Collaboration
from wagtail.models import Locale

home = HomePage.objects.get(depth=2, locale__language_code="en")
parta = ProjectPage.objects.child_of(home).get(slug="parta")
assert parta.get_children().count() == 7
assert not parta.get_children().live().exists()
cs = Locale.objects.get(language_code="cs")
parta_cs = parta.get_translation(cs)
assert parta_cs.get_children().count() == 7
assert not parta_cs.get_children().live().exists()
project = ProjectPage.objects.get(slug="behavior-dynamics", locale=cs)
assert "osobních zkušeností" in str(project.body)
assert Collaboration.objects.filter(locale=cs, description="Mezinárodní spolupráce").count() == 3
assert home.about_financing
assert home.hero_title == "How do individual choices become collective change?"
assert home.sections[0].block_type == "about"
home_cs = home.get_translation(cs).specific
assert home_cs.sections[0].value["title"] == "Od individuální změny k sociálnímu šíření"
assert home_cs.sections[3].value["project"].locale_id == cs.pk
published_child = parta.get_children().specific().get(slug="for-schools")
published_child.body = [("text", "<p>Confirmed editor materials</p>")]
published_child.save_revision().publish()
home.intro = ""
home.body = []
home.sections = []
home.about_financing = ""
home.save_revision().publish()
child = parta.get_children().specific().get(slug="results")
child.intro = "<p>Editor draft only</p>"
child.save_revision()
call_command("seed_biglab", bootstrap=True, force=True, verbosity=0)
home.refresh_from_db()
assert not home.intro and not home.body and not home.sections and not home.about_financing
child.refresh_from_db()
assert not child.live
published_child.refresh_from_db()
assert published_child.live
assert "Confirmed editor materials" in str(published_child.body)
assert "Editor draft only" in str(child.get_latest_revision_as_object().intro)
'''
        env = self.environment("config.settings.dev")
        with tempfile.TemporaryDirectory() as directory:
            env["SQLITE_PATH"] = str(Path(directory) / "db.sqlite3")
            env["MEDIA_ROOT"] = str(Path(directory) / "media")
            result = self.run_python("-c", script, env=env)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_development_snapshot_seeds_fresh_database_with_different_ids(self):
        script = '''
import django
import json
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import connections
django.setup()
from wagtail.models import Site
from wagtail.images import get_image_model
from home.models import ContentPage, HomePage, ProjectPage
from home.content_snapshot import DEFAULT_BUNDLE, import_bundle
try:
    call_command("migrate", verbosity=0)
    home = Site.objects.get(is_default_site=True).root_page.specific
    home.add_child(instance=ContentPage(title="Unrelated target page", slug="unrelated", live=False))
    payload = BytesIO()
    Image.new("RGB", (10,10), "red").save(payload, format="JPEG")
    get_image_model().objects.create(title="Unrelated photo", file=SimpleUploadedFile("other.jpg", payload.getvalue(), "image/jpeg"))
    result = import_bundle()
    snapshot = json.loads((DEFAULT_BUNDLE / "content.json").read_text(encoding="utf-8"))
    expected_home = next(p for p in snapshot["pages"] if p["id"] == snapshot["default_root"])
    home.refresh_from_db()
    assert home.hero_summary == expected_home["fields"]["hero_summary"]
    assert home.hero_title == expected_home["fields"]["hero_title"]
    assert HomePage.objects.get(locale__language_code="cs").hero_summary
    assert not ProjectPage.objects.get(slug="parta", locale__language_code="en").get_children().live().exists()
    assert get_image_model().objects.count() == len(snapshot["assets"]) + 1
    assert import_bundle()["pages"] == 0
finally:
    connections.close_all()
'''
        env = self.environment("config.settings.dev")
        with tempfile.TemporaryDirectory() as directory:
            env["SQLITE_PATH"] = str(Path(directory) / "db.sqlite3")
            env["MEDIA_ROOT"] = str(Path(directory) / "media")
            result = self.run_python("-c", script, env=env)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_backup_archive_closes_sqlite_copy_and_restores_cleanly(self):
        script = '''
import json
import sqlite3
import tarfile
import tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
import django
from django.conf import settings
from django.core.management import call_command
from django.db import connections

django.setup()
call_command("migrate", verbosity=0)
media = Path(settings.MEDIA_ROOT)
media.mkdir(parents=True)
(media / "test-document.txt").write_text("Verified media", encoding="utf-8")
output = media.parent / "backups"
original_connect = sqlite3.connect
copies = []
def tracked_connect(*args, **kwargs):
    connection = original_connect(*args, **kwargs)
    copies.append(connection)
    return connection
# Open Django's source connection before intercepting only the backup destination.
connections["default"].ensure_connection()
with patch("home.management.commands.backup_site.sqlite3.connect", side_effect=tracked_connect):
    call_command("backup_site", output_dir=output)
assert len(copies) == 1
try:
    copies[0].execute("SELECT 1")
except sqlite3.ProgrammingError:
    pass
else:
    raise AssertionError("The SQLite backup destination was not closed")
archive_path, = output.glob("biglab-backup-*.tar.gz")
with tarfile.open(archive_path) as archive:
    assert {"db.sqlite3", "manifest.json", "media/test-document.txt"} <= set(archive.getnames())
    manifest = json.load(archive.extractfile("manifest.json"))
    assert manifest["media_files"] == 1
    assert archive.extractfile("media/test-document.txt").read() == b"Verified media"
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "db.sqlite3"
        database.write_bytes(archive.extractfile("db.sqlite3").read())
        with closing(original_connect(database)) as restored:
            assert restored.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            assert restored.execute("SELECT COUNT(*) FROM wagtailcore_page").fetchone()[0] > 0
        database.unlink()  # Also verifies closed handles on Windows.
connections.close_all()
'''
        env = self.environment("config.settings.dev")
        with tempfile.TemporaryDirectory() as directory:
            env["SQLITE_PATH"] = str(Path(directory) / "db.sqlite3")
            env["MEDIA_ROOT"] = str(Path(directory) / "media")
            result = self.run_python("-c", script, env=env)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_full_reset_restores_real_bilingual_snapshot_after_cms_testing(self):
        script = '''
import json
import django
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connections
django.setup()
from home.content_snapshot import DEFAULT_BUNDLE, import_bundle
from home.models import ContentPage, HomePage, PersonPage, ProjectPage, Publication
from wagtail.models import Page, Site
try:
    call_command("migrate", verbosity=0)
    import_bundle()
    snapshot = json.loads((DEFAULT_BUNDLE / "content.json").read_text(encoding="utf-8"))
    site = Site.objects.get(is_default_site=True)
    site.hostname = "test-deployment.example"
    site.port = 443
    site.save()
    user = get_user_model().objects.create_user("editor", password="test-password")
    password_hash = user.password
    home = HomePage.objects.get(locale__language_code="en", depth=2)
    cs_home = HomePage.objects.get(locale__language_code="cs", depth=2)
    parta = ProjectPage.objects.child_of(cs_home).get(slug="parta")
    extra = parta.add_child(instance=ContentPage(title="Test Czech page", slug="test-czech-page", locale=cs_home.locale))
    extra.add_child(instance=ContentPage(title="Nested draft", slug="nested-draft", locale=cs_home.locale, live=False))
    PersonPage.objects.filter(locale=cs_home.locale).first().delete()
    home.hero_title = "Test homepage"
    home.save_revision().publish()
    Publication.objects.create(locale=home.locale, title="Test article", authors="Tester", year=2026)
    call_command("seed_biglab", reset=True, verbosity=0)
    assert Page.objects.filter(depth__gte=2).count() == len(snapshot["pages"])
    assert not Page.objects.filter(slug__in=["test-czech-page", "nested-draft"]).exists()
    assert not Publication.objects.filter(title="Test article").exists()
    for item in snapshot["pages"]:
        restored = Page.objects.get(translation_key=item["translation_key"], locale__language_code=item["locale"])
        assert restored.slug == item["fields"]["slug"]
        assert restored.live == item["live"]
    home.refresh_from_db()
    home.hero_title = "Approved editor change after reset"
    home.save_revision().publish()
    assert import_bundle(if_changed=True)["unchanged"]
    home.refresh_from_db()
    assert home.hero_title == "Approved editor change after reset"
    user.refresh_from_db()
    site.refresh_from_db()
    assert user.password == password_hash
    assert (site.hostname, site.port) == ("test-deployment.example", 443)
finally:
    connections.close_all()
'''
        env = self.environment("config.settings.dev")
        with tempfile.TemporaryDirectory() as directory:
            env["SQLITE_PATH"] = str(Path(directory) / "db.sqlite3")
            env["MEDIA_ROOT"] = str(Path(directory) / "media")
            result = self.run_python("-c", script, env=env)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_sqlite_container_has_one_worker_and_persistent_paths(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("DJANGO_SETTINGS_MODULE=config.settings.build python manage.py collectstatic", dockerfile)
        entrypoint = (ROOT / "deploy/entrypoint.sh").read_text(encoding="utf-8")
        self.assertIn("--workers 1 --threads 2", entrypoint)
        self.assertIn("SQLITE_PATH=/data/db.sqlite3", dockerfile)
        self.assertIn("MEDIA_ROOT=/data/media", dockerfile)
        self.assertNotIn("DJANGO_SECRET_KEY", dockerfile)
