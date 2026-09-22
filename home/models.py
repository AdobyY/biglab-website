from django.db import models

from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page, TranslatableMixin
from wagtail.snippets.models import register_snippet

from .blocks import CONTENT_BLOCKS, HOME_SECTION_BLOCKS


class BaseContentPage(Page):
    """Shared content fields used by editable BIG Lab pages."""

    intro = RichTextField(blank=True, features=["bold", "italic", "link"])
    body = StreamField(CONTENT_BLOCKS, blank=True, use_json_field=True)

    content_panels = Page.content_panels + [FieldPanel("intro"), FieldPanel("body")]

    class Meta:
        abstract = True


class HomePage(BaseContentPage):
    """The site's root page, which begins with the About BIG Lab content."""

    hero_title = models.CharField(max_length=160, default="About BIG Lab")
    hero_summary = models.TextField(blank=True)
    sections = StreamField(
        HOME_SECTION_BLOCKS,
        blank=True,
        use_json_field=True,
        help_text=(
            "Build the homepage below the hero. Add, duplicate, remove, hide, and drag sections "
            "into the required order."
        ),
    )

    content_panels = Page.content_panels + [
        FieldPanel("hero_title"),
        FieldPanel("hero_summary"),
        FieldPanel("sections"),
    ]

    subpage_types = [
        "home.ContentPage",
        "home.SciencePage",
        "home.PeopleIndexPage",
        "home.NewsIndexPage",
        "home.ProjectsIndexPage",
        "home.ProjectPage",
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        children = self.get_children().live().specific()
        science = next((child for child in children if isinstance(child, SciencePage)), None)
        people_index = next((child for child in children if isinstance(child, PeopleIndexPage)), None)
        news_index = next((child for child in children if isinstance(child, NewsIndexPage)), None)
        projects_index = next((child for child in children if isinstance(child, ProjectsIndexPage)), None)
        context.update(
            {
                "science_page": science,
                "research_areas": science.get_children().live().specific() if science else [],
                "people_index": people_index,
                "people": PersonPage.objects.child_of(people_index).live().filter(portrait__isnull=False)
                if people_index
                else [],
                "news_index": news_index,
                "news_items": NewsPage.objects.child_of(news_index).live().order_by("-date")
                if news_index
                else [],
                "latest_news": NewsPage.objects.child_of(news_index).live().order_by("-date").first()
                if news_index
                else None,
                "projects_index": projects_index,
                "featured_projects": ProjectPage.objects.child_of(self).live().filter(is_featured=True),
                "current_projects": ProjectPage.objects.child_of(projects_index).live().order_by("-start_date")
                if projects_index
                else [],
                "publications": Publication.objects.filter(locale=self.locale).order_by("-year", "title"),
                "collaborations": Collaboration.objects.filter(locale=self.locale).order_by("sort_order", "name"),
            }
        )
        return context


class ContentPage(BaseContentPage):
    """A flexible information page, including Parta's future sub-pages."""

    cover_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    content_panels = Page.content_panels + [
        FieldPanel("cover_image"),
        FieldPanel("intro"),
        FieldPanel("body"),
    ]

    show_in_menus_default = True
    parent_page_types = ["home.HomePage", "home.ContentPage", "home.ProjectPage"]
    subpage_types = ["home.ContentPage"]


class PeopleIndexPage(BaseContentPage):
    show_in_menus_default = True
    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.PersonPage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["people"] = PersonPage.objects.child_of(self).live().filter(portrait__isnull=False)
        return context


class PersonPage(BaseContentPage):
    role = models.CharField(max_length=120)
    portrait = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    show_portrait = models.BooleanField(default=True)
    portrait_size = models.CharField(
        max_length=12,
        choices=[("small", "Small"), ("standard", "Standard"), ("large", "Large")],
        default="standard",
    )
    portrait_format = models.CharField(
        max_length=12,
        choices=[("portrait", "Portrait"), ("square", "Square"), ("original", "Original ratio")],
        default="portrait",
    )
    portrait_fit = models.CharField(
        max_length=12,
        choices=[("cover", "Crop to fill"), ("contain", "Show whole image")],
        default="cover",
    )
    email = models.EmailField(blank=True)
    profile_url = models.URLField(blank=True, help_text="Optional external profile URL.")

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("role"),
                FieldPanel("portrait"),
                FieldPanel("show_portrait"),
                FieldPanel("portrait_size"),
                FieldPanel("portrait_format"),
                FieldPanel("portrait_fit"),
            ],
            heading="Profile and portrait display",
        ),
        MultiFieldPanel([FieldPanel("email"), FieldPanel("profile_url")], heading="Contact"),
        FieldPanel("intro"),
        FieldPanel("body"),
    ]

    parent_page_types = ["home.PeopleIndexPage"]
    subpage_types = []


class NewsIndexPage(BaseContentPage):
    show_in_menus_default = True
    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.NewsPage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["news_items"] = NewsPage.objects.child_of(self).live().order_by(
            "-date", "-first_published_at"
        )
        return context


class NewsPage(BaseContentPage):
    date = models.DateField("publication date")
    cover_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("cover_image"),
        FieldPanel("intro"),
        FieldPanel("body"),
    ]

    parent_page_types = ["home.NewsIndexPage"]
    subpage_types = []


class ProjectsIndexPage(BaseContentPage):
    show_in_menus_default = True
    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.ProjectPage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["projects"] = self.get_children().live().specific()
        return context


class ProjectPage(BaseContentPage):
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    funder = models.CharField(max_length=255, blank=True)
    external_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("start_date"),
                FieldPanel("end_date"),
                FieldPanel("funder"),
                FieldPanel("external_url"),
                FieldPanel("is_featured"),
            ],
            heading="Project details",
        ),
        FieldPanel("intro"),
        FieldPanel("body"),
    ]

    show_in_menus_default = True
    parent_page_types = ["home.HomePage", "home.ProjectsIndexPage"]
    subpage_types = ["home.ContentPage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["project_sections"] = self.get_children().live().specific()
        return context


class SciencePage(BaseContentPage):
    show_in_menus_default = True
    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.ContentPage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["publications"] = Publication.objects.filter(locale=self.locale).order_by("-year", "title")
        context["collaborations"] = Collaboration.objects.filter(locale=self.locale).order_by(
            "sort_order", "name"
        )
        return context


@register_snippet
class Publication(TranslatableMixin, ClusterableModel):
    title = models.CharField(max_length=500)
    authors = models.TextField(help_text="List authors in the desired display order.")
    year = models.PositiveSmallIntegerField()
    publication_type = models.CharField(max_length=120, blank=True)
    journal_or_publisher = models.CharField(max_length=255, blank=True)
    doi_or_url = models.URLField(blank=True)

    panels = [
        FieldPanel("title"),
        FieldPanel("authors"),
        MultiFieldPanel([FieldPanel("year"), FieldPanel("publication_type")], heading="Details"),
        FieldPanel("journal_or_publisher"),
        FieldPanel("doi_or_url"),
    ]

    class Meta(TranslatableMixin.Meta):
        verbose_name = "publication"
        verbose_name_plural = "publications"
        ordering = ["-year", "title"]

    def __str__(self):
        return self.title


@register_snippet
class Collaboration(TranslatableMixin, ClusterableModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    sort_order = models.PositiveIntegerField(default=0)

    panels = [
        FieldPanel("name"),
        FieldPanel("description"),
        FieldPanel("website"),
        FieldPanel("logo"),
        FieldPanel("sort_order"),
    ]

    class Meta(TranslatableMixin.Meta):
        verbose_name = "collaboration"
        verbose_name_plural = "collaborations"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


@register_setting
class ContactSettings(BaseSiteSetting):
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)

    panels = [
        MultiFieldPanel([FieldPanel("email"), FieldPanel("phone"), FieldPanel("address")], heading="Contact"),
        MultiFieldPanel(
            [FieldPanel("linkedin_url"), FieldPanel("instagram_url"), FieldPanel("facebook_url")],
            heading="Social media",
        ),
    ]
