from io import BytesIO
from tempfile import TemporaryDirectory

from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from PIL import Image as PILImage
from wagtail import blocks
from wagtail.images import get_image_model
from wagtail.models import Locale, Page

from home.blocks import CallToActionBlock, CalloutHomeSectionBlock, RichMediaHomeSectionBlock
from home.models import ContentPage, HomePage, PeopleIndexPage, PersonPage, ProjectPage, Publication, SciencePage


class ButtonValidationTests(SimpleTestCase):
    def test_button_needs_one_destination_and_renders_a_working_link(self):
        block = CallToActionBlock()
        for data in ({"label": "Open", "page": None, "url": ""}, {"label": "", "page": None, "url": "https://example.org/"}):
            with self.subTest(data=data), self.assertRaises(blocks.StructBlockValidationError):
                block.clean(block.to_python(data))
        value = block.clean(block.to_python({"label": "Open", "url": "https://example.org/"}))
        self.assertIn('href="https://example.org/"', block.render(value))

    def test_optional_section_button_can_be_empty_but_not_half_complete(self):
        for block in (CalloutHomeSectionBlock(), RichMediaHomeSectionBlock()):
            data = block.get_prep_value(block.get_default())
            data["title"] = "Section"
            block.clean(block.to_python(data))
            data["button_label"] = "Open"
            with self.subTest(block=type(block).__name__), self.assertRaises(blocks.StructBlockValidationError):
                block.clean(block.to_python(data))


class ContentEditorTests(TestCase):
    def setUp(self):
        self.home = Page.get_first_root_node().add_child(instance=HomePage(title="Editor test home", slug="editor-test-home"))
        self.people = self.home.add_child(instance=PeopleIndexPage(title="People", slug="people"))
        self.science = self.home.add_child(instance=SciencePage(title="Science", slug="science"))
        self.user = get_user_model().objects.create_user(username="content-editor", password="test-password")
        self.user.groups.add(Group.objects.get(name="Editors"))
        self.client.force_login(self.user)

    def test_editor_can_manage_shared_content_settings_media_and_translations(self):
        for path in (
            "/admin/snippets/home/publication/", "/admin/snippets/home/collaboration/",
            "/admin/snippets/home/interfacetext/", "/admin/images/add/", "/admin/documents/add/",
            "/admin/settings/home/contactsettings/", "/admin/settings/home/homepagedesignsettings/",
            f"/admin/translation/submit/page/{self.home.pk}/",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path, follow=True).status_code, 200)
                response = self.client.get(path)
                self.assertNotEqual(response.get("Location"), "/admin/")
        self.assertTrue(self.people.permissions_for_user(self.user).can_publish())
        self.assertFalse(self.user.has_perm("auth.change_user"))
        self.assertFalse(self.user.has_perm("auth.change_group"))

    def test_editor_can_create_publication_with_a_raw_doi_and_save_remains_immediate(self):
        response = self.client.post("/admin/snippets/home/publication/add/?locale=en", {
            "title": "Editor publication", "authors": "Researcher", "year": "2027", "doi_or_url": "doi:10.1234/example",
        })
        self.assertEqual(response.status_code, 302)
        publication = Publication.objects.get(title="Editor publication")
        self.assertEqual(publication.doi_or_url, "https://doi.org/10.1234/example")
        self.assertIn(publication, self.science.get_context(self.client.get("/").wsgi_request)["publications"])

    def test_publication_year_zero_and_reversed_project_dates_are_rejected(self):
        response = self.client.post("/admin/snippets/home/publication/add/?locale=en", {
            "title": "Bad year", "authors": "Researcher", "year": "0",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Publication.objects.filter(title="Bad year").exists())
        from datetime import date
        project = ProjectPage(title="Invalid dates", start_date=date(2027, 12, 1), end_date=date(2027, 1, 1))
        with self.assertRaisesMessage(ValidationError, "End date must be on or after"):
            project.clean()

    def test_publishing_a_profile_still_publishes_other_language_aliases(self):
        locale, _ = Locale.objects.get_or_create(language_code="cs")
        response = self.client.post(f"/admin/pages/add/home/personpage/{self.people.pk}/", {
            "title": "Shared language profile", "slug": "shared-language-profile", "role": "Researcher",
            "show_portrait": "on", "portrait_size": "standard", "portrait_format": "portrait", "portrait_fit": "contain",
            "body-count": "0", "sections-count": "0", "after_body-count": "0", "action-publish": "Publish",
        })
        self.assertEqual(response.status_code, 302)
        original = PersonPage.objects.get(title="Shared language profile", locale=self.home.locale)
        alias = original.get_translation(locale)
        self.assertTrue(original.live)
        self.assertTrue(alias.live)
        self.assertEqual(alias.alias_of_id, original.pk)

    def section_form(self, sections):
        page = self.home.add_child(instance=ContentPage(title="Sections test", slug="sections-test"))
        data = {"title": page.title, "slug": page.slug, "body-count": "0", "after_body-count": "0", "sections-count": str(len(sections))}
        for i, (kind, values) in enumerate(sections):
            prefix = f"sections-{i}"
            data.update({prefix + "-type": kind, prefix + "-order": str(i), prefix + "-deleted": ""})
            values = {"title": "Section", "is_visible": "1", "theme": "paper", **values}
            for key, value in values.items():
                data[f"{prefix}-value-{key}"] = value
        return page.get_edit_handler().get_form_class()(data=data, instance=page, parent_page=self.home)

    def test_duplicate_anchor_errors_are_attached_to_the_section(self):
        form = self.section_form([("about", {"anchor": "duplicate"}), ("about", {"anchor": "duplicate"})])
        self.assertFalse(form.is_valid())
        error = form.errors.as_data()["sections"][0]
        self.assertIn("anchor", error.block_errors[1].block_errors)

    def test_other_language_research_selection_is_rejected(self):
        locale, _ = Locale.objects.get_or_create(language_code="cs")
        area = self.science.add_child(instance=ContentPage(title="Czech research", locale=locale))
        form = self.section_form([("research", {
            "limit": "5", "selected_areas-count": "1", "selected_areas-0-order": "0", "selected_areas-0-deleted": "", "selected_areas-0-value": str(area.pk),
        })])
        self.assertFalse(form.is_valid())
        error = form.errors.as_data()["sections"][0]
        self.assertIn("selected_areas", error.block_errors[0].block_errors)

    def test_editor_forms_explain_language_copies_and_immediate_shared_saves(self):
        response = self.client.get(f"/admin/pages/{self.people.pk}/edit/")
        self.assertContains(response, "linked language copies (aliases)")
        self.assertContains(response, "Recommended: People")
        response = self.client.get("/admin/snippets/home/publication/add/?locale=en")
        self.assertContains(response, "Save applies changes immediately")


class PortraitRenderingTests(TestCase):
    def test_contain_keeps_the_original_ratio_on_profile_and_card(self):
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            original = BytesIO()
            PILImage.new("RGB", (2400, 800), "#995533").save(original, "JPEG")
            image = get_image_model().objects.create(title="Wide portrait", file=ContentFile(original.getvalue(), name="wide.jpg"))
            home = HomePage.objects.first()
            people = home.add_child(instance=PeopleIndexPage(title="Portrait test people", slug="portrait-test-people"))
            person = people.add_child(instance=PersonPage(title="Wide photo", role="Researcher", portrait=image, portrait_fit="contain", portrait_format="portrait"))
            request = RequestFactory().get("/")
            profile = BeautifulSoup(render_to_string("home/person_page.html", {"page": person}, request=request), "html.parser").select_one(".profile-image img")
            card = BeautifulSoup(render_to_string("home/includes/people_list.html", {"people_items": [person]}, request=request), "html.parser").select_one(".person-tile-image img")
            for node in (profile, card):
                self.assertAlmostEqual(int(node["width"]) / int(node["height"]), 3, delta=0.01)
                self.assertNotIn("fill-", node["src"])

    def test_homepage_featured_label_is_visible(self):
        home = HomePage(title="Home", hero_layout="constellation")
        project = ProjectPage(title="Project", live=True)
        from home.blocks import FeaturedProjectHomeSectionBlock
        block = FeaturedProjectHomeSectionBlock()
        value = block.get_default()
        value.update(is_visible=True, project=project, label="Verified project label")
        self.assertIn("Verified project label", block.render(value, context={"page": home}))
