import math
from types import SimpleNamespace

from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import format_html_join
from wagtail.models import Locale, Site
from home.templatetags.ui_tags import ui


register = template.Library()


@register.simple_tag
def article_contents(page):
    """Build the reading index and render IDs from the same owned heading blocks."""
    result = {"items": []}
    for field in ("body", "after_body"):
        result[field] = []
        for position, block in enumerate(getattr(page, field, ()) or ()):
            heading_id = ""
            if block.block_type == "heading":
                heading_id = f"article-{page.pk}-{field}-{block.id or position}"
                result["items"].append({"id": heading_id, "label": block.value})
            result[field].append({"block": block, "heading_id": heading_id})
    result["show_outline"] = len(result["items"]) >= 3
    return result


@register.simple_tag(takes_context=True)
def render_reading_blocks(context, value, entries):
    """Keep Wagtail's own wrappers while supplying each heading's stable anchor."""
    parent_context = context.flatten()
    return format_html_join("\n", "{}", (
        (value.stream_block.render_basic(
            [item["block"]], context={**parent_context, "heading_id": item["heading_id"]},
        ),)
        for item in entries
    ))


@register.inclusion_tag("home/includes/breadcrumbs.html", takes_context=True)
def breadcrumbs(context, home):
    page = context.get("page")
    items = []
    if home and context.get("is_about_page"):
        items = [home, SimpleNamespace(title=ui(context, "about"))]
    elif page and home and page.pk != home.pk and page.path.startswith(home.path):
        items = list(page.get_ancestors(inclusive=True).live().filter(depth__gte=home.depth))
        # Wagtail previews may show an unpublished page; it is still the current crumb.
        if not items or items[-1].pk != page.pk:
            items.append(page)
    if items and context.get("research_collection_name"):
        items.append(SimpleNamespace(title=context["collection_title"]))
    return {"breadcrumb_items": items, "page": page, "request": context.get("request")}


@register.inclusion_tag("home/includes/page_navigation.html", takes_context=True)
def page_navigation(context, collection_name, previous_label, next_label, team_section=None):
    """Browse a directory or news archive in its own published order."""
    collection = context.get(collection_name)
    if collection is None:
        return {}
    page = context["page"]
    entries = collection.only("title", "path", "url_path", "locale")
    siblings = complete_team(team_section, entries) if team_section else list(entries)
    position = next((i for i, sibling in enumerate(siblings) if sibling.pk == page.pk), None)
    if position is None:
        return {}
    return {
        "page": page, "request": context.get("request"),
        "previous_page": siblings[position - 1] if position > 0 else None,
        "next_page": siblings[position + 1] if position + 1 < len(siblings) else None,
        "previous_label": previous_label, "next_label": next_label,
    }


@register.inclusion_tag("home/includes/child_page_navigation.html", takes_context=True)
def child_page_navigation(context, parent=None, embedded=False):
    """Expose the next level even when it is beyond the header menu's depth."""
    parent = parent or context.get("page")
    result = {"page": parent, "request": context.get("request"), "embedded": embedded}
    if context.get("research_collection_name") or not parent or parent.__class__.__name__ not in {"ContentPage", "ProjectPage", "SciencePage"}:
        return result
    sections = getattr(parent, "sections", [])
    # The inline collection already exposes children; do not repeat it.
    if (not sections and parent.__class__.__name__ in {"ProjectPage", "SciencePage"}) or any(
        block.block_type == "child_sections" and block.value.get("is_visible")
        for block in sections
    ):
        return result
    # Curated cards own their links. Only expose children they do not cover.
    covered_ids = {
        item["page"].pk
        for block in sections
        if block.block_type == "page_links" and block.value.get("is_visible")
        for item in block.value.get("pages", [])
        if item.get("page") and item["page"].live
    }
    for field in (getattr(parent, "body", []), getattr(parent, "after_body", [])):
        for block in field:
            if block.block_type == "button":
                target = block.value.get("page")
                if target and target.live and block.value.get("label"):
                    covered_ids.add(target.pk)
    for block in sections:
        if block.value.get("is_visible") and block.value.get("button_label"):
            target = block.value.get("button_page")
            if target and target.live:
                covered_ids.add(target.pk)
    result["child_navigation_pages"] = parent.get_children().live().in_menu().exclude(pk__in=covered_ids).specific()
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
    url = science.collection_url("publications") if science and science.live else ""
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


@register.simple_tag
def homepage_url(home, destination="home"):
    url = getattr(home, "url", None)
    if not url:
        return ""
    if destination == "about":
        url += home.reverse_subpage("about")
    return url


@register.simple_tag(takes_context=True)
def translation_url(context, page):
    url = page.url
    if context.get("is_about_page"):
        url += page.specific.reverse_subpage("about")
    elif context.get("research_collection_name"):
        url = page.specific.collection_url(context["research_collection_name"]) or url
    return url


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
    """Group the lab, people and news; expose real science section anchors."""
    page = context.get("page")
    language = getattr(getattr(page, "locale", None), "language_code", "en")
    about_url = homepage_url(root, "about")
    about_current = bool(context.get("is_about_page"))
    items = _build_menu(root, page)
    about_children = []
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
            for collection in item["page"].collection_sections():
                current = context.get("research_collection_name") == collection["name"] and page.pk == item["page"].pk
                item["children"].append({"page": SimpleNamespace(id=f"{item['page'].pk}-{collection['name']}", title=ui(context, collection["name"])),
                    "url": collection["url"], "active": current, "current": current, "children": []})
            if context.get("research_collection_name") and page.pk == item["page"].pk:
                item["current"] = False
            break
    else:
        remaining.extend(project_items)
    # The document's About group has a semantic order; reuse the same published page records.
    about_children.sort(key=lambda child: child["page"].__class__.__name__ != "PeopleIndexPage")
    about = {'page': SimpleNamespace(id=root.pk, title=ui(context, 'about')),
             'url': about_url, 'active': about_current or any(child['active'] for child in about_children),
             'current': about_current, 'children': about_children}
    return {
        "menu_items": [about, *remaining],
        "language_code": language,
        "page": page,
        "request": context.get("request"),
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
def project_audience_links(project):
    """Reuse the project's curated nested-page links as its audience navigation."""
    result, seen = [], set()
    for block in getattr(project, "sections", ()) or ():
        if block.block_type != "page_links" or not block.value.get("is_visible"):
            continue
        for item in block.value.get("pages", ()):
            target = item.get("page")
            if (target and target.live and target.pk not in seen
                    and target.locale_id == project.locale_id
                    and target.depth > project.depth + 1
                    and target.path.startswith(project.path)):
                result.append({"page": target, "label": item.get("label") or target.title})
                seen.add(target.pk)
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
    if url and context.get("research_collection_name"):
        url += page.specific.reverse_subpage(context["research_collection_name"])
    return request.build_absolute_uri(url) if request and url else ""


@register.simple_tag(takes_context=True)
def localized_home(context):
    if context.get("site_home"):
        return context["site_home"]
    page = context.get("page")
    home = Site.find_for_request(context["request"]).root_page.specific
    target_locale = page.locale if page else Locale.get_active()
    if target_locale.id != home.locale_id:
        try:
            return home.get_translation(target_locale).specific
        except ObjectDoesNotExist:
            pass
    return home
