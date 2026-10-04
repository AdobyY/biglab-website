from io import BytesIO
import tempfile

from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from wagtail.images import get_image_model
from wagtail.models import Site

from home.models import ContactSettings


class SharedBrandTests(TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        override = self.settings(MEDIA_ROOT=directory.name)
        override.enable()
        self.addCleanup(override.disable)
        self.site = Site.objects.get(is_default_site=True)
        self.settings = ContactSettings.for_site(self.site)
        self.editor = get_user_model().objects.create_superuser("brand-editor", "", "test-password")

    def soup(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return BeautifulSoup(response.content, "html.parser")

    def test_default_logo_on_public_pages_login_and_sidebar(self):
        public = self.soup("/")
        self.assertEqual(len(public.select("header .brand-mark, footer .brand-mark")), 2)
        self.assertTrue(all(image["src"].endswith("images/biglab-logo.png") for image in public.select(".brand-mark")))
        login = self.soup("/admin/login/")
        self.assertIn("BIG Lab", login.title.text)
        self.assertIsNone(login.select_one("svg.icon-wagtail"))
        self.assertTrue(login.select_one(".biglab-admin-logo")["src"].endswith("images/biglab-logo.png"))
        self.client.force_login(self.editor)
        admin = self.soup("/admin/")
        self.assertIsNotNone(admin.select_one("template[data-wagtail-sidebar-branding-logo] .biglab-admin-logo"))
        self.assertTrue(admin.select_one('link[rel="icon"]')["href"].endswith("images/biglab-logo.png"))

    def test_one_logo_setting_updates_public_admin_and_userbar(self):
        for color in ("red", "green"):
            payload = BytesIO()
            Image.new("RGB", (100, 100), color).save(payload, format="PNG")
            logo = get_image_model().objects.create(title=color, file=SimpleUploadedFile(color + ".png", payload.getvalue(), "image/png"))
            self.settings.logo = logo
            self.settings.save()
            expected = logo.get_rendition("max-240x240").url
            icon = logo.get_rendition("max-64x64").url
            self.client.logout()
            public = self.soup("/")
            self.assertEqual({image["src"] for image in public.select(".brand-mark")}, {expected})
            self.assertEqual(public.select_one('link[rel="icon"]')["href"], icon)
            self.assertEqual(self.soup("/admin/login/").select_one(".biglab-admin-logo")["src"], expected)
            self.client.force_login(self.editor)
            self.assertEqual(self.soup("/admin/").select_one(".biglab-admin-logo")["src"], expected)
            public = self.soup("/")
            self.assertEqual(public.select_one("#wagtail-userbar-template .biglab-admin-logo")["src"], expected)
            self.assertIsNotNone(public.select_one("#wagtail-userbar-template .w-userbar--bottom-left"))

    def test_password_reset_and_admin_not_found_keep_branding(self):
        reset = self.soup("/admin/password_reset/")
        self.assertIn("BIG Lab", reset.title.text)
        self.assertTrue(reset.select_one('link[rel="icon"]')["href"].endswith("images/biglab-logo.png"))
        self.client.force_login(self.editor)
        response = self.client.get("/admin/nonexistent-brand-test/")
        self.assertEqual(response.status_code, 404)
        soup = BeautifulSoup(response.content, "html.parser")
        self.assertIsNotNone(soup.select_one(".biglab-admin-logo"))
