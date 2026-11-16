"""Research destinations reuse editorial sections and preserve publication data."""
from importlib import import_module

from bs4 import BeautifulSoup
from django.apps import apps
from django.test import SimpleTestCase
from wagtail.models import Locale, Page, Site
from wagtail.test.utils import WagtailPageTestCase

from home.models import HomePage, InterfaceText, Publication, SciencePage


class ResearchCollectionTests(WagtailPageTestCase):
    def setUp(self):
        self.home = Page.get_first_root_node().add_child(instance=HomePage(title="Lab"))
        self.research = self.home.add_child(instance=SciencePage(title="Research", slug="science"))
        self.research.sections = [
            ("publications", {"is_visible": True, "title": "Our papers", "intro": "<p>Editorial introduction.</p>"}),
            ("collaborations", {"is_visible": True}),
            ("project_list", {"is_visible": False, "status": "finished"}),
        ]
        self.research.save_revision().publish()
        Site.objects.update_or_create(hostname="localhost", defaults={"root_page": self.home, "is_default_site": True})

    def get_collection(self, suffix="publications/", query=""):
        response = self.client.get(self.research.url + suffix + query)
        self.assertEqual(response.status_code, 200)
        return BeautifulSoup(response.content, "html.parser")

    def test_separate_destinations_reuse_custom_copy_and_live_snippets(self):
        Publication.objects.create(title="Latest paper", authors="Team", year=2026, locale=self.home.locale)
        soup = self.get_collection()
        self.assertEqual(soup.select_one("main h1").get_text(), "Our papers")
        self.assertEqual(soup.title.get_text().strip(), "Our papers — BIG Lab")
        self.assertEqual(len(soup.select("main h1")), 1)
        self.assertIn("Editorial introduction.", soup.select_one("main").get_text())
        self.assertIn("Latest paper", soup.select_one("main").get_text())
        self.assertTrue(soup.select_one('link[rel="canonical"]')["href"].endswith("/science/publications/"))
        self.assertEqual(soup.select_one('.breadcrumbs [aria-current="page"]').get_text(strip=True), "Our papers")
        self.assertEqual(len(self.get_collection("collaboration/").select("main h1")), 1)

    def test_visibility_controls_navigation_and_routing_together(self):
        self.assertEqual(self.client.get(self.research.url + "finished-projects/").status_code, 404)
        self.research.sections[0].value["is_visible"] = False
        self.research.save_revision().publish()
        self.assertEqual(self.client.get(self.research.url + "publications/").status_code, 404)
        landing = BeautifulSoup(self.client.get(self.research.url).content, "html.parser")
        self.assertFalse(landing.select('a[href$="/publications/"]'))
        self.research.sections[2].value["is_visible"] = True
        self.research.save_revision().publish()
        self.get_collection("finished-projects/")

    def test_language_switch_and_metadata_keep_the_same_collection(self):
        cs, _ = Locale.objects.get_or_create(language_code="cs")
        home_cs = self.home.copy_for_translation(cs)
        home_cs.save_revision().publish()
        research_cs = self.research.copy_for_translation(cs)
        research_cs.save_revision().publish()
        soup = self.get_collection(query="?design=2")
        expected = research_cs.url + "publications/"
        self.assertEqual(soup.select_one('.language-options a[lang="cs"]')["href"], expected + "?design=2")
        self.assertTrue(soup.select_one('link[hreflang="cs"]')["href"].endswith(expected))
        self.assertEqual(self.client.get(expected).status_code, 200)

    def test_empty_builder_uses_the_existing_editor_defaults(self):
        self.research.sections = []
        self.research.save_revision().publish()
        self.get_collection()
        self.get_collection("collaboration/")
        self.assertEqual(self.client.get(self.research.url + "finished-projects/").status_code, 404)

    def test_label_migration_preserves_custom_copy_drafts_and_czech(self):
        migration = import_module("home.migrations.0026_document_research_structure")
        self.research.title = "Science"
        self.research.save_revision().publish()
        section = self.research.sections[0]
        section.value["intro"] = section.block.child_blocks["intro"].to_python("<p>Unpublished editorial work.</p>")
        draft = self.research.save_revision()
        cs, _ = Locale.objects.get_or_create(language_code="cs")
        custom = InterfaceText.objects.create(locale=self.home.locale, key="explore_science", text="Explore our work")
        old_default = InterfaceText.objects.create(locale=self.home.locale, key="science", text="Science")
        czech = InterfaceText.objects.create(locale=cs, key="science", text="Výzkum")
        migration.update_research_labels(apps, None)
        migration.update_research_labels(apps, None)
        self.research.refresh_from_db()
        draft.refresh_from_db()
        custom.refresh_from_db()
        old_default.refresh_from_db()
        czech.refresh_from_db()
        self.assertEqual(self.research.title, "Research")
        self.assertEqual(str(self.research.sections[0].value["intro"]), "<p>Editorial introduction.</p>")
        self.assertEqual(draft.content["title"], "Research")
        self.assertIn("Unpublished editorial work.", str(draft.content["sections"]))
        self.assertEqual(custom.text, "Explore our work")
        self.assertEqual(old_default.text, "Research")
        self.assertEqual(czech.text, "Výzkum")


class ResearchLabelTransformationTests(SimpleTestCase):
    def test_only_exact_old_interface_labels_change(self):
        transform = import_module("home.migrations.0026_document_research_structure").rename_sections
        source = [
            {"type": "research", "value": {"title": "Science", "intro": "<p>Network science.</p>", "link_label": "All science"}},
            {"type": "research", "value": {"title": "Our science", "link_label": "Read more"}},
            {"type": "page_links", "value": {"pages": [{"value": {"label": "Science", "page": 42}}]}},
        ]
        result, changed = transform(source)
        self.assertTrue(changed)
        self.assertEqual(result[0]["value"], {"title": "Research", "intro": "<p>Network science.</p>", "link_label": "All research"})
        self.assertEqual(result[1], source[1])
        self.assertEqual(result[2]["value"]["pages"][0]["value"], {"label": "Research", "page": 42})
        self.assertEqual(source[0]["value"]["title"], "Science")
        self.assertFalse(transform(result)[1])
