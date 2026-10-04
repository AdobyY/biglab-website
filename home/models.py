from django import forms
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page, TranslatableMixin
from wagtail.snippets.models import register_snippet

from .blocks import CONTENT_BLOCKS, HOME_SECTION_BLOCKS
from .editorial import EditorialPageForm
from .ui import UI_LABELS


def editorial_panels():
    return [
        MultiFieldPanel([FieldPanel("intro")], heading="Page header"),
        MultiFieldPanel([FieldPanel("body"), FieldPanel("sections")], heading="Page sections"),
        MultiFieldPanel([FieldPanel("after_body")], heading="Supporting content"),
    ]


class BaseContentPage(Page):
    """Shared content fields used by editable BIG Lab pages."""

    base_form_class = EditorialPageForm

    intro = RichTextField(
        blank=True, features=["bold", "italic", "link"], verbose_name="Header introduction",
        help_text="Short introduction in the page header, above the sections.",
    )
    body = StreamField(
        CONTENT_BLOCKS, blank=True, use_json_field=True, verbose_name="Main editorial content",
        help_text="Existing page content. Kept independently of the section builder.",
    )
    after_body = StreamField(
        CONTENT_BLOCKS, blank=True, use_json_field=True,
        verbose_name="Content below the automatic list / sections",
        help_text="Add text, images or links after the page content and automatic lists. On People, this appears BELOW the people list.",
    )
    sections = StreamField(
        HOME_SECTION_BLOCKS, blank=True, use_json_field=True, verbose_name="Page section builder",
        help_text="Leave empty for the default layout. When nonempty, these sections replace the default layout; the header introduction remains. Add People then About / editorial text to place text below the team. Existing main content is retained, not deleted.",
    )

    content_panels = Page.content_panels + editorial_panels()

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        home = HomePage.objects.ancestor_of(self, inclusive=True).filter(locale=self.locale).first()
        scope = Page.objects.descendant_of(home, inclusive=True) if home else Page.objects.none()

        def index(model):
            return model.objects.filter(pk__in=scope.values("pk")).live().first()

        science = self if isinstance(self, SciencePage) else index(SciencePage)
        people_index = self if isinstance(self, PeopleIndexPage) else index(PeopleIndexPage)
        news_index = self if isinstance(self, NewsIndexPage) else index(NewsIndexPage)
        projects_index = self if isinstance(self, ProjectsIndexPage) else index(ProjectsIndexPage)
        projects = ProjectPage.objects.filter(pk__in=scope.values("pk")).live().order_by("-start_date", "path")
        news = NewsPage.objects.child_of(news_index).live().order_by("-date", "-first_published_at") if news_index else NewsPage.objects.none()
        today = timezone.localdate()
        context.update({
            "site_home": home,
            "science_page": science,
            "research_areas": science.get_children().live().specific() if science else [],
            "people_index": people_index,
            "people": PersonPage.objects.child_of(people_index).live().order_by("path") if people_index else PersonPage.objects.none(),
            "news_index": news_index,
            "news_items": news,
            "latest_news": news.first(),
            "projects_index": projects_index,
            "projects": projects,
            "current_projects": projects.filter(Q(end_date__isnull=True) | Q(end_date__gte=today)),
            "finished_projects": projects.filter(end_date__lt=today),
            "featured_projects": projects.filter(is_featured=True),
            "publications": Publication.objects.filter(locale=self.locale).order_by("-year", "title"),
            "collaborations": Collaboration.objects.filter(locale=self.locale).order_by("sort_order", "name"),
        })
        return context

    class Meta:
        abstract = True


class HomePage(BaseContentPage):
    """The site's root page, which begins with the About BIG Lab content."""

    hero_title = models.CharField(max_length=160, default="About BIG Lab")
    hero_summary = models.TextField(blank=True, verbose_name="Hero summary")
    hero_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        help_text="Optional hero image; select the Image hero layout to display it.",
    )
    hero_layout = models.CharField(
        max_length=20, default="constellation",
        choices=[("constellation", "Constellation"), ("image", "Image"), ("text", "Text only")],
        verbose_name="Hero layout",
    )
    show_contact_section = models.BooleanField(
        default=True, verbose_name="Show homepage contact section",
        help_text="Show the fallback contact section using real site settings when no Contact details block is present. A Contact details block controls its own visibility.",
    )
    about_financing = RichTextField(
        blank=True, verbose_name="About / financing information",
        help_text="Optional verified funding information, used by the fallback financing section and Financing / funding blocks with empty text. Leave blank if there is nothing to publish.",
    )
    sections = StreamField(
        HOME_SECTION_BLOCKS,
        blank=True,
        use_json_field=True,
        verbose_name="Homepage sections",
        help_text=(
            "Build the homepage below the hero. Add, duplicate, remove, hide, and drag sections "
            "into the required order."
        ),
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [FieldPanel("hero_title"), FieldPanel("hero_summary"), FieldPanel("hero_layout"), FieldPanel("hero_image")],
            heading="Hero",
        ),
        MultiFieldPanel([FieldPanel("sections")], heading="Page sections"),
        MultiFieldPanel(
            [FieldPanel("after_body"), FieldPanel("about_financing"), FieldPanel("show_contact_section")],
            heading="Supporting content",
        ),
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
        version = "2" if request.GET.get("design") == "2" else "1"
        switch_query = request.GET.copy()
        if version == "2":
            switch_query.pop("design", None)
        else:
            switch_query["design"] = "2"
        query_string = switch_query.urlencode()
        context["design_version"] = version
        context["design_switch_url"] = request.path + (f"?{query_string}" if query_string else "")
        return context


class ContentPage(BaseContentPage):
    """A flexible information page, including Parta's future sub-pages."""

    cover_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel([FieldPanel("cover_image")], heading="Page image"),
    ] + editorial_panels()

    show_in_menus_default = True
    parent_page_types = ["home.HomePage", "home.ContentPage", "home.ProjectPage", "home.SciencePage"]
    subpage_types = ["home.ContentPage"]


class PeopleIndexPage(BaseContentPage):
    show_in_menus_default = True
    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.PersonPage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["people"] = PersonPage.objects.child_of(self).live().order_by("path")
        return context


class PersonPage(BaseContentPage):
    role = models.CharField(max_length=120)
    portrait = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    card_summary = RichTextField(
        blank=True, features=["bold", "italic", "link"], verbose_name="Team card caption",
        help_text="Optional short caption below the photo on team cards. Profiles remain visible without a portrait.",
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
                FieldPanel("card_summary"),
                FieldPanel("portrait"),
                FieldPanel("show_portrait"),
                FieldPanel("portrait_size"),
                FieldPanel("portrait_format"),
                FieldPanel("portrait_fit"),
            ],
            heading="Profile and portrait display",
        ),
        MultiFieldPanel([FieldPanel("email"), FieldPanel("profile_url")], heading="Contact"),
    ] + editorial_panels()

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
        MultiFieldPanel([FieldPanel("date"), FieldPanel("cover_image")], heading="News details"),
    ] + editorial_panels()

    parent_page_types = ["home.NewsIndexPage"]
    subpage_types = []


class ProjectsIndexPage(BaseContentPage):
    show_in_menus_default = True
    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.ProjectPage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        projects = ProjectPage.objects.child_of(self).live().order_by("-start_date", "path")
        today = timezone.localdate()
        context["projects"] = projects
        context["current_projects"] = projects.filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
        context["finished_projects"] = projects.filter(end_date__lt=today)
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
    ] + editorial_panels()

    show_in_menus_default = True
    parent_page_types = ["home.HomePage", "home.ProjectsIndexPage"]
    subpage_types = ["home.ContentPage"]

    @property
    def is_completed(self):
        return self.end_date is not None and self.end_date < timezone.localdate()

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


@register_snippet
class InterfaceText(TranslatableMixin, ClusterableModel):
    key = models.CharField(
        max_length=100, choices=list(UI_LABELS["en"].items()), verbose_name="Interface label to translate",
        help_text="Choose the built-in label to override in this language. Select the same label for each translation.",
    )
    text = models.CharField(max_length=500, verbose_name="Translated label", help_text="Plain text shown instead of the built-in label in this language.")

    panels = [FieldPanel("key"), FieldPanel("text")]

    class Meta(TranslatableMixin.Meta):
        verbose_name = "interface text"
        verbose_name_plural = "interface texts"
        ordering = ["key"]
        constraints = [models.UniqueConstraint(fields=["locale", "key"], name="home_interface_text_locale_key")]

    def __str__(self):
        return f"{self.key}: {self.text}"


@register_setting
class ContactSettings(BaseSiteSetting):
    site_name = models.CharField(max_length=160, default="BIG Lab", verbose_name="Site / footer brand name")
    tagline = models.CharField(max_length=255, blank=True, help_text="Optional footer tagline. Leave blank to use the translated interface label.")
    copyright_text = models.CharField(max_length=255, blank=True, help_text="Optional custom copyright line.")
    logo = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        help_text="Shared logo for the website header, footer, browser icon and CMS. Change it here once to update every location. Leave blank to use the default BIG Lab logo.",
    )
    show_social_links = models.BooleanField(
        default=True, verbose_name="Show institute social links",
        help_text="Use verified INPSY institute accounts below, not invented BIG Lab accounts. Turn off to hide all social links.",
    )
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)

    panels = [
        MultiFieldPanel(
            [FieldPanel("site_name"), FieldPanel("tagline"), FieldPanel("copyright_text"), FieldPanel("logo")],
            heading="Site and footer brand",
        ),
        MultiFieldPanel([FieldPanel("email"), FieldPanel("phone"), FieldPanel("address")], heading="Verified contact details"),
        MultiFieldPanel(
            [FieldPanel("show_social_links"), FieldPanel("linkedin_url"), FieldPanel("instagram_url"), FieldPanel("facebook_url")],
            heading="INPSY institute social media",
        ),
    ]


HEX_COLOR_VALIDATOR = RegexValidator(
    regex=r"\A#[0-9a-fA-F]{6}\Z",
    message="Enter a six-digit hexadecimal color, for example #0b141e.",
    code="invalid_hex_color",
)


@register_setting
class HomepageDesignSettings(BaseSiteSetting):
    """One homepage Version 2 palette shared by all languages of a site."""

    background = models.CharField(
        max_length=7, default="#0b141e", validators=[HEX_COLOR_VALIDATOR],
        verbose_name="Version 2 background",
        help_text="Background of the homepage in Version 2 only. Use #RRGGBB.",
    )
    foreground = models.CharField(
        max_length=7, default="#eeeae0", validators=[HEX_COLOR_VALIDATOR],
        verbose_name="Version 2 foreground",
        help_text="Main text on the homepage in Version 2 only. Use #RRGGBB.",
    )
    accent = models.CharField(
        max_length=7, default="#dac99c", validators=[HEX_COLOR_VALIDATOR],
        verbose_name="Version 2 accent",
        help_text="Actions and primary network connections on the homepage in Version 2 only. Use #RRGGBB.",
    )
    muted = models.CharField(
        max_length=7, default="#a6b4bd", validators=[HEX_COLOR_VALIDATOR],
        verbose_name="Version 2 muted text",
        help_text="Supporting text on the homepage in Version 2 only. Use #RRGGBB.",
    )
    network_secondary = models.CharField(
        max_length=7, default="#7f9d98", validators=[HEX_COLOR_VALIDATOR],
        verbose_name="Version 2 secondary network color",
        help_text="Secondary network strands on the homepage in Version 2 only. Use #RRGGBB.",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("background", widget=forms.ColorInput()),
                FieldPanel("foreground", widget=forms.ColorInput()),
                FieldPanel("muted", widget=forms.ColorInput()),
            ],
            heading="Version 2 homepage surfaces and text",
            help_text="Shared across all languages. These colors affect only homepage Version 2 (?design=2); Version 1 remains the default.",
        ),
        MultiFieldPanel(
            [
                FieldPanel("accent", widget=forms.ColorInput()),
                FieldPanel("network_secondary", widget=forms.ColorInput()),
            ],
            heading="Version 2 homepage connections and accents",
            help_text="Choose colors with readable contrast against the Version 2 background.",
        ),
    ]

    class Meta:
        verbose_name = "homepage design (Version 2)"
