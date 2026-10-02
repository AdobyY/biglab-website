from datetime import timedelta
from html import unescape
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.db.migrations.loader import MigrationLoader
from django.template import Context, Engine, Template
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from wagtail.admin.panels import MultiFieldPanel
from wagtail.models import Locale, Page, Revision

from home.blocks import HOME_SECTION_BLOCKS
from home.editorial import defaults_for_page
from home.models import (
    ContactSettings, ContentPage, HomePage, InterfaceText, NewsIndexPage, NewsPage,
    PeopleIndexPage, PersonPage, ProjectPage, ProjectsIndexPage, SciencePage,
)
from home.ui import UI_LABELS


class EditorialTests(TestCase):
    def setUp(self):
        self.home = Page.get_first_root_node().add_child(instance=HomePage(title="Editorial home", slug="editorial-home"))
        self.people = self.home.add_child(instance=PeopleIndexPage(title="People", slug="people"))
        self.projects = self.home.add_child(instance=ProjectsIndexPage(title="Projects", slug="projects"))
        self.science = self.home.add_child(instance=SciencePage(title="Science", slug="science"))
        self.news = self.home.add_child(instance=NewsIndexPage(title="News", slug="news"))
        self.request = RequestFactory().get("/")

    def test_people_without_portraits_are_in_home_and_index_context(self):
        person = self.people.add_child(instance=PersonPage(title="No portrait researcher", role="Researcher"))
        for page in (self.home, self.people, self.science):
            self.assertIn(person, page.get_context(self.request)["people"])
        response = self.people.serve(self.request)
        response.render()
        self.assertContains(response, person.title)

    def test_after_body_round_trips_and_renders_below_automatic_people(self):
        person = self.people.add_child(instance=PersonPage(title="Automatic person", role="Researcher"))
        self.people.body = [("text", "<p>Original editorial content</p>")]
        self.people.intro = "<p>Original introduction</p>"
        self.people.after_body = [("text", "<p>Editorial text below the team</p>")]
        self.people.save_revision().publish()
        self.people.refresh_from_db()
        # Exercise the backend rendering contract without owning the parent's page templates.
        template = Template(
            "{% load wagtailcore_tags %}{% for person in people %}{{ person.title }}{% endfor %}"
            "{% include_block page.after_body %}"
        )
        rendered = template.render(Context(self.people.get_context(self.request)))
        self.assertLess(rendered.index(person.title), rendered.index("Editorial text below the team"))
        self.assertIn("Original editorial content", str(self.people.body[0].value))
        self.assertIn("Original introduction", str(self.people.intro))

    def test_project_dates_are_split_on_local_today(self):
        today = timezone.localdate()
        finished = self.projects.add_child(instance=ProjectPage(title="Finished", end_date=today - timedelta(days=1)))
        ends_today = self.projects.add_child(instance=ProjectPage(title="Ends today", end_date=today))
        future = self.projects.add_child(instance=ProjectPage(title="Future", end_date=today + timedelta(days=1)))
        open_ended = self.projects.add_child(instance=ProjectPage(title="Open ended"))
        for page in (self.home, self.projects, self.science):
            context = page.get_context(self.request)
            self.assertEqual(set(context["finished_projects"]), {finished})
            self.assertEqual(set(context["current_projects"]), {ends_today, future, open_ended})
        self.assertTrue(finished.is_completed)
        self.assertFalse(ends_today.is_completed)
        self.assertFalse(open_ended.is_completed)
        with patch("home.models.timezone.localdate", return_value=today + timedelta(days=1)):
            self.assertTrue(ends_today.is_completed)

    def test_featured_projects_include_nested_published_projects(self):
        featured = self.projects.add_child(instance=ProjectPage(title="Nested featured", is_featured=True))
        draft = self.projects.add_child(instance=ProjectPage(title="Draft featured", is_featured=True, live=False))
        context = self.home.get_context(self.request)
        self.assertIn(featured, context["featured_projects"])
        self.assertNotIn(draft, context["featured_projects"])

    def test_child_section_context_and_old_direct_routes(self):
        area = self.science.add_child(instance=ContentPage(title="Research area"))
        project = self.projects.add_child(instance=ProjectPage(title="Project"))
        section = project.add_child(instance=ContentPage(title="Results"))
        self.assertIn(area, self.science.get_context(self.request)["research_areas"])
        self.assertIn(section, project.get_context(self.request)["project_sections"])
        self.assertEqual(section.serve(self.request).status_code, 200)
        self.assertEqual(section.serve_preview(self.request, "").status_code, 200)

    def test_context_indexes_are_available_on_other_indexes(self):
        item = self.news.add_child(instance=NewsPage(title="Update", date=timezone.localdate()))
        context = self.people.get_context(self.request)
        self.assertEqual(context["people_index"], self.people)
        self.assertEqual(context["news_index"], self.news)
        self.assertEqual(context["science_page"], self.science)
        self.assertEqual(context["projects_index"], self.projects)
        self.assertEqual(context["latest_news"], item)

    def test_all_page_editors_expose_the_builder_and_after_body(self):
        for model in (HomePage, ContentPage, PeopleIndexPage, PersonPage, NewsIndexPage, NewsPage, ProjectsIndexPage, ProjectPage, SciencePage):
            with self.subTest(model=model.__name__):
                fields = model.get_edit_handler().get_form_class().base_fields
                self.assertTrue({"sections", "after_body"}.issubset(fields))
                if model is HomePage:
                    self.assertNotIn("intro", fields)
                    self.assertNotIn("body", fields)
                else:
                    self.assertTrue({"intro", "body"}.issubset(fields))
        fields = HomePage.get_edit_handler().get_form_class().base_fields
        self.assertTrue({"hero_image", "hero_layout", "show_contact_section", "about_financing"}.issubset(fields))
        self.assertIn("card_summary", PersonPage.get_edit_handler().get_form_class().base_fields)
        self.assertTrue(ContactSettings._meta.get_field("show_social_links").default)

    def test_full_list_blocks_share_editorial_controls(self):
        blocks = dict(HOME_SECTION_BLOCKS)
        for name in ("publications", "collaborations", "project_list", "child_sections", "news_list", "financing", "contact"):
            block = blocks[name]
            self.assertTrue({"title", "intro", "theme", "is_visible", "background_image", "background_position", "background_overlay"}.issubset(block.child_blocks))
            self.assertEqual(block.meta.template, f"home/sections/{name}.html")
        self.assertIn("status", blocks["project_list"].child_blocks)

    def test_editor_groups_are_clear_and_home_legacy_data_is_retained(self):
        headings = [panel.heading for panel in HomePage.content_panels if isinstance(panel, MultiFieldPanel)]
        self.assertEqual(headings, ["Hero", "Page sections", "Supporting content"])
        self.home.intro = "<p>Legacy intro</p>"
        self.home.body = [("text", "<p>Legacy body</p>")]
        self.home.save()
        self.home.refresh_from_db()
        self.assertIn("Legacy intro", str(self.home.intro))
        self.assertIn("Legacy body", str(self.home.body[0].value))
        for model in (PeopleIndexPage, NewsIndexPage, ProjectsIndexPage, SciencePage, ProjectPage):
            headings = [panel.heading for panel in model.content_panels if isinstance(panel, MultiFieldPanel)]
            self.assertTrue({"Page header", "Page sections", "Supporting content"}.issubset(headings))
        self.assertEqual(self.people.get_context(self.request)["site_home"], self.home)

    def test_new_labels_are_blank_but_existing_editor_labels_are_preserved(self):
        blocks = dict(HOME_SECTION_BLOCKS)
        labels = {
            "people": ["title", "link_label"], "research": ["title", "link_label"],
            "updates": ["title"], "featured_project": ["label", "button_label"],
        }
        for name, fields in labels.items():
            for field in fields:
                block = blocks[name].child_blocks[field]
                self.assertFalse(block.required)
                self.assertEqual(block.get_default(), "")
                self.assertEqual(block.to_python("Editor-owned label"), "Editor-owned label")
        self.assertEqual(dict(blocks["people"].child_blocks["theme"].field.choices)["lilac"], "Legacy cream")
        contact = blocks["contact"].get_default()
        for field in ("show_email", "show_phone", "show_address", "show_people_link", "show_social_links"):
            self.assertTrue(contact[field])
        self.assertFalse(blocks["financing"].child_blocks["text"].required)

    def test_migration_populates_only_empty_canonical_builders_and_preserves_revisions(self):
        project = self.projects.add_child(instance=ProjectPage(title="Migrated project"))
        self.people.intro = "<p>Keep intro</p>"
        self.people.body = [("text", "<p>Keep body</p>")]
        self.people.after_body = [("text", "<p>Keep after body</p>")]
        self.people.save()
        draft = self.people.save_revision()
        revision_snapshot = list(Revision.objects.order_by("pk").values_list("pk", "content"))
        page_snapshot = list(Page.objects.order_by("pk").values_list("pk", "live", "latest_revision_id", "live_revision_id", "has_unpublished_changes"))
        migration = import_module("home.migrations.0013_visible_default_sections")
        historical_apps = MigrationLoader(connection).project_state([("home", "0013_visible_default_sections")]).apps
        migration.populate_empty_sections(historical_apps, SimpleNamespace(connection=connection))
        expected = {
            self.people: ["people"], self.news: ["news_list"],
            self.projects: ["project_list", "project_list"],
            self.science: ["child_sections", "publications", "collaborations"],
            project: ["child_sections"],
        }
        for page, block_types in expected.items():
            page.refresh_from_db()
            self.assertEqual([block.block_type for block in page.sections], block_types)
            for block in page.sections:
                self.assertTrue(block.value["is_visible"])
                self.assertEqual(block.value["theme"], "paper")
                self.assertEqual(block.value["title"], "")
        self.assertEqual([block.value["status"] for block in self.projects.sections], ["current", "finished"])
        self.assertIn("Keep intro", str(self.people.intro))
        self.assertIn("Keep body", str(self.people.body[0].value))
        self.assertIn("Keep after body", str(self.people.after_body[0].value))
        self.assertEqual(revision_snapshot, list(Revision.objects.order_by("pk").values_list("pk", "content")))
        self.assertEqual(page_snapshot, list(Page.objects.order_by("pk").values_list("pk", "live", "latest_revision_id", "live_revision_id", "has_unpublished_changes")))
        self.assertFalse(draft.as_object().sections)
        sections_snapshot = list(self.people.sections.raw_data)
        migration.populate_empty_sections(historical_apps, SimpleNamespace(connection=connection))
        self.people.refresh_from_db()
        self.assertEqual(list(self.people.sections.raw_data), sections_snapshot)

    def test_migration_does_not_replace_a_nonempty_editor_builder(self):
        self.people.sections = [("about", {"title": "Editor's section", "text": "<p>Keep me</p>", "theme": "coral", "is_visible": False})]
        self.people.save()
        snapshot = list(self.people.sections.raw_data)
        migration = import_module("home.migrations.0013_visible_default_sections")
        historical_apps = MigrationLoader(connection).project_state([("home", "0013_visible_default_sections")]).apps
        migration.populate_empty_sections(historical_apps, SimpleNamespace(connection=connection))
        self.people.refresh_from_db()
        self.assertEqual(list(self.people.sections.raw_data), snapshot)

    def test_repair_migration_handles_legacy_sql_empty_values_in_both_locales(self):
        cs, _ = Locale.objects.get_or_create(language_code="cs")
        historical_apps = MigrationLoader(connection).project_state([("home", "0014_repair_empty_sections")]).apps
        model = historical_apps.get_model("home", "PeopleIndexPage")
        table = connection.ops.quote_name(model._meta.db_table)
        pk_column = connection.ops.quote_name(model._meta.pk.column)
        sections_column = connection.ops.quote_name(model._meta.get_field("sections").column)
        # StreamField's JSON column is NOT NULL. JSON null and JSON empty
        # strings are valid legacy representations; SQL NULL/invalid JSON are not.
        raw_values = ["[]", "[ ]", "null", '""', '"[]"']
        pages = []
        for locale in (self.home.locale, cs):
            for index, raw_value in enumerate(raw_values):
                page = self.home.add_child(instance=PeopleIndexPage(
                    title=f"Legacy {locale.language_code} {index}",
                    slug=f"legacy-{locale.language_code}-{index}", locale=locale,
                    intro="<p>Retain legacy intro</p>",
                    body=[("text", "<p>Retain legacy body</p>")],
                ))
                page.save_revision()
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"UPDATE {table} SET {sections_column} = %s WHERE {pk_column} = %s",
                        [raw_value, page.pk],
                    )
                page.refresh_from_db()
                self.assertFalse(page.sections, raw_value)
                pages.append(page)
        revision_snapshot = list(Revision.objects.order_by("pk").values_list("pk", "content"))
        page_snapshot = list(Page.objects.order_by("pk").values_list("pk", "live", "latest_revision_id", "live_revision_id", "has_unpublished_changes"))
        migration = import_module("home.migrations.0014_repair_empty_sections")
        migration.repair_empty_sections(historical_apps, SimpleNamespace(connection=connection))
        for page in pages:
            page.refresh_from_db()
            self.assertEqual([block.block_type for block in page.sections], ["people"])
            self.assertTrue(page.sections[0].value["is_visible"])
            self.assertEqual(page.sections[0].value["theme"], "paper")
            self.assertIn("Retain legacy intro", str(page.intro))
            self.assertIn("Retain legacy body", str(page.body[0].value))
        self.assertEqual(revision_snapshot, list(Revision.objects.order_by("pk").values_list("pk", "content")))
        self.assertEqual(page_snapshot, list(Page.objects.order_by("pk").values_list("pk", "live", "latest_revision_id", "live_revision_id", "has_unpublished_changes")))
        snapshot = [list(page.sections.raw_data) for page in pages]
        migration.repair_empty_sections(historical_apps, SimpleNamespace(connection=connection))
        for page, original in zip(pages, snapshot):
            page.refresh_from_db()
            self.assertEqual(list(page.sections.raw_data), original)

    def test_repair_migration_preserves_nonempty_editor_builders(self):
        self.people.sections = [("about", {"title": "Keep editor content", "text": "<p>Keep me</p>", "theme": "coral", "is_visible": False})]
        self.people.save()
        snapshot = list(self.people.sections.raw_data)
        migration = import_module("home.migrations.0014_repair_empty_sections")
        historical_apps = MigrationLoader(connection).project_state([("home", "0014_repair_empty_sections")]).apps
        migration.repair_empty_sections(historical_apps, SimpleNamespace(connection=connection))
        self.people.refresh_from_db()
        self.assertEqual(list(self.people.sections.raw_data), snapshot)

    def test_unbound_editor_defaults_for_all_automatic_container_pages(self):
        project = self.projects.add_child(instance=ProjectPage(title="Editable project"))
        expected = {
            self.people: ["people"], self.news: ["news_list"],
            self.projects: ["project_list", "project_list"],
            self.science: ["child_sections", "publications", "collaborations"],
            project: ["child_sections"],
        }
        for page, block_types in expected.items():
            with self.subTest(page=page.__class__.__name__):
                form = page.get_edit_handler().get_form_class()(instance=page, parent_page=self.home)
                self.assertEqual([block.block_type for block in form["sections"].value()], block_types)
                for block in form["sections"].value():
                    self.assertTrue(block.value["is_visible"])
                    self.assertEqual(block.value["title"], "")
                    self.assertEqual(block.value["theme"], "paper")
                self.assertFalse(page.sections)
                page.refresh_from_db()
                self.assertFalse(page.sections)
        self.assertEqual([block.value["status"] for block in defaults_for_page(self.projects)], ["current", "finished"])
        home_form = self.home.get_edit_handler().get_form_class()(instance=self.home)
        self.assertFalse(home_form["sections"].value())

    def test_actual_admin_editor_shows_people_for_an_old_blank_revision(self):
        draft = self.people.save_revision()
        self.people.sections = defaults_for_page(self.people)
        self.people.save(update_fields=["sections"])
        revision_snapshot = list(Revision.objects.order_by("pk").values_list("pk", "content"))
        user = get_user_model().objects.create_superuser(
            username="editor-defaults", email="editor@example.com", password="test-password",
        )
        self.client.force_login(user)
        response = self.client.get(reverse("wagtailadmin_pages:edit", args=[self.people.pk]))
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertFalse(form.instance.sections)
        self.assertEqual(form.instance.latest_revision_id, draft.pk)
        self.assertEqual([block.block_type for block in form["sections"].value()], ["people"])
        # Verify actual widget initialization, not just the available block menu.
        widget = unescape(str(form["sections"]))
        self.assertIn('"type": "people"', widget)
        self.assertIn('"limit": "24"', widget)
        self.assertIn('"limit": "24"', unescape(response.content.decode()))
        self.assertEqual(revision_snapshot, list(Revision.objects.order_by("pk").values_list("pk", "content")))
        self.assertFalse(draft.as_object().sections)

    def test_bound_empty_submission_can_clear_and_save_the_builder(self):
        self.people.sections = defaults_for_page(self.people)
        form_class = self.people.get_edit_handler().get_form_class()
        form = form_class(
            data={
                "title": self.people.title, "slug": self.people.slug,
                "intro": '{"blocks": [], "entityMap": {}}',
                "body-count": "0", "sections-count": "0", "after_body-count": "0",
            },
            instance=self.people, parent_page=self.home,
        )
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data["sections"])
        self.assertFalse(form["sections"].value())
        page = form.save(commit=False)
        revision = page.save_revision()
        self.assertFalse(revision.as_object().sections)

    def test_nonempty_builder_and_explicit_initial_are_not_replaced(self):
        self.people.sections = [("about", {"title": "Keep this custom layout", "theme": "coral"})]
        form_class = self.people.get_edit_handler().get_form_class()
        form = form_class(instance=self.people)
        self.assertEqual(form["sections"].value()[0].block_type, "about")
        self.assertEqual(form["sections"].value()[0].value["title"], "Keep this custom layout")
        self.people.sections = []
        initial = self.people._meta.get_field("sections").to_python([
            ("about", {"title": "Explicit initial", "theme": "paper"}),
        ])
        form = form_class(instance=self.people, initial={"sections": initial})
        self.assertEqual(form["sections"].value()[0].value["title"], "Explicit initial")

    def test_editor_defaults_are_fresh_and_match_the_frozen_migration(self):
        first = defaults_for_page(self.people)
        first[0].value["selected_people"].append("Not a shared default")
        self.assertEqual(list(defaults_for_page(self.people)[0].value["selected_people"]), [])
        migration = import_module("home.migrations.0013_visible_default_sections")
        historical_apps = MigrationLoader(connection).project_state([("home", "0013_visible_default_sections")]).apps
        migration.populate_empty_sections(historical_apps, SimpleNamespace(connection=connection))
        self.people.refresh_from_db()
        block = dict(HOME_SECTION_BLOCKS)["people"]
        self.assertEqual(
            block.get_prep_value(defaults_for_page(self.people)[0].value),
            block.get_prep_value(self.people.sections[0].value),
        )


class InterfaceTextTests(TestCase):
    def setUp(self):
        self.en = Locale.objects.get(language_code="en")
        self.cs, _ = Locale.objects.get_or_create(language_code="cs")
        self.de, _ = Locale.objects.get_or_create(language_code="de")
        self.template = Template("{% load ui_tags %}{% ui 'people' %}|{% ui 'skip_content' %}|{% ui 'people' %}")

    def test_localized_overrides_are_loaded_once_per_render(self):
        InterfaceText.objects.create(locale=self.en, key="people", text="Our team")
        InterfaceText.objects.create(locale=self.cs, key="people", text="Náš tým")
        with self.assertNumQueries(1):
            output = self.template.render(Context({"locale": self.cs}))
        self.assertEqual(output, "Náš tým|Přejít na obsah|Náš tým")
        self.assertEqual(self.template.render(Context({"locale": self.en})), "Our team|Skip to content|Our team")

    def test_includes_share_cache_but_separate_renders_refresh_overrides(self):
        label = InterfaceText.objects.create(locale=self.en, key="people", text="Team")
        engine = Engine(
            libraries={"ui_tags": "home.templatetags.ui_tags"},
            loaders=[("django.template.loaders.locmem.Loader", {
                "label.html": "{% load ui_tags %}{% ui 'people' %}",
            })],
        )
        template = engine.from_string('{% include "label.html" %}|{% include "label.html" %}')
        context = Context({"locale": self.en})
        with self.assertNumQueries(1):
            self.assertEqual(template.render(context), "Team|Team")
        label.text = "Updated team"
        label.save()
        with self.assertNumQueries(1):
            self.assertEqual(template.render(context), "Updated team|Updated team")

    def test_new_language_falls_back_to_english_and_unknown_key_is_readable(self):
        self.assertEqual(self.template.render(Context({"locale": self.de})), "People|Skip to content|People")
        template = Template("{% load ui_tags %}{% ui 'new_label' %}")
        self.assertEqual(template.render(Context({"locale": self.de})), "new_label")
        self.assertEqual(set(UI_LABELS["en"]), set(UI_LABELS["cs"]))

    def test_request_language_is_used_without_a_page(self):
        request = RequestFactory().get("/")
        request.LANGUAGE_CODE = "cs"
        self.assertEqual(self.template.render(Context({"request": request})), "Lidé|Přejít na obsah|Lidé")

    def test_labels_are_escaped(self):
        InterfaceText.objects.create(locale=self.en, key="people", text='<script>alert("x")</script>')
        self.assertNotIn("<script>", self.template.render(Context({"locale": self.en})))

    def test_editor_selects_human_readable_interface_labels(self):
        fields = InterfaceText.get_edit_handler().get_form_class().base_fields
        self.assertEqual(dict(fields["key"].choices)["skip_content"], "Skip to content")
        self.assertEqual(fields["key"].label, "Interface label to translate")
        self.assertEqual(fields["text"].label, "Translated label")

    def test_keys_are_unique_per_locale(self):
        InterfaceText.objects.create(locale=self.en, key="people", text="Team")
        InterfaceText.objects.create(locale=self.cs, key="people", text="Tým")
        with self.assertRaises(IntegrityError), transaction.atomic():
            InterfaceText.objects.create(locale=self.en, key="people", text="Duplicate")
