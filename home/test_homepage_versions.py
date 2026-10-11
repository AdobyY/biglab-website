from bs4 import BeautifulSoup
from django.test import TestCase
from wagtail.models import Locale, Page, Site

from home.models import ContactSettings, HomePage, PeopleIndexPage, PersonPage, SciencePage
from home.templatetags.navigation_tags import design_url


class HomepageVersionTests(TestCase):
    def setUp(self):
        self.home = Page.get_first_root_node().add_child(instance=HomePage(
            title="About BIG Lab", slug="lab", hero_title="Our connected world",
            hero_summary="A shared research question.", show_contact_section=True,
            about_financing="<p>Verified funding details.</p>",
            sections=[
                ("about", {"title": "Our mission", "text": "<p>Original CMS mission.</p>", "anchor": "about", "theme": "paper", "is_visible": True}),
                ("about", {"title": "Hidden section", "text": "<p>Keep this hidden.</p>", "theme": "paper", "is_visible": False}),
            ],
            after_body=[("text", "<p>Editorial content at the bottom.</p>")],
        ))
        Site.objects.all().delete()
        Site.objects.create(hostname="localhost", root_page=self.home, is_default_site=True)
        self.science = self.home.add_child(instance=SciencePage(title="Science", slug="science", show_in_menus=True))
        self.people = self.home.add_child(instance=PeopleIndexPage(title="People", slug="people", show_in_menus=True))

    def soup(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return BeautifulSoup(response.content, "html.parser")

    def test_full_homepage_retains_sections_financing_and_after_body(self):
        soup = self.soup("/")
        self.assertIn("homepage-design-1", soup.body["class"])
        self.assertEqual(soup.select_one("h1").get_text(), "Our connected world")
        self.assertIn("Original CMS mission.", soup.select_one("#home-sections").get_text())
        self.assertIn("Verified funding details.", soup.get_text())
        self.assertIn("Editorial content at the bottom.", soup.get_text())
        self.assertNotIn("Keep this hidden.", soup.get_text())
        self.assertEqual(soup.select_one(".site-nav > li > .nav-entry > a")["href"], "/#about")

    def test_compact_homepage_has_only_hero_and_footer(self):
        soup = self.soup("/?design=2")
        self.assertIn("homepage-design-2", soup.body["class"])
        self.assertEqual(len(soup.select("main > section")), 1)
        self.assertIsNone(soup.select_one("#home-sections"))
        self.assertIsNone(soup.select_one("main .contact-surface"))
        self.assertNotIn("Original CMS mission.", soup.get_text())
        self.assertNotIn("Verified funding details.", soup.get_text())
        self.assertNotIn("Editorial content at the bottom.", soup.get_text())
        self.assertIsNotNone(soup.select_one("footer#site-footer"))
        self.assertEqual(soup.select_one(".contact-nav-link")["href"], "/about/?design=2#contact")
        self.assertEqual(soup.select_one(".site-nav > li > .nav-entry > a")["href"], "/about/?design=2")
        self.assertFalse(soup.select_one(".site-nav > li > .nav-entry > a").has_attr("aria-current"))
        self.assertEqual(soup.select_one(".footer-bottom a")["href"], "/about/?design=2")
        self.assertIsNone(soup.select_one(".hero-footnote"))
        self.assertFalse(soup.select("script[src*='research-preview'], script[src$='/homepage.js']"))

    def test_about_route_uses_the_live_sections_without_a_second_hero(self):
        for url in ("/about/", "/about/?design=2"):
            with self.subTest(url=url):
                soup = self.soup(url)
                self.assertEqual(soup.select_one("h1").get_text(), "About BIG Lab")
                self.assertEqual(len(soup.select("h1")), 1)
                self.assertIsNone(soup.select_one(".hero, canvas, [data-design-switch]"))
                self.assertIn("Original CMS mission.", soup.get_text())
                self.assertIn("Verified funding details.", soup.get_text())
                self.assertIn("Editorial content at the bottom.", soup.get_text())
                self.assertNotIn("Keep this hidden.", soup.get_text())
                self.assertIsNotNone(soup.select_one("main #contact.contact-surface--dark"))
                self.assertEqual(soup.select_one(".contact-nav-link")["href"], "/about/?design=2#contact")
                self.assertEqual(soup.select_one(".about-home-link")["href"], "/?design=2")
                self.assertEqual(soup.select_one(".site-nav > li > .nav-entry > a")["aria-current"], "page")
                self.assertEqual(soup.select_one("link[rel='canonical']")["href"], "http://testserver/about/")
                self.assertFalse(soup.select("script[src*='hero-network']"))
        self.home.sections = [("about", {"title": "Updated mission", "text": "<p>New published CMS copy.</p>", "theme": "paper", "is_visible": True})]
        self.home.save_revision().publish()
        self.assertIn("New published CMS copy.", self.soup("/about/").get_text())
        self.assertIn("New published CMS copy.", self.soup("/").get_text())

    def test_existing_child_routes_keep_working_and_navigation_returns_to_v2(self):
        for child in (self.science, self.people):
            soup = self.soup(f"{child.url}?design=2")
            self.assertEqual(soup.select_one("header.site-header a.site-name")["href"], "/?design=2")
            self.assertEqual(soup.select_one(".site-nav > li > .nav-entry > a")["href"], "/about/?design=2")

    def test_translations_retain_about_route_version_and_canonical(self):
        locale, _ = Locale.objects.get_or_create(language_code="cs")
        translated = self.home.copy_for_translation(locale)
        translated.title = "O BIG Lab"
        translated.save_revision().publish()
        soup = self.soup("/about/?design=2")
        self.assertEqual(soup.select_one(".language-options a[lang='cs']")["href"], "/cs/about/?design=2")
        self.assertEqual(soup.select_one("link[rel='alternate'][hreflang='cs']")["href"], "http://testserver/cs/about/")
        soup = self.soup("/cs/about/?design=2")
        self.assertEqual(soup.select_one("h1").get_text(), "O BIG Lab")
        self.assertEqual(soup.select_one(".about-home-link")["href"], "/cs/?design=2")
        self.assertEqual(soup.select_one("link[rel='canonical']")["href"], "http://testserver/cs/about/")
        self.assertEqual(soup.select_one(".language-options a[lang='en']")["href"], "/about/?design=2")
        self.assertIsNotNone(soup.select_one("main #contact.contact-surface--dark"))
        soup = self.soup("/cs/?design=2")
        self.assertIsNone(soup.select_one("#home-sections"))
        self.assertIsNone(soup.select_one(".hero-footnote"))
        self.assertIsNone(soup.select_one("main .contact-surface"))
        self.assertEqual(soup.select_one(".contact-nav-link")["href"], "/cs/about/?design=2#contact")

    def test_version_parameter_is_inserted_before_the_fragment(self):
        self.assertEqual(design_url("/science/?filter=all#publications", "2"), "/science/?filter=all&design=2#publications")
        self.assertEqual(design_url("/science/#publications", "1"), "/science/#publications")

    def test_empty_builder_keeps_legacy_content_on_about(self):
        self.home.sections = []
        self.home.body = [("text", "<p>Legacy editorial copy.</p>")]
        self.home.save_revision().publish()
        self.assertIn("Legacy editorial copy.", self.soup("/about/").get_text())
        self.assertNotIn("Legacy editorial copy.", self.soup("/?design=2").get_text())

    def test_complete_team_keeps_curated_order_without_omitting_other_members(self):
        members = [self.people.add_child(instance=PersonPage(title=f"Member {i}", slug=f"member-{i}", role="Researcher")) for i in range(9)]
        draft = self.people.add_child(instance=PersonPage(title="Unpublished member", role="Researcher", live=False))
        selection = {"is_visible": True, "selected_people": [members[-1], members[-1], draft], "limit": 1, "show_roles": True}
        self.home.sections = [("people", selection)]
        self.home.save_revision().publish()
        self.people.sections = [("people", selection)]
        self.people.save_revision().publish()
        expected = [members[-1].title] + [member.title for member in members[:-1]]
        for url, selector in (("/", ".home-team-copy h3"), ("/about/", ".home-team-copy h3"), ("/people/", ".person-name")):
            with self.subTest(url=url):
                soup = self.soup(url)
                self.assertEqual([heading.get_text(strip=True) for heading in soup.select(selector)], expected)
                self.assertNotIn(draft.title, soup.get_text())
        self.home.sections = []
        self.home.save_revision().publish()
        self.assertEqual(len(self.soup("/").select(".home-team-person")), 9)

    def test_contact_variants_use_real_settings_and_custom_anchor(self):
        site = Site.objects.get(is_default_site=True)
        contact = ContactSettings.for_site(site)
        contact.address = "Joštova 10, Brno"
        contact.email = "lab@example.org"
        contact.phone = "+420 123 456 789"
        contact.save()
        self.home.sections = [("contact", {"is_visible": True, "anchor": "reach-us", "title": "Write to us", "show_email": True, "show_phone": True, "show_address": True, "show_people_link": True})]
        self.home.save_revision().publish()
        for url, variant in (("/", "light"), ("/about/", "dark")):
            with self.subTest(url=url):
                soup = self.soup(url)
                section = soup.select_one(f"#reach-us.contact-surface--{variant}")
                self.assertIsNotNone(section)
                self.assertEqual(len(soup.select(".contact-surface")), 1)
                self.assertIn("Write to us", section.get_text())
                self.assertEqual(section.select_one("a[href^='mailto:']")["href"], "mailto:lab@example.org")
                self.assertEqual(section.select_one("a[href^='tel:']")["href"], "tel:+420123456789")
                self.assertIn("Jo%C5%A1tova", section.select_one("iframe")["src"])
                self.assertTrue(soup.select_one(".contact-nav-link")["href"].endswith("#reach-us"))
        compact = self.soup("/?design=2")
        self.assertIsNone(compact.select_one("main .contact-surface"))
        self.assertEqual(compact.select_one(".contact-nav-link")["href"], "/about/?design=2#reach-us")
        self.home.sections[0].value["show_address"] = False
        self.home.sections[0].value["show_email"] = False
        self.home.save_revision().publish()
        section = self.soup("/about/").select_one("#reach-us")
        self.assertIsNone(section.select_one("iframe, address, a[href^='mailto:']"))

    def test_empty_contact_settings_do_not_render_an_empty_map_or_email(self):
        section = self.soup("/about/").select_one("#contact")
        self.assertIsNone(section.select_one("iframe, a[href^='mailto:'], a[href^='tel:']"))
        self.assertEqual(section.select_one(".contact-actions .button")["href"], "/people/?design=2")
