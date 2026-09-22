from home.models import ProjectPage


def default_home_sections(home):
    """Build the editable default homepage from the locale's existing content."""
    is_czech = home.locale.language_code == "cs"
    headings = [str(block.value) for block in home.body if block.block_type == "heading"]
    paragraphs = [str(block.value) for block in home.body if block.block_type == "text"]
    featured = (
        ProjectPage.objects.child_of(home)
        .live()
        .filter(locale=home.locale)
        .order_by("path")
        .first()
    )

    return [
        (
            "about",
            {
                "is_visible": True,
                "anchor": "about",
                "title": headings[0]
                if headings
                else ("Od individuální změny k sociálnímu šíření" if is_czech else "From individual change to social spread"),
                "intro": str(home.intro),
                "text": "".join(paragraphs),
                "theme": "paper",
            },
        ),
        (
            "research",
            {
                "is_visible": True,
                "anchor": "research",
                "title": "Oblasti výzkumu" if is_czech else "Research areas",
                "link_label": "Veškerý výzkum" if is_czech else "All science",
                "selected_areas": [],
                "limit": 5,
                "show_images": True,
                "theme": "paper",
            },
        ),
        (
            "people",
            {
                "is_visible": True,
                "anchor": "people",
                "title": "Lidé za výzkumem" if is_czech else "People behind the research",
                "link_label": "Celý tým" if is_czech else "Full team",
                "selected_people": [],
                "limit": 12,
                "show_roles": True,
                "enable_carousel": True,
                "carousel_after": 6,
                "theme": "lilac",
            },
        ),
        (
            "featured_project",
            {
                "is_visible": True,
                "anchor": "featured-project",
                "project": featured,
                "label": "PARTA / BIG LAB",
                "button_label": "O projektu" if is_czech else "About the project",
                "theme": "coral",
            },
        ),
        (
            "updates",
            {
                "is_visible": True,
                "anchor": "updates",
                "title": "Právě probíhá" if is_czech else "In progress",
                "show_news": True,
                "news_heading": "",
                "selected_news": [],
                "news_limit": 1,
                "show_projects": True,
                "projects_heading": "",
                "selected_projects": [],
                "projects_limit": 2,
                "show_publications": True,
                "publications_heading": "",
                "selected_publications": [],
                "publications_limit": 2,
                "theme": "paper",
            },
        ),
    ]


def ensure_home_sections(home, *, force=False):
    """Populate the builder only when empty, unless an explicit refresh is requested."""
    if home.sections and not force:
        return False
    home.sections = default_home_sections(home)
    home.save_revision().publish()
    return True
