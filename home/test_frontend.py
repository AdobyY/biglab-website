from datetime import date

from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from django.test import RequestFactory
from wagtail.models import Locale, Page, Site
from wagtail.test.utils import WagtailPageTestCase

from home.models import ContentPage, HomePage, NewsIndexPage, NewsPage, PeopleIndexPage, PersonPage, ProjectPage, SciencePage
from home.templatetags.navigation_tags import _build_menu, constellation_nodes, section_url
from home.templatetags.visual_tags import editorial_parts


class FrontendContractTests(WagtailPageTestCase):
    def setUp(self):
        self.home = Page.get_first_root_node().add_child(instance=HomePage(title="Lab"))
        self.science = self.home.add_child(instance=SciencePage(title="Science", show_in_menus=True))
        self.project = self.home.add_child(instance=ProjectPage(title="Parta", show_in_menus=True))

    def test_about_layout_preserves_rich_text_and_custom_markup(self):
        source = '<p>First <a href="https://example.com">linked paragraph</a>.</p><h3>Methods</h3><ul><li>Full details</li></ul>'
        parts = editorial_parts(source)
        self.assertEqual(parts['lead'] + parts['body'], source)
        self.assertEqual(editorial_parts('<h3>Custom opening</h3><p>Keep this.</p>'),
                         {'lead': '', 'body': '<h3>Custom opening</h3><p>Keep this.</p>'})
        block = self.home._meta.get_field('sections').stream_block.child_blocks['about']
        value = block.to_python({'title': 'About the lab', 'is_visible': True, 'text': source})
        soup = BeautifulSoup(block.render(value, context={'page': self.home}), 'html.parser')
        self.assertEqual(soup.select_one('.about-lead a')['href'], 'https://example.com')
        self.assertEqual(soup.select_one('.about-details h3').text, 'Methods')
        self.assertEqual(soup.select_one('.about-details li').text, 'Full details')
        value['title'] = self.home.title
        about = BeautifulSoup(block.render(value, context={'page': self.home, 'is_about_page': True}), 'html.parser')
        self.assertFalse(about.select('.section-heading'))
        home = BeautifulSoup(block.render(value, context={'page': self.home}), 'html.parser')
        self.assertEqual(home.select_one('.section-heading h2').text, self.home.title)

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

    def test_featured_audiences_follow_owned_links_labels_and_publication_state(self):
        Site.objects.update_or_create(hostname='localhost', defaults={'root_page': self.home, 'is_default_site': True})
        about = self.project.add_child(instance=ContentPage(title='About the project'))
        schools = about.add_child(instance=ContentPage(title='For schools', slug='for-schools'))
        parents = about.add_child(instance=ContentPage(title='For parents', slug='for-parents'))
        draft = about.add_child(instance=ContentPage(title='Draft audience', live=False))
        timeline = self.project.add_child(instance=ContentPage(title='Timeline'))
        unrelated = self.science.add_child(instance=ContentPage(title='Unrelated research'))
        self.project.sections = [('page_links', {'is_visible': True, 'pages': [
            {'page': parents, 'label': 'Parent information'}, {'page': draft},
            {'page': timeline}, {'page': unrelated}, {'page': schools}, {'page': schools},
        ]})]
        self.project.save()
        block = self.home._meta.get_field('sections').stream_block.child_blocks['featured_project']
        value = block.to_python({'project': self.project.pk, 'is_visible': True})
        soup = BeautifulSoup(block.render(value, context={'page': self.home}), 'html.parser')
        links = soup.select('.parta-audience-list a')
        self.assertEqual([a.get_text(' ', strip=True) for a in links], ['Parent information', 'For schools'])
        self.assertEqual([a['href'] for a in links], [parents.url, schools.url])
        self.project.sections[0].value['is_visible'] = False
        self.project.save()
        self.assertNotIn('parta-audience-list', block.render(block.to_python({'project': self.project.pk, 'is_visible': True}), context={'page': self.home}))

    def test_long_article_index_preserves_copy_and_stable_unique_heading_destinations(self):
        page = self.home.add_child(instance=ContentPage(title='School information', body=[
            ('heading', 'Benefits'), ('text', '<p>All original benefits.</p>'),
            ('heading', 'Benefits'), ('text', '<p>Another distinct section.</p>'),
        ], after_body=[('heading', 'How to join'), ('text', '<p>Contact the research team.</p>')]))
        soup = self.render_page(page)
        links = soup.select('.article-outline a')
        self.assertEqual([a.text for a in links], ['Benefits', 'Benefits', 'How to join'])
        destinations = [a['href'] for a in links]
        self.assertEqual(len(set(destinations)), 3)
        for link in links:
            self.assertEqual(soup.select_one(link['href']).text, link.text)
        for text in ('All original benefits.', 'Another distinct section.', 'Contact the research team.'):
            self.assertIn(text, soup.select_one('.content-reading-main').get_text())
        original_body = page.body.get_prep_value()
        page.body = [{'type': 'text', 'value': '<p>A new introduction.</p>'}] + original_body
        page.save()
        page.refresh_from_db()
        updated = self.render_page(page)
        self.assertEqual([a['href'] for a in updated.select('.article-outline a')], destinations)
        page.after_body = []
        self.assertFalse(self.render_page(page).select('.article-outline'))

    def test_page_links_keep_custom_headings_and_use_the_correct_card_level(self):
        child = self.project.add_child(instance=ContentPage(title="For schools", live=True))
        block = self.project._meta.get_field("sections").stream_block.child_blocks["page_links"]
        value = block.to_python({
            "title": "Next steps", "intro": "<p>Choose an audience.</p>", "is_visible": True,
            "columns": "2", "pages": [{"page": child.pk, "label": "School information", "description": ""}],
        })
        soup = BeautifulSoup(render_to_string("home/sections/page_links.html", {
            "page": self.project, "value": value,
        }), "html.parser")
        self.assertEqual(soup.select_one(".section-heading h2").text,"Next steps")
        self.assertEqual(soup.select_one("h3.page-link-title").text,"School information")
        self.assertIn("Choose an audience.",soup.get_text())

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

    def test_v2_hero_preserves_copy_and_moves_editorial_content_off_the_homepage(self):
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
        self.assertIsNone(soup.select_one("[data-design-switch]"))
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
        self.assertIsNone(soup.select_one("#home-sections"))
        self.assertIsNone(soup.select_one(".research-section"))
        self.assertEqual(len(soup.select("main > section")), 1)
        self.assertIsNone(soup.select_one("main .contact-surface"))
        self.assertIsNone(hero.select_one(".hero-footnote"))
        self.assertIsNotNone(soup.select_one("footer#site-footer"))

    def test_about_network_links_to_the_published_research_topics(self):
        Site.objects.update_or_create(hostname="localhost", defaults={"root_page": self.home, "is_default_site": True})
        area = self.science.add_child(instance=ContentPage(title="Research topic"))
        soup = BeautifulSoup(self.client.get("/about/").content, "html.parser")
        network = soup.select_one(".relationship-network")
        self.assertEqual(network.select_one("canvas[data-topic-network]")["aria-hidden"], "true")
        topic = network.select_one("[data-constellation-topic]")
        self.assertEqual(topic.get_text(strip=True), area.title)
        self.assertEqual(topic["href"], section_url(area))

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

    def test_contact_navigation_follows_the_published_page(self):
        Site.objects.update_or_create(hostname="localhost", defaults={"root_page": self.home, "is_default_site": True})
        contact = self.home.add_child(instance=ContentPage(title="Write to the lab", slug="reach-us", show_in_menus=True))
        self.assertIn(contact.url, [item["url"] for item in _build_menu(self.home)])
        contact.unpublish()
        self.assertNotIn(contact.url, [item["url"] for item in _build_menu(self.home)])

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
        self.assertEqual(soup.select(".breadcrumbs a")[-1]["href"], people.url)
        self.assertEqual(nav.select_one("a[rel=next]")["href"], last.url)
        self.assertFalse(nav.select("a[rel=prev]"))
        self.assertNotIn("Draft", nav.get_text())

    def test_news_pager_follows_its_own_archive_order(self):
        other = self.home.add_child(instance=NewsIndexPage(title="Other archive"))
        other.add_child(instance=NewsPage(title="Other story", date=date(2025, 1, 1)))
        archive = self.home.add_child(instance=NewsIndexPage(title="Lab news"))
        older = archive.add_child(instance=NewsPage(title="Earlier", date=date(2026, 1, 1)))
        newer = archive.add_child(instance=NewsPage(title="Later", date=date(2026, 2, 1)))
        soup = self.render_page(newer)
        links = soup.select(".page-navigation a")
        self.assertEqual([link["href"] for link in links], [older.url])
        self.assertIn("Older article", links[0].get_text())
        self.assertIn("Newer article", self.render_page(older).select_one(".page-navigation a").get_text())

    def test_standalone_topics_keep_the_research_breadcrumb_and_project_contents_work(self):
        first = self.science.add_child(instance=ContentPage(title="First topic", intro="<p>Topic summary</p>"))
        last = self.science.add_child(instance=ContentPage(title="Last topic"))
        soup = self.render_page(self.science)
        self.assertFalse(soup.select('.section-contents, .section-toc, .contents-return'))
        self.assertIn('inline-collection--continuous', soup.select_one('.inline-collection')['class'])
        self.assertIn("Topic summary", soup.select_one(f"#section-{first.pk}").get_text())
        topic = self.render_page(first)
        self.assertFalse(topic.select(".page-navigation"))
        self.assertEqual(topic.select(".breadcrumbs a")[-1]["href"], self.science.url)
        self.project.add_child(instance=ContentPage(title='Project details'))
        self.assertFalse(self.render_page(self.project).select(".section-toc, .contents-return"))
        self.project.add_child(instance=ContentPage(title='Timeline'))
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
