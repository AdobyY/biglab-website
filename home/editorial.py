"""Non-persistent defaults for automatic containers in the page editor."""

from copy import deepcopy

from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.blocks import StreamValue


_DEFAULT_SECTIONS = {
    "peopleindexpage": [("people", {
        "selected_people": [], "limit": 24, "link_label": "",
        "show_roles": True, "enable_carousel": True, "carousel_after": 6,
    })],
    "newsindexpage": [("news_list", {})],
    "projectsindexpage": [
        ("project_list", {"status": "current"}),
        ("project_list", {"status": "finished"}),
    ],
    "sciencepage": [("child_sections", {}), ("publications", {}), ("collaborations", {})],
    "projectpage": [("child_sections", {})],
}


def defaults_for_page(page):
    """Build fresh section values from the current block schema, without DB writes.

    These mirror migration 0013's frozen defaults; the migration intentionally
    does not import this runtime helper so future schema changes cannot alter it.
    Blank labels let the public templates choose the page's translated UI text.
    """
    stream_block = page._meta.get_field("sections").stream_block
    sections = []
    for block_type, overrides in _DEFAULT_SECTIONS.get(page._meta.model_name, []):
        block = stream_block.child_blocks[block_type]
        value = block.get_default()
        initial = {
            "is_visible": True, "title": "", "intro": "", "theme": "paper",
            "anchor": "", "background_image": None,
            "background_position": "center", "background_overlay": "medium",
            **deepcopy(overrides),
        }
        for name, raw_value in initial.items():
            value[name] = block.child_blocks[name].to_python(raw_value)
        sections.append((block_type, value))
    return StreamValue(stream_block, sections, is_lazy=False)


class EditorialPageForm(WagtailAdminPageForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Wagtail may supply an older empty revision, not the canonical record.
        # Populate only the display initial: never mutate that revision/instance
        # or a submitted empty builder that the editor deliberately cleared.
        if (
            not self.is_bound
            and "sections" in self.fields
            and not self.instance.sections
            and not self.initial.get("sections")
        ):
            defaults = defaults_for_page(self.instance)
            if defaults:
                self.initial["sections"] = defaults
