from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from django.test import RequestFactory
from wagtail.models import Locale, Page, Site
from wagtail.test.utils import WagtailPageTestCase

from home.models import ContentPage, HomePage, PeopleIndexPage, ProjectPage, SciencePage
from home.templatetags.navigation_tags import _build_menu, constellation_nodes, contact_url, section_url


class FrontendContractTests(WagtailPageTestCase):
    def setUp(self):
        self.home = Page.get_first_root_node().add_child(instance=HomePage(title="Lab"))
        self.science = self.home.add_child(instance=SciencePage(title="Science", show_in_menus=True))
        self.project = self.home.add_child(instance=ProjectPage(title="Parta", show_in_menus=True))

    def test_navigation_keeps_submenu_inside_its_parent_list(self):
        self.project.add_child(instance=ContentPage(title="Parents", show_in_menus=True))
        html = render_to_string("home/includes/navigation_menu.html", {
            "menu_items": _build_menu(self.home), "page": self.home,
            "request": RequestFactory().get("/"), "nested": False,
        })
        soup = BeautifulSoup(html, "html.parser")
        self.assertEqual(len(soup.select("ul.site-nav > li")), 2)
        self.assertEqual(len(soup.select("ul.site-nav > li > ul.submenu > li")), 1)
        self.assertEqual(len(soup.select("ul.site-nav > li > ul.submenu > li a")), 1)
        self.assertNotIn("</ul>\n\n    <li", html)

    def test_constellation_uses_actual_labels_and_inline_destinations(self):
        areas = [self.science.add_child(instance=ContentPage(title=f"Topic {i}")) for i in range(9)]
        nodes = constellation_nodes(areas)
        self.assertEqual(len(nodes), 9)
        for area, node in zip(areas, nodes):
            self.assertEqual(node["page"].title, area.title)
            self.assertTrue(node["url"].endswith(f"#section-{area.pk}"))
            self.assertGreaterEqual(node["x"], 0)
            self.assertLessEqual(node["x"], 100)
        reordered = constellation_nodes(list(reversed(areas)))
        self.assertEqual(reordered[0]["page"], areas[-1])
        self.assertTrue(reordered[0]["url"].endswith(f"#section-{areas[-1].pk}"))

    def test_hero_entrance_preserves_visible_copy_and_topic_destinations(self):
        Site.objects.update_or_create(hostname="localhost", defaults={"root_page": self.home, "is_default_site": True})
        areas = [self.science.add_child(instance=ContentPage(title=f"Topic {i}")) for i in range(9)]
        self.home.hero_layout = "constellation"
        self.home.hero_title = "Research together"
        self.home.hero_summary = "Our research summary"
        request = RequestFactory().get("/")
        context = self.home.get_context(request)
        context.update(research_areas=areas, science_page=self.science)
        soup = BeautifulSoup(render_to_string("home/home_page.html", context, request=request), "html.parser")
        hero = soup.select_one(".hero[data-hero-entrance]")
        self.assertEqual(hero.select_one("h1").get_text(), self.home.hero_title)
        self.assertFalse(hero.select("[data-network-toggle]"))
        self.assertEqual(hero.select_one(".summary").get_text(), self.home.hero_summary)
        self.assertEqual(hero.select_one(".hero-actions a")["href"], self.science.url)
        self.assertFalse(hero.select("[hidden], .hero-copy[aria-hidden='true'], .constellation-topics [aria-hidden='true']:not(.topic-star)"))
        self.assertFalse(hero.select(".hero-copy [style], .constellation-topics a[style]"))
        self.assertEqual(hero.select_one(".constellation-lines")["aria-hidden"], "true")
        self.assertEqual(hero.select_one(".constellation-lines")["focusable"], "false")
        paths = hero.select(".constellation-connections path[data-constellation-connection]")
        links = hero.select(".constellation-topics a[data-constellation-topic]")
        self.assertEqual(len(paths), len(areas))
        self.assertEqual(len(links), len(areas))
        for index, (path, link, node) in enumerate(zip(paths, links, constellation_nodes(areas))):
            self.assertEqual(path["data-constellation-connection"], str(index))
            self.assertEqual(link["data-constellation-topic"], str(index))
            self.assertEqual(link["href"], node["url"])
            self.assertEqual(link.select_one(".topic-label").get_text(), node["page"].title)

    def test_text_hero_entrance_keeps_optional_content_optional(self):
        self.home.hero_layout = "text"
        self.home.hero_summary = ""
        request = RequestFactory().get("/")
        soup = BeautifulSoup(render_to_string(
            "home/home_page.html", self.home.get_context(request), request=request,
        ), "html.parser")
        hero = soup.select_one(".hero[data-hero-entrance]")
        self.assertIsNotNone(hero.select_one("h1"))
        self.assertIsNone(hero.select_one(".summary"))
        self.assertIsNone(hero.select_one(".constellation"))

    def test_child_menu_uses_direct_route_when_inline_collection_removed(self):
        child = self.project.add_child(instance=ContentPage(title="Parents", show_in_menus=True))
        self.project.sections = [("about", {"title": "Overview", "text": "", "theme": "paper", "is_visible": True})]
        self.project.save_revision().publish()
        menu = _build_menu(self.home)
        self.assertEqual(menu[1]["children"][0]["url"], child.url)

    def test_hidden_inline_collection_uses_real_child_route_everywhere(self):
        child = self.science.add_child(instance=ContentPage(title="Influence", show_in_menus=True))
        self.science.sections = [("child_sections", {"is_visible": False, "title": "", "theme": "paper"})]
        self.science.save_revision().publish()
        self.assertEqual(section_url(child), child.url)
        self.assertEqual(constellation_nodes([child])[0]["url"], child.url)
        menu = _build_menu(self.home)
        self.assertEqual(menu[0]["children"][0]["url"], child.url)
        html = render_to_string("home/sections/research.html", {
            "page": self.home, "science_page": self.science, "research_areas": [child],
            "value": {"is_visible": True, "title": "Research", "limit": 5, "theme": "paper"},
        })
        self.assertIn(f'href="{child.url}"', html)
        self.assertNotIn(f"#section-{child.pk}", html)

    def test_removed_inline_collection_research_rows_use_real_child_route(self):
        child = self.science.add_child(instance=ContentPage(title="Influence"))
        self.science.sections = [("publications", {"is_visible": True, "title": "", "theme": "paper"})]
        self.science.save_revision().publish()
        self.assertEqual(section_url(child), child.url)
        html = render_to_string("home/sections/research.html", {
            "page": self.home, "science_page": self.science, "research_areas": [child],
            "value": {"is_visible": True, "title": "Research", "limit": 5, "theme": "paper"},
        })
        self.assertIn(f'href="{child.url}"', html)
        self.assertNotIn(f"#section-{child.pk}", html)

    def test_mobile_menu_has_a_localized_accessible_name(self):
        request = RequestFactory().get("/")
        html = render_to_string("home/home_page.html", self.home.get_context(request), request=request)
        menu = BeautifulSoup(html, "html.parser").select_one("button.menu-toggle")
        self.assertEqual(menu.get("aria-label"), "Menu")

    def test_language_dropdown_links_to_published_translation_of_current_page(self):
        Site.objects.update_or_create(hostname="localhost", defaults={"root_page": self.home, "is_default_site": True})
        locale, _ = Locale.objects.get_or_create(language_code="cs")
        translated_home = self.home.copy_for_translation(locale)
        translated_science = self.science.copy_for_translation(locale)
        translated_home.save_revision().publish()
        translated_science.save_revision().publish()
        request = RequestFactory().get(self.science.url)
        soup = BeautifulSoup(render_to_string(
            self.science.get_template(request), self.science.get_context(request), request=request,
        ), "html.parser")
        languages = soup.select_one("details.language-nav")
        self.assertEqual(languages.select_one("[aria-current='page']").get_text(strip=True), "English")
        link = languages.select_one("a[hreflang='cs']")
        self.assertEqual(link["href"], translated_science.url)
        self.assertEqual(link.get_text(strip=True), "Česky")
        translated_science.refresh_from_db()
        translated_science.unpublish()
        soup = BeautifulSoup(render_to_string(
            self.science.get_template(request), self.science.get_context(request), request=request,
        ), "html.parser")
        self.assertFalse(soup.select(".language-options a"))

    def test_hidden_custom_contact_does_not_create_a_dead_header_link(self):
        self.home.sections = [("contact", {"title": "", "theme": "paper", "is_visible": False})]
        self.assertEqual(contact_url(self.home), "")
        self.home.sections = [("contact", {"title": "", "anchor": "reach-us", "theme": "paper", "is_visible": True})]
        self.assertTrue(contact_url(self.home).endswith("#reach-us"))

    def test_builder_order_places_editorial_text_below_people(self):
        people = self.home.add_child(instance=PeopleIndexPage(title="Team"))
        people.sections = [
            ("people", {"is_visible": True, "title": "Our team", "theme": "paper", "limit": 24, "show_roles": True}),
            ("about", {"is_visible": True, "title": "Join the lab", "text": "<p>Text below the photos</p>", "theme": "paper"}),
        ]
        request = RequestFactory().get("/")
        html = people.get_template(request)
        content = render_to_string(html, people.get_context(request), request=request)
        self.assertLess(content.index('class="people-grid'), content.index("Text below the photos"))
        self.assertEqual(BeautifulSoup(content, "html.parser").select("h1")[0].get_text(), "Team")
