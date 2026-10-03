from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse
from wagtail.contrib.settings.views import get_setting_edit_handler
from wagtail.models import Locale, Page, Site

from home.models import HomePage, HomepageDesignSettings


PALETTE_FIELDS = ("background", "foreground", "accent", "muted", "network_secondary")


class HomepagePaletteValidationTests(SimpleTestCase):
    def test_palette_accepts_only_complete_hex_colors(self):
        for name in PALETTE_FIELDS:
            field = HomepageDesignSettings._meta.get_field(name)
            for value in ("#0b141e", "#ABCDEF", "#000000", "#ffffff"):
                with self.subTest(field=name, valid=value):
                    self.assertEqual(field.clean(value, None), value)
            for value in ("red", "#abc", "#12345g", "#123456\n", " #123456", "#123456; color:red", ""):
                with self.subTest(field=name, invalid=value), self.assertRaises(ValidationError):
                    field.clean(value, None)

    def test_wagtail_form_uses_color_controls_and_rejects_css_injection(self):
        form_class = get_setting_edit_handler(HomepageDesignSettings).get_form_class()
        self.assertEqual(set(form_class.base_fields), set(PALETTE_FIELDS))
        for field in form_class.base_fields.values():
            self.assertEqual(field.widget.input_type, "color")
        values = {name: "#123456" for name in PALETTE_FIELDS}
        values["accent"] = "#123456;--background:red"
        form = form_class(data=values)
        self.assertFalse(form.is_valid())
        self.assertIn("accent", form.errors)


class HomepageDesignContextTests(TestCase):
    def setUp(self):
        self.home = Page.get_first_root_node().add_child(instance=HomePage(title="Design preview home"))
        self.factory = RequestFactory()

    def test_only_explicit_version_two_selects_the_alternative(self):
        for query, expected in (("", "1"), ("?design=2", "2"), ("?design=1", "1"), ("?design=02", "1"), ("?design=other", "1")):
            with self.subTest(query=query):
                context = self.home.get_context(self.factory.get("/cs/" + query))
                self.assertEqual(context["design_version"], expected)

    def test_switch_preserves_localized_path_and_repeated_query_parameters(self):
        context = self.home.get_context(self.factory.get("/cs/?tag=parents&tag=school&q=linked+people"))
        url = urlsplit(context["design_switch_url"])
        self.assertEqual(url.path, "/cs/")
        self.assertEqual(parse_qs(url.query), {"tag": ["parents", "school"], "q": ["linked people"], "design": ["2"]})
        context = self.home.get_context(self.factory.get(context["design_switch_url"]))
        url = urlsplit(context["design_switch_url"])
        self.assertEqual(url.path, "/cs/")
        self.assertEqual(parse_qs(url.query), {"tag": ["parents", "school"], "q": ["linked people"]})

    def test_returning_to_default_removes_all_design_parameters(self):
        context = self.home.get_context(self.factory.get("/?design=1&design=2"))
        self.assertEqual(context["design_version"], "2")
        self.assertEqual(context["design_switch_url"], "/")


class HomepagePaletteAdminTests(TestCase):
    def setUp(self):
        self.home = Page.get_first_root_node().add_child(instance=HomePage(title="Palette admin home"))
        Site.objects.filter(is_default_site=True).update(is_default_site=False)
        self.site = Site.objects.create(hostname="testserver", root_page=self.home, is_default_site=True)
        user = get_user_model().objects.create_superuser(
            username="palette-editor", email="palette-editor@example.com", password="test-password",
        )
        self.client.force_login(user)
        self.edit_url = reverse("wagtailsettings:edit", args=["home", "homepagedesignsettings", self.site.pk])

    def test_settings_editor_exposes_palette_and_saves_changes(self):
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        for name in PALETTE_FIELDS:
            control = soup.select_one(f"input[name='{name}']")
            self.assertIsNotNone(control)
            self.assertEqual(control["type"], "color")
        self.assertContains(response, "Version 1 remains the default")
        values = {name: "#123456" for name in PALETTE_FIELDS}
        response = self.client.post(self.edit_url, values)
        self.assertEqual(response.status_code, 302)
        saved = HomepageDesignSettings.for_site(self.site)
        for name in PALETTE_FIELDS:
            self.assertEqual(getattr(saved, name), "#123456")

    def test_invalid_admin_color_does_not_replace_saved_palette(self):
        palette = HomepageDesignSettings.for_site(self.site)
        values = {name: getattr(palette, name) for name in PALETTE_FIELDS}
        values["background"] = "url(https://example.com)"
        response = self.client.post(self.edit_url, values)
        self.assertEqual(response.status_code, 200)
        palette.refresh_from_db()
        self.assertEqual(palette.background, "#0b141e")

    def test_palette_is_shared_by_languages_of_the_same_site(self):
        locale, _ = Locale.objects.get_or_create(language_code="cs")
        self.home.copy_for_translation(locale)
        palette = HomepageDesignSettings.for_site(self.site)
        palette.accent = "#654321"
        palette.save()
        factory = RequestFactory()
        english = HomepageDesignSettings.for_request(factory.get("/"))
        czech = HomepageDesignSettings.for_request(factory.get("/cs/"))
        self.assertEqual(english.pk, czech.pk)
        self.assertEqual(czech.accent, "#654321")
