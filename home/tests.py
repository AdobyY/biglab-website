from tempfile import TemporaryDirectory

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse

from home.models import (
    ContentPage,
    HomePage,
    NewsIndexPage,
    NewsPage,
    PeopleIndexPage,
    PersonPage,
    ProjectPage,
    ProjectsIndexPage,
    SciencePage,
)
from home.blocks import HOME_SECTION_BLOCKS
from home.templatetags.navigation_tags import _build_menu, curated_items, should_carousel

from wagtail.models import Page, Site
from wagtail.admin.action_menu import PageActionMenu
from wagtail.coreutils import get_content_languages
from wagtail.test.utils import WagtailPageTestCase


class HomeSetUpTests(WagtailPageTestCase):
    """
    Tests for basic page structure setup and HomePage creation.
    """

    def test_root_create(self):
        root_page = Page.objects.get(pk=1)
        self.assertIsNotNone(root_page)

    def test_homepage_create(self):
        root_page = Page.objects.get(pk=1)
        homepage = HomePage(title="Home")
        root_page.add_child(instance=homepage)
        self.assertTrue(HomePage.objects.filter(title="Home").exists())


class HomeTests(WagtailPageTestCase):
    """
    Tests for homepage functionality and rendering.
    """

    def setUp(self):
        """
        Create a homepage instance for testing.
        """
        root_page = Page.get_first_root_node()
        Site.objects.create(hostname="testsite", root_page=root_page, is_default_site=True)
        self.homepage = HomePage(title="Home")
        root_page.add_child(instance=self.homepage)

    def test_homepage_is_renderable(self):
        self.assertPageIsRenderable(self.homepage)

    def test_homepage_template_used(self):
        response = self.client.get(self.homepage.url)
        self.assertTemplateUsed(response, "home/home_page.html")

    def test_homepage_admin_editor_loads(self):
        user = get_user_model().objects.create_superuser(
            username="editor-check",
            email="editor-check@example.com",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse("wagtailadmin_pages:edit", args=[self.homepage.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "sections", html=False)

    def test_publish_is_the_primary_editor_action(self):
        user = get_user_model().objects.create_superuser(
            username="publish-action-check",
            email="publish-action-check@example.com",
            password="test-password",
        )
        request = RequestFactory().get(
            reverse("wagtailadmin_pages:edit", args=[self.homepage.pk])
        )
        request.user = user
        action_menu = PageActionMenu(
            request,
            page=self.homepage,
            view="edit",
            lock=None,
            locked_for_user=False,
        )

        self.assertEqual(action_menu.default_item.name, "action-publish")
        self.assertIn(
            "action-save-draft",
            [item.name for item in action_menu.menu_items],
        )

    def test_homepage_sections_render_in_editor_order(self):
        self.homepage.sections = [
            (
                "about",
                {
                    "is_visible": True,
                    "anchor": "first",
                    "title": "First editable section",
                    "intro": "",
                    "text": "",
                    "theme": "paper",
                },
            ),
            (
                "about",
                {
                    "is_visible": True,
                    "anchor": "second",
                    "title": "Second editable section",
                    "intro": "",
                    "text": "",
                    "theme": "lilac",
                },
            ),
        ]
        self.homepage.save_revision().publish()

        content = self.client.get(self.homepage.url).content.decode()

        self.assertLess(content.index("First editable section"), content.index("Second editable section"))

    def test_hidden_homepage_section_keeps_content_out_of_public_page(self):
        self.homepage.sections = [
            (
                "about",
                {
                    "is_visible": False,
                    "anchor": "hidden",
                    "title": "Hidden editorial section",
                    "intro": "",
                    "text": "",
                    "theme": "paper",
                },
            )
        ]
        self.homepage.save_revision().publish()

        response = self.client.get(self.homepage.url)

        self.assertNotContains(response, "Hidden editorial section")


class ContentStructureTests(WagtailPageTestCase):
    def test_top_level_sections_can_be_created_beneath_home(self):
        for page_type in (
            ContentPage,
            SciencePage,
            PeopleIndexPage,
            NewsIndexPage,
            ProjectsIndexPage,
            ProjectPage,
        ):
            self.assertCanCreateAt(HomePage, page_type)

    def test_content_children_follow_the_editorial_structure(self):
        self.assertCanCreateAt(PeopleIndexPage, PersonPage)
        self.assertCanCreateAt(NewsIndexPage, NewsPage)
        self.assertCanCreateAt(ProjectsIndexPage, ProjectPage)
        self.assertCanCreateAt(ProjectPage, ContentPage)

    def test_homepage_builder_contains_advanced_media_blocks(self):
        blocks = dict(HOME_SECTION_BLOCKS)
        block_names = set(blocks)

        self.assertTrue({"gallery", "comparison", "slider"}.issubset(block_names))
        self.assertTrue(
            {"selected_people", "enable_carousel", "carousel_after"}.issubset(
                blocks["people"].child_blocks
            )
        )
        self.assertIn("selected_areas", blocks["research"].child_blocks)
        self.assertTrue(
            {"selected_news", "selected_projects", "selected_publications"}.issubset(
                blocks["updates"].child_blocks
            )
        )

    def test_person_editor_exposes_controlled_portrait_options(self):
        fields = PersonPage.get_edit_handler().get_form_class().base_fields

        self.assertTrue(
            {"show_portrait", "portrait_size", "portrait_format", "portrait_fit"}.issubset(fields)
        )

    def test_curated_items_preserve_manual_order_and_limit(self):
        manual = ["third", "first", "second"]

        result = curated_items(
            {"selected": manual, "maximum": 2},
            "selected",
            ["automatic"],
            "maximum",
        )

        self.assertEqual(result, ["third", "first"])
        self.assertTrue(should_carousel(result, True, 1))
        self.assertFalse(should_carousel(result, False, 1))

    def test_nested_show_in_menus_controls_generated_navigation(self):
        root = Page.get_first_root_node()
        home = HomePage(title="Menu home")
        root.add_child(instance=home)
        people = PeopleIndexPage(title="Menu people", show_in_menus=True)
        home.add_child(instance=people)
        person = PersonPage(title="Visible person", role="Researcher", show_in_menus=True)
        people.add_child(instance=person)

        menu = _build_menu(home, person)

        self.assertEqual(menu[0]["page"].pk, people.pk)
        self.assertEqual(menu[0]["children"][0]["page"].pk, person.pk)
        self.assertTrue(menu[0]["active"])
        self.assertTrue(menu[0]["children"][0]["current"])

        person.show_in_menus = False
        person.save_revision().publish()

        self.assertEqual(_build_menu(home, person)[0]["children"], [])


class SQLiteConfigurationTests(SimpleTestCase):
    def test_wagtail_writes_wait_for_sqlite_contention(self):
        options = settings.DATABASES["default"]["OPTIONS"]

        self.assertGreaterEqual(options["timeout"], 20)
        self.assertEqual(options["transaction_mode"], "IMMEDIATE")
        self.assertIn("journal_mode=WAL", options["init_command"])
        self.assertIn("busy_timeout=20000", options["init_command"])


class LanguageConfigurationTests(SimpleTestCase):
    def test_administrators_can_create_locales_from_the_full_language_list(self):
        languages = get_content_languages()

        self.assertGreater(len(languages), 50)
        self.assertTrue({"en", "cs", "uk", "de", "fr", "ar", "ja"}.issubset(languages))


class LocaleAdminTests(WagtailPageTestCase):
    def test_locales_are_available_from_wagtail_settings(self):
        user = get_user_model().objects.create_superuser(
            username="locale-admin-check",
            email="locale-admin-check@example.com",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("wagtaillocales:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Locales")
        self.assertContains(response, "Add a locale")


class InitialContentTests(WagtailPageTestCase):
    def test_seed_is_repeatable_without_replacing_editor_content(self):
        with TemporaryDirectory() as media_root, self.settings(MEDIA_ROOT=media_root):
            call_command("seed_biglab", verbosity=0)
            home = HomePage.objects.get(depth=2, locale__language_code="en")
            self.assertTrue(home.sections)
            self.assertTrue(PersonPage.objects.filter(locale__language_code="en").exists())
            self.assertTrue(HomePage.objects.filter(locale__language_code="cs").exists())

            home.hero_title = "Editor-owned headline"
            home.save_revision().publish()

            call_command("seed_biglab", verbosity=0)
            home.refresh_from_db()

            self.assertEqual(home.hero_title, "Editor-owned headline")
