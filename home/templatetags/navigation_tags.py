import math
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django import template
from django.core.exceptions import ObjectDoesNotExist
from wagtail.models import Locale, Site
from home.ui import default_ui_text


register = template.Library()


@register.inclusion_tag("home/includes/breadcrumbs.html", takes_context=True)
def breadcrumbs(context, home):
    page = context.get("page")
    items = []
    if page and home and page.pk != home.pk and page.path.startswith(home.path):
        items = list(page.get_ancestors(inclusive=True).live().filter(depth__gte=home.depth))
        # Wagtail previews may show an unpublished page; it is still the current crumb.
        if not items or items[-1].pk != page.pk:
            items.append(page)
    return {"breadcrumb_items": items, "page": page, "request": context.get("request")}


@register.inclusion_tag("home/includes/page_navigation.html", takes_context=True)
def page_navigation(context):
    page = context.get("page")
    result = {"page": page, "request": context.get("request"), "people_index": context.get("people_index")}
    if not page or page.__class__.__name__ not in {"PersonPage", "NewsPage", "ContentPage", "ProjectPage"}:
        return result
    parent = page.get_parent().specific
    if not parent.live:
        return result
    siblings = parent.get_children().live().type(type(page))
    if page.__class__.__name__ == "NewsPage":
        siblings = siblings.specific()
        siblings = sorted(siblings, key=lambda item: (item.date, item.path), reverse=True)
    else:
        siblings = list(siblings.order_by("path").specific())
    position = next((i for i, sibling in enumerate(siblings) if sibling.pk == page.pk), None)
    result.update(
        navigation_parent=parent,
        previous_page=siblings[position - 1] if position is not None and position > 0 else None,
        next_page=siblings[position + 1] if position is not None and position + 1 < len(siblings) else None,
    )
    return result


@register.inclusion_tag("home/includes/child_page_navigation.html", takes_context=True)
def child_page_navigation(context, parent=None, embedded=False):
    """Expose the next level even when it is beyond the header menu's depth."""
    parent = parent or context.get("page")
    result = {"page": parent, "request": context.get("request"), "embedded": embedded}
    if not parent or parent.__class__.__name__ not in {"ContentPage", "ProjectPage", "SciencePage"}:
        return result
    sections = getattr(parent, "sections", [])
    # The inline collection already exposes children; do not repeat it.
    if (not sections and parent.__class__.__name__ in {"ProjectPage", "SciencePage"}) or any(
        block.block_type == "child_sections" and block.value.get("is_visible")
        for block in sections
    ):
        return result
    result["child_navigation_pages"] = parent.get_children().live().in_menu().specific()
    return result


@register.simple_tag(takes_context=True)
def publication_collection(context, section=None):
    """Bound homepage growth while retaining the complete reading-page list."""
    items = context.get("publications", [])
    if context.get("page").__class__.__name__ != "HomePage":
        return {"items": items, "url": ""}
    try:
        limit = int(section.get("homepage_limit", 3))
    except (AttributeError, TypeError, ValueError):
        limit = 3
    limit = max(1, min(limit, 6))
    science = context.get("science_page")
    url = ""
    if science and science.live and science.url:
        sections = science.sections
        if not sections:
            url = science.url
        else:
            for block in sections:
                if block.block_type == "publications" and block.value.get("is_visible"):
                    anchor = block.value.get("anchor")
                    url = science.url + (f"#{anchor}" if anchor else "")
                    break
    return {"items": items[:limit], "url": url}


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


@register.filter
def design_url(url, version):
    """Keep the explicit homepage variant while following internal links."""
    if version != "2" or not url:
        return url
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "design"]
    query.append(("design", "2"))
    return urlunsplit(parts._replace(query=urlencode(query)))


@register.simple_tag
def homepage_url(home, version="1", destination="home"):
    url = getattr(home, "url", None)
    if not url:
        return ""
    if destination == "about" and version == "2":
        url += home.reverse_subpage("about")
    return design_url(url, version)


@register.simple_tag(takes_context=True)
def translation_url(context, page):
    url = page.url
    if context.get("is_about_page"):
        url += page.specific.reverse_subpage("about")
    return design_url(url, context.get("design_version", "1"))


def _build_menu(parent, current_page=None, levels=3, version="1"):
    if levels <= 0:
        return []
    current_path = getattr(current_page, "path", "")
    items = []
    for child in parent.get_children().live().in_menu().specific():
        items.append(
            {
                "page": child,
                "url": design_url(section_url(child), version),
                "active": bool(current_path and current_path.startswith(child.path)),
                "current": getattr(current_page, "pk", None) == child.pk,
                "children": _build_menu(child, current_page, levels - 1, version),
            }
        )
    return items


@register.inclusion_tag("home/includes/navigation_menu.html", takes_context=True)
def primary_navigation(context, root):
    """Group the lab, people and news; expose real science section anchors."""
    page = context.get("page")
    language = getattr(getattr(page, "locale", None), "language_code", "en")
    version = context.get("design_version", "1")
    about_url = homepage_url(root, version, "about") if version == "2" else f"{root.url}#about"
    about_current = bool(page and page.pk == root.pk and (version != "2" or context.get("is_about_page")))
    items = _build_menu(root, page, version=version)
    about_children = [{"page": SimpleNamespace(id=f'lab-{root.pk}', title='Lab'),
                       "url": about_url, "active": about_current,
                       "current": about_current, "children": []}]
    remaining = []
    project_items = []
    for item in items:
        model = item['page'].__class__.__name__
        if model in {'PeopleIndexPage', 'NewsIndexPage'}:
            about_children.append(item)
        elif model == 'ProjectsIndexPage':
            project_items.append(item)
        else:
            remaining.append(item)
    for item in remaining:
        if item['page'].__class__.__name__ == 'SciencePage':
            item['children'].extend(project_items)
            item['active'] = item['active'] or any(child['active'] for child in project_items)
            for block in item['page'].sections:
                if block.block_type in {'publications', 'collaborations', 'project_list'} and block.value.get('is_visible') and block.value.get('anchor'):
                    key = block.block_type if block.block_type != 'project_list' else ('finished_projects' if block.value.get('status') == 'finished' else 'projects')
                    item['children'].append({'page': SimpleNamespace(id=f"{item['page'].pk}-{block.value['anchor']}", title=block.value.get('title') or default_ui_text(key, language)),
                        'url': design_url(f"{item['page'].url}#{block.value['anchor']}", version), 'active': False, 'current': False, 'children': []})
            break
    else:
        remaining.extend(project_items)
    about = {'page': SimpleNamespace(id=root.pk, title=default_ui_text('about', language)),
             'url': about_url, 'active': any(child['active'] for child in about_children),
             'current': about_current, 'children': about_children}
    return {
        "menu_items": [about, *remaining],
        "language_code": language,
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
def contact_url(home, version="1"):
    destination = "about" if version == "2" else "home"
    base_url = homepage_url(home, version, destination)
    contact_sections = [block for block in getattr(home, "sections", []) if block.block_type == "contact"]
    for block in contact_sections:
        if block.value.get("is_visible"):
            return f"{base_url}#{block.value.get('anchor') or 'contact'}"
    if not contact_sections and getattr(home, "show_contact_section", False):
        return f"{base_url}#contact"
    return ""


@register.simple_tag
def complete_team(section, automatic_items):
    """Keep chosen ordering, then include every published member of this team."""
    members = list(automatic_items or [])
    by_id = {member.pk: member for member in members}
    selected = section.get("selected_people", []) if section else []
    result, seen = [], set()
    for member in list(selected or []) + members:
        if member and member.pk in by_id and member.pk not in seen:
            result.append(by_id[member.pk])
            seen.add(member.pk)
    return result


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
    if url and context.get("is_about_page"):
        url += page.specific.reverse_subpage("about")
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
