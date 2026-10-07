"""Content growth must preserve a bounded homepage and discoverable descendants."""

from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from django.test import RequestFactory
from wagtail.models import Locale, Page, Site
from wagtail.test.utils import WagtailPageTestCase

from home.models import ContentPage, HomePage, ProjectPage, Publication, SciencePage


class ContentGrowthTests(WagtailPageTestCase):
    def setUp(self):
        self.home = Page.get_first_root_node().add_child(instance=HomePage(title="Growth lab"))
        self.science = self.home.add_child(instance=SciencePage(title="Science", show_in_menus=True))
        self.science.sections = [("publications", {"is_visible": True, "anchor": "papers"})]
        self.science.save()
        self.home.sections = [("publications", {"is_visible": True, "anchor": "publications"})]
        self.home.save()
        Site.objects.update_or_create(hostname="localhost", defaults={"root_page": self.home, "is_default_site": True})

    def render_page(self, page):
        request = RequestFactory().get(page.url or "/")
        return BeautifulSoup(render_to_string(page.get_template(request), page.get_context(request), request=request), "html.parser")

    def add_publications(self, count=100):
        Publication.objects.bulk_create([
            Publication(title=f"Paper {number:03}", authors="Research team", year=2025, locale=self.home.locale)
            for number in range(count)
        ])

    def test_homepage_is_bounded_and_its_link_opens_the_complete_collection(self):
        self.add_publications()
        cs, _ = Locale.objects.get_or_create(language_code="cs")
        Publication.objects.create(title="Other language", authors="Team", year=2029, locale=cs)
        soup = self.render_page(self.home)
        self.assertEqual(len(soup.select(".publication-section .publication-list > li")), 3)
        self.assertNotIn("Other language", soup.get_text())
        self.assertEqual(soup.select_one(".publication-all-link")["href"], self.science.url + "#papers")
        full = self.render_page(self.science)
        self.assertEqual(len(full.select(".publication-list > li")), 100)
        self.assertIsNotNone(full.select_one("#papers"))
        self.assertFalse(full.select(".publication-all-link"))

    def test_editor_limit_and_newest_publication_survive_content_growth(self):
        self.add_publications()
        self.home.sections[0].value["homepage_limit"] = 6
        self.home.save()
        newest = Publication.objects.create(title="New discovery", authors="Team", year=2026, locale=self.home.locale)
        soup = self.render_page(self.home)
        self.assertEqual(len(soup.select(".publication-list > li")), 6)
        self.assertEqual(soup.select_one(".publication-copy h3").get_text(), newest.title)

    def test_hidden_science_collection_does_not_create_a_dead_full_list_link(self):
        self.add_publications(2)
        self.science.sections[0].value["is_visible"] = False
        self.science.save()
        self.assertFalse(self.render_page(self.home).select(".publication-all-link"))

    def test_deep_pages_are_reachable_in_inline_and_standalone_parents(self):
        project = self.home.add_child(instance=ProjectPage(title="PARTA", show_in_menus=True))
        chain = [project]
        for number in range(4):
            chain.append(chain[-1].add_child(instance=ContentPage(title=f"Level {number + 1}", show_in_menus=True)))
        inline = self.render_page(project)
        self.assertEqual(inline.select_one("[data-child-navigation] a")["href"], chain[2].url)
        for parent, child in zip(chain[1:-1], chain[2:]):
            soup = self.render_page(parent)
            self.assertEqual(soup.select_one("[data-child-navigation] a")["href"], child.url)
            self.assertEqual(len(soup.select("h1")), 1)
            ids = [node["id"] for node in soup.select("[id]")]
            self.assertEqual(len(ids), len(set(ids)))
        self.assertFalse(self.render_page(chain[-1]).select("[data-child-navigation]"))

    def test_local_navigation_skips_drafts_and_pages_hidden_from_menus(self):
        parent = self.home.add_child(instance=ContentPage(title="Overview"))
        child = parent.add_child(instance=ContentPage(title="Visible", show_in_menus=True))
        parent.add_child(instance=ContentPage(title="Draft", live=False, show_in_menus=True))
        parent.add_child(instance=ContentPage(title="Hidden", show_in_menus=False))
        soup = self.render_page(parent)
        links = soup.select("[data-child-navigation] a")
        self.assertEqual([link["href"] for link in links], [child.url])

    def test_inline_collection_does_not_repeat_automatic_child_links(self):
        parent = self.home.add_child(instance=ContentPage(title="Overview"))
        child = parent.add_child(instance=ContentPage(title="Details", show_in_menus=True))
        parent.sections = [("child_sections", {"is_visible": True})]
        parent.save()
        soup = self.render_page(parent)
        self.assertIsNotNone(soup.select_one(f"#section-{child.pk}"))
        self.assertFalse(soup.select("[data-child-navigation]"))

    def test_czech_preview_and_child_navigation_stay_in_the_czech_tree(self):
        cs, _ = Locale.objects.get_or_create(language_code="cs")
        home = self.home.copy_for_translation(cs)
        home.save_revision().publish()
        science = self.science.copy_for_translation(cs)
        science.save_revision().publish()
        Publication.objects.create(title="Studie", authors="Tým", year=2026, locale=cs)
        soup = self.render_page(home)
        link = soup.select_one(".publication-all-link")
        self.assertEqual(link.get_text(), "Všechny publikace")
        self.assertEqual(link["href"], science.url + "#papers")
        parent = home.add_child(instance=ContentPage(title="Přehled", locale=cs))
        child = parent.add_child(instance=ContentPage(title="Podrobnosti", locale=cs, show_in_menus=True))
        soup = self.render_page(parent)
        self.assertEqual(soup.select_one("[data-child-navigation] h2").get_text(), "V této sekci")
        self.assertEqual(soup.select_one("[data-child-navigation] a")["href"], child.url)
