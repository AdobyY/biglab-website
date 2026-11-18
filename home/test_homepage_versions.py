from bs4 import BeautifulSoup
from django.db import OperationalError, connection
from django.test import RequestFactory, TestCase
from django.urls import get_resolver
from wagtail.models import Locale, Page, Site

from home.models import ContactSettings, ContentPage, HomePage, PeopleIndexPage, PersonPage, SciencePage


class HomepageVersionTests(TestCase):
    def setUp(self):
        self.home = Page.get_first_root_node().add_child(instance=HomePage(
            title="About BIG Lab", slug="lab", hero_title="Our connected world",
            hero_summary="A shared research question.",
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

        self.contact = self.home.add_child(instance=ContentPage(
            title="Contact", slug="contact", show_in_menus=True,
            sections=[("contact", {"is_visible": True, "show_email": True, "show_phone": True,
                                   "show_address": True, "show_people_link": True})],
        ))

    def soup(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return BeautifulSoup(response.content, "html.parser")

    def test_homepage_is_compact_for_all_old_version_links(self):
        for query in ("", "?design=1", "?design=2", "?design=other"):
            with self.subTest(query=query):
                soup = self.soup("/" + query)
                self.assertEqual(soup.h1.get_text(), "Our connected world")
                self.assertIsNotNone(soup.select_one(".hero > canvas[data-research-network]"))
                self.assertFalse(soup.select("#home-sections, [data-design-switch], .contact-surface, .hero-footnote"))
                self.assertFalse(soup.select("a[href*='design=']"))
                self.assertIsNotNone(soup.select_one("header a[href='/about/']"))
                self.assertIsNotNone(soup.select_one("header a[href='/contact/']"))
                self.assertEqual(soup.select_one("link[rel=canonical]")["href"], "http://testserver/")

    def test_about_shows_the_network_beside_the_published_introduction(self):
        for url in ("/about/", "/about/?design=2"):
            soup = self.soup(url)
            self.assertEqual([h.get_text() for h in soup.select("h1")], ["About BIG Lab"])
            self.assertEqual(len(soup.select(".home-about [data-topic-network]")), 1)
            self.assertFalse(soup.select(".hero, .financing-section, .contact-surface"))
            self.assertIn("Original CMS mission.", soup.get_text())
            self.assertIn("Editorial content at the bottom.", soup.get_text())
            self.assertNotIn("Keep this hidden.", soup.get_text())
            self.assertNotIn("Verified funding details.", soup.get_text())
            self.assertEqual(soup.select_one(".breadcrumbs a")["href"], "/")
            self.assertIsNotNone(soup.select_one(".breadcrumbs [aria-current='page']"))
            self.assertEqual(len(soup.select("header a[href='/about/']")), 1)
            self.assertIsNotNone(soup.select_one("header a[aria-current='page'][href='/about/']"))
            self.assertEqual(soup.select_one("link[rel='canonical']")["href"], "http://testserver/about/")
        self.home.sections[0].value["title"] = "Updated mission"
        self.home.save_revision().publish()
        self.assertIn("Updated mission", self.soup("/about/").get_text())
        self.assertNotIn("Updated mission", self.soup("/").get_text())

    def test_explicit_network_placement_and_visibility(self):
        self.home.sections = [
            ("about", {"title": "Introduction", "is_visible": True}),
            ("topic_network", {"is_visible": True, "anchor": "network"}),
        ]
        self.home.save_revision().publish()
        soup = self.soup("/about/")
        self.assertEqual(len(soup.select("[data-topic-network]")), 1)
        self.assertIsNotNone(soup.select_one(".home-about + #network [data-topic-network]"))
        self.home.sections[1].value["is_visible"] = False
        self.home.save_revision().publish()
        self.assertFalse(self.soup("/about/").select("[data-topic-network]"))

    def test_translated_navigation_and_canonicals_use_the_corresponding_pages(self):
        locale, _ = Locale.objects.get_or_create(language_code="cs")
        translated = self.home.copy_for_translation(locale)
        translated.title = "O BIG Lab"
        translated.save_revision().publish()
        contact = self.contact.copy_for_translation(locale)
        contact.title, contact.slug = "Kontakt", "napiste-nam"
        contact.save_revision().publish()
        for path, counterpart in (("/", "/cs/"), ("/about/", "/cs/about/"), ("/contact/", "/cs/napiste-nam/")):
            soup = self.soup(path + "?design=2")
            self.assertEqual(soup.select_one(".language-options a[lang='cs']")["href"], counterpart)
            self.assertEqual(soup.select_one("link[rel=alternate][hreflang=cs]")["href"], "http://testserver" + counterpart)
            translated_page = self.soup(counterpart)
            self.assertEqual(translated_page.select_one(".language-options a[lang='en']")["href"], path)
            self.assertEqual(translated_page.select_one("link[rel=canonical]")["href"], "http://testserver" + counterpart)
            self.assertIsNotNone(translated_page.select_one("header a[href='/cs/napiste-nam/']"))
            self.assertEqual(translated_page.select_one(".footer-lead p").get_text(), "behavior of individuals and groups")

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
        for url, selector in (("/about/", ".home-team-copy h3"), ("/people/", ".person-name")):
            with self.subTest(url=url):
                soup = self.soup(url)
                self.assertEqual([heading.get_text(strip=True) for heading in soup.select(selector)], expected)
                self.assertNotIn(draft.title, soup.get_text())
        first_profile = self.soup(members[-1].url)
        self.assertFalse(first_profile.select(".page-navigation [rel=prev]"))
        self.assertEqual(first_profile.select_one(".page-navigation [rel=next]")["href"], members[0].url)
        self.home.sections = []
        self.home.save_revision().publish()
        self.assertEqual(len(self.soup("/about/").select(".home-team-person")), 9)

    def test_standalone_contact_uses_settings_and_its_own_visibility_controls(self):
        contact = ContactSettings.for_site(Site.objects.get(is_default_site=True))
        contact.address, contact.email, contact.phone = "Joštova 10, Brno", "lab@example.org", "+420 123 456 789"
        contact.save()
        self.contact.sections[0].value.update(anchor="reach-us", title="Write to us")
        self.contact.save_revision().publish()
        soup = self.soup("/contact/")
        section = soup.select_one("#reach-us.contact-surface")
        self.assertIsNotNone(soup.select_one("header a[aria-current=page][href='/contact/']"))
        self.assertIn("Write to us", section.get_text())
        self.assertEqual(section.select_one("a[href^='mailto:']")["href"], "mailto:lab@example.org")
        self.assertEqual(section.select_one("a[href^='tel:']")["href"], "tel:+420123456789")
        self.assertIn("Jo%C5%A1tova", section.select_one("iframe")["src"])
        self.assertFalse(soup.select(".page-navigation"))
        shared_footer = self.soup("/").footer
        self.assertEqual(soup.footer, shared_footer)
        self.assertIsNotNone(soup.footer.select_one("a[href='mailto:lab@example.org']"))
        self.contact.sections[0].value.update(show_address=False, show_email=False)
        self.contact.save_revision().publish()
        contact_page = self.soup("/contact/")
        self.assertFalse(contact_page.select("#reach-us :is(iframe, address, a[href^='mailto:'])"))
        self.assertEqual(contact_page.footer, shared_footer)

    def test_error_pages_share_the_footer_and_survive_a_database_outage(self):
        contact = ContactSettings.for_site(Site.objects.get(is_default_site=True))
        contact.email = "lab@example.org"
        contact.save()
        footer = self.soup("/").footer
        missing = self.client.get("/missing-page/")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(BeautifulSoup(missing.content, "html.parser").footer, footer)

        server_error = get_resolver().resolve_error_handler(500)
        response = server_error(RequestFactory().get("/"))
        self.assertEqual(response.status_code, 500)
        self.assertEqual(BeautifulSoup(response.content, "html.parser").footer, footer)

        def database_unavailable(*args):
            raise OperationalError("Database unavailable")

        with connection.execute_wrapper(database_unavailable):
            fallback = server_error(RequestFactory().get("/"))
        self.assertEqual(fallback.status_code, 500)
        self.assertEqual(BeautifulSoup(fallback.content, "html.parser").select_one("main a")["href"], "/")

    def test_empty_contact_settings_do_not_render_an_empty_map_or_email(self):
        section = self.soup("/contact/").select_one(".contact-surface")
        self.assertIsNone(section.select_one("iframe, a[href^='mailto:'], a[href^='tel:']"))
        self.assertEqual(section.select_one(".contact-team-link")["href"], "/people/")
