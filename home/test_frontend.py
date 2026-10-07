from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from django.test import RequestFactory
from wagtail.models import Locale, Page, Site
from wagtail.test.utils import WagtailPageTestCase

from home.models import ContentPage, HomePage, PeopleIndexPage, PersonPage, ProjectPage, SciencePage
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

    def test_v2_hero_preserves_copy_and_keeps_research_links_in_the_collection(self):
        Site.objects.update_or_create(hostname="localhost", defaults={"root_page": self.home, "is_default_site": True})
        areas = [self.science.add_child(instance=ContentPage(title=f"Topic {i}")) for i in range(9)]
        people = self.home.add_child(instance=PeopleIndexPage(title="Team"))
        self.home.hero_layout = "constellation"
        self.home.hero_title = "Research together"
        self.home.hero_summary = "Our research summary"
        request = RequestFactory().get("/?design=2")
        context = self.home.get_context(request)
        context.update(research_areas=areas, science_page=self.science, people_index=people)
        soup = BeautifulSoup(render_to_string("home/home_page.html", context, request=request), "html.parser")
        self.assertIn("homepage-design-2", soup.body.get("class", []))
        switch = soup.select_one("a[data-design-switch]")
        self.assertIsNotNone(switch)
        self.assertNotIn("design", parse_qs(urlsplit(switch["href"]).query))
        hero = soup.select_one(".hero[data-hero-entrance]")
        self.assertEqual(hero.select_one("h1").get_text(), self.home.hero_title)
        self.assertFalse(hero.select("[data-network-toggle]"))
        self.assertEqual(hero.select_one(".summary").get_text(), self.home.hero_summary)
        self.assertEqual(hero.select_one(".hero-actions a")["href"], self.science.url)
        self.assertEqual(hero.select_one(".hero-actions a.text-link")["href"], people.url)
        self.assertFalse(hero.select(".hero-copy[hidden], .hero-copy[aria-hidden='true']"))
        self.assertFalse(hero.select(".hero-copy [style]"))
        canvas = hero.select_one("canvas[data-research-network]")
        self.assertIsNotNone(canvas)
        self.assertIs(canvas.parent, hero)
        self.assertEqual(canvas["aria-hidden"], "true")
        self.assertFalse(canvas.has_attr("tabindex"))
        self.assertFalse(hero.select(".constellation, .constellation-topics, [data-constellation-topic]"))
        self.assertFalse(hero.select(".central-star, .star-orbit, .constellation-connections, .constellation-caption, [data-network-hint]"))
        self.assertNotIn("Research areas", hero.get_text(" ", strip=True))
        self.assertEqual(soup.select_one(".research-section h2").get_text(), "Research areas")
        links = soup.select("#home-sections .research-row h3 a")
        self.assertEqual(len(links), len(areas))
        for link, node in zip(links, constellation_nodes(areas)):
            self.assertEqual(link["href"], node["url"])
            self.assertEqual(link.get_text(), node["page"].title)
            self.assertNotIn(node["page"].title, hero.get_text(" ", strip=True))

    def test_design_one_is_default_without_central_star_or_network_caption(self):
        Site.objects.update_or_create(hostname="localhost", defaults={"root_page": self.home, "is_default_site": True})
        area = self.science.add_child(instance=ContentPage(title="Research topic"))
        self.home.hero_layout = "constellation"
        for query in ["", "?design=1", "?design=unknown", "?design=02"]:
            with self.subTest(query=query):
                request = RequestFactory().get(f"/{query}")
                context = self.home.get_context(request)
                context.update(research_areas=[area])
                soup = BeautifulSoup(render_to_string("home/home_page.html", context, request=request), "html.parser")
                self.assertIn("homepage-design-1", soup.body.get("class", []))
                self.assertNotIn("homepage-design-2", soup.body.get("class", []))
                hero = soup.select_one(".hero[data-hero-entrance]")
                self.assertFalse(hero.select(".central-star, .star-orbit, .star-dust, .constellation-connections, [data-constellation-connection]"))
                self.assertFalse(hero.select(".constellation-caption, .network-hint, [data-network-hint]"))
                self.assertNotIn("Research areas", hero.get_text(" ", strip=True))
                field = hero.select_one(".constellation-field")
                canvas = field.select_one("canvas[data-research-network]")
                self.assertIsNotNone(canvas)
                self.assertIs(canvas.parent, field)
                self.assertEqual(canvas["aria-hidden"], "true")
                self.assertFalse(canvas.has_attr("tabindex"))
                self.assertFalse(hero.select(":scope > canvas[data-research-network]"))
                self.assertFalse(hero.select("[data-network-toggle]"))
                topic = hero.select_one(".constellation-topics a[data-constellation-topic]")
                self.assertEqual(topic.get_text(strip=True), area.title)
                self.assertEqual(topic["href"], constellation_nodes([area])[0]["url"])
                switch = soup.select_one("a[data-design-switch]")
                self.assertIsNotNone(switch)
                self.assertEqual(parse_qs(urlsplit(switch["href"]).query).get("design"), ["2"])

    def test_text_hero_entrance_keeps_optional_content_optional(self):
        self.home.hero_layout = "text"
        self.home.hero_summary = ""
        request = RequestFactory().get("/?design=2")
        soup = BeautifulSoup(render_to_string(
            "home/home_page.html", self.home.get_context(request), request=request,
        ), "html.parser")
        hero = soup.select_one(".hero[data-hero-entrance]")
        self.assertIsNotNone(hero.select_one("h1"))
        self.assertIsNone(hero.select_one(".summary"))
        self.assertIsNone(hero.select_one(".constellation"))
        self.assertIsNone(hero.select_one("[data-research-network]"))

    def test_v2_network_appears_only_for_constellation_regardless_of_research_topics(self):
        area = self.science.add_child(instance=ContentPage(title="Research topic"))
        request = RequestFactory().get("/?design=2")
        for layout, areas in [
            ("constellation", []), ("constellation", [area]),
            ("image", []), ("image", [area]), ("text", []), ("text", [area]),
        ]:
            with self.subTest(layout=layout, has_topics=bool(areas)):
                self.home.hero_layout = layout
                self.home.hero_image = None
                context = self.home.get_context(request)
                context.update(research_areas=areas)
                soup = BeautifulSoup(render_to_string("home/home_page.html", context, request=request), "html.parser")
                hero = soup.select_one(".hero[data-hero-entrance]")
                self.assertIsNotNone(hero.select_one("h1"))
                canvas = hero.select_one("canvas[data-research-network]")
                if layout == "constellation":
                    self.assertIsNotNone(canvas)
                    self.assertIs(canvas.parent, hero)
                    self.assertEqual(canvas["aria-hidden"], "true")
                    self.assertFalse(canvas.has_attr("tabindex"))
                else:
                    self.assertIsNone(canvas)
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

    def render_page(self, page):
        request = RequestFactory().get(page.url or "/")
        Site.objects.update_or_create(hostname="localhost", defaults={"root_page": self.home, "is_default_site": True})
        return BeautifulSoup(render_to_string(page.get_template(request), page.get_context(request), request=request), "html.parser")

    def test_breadcrumbs_follow_the_tree_and_keep_current_page_as_text(self):
        people = self.home.add_child(instance=PeopleIndexPage(title="Team"))
        person = people.add_child(instance=PersonPage(title="Researcher", role="Research fellow"))
        soup = self.render_page(person)
        crumbs = soup.select_one("nav.breadcrumbs")
        self.assertEqual([a.get_text(strip=True) for a in crumbs.select("a")], ["Home", "Team"])
        self.assertEqual([a["href"] for a in crumbs.select("a")], [self.home.url, people.url])
        self.assertEqual(crumbs.select_one("[aria-current='page']").get_text(), person.title)
        self.assertFalse(crumbs.select("a[aria-current]"))
        self.assertFalse(self.render_page(self.home).select(".breadcrumbs"))

    def test_translated_breadcrumbs_never_link_to_the_english_tree(self):
        locale, _ = Locale.objects.get_or_create(language_code="cs")
        translated_home = self.home.copy_for_translation(locale)
        translated_home.save_revision().publish()
        translated_science = self.science.copy_for_translation(locale)
        translated_science.title = "Výzkum"
        translated_science.save_revision().publish()
        soup = self.render_page(translated_science)
        crumb = soup.select_one(".breadcrumbs a")
        self.assertEqual(crumb.get_text(), "Úvod")
        self.assertEqual(crumb["href"], translated_home.url)
        self.assertEqual(soup.select_one(".breadcrumbs")["aria-label"], "Drobečková navigace")

    def test_profile_navigation_skips_drafts_and_handles_a_missing_portrait(self):
        people = self.home.add_child(instance=PeopleIndexPage(title="Team"))
        first = people.add_child(instance=PersonPage(title="First", role="Researcher", portrait_size="large"))
        draft = people.add_child(instance=PersonPage(title="Draft", role="Researcher"))
        draft.unpublish()
        last = people.add_child(instance=PersonPage(title="Last", role="Researcher"))
        soup = self.render_page(first)
        self.assertIsNotNone(soup.select_one(".profile-image .person-placeholder svg"))
        nav = soup.select_one(".page-navigation")
        self.assertEqual(nav.select_one(".page-navigation-parent")["href"], people.url)
        self.assertEqual(nav.select_one(".page-navigation-next")["href"], last.url)
        self.assertFalse(nav.select(".page-navigation-previous"))
        self.assertNotIn("Draft", nav.get_text())

    def test_inline_contents_and_sibling_navigation_keep_working_destinations(self):
        first = self.science.add_child(instance=ContentPage(title="First topic", intro="<p>Topic summary</p>"))
        last = self.science.add_child(instance=ContentPage(title="Last topic"))
        soup = self.render_page(self.science)
        self.assertFalse(soup.select('.section-contents, .section-toc, .contents-return'))
        self.assertIn('inline-collection--continuous', soup.select_one('.inline-collection')['class'])
        self.assertIn("Topic summary", soup.select_one(f"#section-{first.pk}").get_text())
        self.assertEqual(self.render_page(first).select_one(".page-navigation-next")["href"], section_url(last))
        # Project contents remain useful and retain working anchor destinations.
        self.project.add_child(instance=ContentPage(title='Project details'))
        soup = self.render_page(self.project)
        self.assertIsNotNone(soup.select_one('.section-toc a'))
        for link in soup.select(".section-toc a, .contents-return"):
            self.assertIsNotNone(soup.select_one(link["href"]))

    def test_team_index_avoids_redundant_self_links_but_keeps_custom_headings(self):
        people = self.home.add_child(instance=PeopleIndexPage(title="People"))
        people.add_child(instance=PersonPage(title="Researcher", role="Research fellow"))
        people.sections = [("people", {"is_visible": True, "title": "People", "theme": "paper", "limit": 24, "show_roles": True})]
        soup = self.render_page(people)
        self.assertFalse(soup.select(".people-preview .section-heading"))
        self.assertEqual(soup.select_one(".person-name").name, "h2")
        people.sections[0].value["title"] = "Meet our researchers"
        self.assertEqual(self.render_page(people).select_one(".people-preview h2").get_text(), "Meet our researchers")
