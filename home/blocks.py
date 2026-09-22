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


class CallToActionBlock(blocks.StructBlock):
    label = blocks.CharBlock(max_length=80)
    page = blocks.PageChooserBlock(required=False)
    url = blocks.URLBlock(required=False, help_text="Use this for an external link.")

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
    ("paper", "Paper"),
    ("lilac", "Pale lilac"),
    ("midnight", "Midnight blue"),
    ("coral", "Coral"),
]


class HomeSectionBlock(blocks.StructBlock):
    """Shared editorial controls for reorderable homepage sections."""

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
    title = blocks.CharBlock(max_length=120, default="Research areas")
    link_label = blocks.CharBlock(required=False, max_length=80, default="All science")
    selected_areas = blocks.ListBlock(
        blocks.PageChooserBlock(page_type="home.ContentPage"),
        required=False,
        default=[],
        max_num=12,
        label="Selected research areas",
        help_text="Optional. Choose and drag pages into order; leave empty to show research pages automatically.",
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
    title = blocks.CharBlock(max_length=120, default="People behind the research")
    link_label = blocks.CharBlock(required=False, max_length=80, default="Full team")
    selected_people = blocks.ListBlock(
        blocks.PageChooserBlock(page_type="home.PersonPage"),
        required=False,
        default=[],
        max_num=24,
        label="Selected people",
        help_text="Optional. Choose and drag people into order; leave empty to use the published team automatically.",
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
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="lilac")

    class Meta:
        icon = "group"
        label = "People"
        template = "home/sections/people.html"


class FeaturedProjectHomeSectionBlock(HomeSectionBlock):
    project = blocks.PageChooserBlock(required=False, page_type="home.ProjectPage")
    label = blocks.CharBlock(required=False, max_length=80, default="PARTA / BIG LAB")
    button_label = blocks.CharBlock(required=False, max_length=80, default="About the project")
    theme = blocks.ChoiceBlock(choices=SECTION_THEME_CHOICES, default="coral")

    class Meta:
        icon = "folder-open-inverse"
        label = "Featured project"
        template = "home/sections/featured_project.html"


class UpdatesHomeSectionBlock(HomeSectionBlock):
    title = blocks.CharBlock(max_length=120, default="In progress")
    show_news = blocks.BooleanBlock(required=False, default=True)
    news_heading = blocks.CharBlock(required=False, max_length=80)
    selected_news = blocks.ListBlock(
        blocks.PageChooserBlock(page_type="home.NewsPage"),
        required=False,
        default=[],
        max_num=6,
        label="Selected news",
        help_text="Optional. Leave empty to show the newest published news automatically.",
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
        help_text="Optional. Leave empty to show the latest projects automatically.",
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
        help_text="Optional. Leave empty to show the newest publications automatically.",
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
]


CONTENT_BLOCKS = [
    ("heading", HeadingBlock(form_classname="title")),
    ("text", blocks.RichTextBlock(features=["h2", "h3", "bold", "italic", "link", "ol", "ul"])),
    ("image", ImageBlock()),
    ("video", EmbedBlock(help_text="Paste a public video URL, for example YouTube or Vimeo.")),
    ("document", DocumentBlock()),
    ("button", CallToActionBlock()),
    ("simulation", SimulationBlock()),
]
