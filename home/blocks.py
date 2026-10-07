from django.core.exceptions import ValidationError
from wagtail import blocks
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.blocks import SnippetChooserBlock


class HeadingBlock(blocks.CharBlock):
    class Meta:
        icon = "title"
        template = "home/blocks/heading.html"


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    caption = blocks.CharBlock(required=False, max_length=250)

    class Meta:
        icon = "image"
        template = "home/blocks/image.html"


class DocumentBlock(blocks.StructBlock):
    document = DocumentChooserBlock()
    label = blocks.CharBlock(
        required=False,
        help_text="Optional public label. The document title is used if this is empty.",
    )

    class Meta:
        icon = "doc-full"
        template = "home/blocks/document.html"


def validate_link(value, label_field, page_field, url_field, required=False):
    """Keep an optional link empty, or require a complete, unambiguous link."""
    errors = {}
    page, url, label = value.get(page_field), value.get(url_field), value.get(label_field)
    if page and url:
        errors[url_field] = ValidationError("Choose an internal page OR enter an external URL, not both.")
    if (required or label) and not (page or url):
        errors[page_field] = ValidationError("Choose a page or enter a URL for this button.")
    if (page or url) and not label:
        errors[label_field] = ValidationError("Enter the text visitors will see on this button.")
    if errors:
        raise blocks.StructBlockValidationError(block_errors=errors)
    return value


class CallToActionBlock(blocks.StructBlock):
    label = blocks.CharBlock(max_length=80)
    page = blocks.PageChooserBlock(required=False)
    url = blocks.URLBlock(required=False, help_text="Use this for an external link.")

    def clean(self, value):
        return validate_link(super().clean(value), "label", "page", "url", required=True)

    class Meta:
        icon = "link"
        template = "home/blocks/call_to_action.html"


class SimulationBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=False, max_length=120)
    description = blocks.TextBlock(required=False)
    embed_url = blocks.URLBlock(
        help_text="URL of a prepared, trusted interactive simulation. Do not paste JavaScript here."
    )

    class Meta:
        icon = "pick"
        template = "home/blocks/simulation.html"
        help_text = "Embed a prepared animation or interactive simulation."


SECTION_THEME_CHOICES = [
    ("paper", "Cream"),
    ("lilac", "Legacy cream"),
    ("midnight", "Midnight"),
    ("coral", "Brick red"),
]


class HomeSectionBlock(blocks.StructBlock):
    """Shared editorial controls for reorderable page sections."""

    intro = blocks.RichTextBlock(
        required=False, features=["bold", "italic", "link"],
        label="Section introduction",
        help_text="Optional introduction above this section's content.",
    )

    is_visible = blocks.BooleanBlock(
        required=False,
        default=True,
        label="Show this section",
        help_text="Turn this off to hide the section without deleting its content.",
    )
    anchor = blocks.RegexBlock(
        required=False,
        regex=r"^[a-z0-9-]*$",
        max_length=60,
        label="Anchor",
        help_text="Optional URL anchor, for example: our-methods",
    )
    background_image = ImageChooserBlock(
        required=False,
        help_text="Optional section background. The original image remains reusable elsewhere.",
    )
    background_position = blocks.ChoiceBlock(
        choices=[
            ("center", "Centre"),
            ("top", "Top"),
            ("bottom", "Bottom"),
            ("left", "Left"),
            ("right", "Right"),
        ],
        default="center",
        required=False,
    )
    background_overlay = blocks.ChoiceBlock(
        choices=[
            ("none", "No overlay"),
            ("light", "Light overlay"),
            ("medium", "Medium overlay"),
            ("dark", "Dark overlay"),
        ],
        default="medium",
        required=False,
        help_text="Adds contrast between the background image and text.",
    )

    def get_form_layout(self):
        appearance = [name for name in (
            "theme", "anchor", "background_image", "background_position", "background_overlay"
        ) if name in self.child_blocks]
        content = [name for name in self.child_blocks if name not in appearance]
        if "title" in content:
            content.remove("title")
            content.insert(0, "title")
        # Native Wagtail settings expand automatically when a field has an error.
        self.meta.label_format = "{title}" if "title" in content else "{label}" if "label" in content else ""
        return blocks.BlockGroup(content, settings=appearance)

    def clean(self, value):
        value = super().clean(value)
        if "button_label" in self.child_blocks and "button_page" in self.child_blocks:
            validate_link(value, "button_label", "button_page", "button_url")
        return value

    class Meta:
        abstract = True


class AboutHomeSectionBlock(HomeSectionBlock):
    title = blocks.CharBlock(max_length=160)
    intro = blocks.RichTextBlock(required=False, features=["bold", "italic", "link"])
    text = blocks.RichTextBlock(
        required=False,
        features=["h2", "h3", "bold", "italic", "link", "ol", "ul"],
    )
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="paper")

    class Meta:
        icon = "doc-full"
        label = "About / editorial text"
        template = "home/sections/about.html"


class RichMediaHomeSectionBlock(HomeSectionBlock):
    title = blocks.CharBlock(max_length=180)
    text = blocks.RichTextBlock(
        required=False,
        features=["h2", "h3", "bold", "italic", "link", "ol", "ul"],
    )
    image = ImageChooserBlock(required=False)
    image_caption = blocks.CharBlock(required=False, max_length=250)
    layout = blocks.ChoiceBlock(
        choices=[
            ("text-left", "Text left, image right"),
            ("image-left", "Image left, text right"),
            ("full-image", "Large image below text"),
            ("text-only", "Text only"),
        ],
        default="text-left",
    )
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="paper")
    button_label = blocks.CharBlock(required=False, max_length=80)
    button_page = blocks.PageChooserBlock(required=False)
    button_url = blocks.URLBlock(required=False)

    class Meta:
        icon = "image"
        label = "Text and image"
        template = "home/sections/rich_media.html"


class ResearchHomeSectionBlock(HomeSectionBlock):
    title = blocks.CharBlock(required=False, max_length=120, default="", help_text="Leave blank for the translated research heading.")
    link_label = blocks.CharBlock(required=False, max_length=80, default="", help_text="Leave blank for the translated science link label.")
    selected_areas = blocks.ListBlock(
        blocks.PageChooserBlock(page_type="home.ContentPage"),
        required=False,
        default=[],
        max_num=12,
        label="Selected research areas",
        help_text="Choose research pages under Science in this page's language, then drag into order. Leave empty for the automatic list. Draft pages appear only after publication.",
    )
    limit = blocks.IntegerBlock(
        min_value=1,
        max_value=12,
        default=5,
        label="Maximum number of areas",
    )
    show_images = blocks.BooleanBlock(required=False, default=True)
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="paper")

    class Meta:
        icon = "site"
        label = "Research areas"
        template = "home/sections/research.html"


class PeopleHomeSectionBlock(HomeSectionBlock):
    title = blocks.CharBlock(required=False, max_length=120, default="", help_text="Leave blank for the translated team heading.")
    link_label = blocks.CharBlock(required=False, max_length=80, default="", help_text="Leave blank for the translated team link label.")
    selected_people = blocks.ListBlock(
        blocks.PageChooserBlock(page_type="home.PersonPage"),
        required=False,
        default=[],
        max_num=24,
        label="Selected people",
        help_text="Choose people in this page's language, then drag into order. Leave empty for the automatic team. Draft profiles appear only after publication.",
    )
    limit = blocks.IntegerBlock(
        min_value=1,
        max_value=24,
        default=12,
        label="Maximum number of people",
    )
    show_roles = blocks.BooleanBlock(required=False, default=True)
    enable_carousel = blocks.BooleanBlock(
        required=False,
        default=True,
        help_text="Adds previous/next controls when the list exceeds the threshold below.",
    )
    carousel_after = blocks.IntegerBlock(
        min_value=2,
        max_value=8,
        default=6,
        label="Start carousel after",
    )
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="paper")

    class Meta:
        icon = "group"
        label = "People"
        template = "home/sections/people.html"


class FeaturedProjectHomeSectionBlock(HomeSectionBlock):
    project = blocks.PageChooserBlock(required=False, page_type="home.ProjectPage")
    label = blocks.CharBlock(required=False, max_length=80, default="", label="Project subtitle", help_text="Optional subtitle beneath the project title. Leave blank to omit it.")
    button_label = blocks.CharBlock(required=False, max_length=80, default="", help_text="Leave blank for the translated project link label.")
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="coral")

    class Meta:
        icon = "folder-open-inverse"
        label = "Featured project"
        template = "home/sections/featured_project.html"


class UpdatesHomeSectionBlock(HomeSectionBlock):
    title = blocks.CharBlock(required=False, max_length=120, default="", help_text="Leave blank for the translated updates heading.")
    show_news = blocks.BooleanBlock(required=False, default=True)
    news_heading = blocks.CharBlock(required=False, max_length=80)
    selected_news = blocks.ListBlock(
        blocks.PageChooserBlock(page_type="home.NewsPage"),
        required=False,
        default=[],
        max_num=6,
        label="Selected news",
        help_text="Choose news in this page's language. Leave empty for the newest published news. Draft items appear only after publication.",
    )
    news_limit = blocks.IntegerBlock(min_value=1, max_value=6, default=1)
    show_projects = blocks.BooleanBlock(required=False, default=True)
    projects_heading = blocks.CharBlock(required=False, max_length=80)
    selected_projects = blocks.ListBlock(
        blocks.PageChooserBlock(page_type="home.ProjectPage"),
        required=False,
        default=[],
        max_num=6,
        label="Selected projects",
        help_text="Choose projects in this page's language. Leave empty for the latest current projects. Draft items appear only after publication.",
    )
    projects_limit = blocks.IntegerBlock(min_value=1, max_value=6, default=2)
    show_publications = blocks.BooleanBlock(required=False, default=True)
    publications_heading = blocks.CharBlock(required=False, max_length=80)
    selected_publications = blocks.ListBlock(
        SnippetChooserBlock("home.Publication"),
        required=False,
        default=[],
        max_num=6,
        label="Selected publications",
        help_text="Choose publications in this page's language. Leave empty for the newest publications automatically.",
    )
    publications_limit = blocks.IntegerBlock(min_value=1, max_value=6, default=2)
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="paper")

    class Meta:
        icon = "date"
        label = "News, projects and publications"
        template = "home/sections/updates.html"


class SelectedPageBlock(blocks.StructBlock):
    page = blocks.PageChooserBlock()
    label = blocks.CharBlock(required=False, max_length=100)
    description = blocks.TextBlock(required=False, max_length=300)


class PageLinksHomeSectionBlock(HomeSectionBlock):
    title = blocks.CharBlock(max_length=160)
    intro = blocks.RichTextBlock(required=False, features=["bold", "italic", "link"])
    pages = blocks.ListBlock(SelectedPageBlock(), min_num=1, max_num=12)
    columns = blocks.ChoiceBlock(
        choices=[("two", "Two columns"), ("three", "Three columns"), ("list", "Editorial list")],
        default="three",
    )
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="paper")

    class Meta:
        icon = "link"
        label = "Selected pages"
        template = "home/sections/page_links.html"


class GalleryImageBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    caption = blocks.CharBlock(required=False, max_length=250)


class GalleryHomeSectionBlock(HomeSectionBlock):
    title = blocks.CharBlock(required=False, max_length=160)
    intro = blocks.RichTextBlock(required=False, features=["bold", "italic", "link"])
    images = blocks.ListBlock(GalleryImageBlock(), min_num=2, max_num=12)
    columns = blocks.ChoiceBlock(
        choices=[("two", "Two columns"), ("three", "Three columns"), ("four", "Four columns")],
        default="three",
    )
    enable_lightbox = blocks.BooleanBlock(
        required=False,
        default=True,
        label="Open images full screen",
    )
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="paper")

    class Meta:
        icon = "image"
        label = "Image gallery"
        template = "home/sections/gallery.html"


class ComparisonHomeSectionBlock(HomeSectionBlock):
    title = blocks.CharBlock(required=False, max_length=160)
    intro = blocks.RichTextBlock(required=False, features=["bold", "italic", "link"])
    before_image = ImageChooserBlock(label="Before image")
    after_image = ImageChooserBlock(label="After image")
    before_label = blocks.CharBlock(required=False, max_length=40, default="Before")
    after_label = blocks.CharBlock(required=False, max_length=40, default="After")
    start_position = blocks.IntegerBlock(
        min_value=10,
        max_value=90,
        default=50,
        help_text="Initial divider position, in percent.",
    )
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="paper")

    class Meta:
        icon = "image"
        label = "Image comparison"
        template = "home/sections/comparison.html"


class SliderHomeSectionBlock(HomeSectionBlock):
    title = blocks.CharBlock(required=False, max_length=160)
    intro = blocks.RichTextBlock(required=False, features=["bold", "italic", "link"])
    images = blocks.ListBlock(GalleryImageBlock(), min_num=2, max_num=12)
    autoplay = blocks.BooleanBlock(required=False, default=False)
    interval = blocks.IntegerBlock(
        min_value=3,
        max_value=12,
        default=6,
        label="Autoplay interval (seconds)",
    )
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="paper")

    class Meta:
        icon = "media"
        label = "Image slider"
        template = "home/sections/slider.html"


class CalloutHomeSectionBlock(HomeSectionBlock):
    title = blocks.CharBlock(max_length=180)
    text = blocks.RichTextBlock(required=False, features=["bold", "italic", "link"])
    button_label = blocks.CharBlock(required=False, max_length=80)
    button_page = blocks.PageChooserBlock(required=False)
    button_url = blocks.URLBlock(required=False)
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="coral")

    class Meta:
        icon = "pick"
        label = "Call to action"
        template = "home/sections/callout.html"


class VideoHomeSectionBlock(HomeSectionBlock):
    title = blocks.CharBlock(required=False, max_length=160)
    intro = blocks.RichTextBlock(required=False, features=["bold", "italic", "link"])
    video = EmbedBlock()
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="midnight")

    class Meta:
        icon = "media"
        label = "Video"
        template = "home/sections/video.html"


class SimulationHomeSectionBlock(HomeSectionBlock):
    title = blocks.CharBlock(required=False, max_length=160)
    description = blocks.TextBlock(required=False)
    embed_url = blocks.URLBlock(
        help_text="URL of a trusted animation or simulation. JavaScript cannot be pasted here."
    )
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="paper")

    class Meta:
        icon = "cogs"
        label = "Animation / simulation"
        template = "home/sections/simulation.html"


class AutomaticListSectionBlock(HomeSectionBlock):
    title = blocks.CharBlock(
        required=False, max_length=160, label="Section heading",
        help_text="Leave blank to use the translated interface label.",
    )
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="paper")

    class Meta:
        abstract = True


class PublicationsSectionBlock(AutomaticListSectionBlock):
    homepage_limit = blocks.IntegerBlock(
        min_value=1, max_value=6, default=3, label="Publications on the homepage",
        help_text="Show the newest 1–6 publications on the homepage, with a link to the full list in Science. Other pages always show the full list.",
    )

    class Meta:
        icon = "doc-full"
        label = "Publications"
        help_text = "Newest publications in this page's language. A short preview on the homepage; the full list on other pages."
        template = "home/sections/publications.html"


class CollaborationsSectionBlock(AutomaticListSectionBlock):
    class Meta:
        icon = "group"
        label = "Collaborations — full list"
        help_text = "All collaboration snippets in this page's language, in editorial order."
        template = "home/sections/collaborations.html"


class ProjectListSectionBlock(AutomaticListSectionBlock):
    status = blocks.ChoiceBlock(
        choices=[("all", "All projects"), ("current", "Current projects"), ("finished", "Finished projects")],
        default="all", label="Projects to display",
        help_text="A project is finished when its end date is before today. No end date means current.",
    )

    class Meta:
        icon = "folder-open-inverse"
        label = "Projects — full list"
        template = "home/sections/project_list.html"


class ChildSectionsBlock(AutomaticListSectionBlock):
    class Meta:
        icon = "doc-full"
        label = "Child pages — inline sections"
        help_text = (
            "Show published project child pages or science research areas in full on this page. "
            "Each has a stable anchor such as section-123. Edit the content on the child page."
        )
        template = "home/sections/child_sections.html"


class NewsListSectionBlock(AutomaticListSectionBlock):
    class Meta:
        icon = "date"
        label = "News — full list"
        help_text = "All published news in this page's language, newest first."
        template = "home/sections/news_list.html"


class FinancingSectionBlock(AutomaticListSectionBlock):
    text = blocks.RichTextBlock(
        required=False, features=["h2", "h3", "bold", "italic", "link", "ol", "ul"],
        label="Funding information",
        help_text="Verified funding information only. Leave blank to use the homepage's About / financing information, if provided.",
    )

    class Meta:
        icon = "doc-full"
        label = "Financing / funding"
        template = "home/sections/financing.html"


class ContactSectionBlock(AutomaticListSectionBlock):
    text = blocks.RichTextBlock(
        required=False, features=["bold", "italic", "link", "ol", "ul"],
        label="Contact introduction",
        help_text="Optional text above the real contact details from site settings.",
    )
    show_email = blocks.BooleanBlock(required=False, default=True, label="Show email address")
    show_phone = blocks.BooleanBlock(required=False, default=True, label="Show phone number")
    show_address = blocks.BooleanBlock(required=False, default=True, label="Show postal address")
    show_people_link = blocks.BooleanBlock(
        required=False, default=True, label="Show link to the team",
        help_text="Links to the published People page in this language, when available.",
    )
    show_social_links = blocks.BooleanBlock(
        required=False, default=True, label="Show institute social links",
        help_text="Uses verified INPSY links from site settings; the site's social-links visibility setting still applies.",
    )

    class Meta:
        icon = "mail"
        label = "Contact details"
        help_text = "Only configured contact details are displayed. Manage actual addresses and accounts in site settings."
        template = "home/sections/contact.html"


HOME_SECTION_BLOCKS = [
    ("about", AboutHomeSectionBlock()),
    ("text_image", RichMediaHomeSectionBlock()),
    ("research", ResearchHomeSectionBlock()),
    ("people", PeopleHomeSectionBlock()),
    ("featured_project", FeaturedProjectHomeSectionBlock()),
    ("updates", UpdatesHomeSectionBlock()),
    ("page_links", PageLinksHomeSectionBlock()),
    ("gallery", GalleryHomeSectionBlock()),
    ("comparison", ComparisonHomeSectionBlock()),
    ("slider", SliderHomeSectionBlock()),
    ("callout", CalloutHomeSectionBlock()),
    ("video", VideoHomeSectionBlock()),
    ("simulation", SimulationHomeSectionBlock()),
    ("publications", PublicationsSectionBlock()),
    ("collaborations", CollaborationsSectionBlock()),
    ("project_list", ProjectListSectionBlock()),
    ("child_sections", ChildSectionsBlock()),
    ("news_list", NewsListSectionBlock()),
    ("financing", FinancingSectionBlock()),
    ("contact", ContactSectionBlock()),
]

# Keep every existing block available while making the insertion menu scannable.
for _name, _block in HOME_SECTION_BLOCKS:
    if _name in {"about", "text_image", "page_links", "callout"}:
        _block.meta.group = "Text and links"
    elif _name in {"gallery", "comparison", "slider", "video", "simulation"}:
        _block.meta.group = "Images and media"
    elif _name in {"financing", "contact"}:
        _block.meta.group = "Contact and funding"
    else:
        _block.meta.group = "People and content lists"


CONTENT_BLOCKS = [
    ("heading", HeadingBlock(form_classname="title")),
    ("text", blocks.RichTextBlock(features=["h2", "h3", "bold", "italic", "link", "ol", "ul"])),
    ("image", ImageBlock()),
    ("video", EmbedBlock(help_text="Paste a public video URL, for example YouTube or Vimeo.")),
    ("document", DocumentBlock()),
    ("button", CallToActionBlock()),
    ("simulation", SimulationBlock()),
]
