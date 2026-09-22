from django import template
from django.core.exceptions import ObjectDoesNotExist
from wagtail.models import Locale, Site


register = template.Library()


def _build_menu(parent, current_page=None, levels=3):
    if levels <= 0:
        return []
    current_path = getattr(current_page, "path", "")
    items = []
    for child in parent.get_children().live().in_menu().specific():
        items.append(
            {
                "page": child,
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
        "nested": False,
    }


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
