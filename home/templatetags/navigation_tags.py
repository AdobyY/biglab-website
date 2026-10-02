import math

from django import template
from django.core.exceptions import ObjectDoesNotExist
from wagtail.models import Locale, Site


register = template.Library()


@register.filter(name="section_destination")
def section_url(page):
    """Keep child content on its owning long page when that layout is enabled."""
    parent = page.get_parent().specific
    if parent.__class__.__name__ in {"ProjectPage", "SciencePage"}:
        sections = getattr(parent, "sections", [])
        if not sections or any(
                    block.block_type == "child_sections" and block.value.get("is_visible")
                    for block in sections
                ):
            return f"{parent.url}#section-{page.pk}"
    return page.url


def _build_menu(parent, current_page=None, levels=3):
    if levels <= 0:
        return []
    current_path = getattr(current_page, "path", "")
    items = []
    for child in parent.get_children().live().in_menu().specific():
        items.append(
            {
                "page": child,
                "url": section_url(child),
                "active": bool(current_path and current_path.startswith(child.path)),
                "current": getattr(current_page, "pk", None) == child.pk,
                "children": _build_menu(child, current_page, levels - 1),
            }
        )
    return items


@register.inclusion_tag("home/includes/navigation_menu.html", takes_context=True)
def primary_navigation(context, root):
    """Render every published page marked for menus, including nested pages."""
    page = context.get("page")
    return {
        "menu_items": _build_menu(root, page),
        "language_code": getattr(getattr(page, "locale", None), "language_code", "en"),
        "page": page,
        "request": context.get("request"),
        "nested": False,
    }


@register.filter
def has_section(sections, block_type):
    return any(block.block_type == block_type for block in sections or [])


@register.filter
def take(items, count):
    """Return the first ``count`` items from a list or queryset."""
    try:
        return items[: int(count)]
    except (TypeError, ValueError):
        return items


@register.simple_tag
def section_background_url(section):
    """Return a responsive rendition URL for an optional section background."""
    image = section.get("background_image") if section else None
    if not image:
        return ""
    return image.get_rendition("width-2400").url


@register.simple_tag
def curated_items(section, selected_field, automatic_items, limit_field):
    """Resolve a manually ordered selection or fall back to automatic content."""
    selected = section.get(selected_field) if section else None
    selected_items = [item for item in list(selected or []) if item is not None]
    source = selected_items if selected_items else list(automatic_items or [])
    result = []
    for item in source:
        if item is None or (hasattr(item, "live") and not item.live):
            continue
        result.append(item.specific if hasattr(item, "specific") else item)
    try:
        limit = int(section.get(limit_field))
    except (TypeError, ValueError):
        limit = len(result)
    return result[:limit]


@register.simple_tag
def should_carousel(items, enabled, threshold):
    try:
        return bool(enabled) and len(items) > int(threshold)
    except (TypeError, ValueError):
        return False


@register.simple_tag
def contact_url(home):
    contact_sections = [block for block in getattr(home, "sections", []) if block.block_type == "contact"]
    for block in contact_sections:
        if block.value.get("is_visible"):
            return f"{home.url}#{block.value.get('anchor') or 'contact'}"
    if not contact_sections and getattr(home, "show_contact_section", False):
        return f"{home.url}#contact"
    return ""


@register.simple_tag
def constellation_nodes(areas):
    """Arrange real editorial topics without implying measured network data."""
    pages = list(areas or [])
    count = len(pages)
    nodes = []
    for index, page in enumerate(pages):
        angle = -math.pi / 2 + 2 * math.pi * index / max(count, 1)
        x = 50 + 34 * math.cos(angle)
        y = 46 + 32 * math.sin(angle)
        nodes.append({
            "page": page, "url": section_url(page),
            "x": round(x, 2), "y": round(y, 2),
            "sx": round(x * 6, 2), "sy": round(y * 6, 2),
        })
    return nodes


@register.simple_tag(takes_context=True)
def absolute_page_url(context, page):
    request = context.get("request")
    url = getattr(page, "url", None)
    return request.build_absolute_uri(url) if request and url else ""


@register.simple_tag(takes_context=True)
def localized_home(context):
    page = context.get("page")
    home = Site.find_for_request(context["request"]).root_page.specific
    target_locale = page.locale if page else Locale.get_active()
    if target_locale.id != home.locale_id:
        try:
            return home.get_translation(target_locale).specific
        except ObjectDoesNotExist:
            pass
    return home
