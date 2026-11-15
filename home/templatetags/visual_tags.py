"""Small presentation helpers for the editable homepage content."""
import re
from django import template

register = template.Library()


@register.filter
def editorial_parts(value):
    """Give the opening paragraph prominence without rewriting editable copy."""
    source = getattr(value, 'source', str(value or ''))
    match = re.fullmatch(r'\s*(<p(?:\s[^>]*)?>.*?</p>)(.*)', source, re.DOTALL)
    return {'lead': match[1], 'body': match[2]} if match else {'lead': '', 'body': source}


@register.filter
def method_parts(value):
    source = getattr(value, 'source', str(value or ''))
    parts = [part for part in re.split(r'(?=<h3(?:\s|>))', source) if part.strip()]
    icons = ('network', 'models', 'experiment')
    return [{'html': part, 'icon': icons[index % len(icons)]} for index, part in enumerate(parts)]


@register.filter
def page_icon(page):
    audience_icons = {'for-schools': 'school', 'for-parents': 'team', 'for-students': 'student', 'timeline': 'calendar'}
    if getattr(page, 'slug', '') in audience_icons:
        return audience_icons[page.slug]
    model = getattr(getattr(page, 'content_type', None), 'model', '')
    return {'sciencepage': 'science', 'peopleindexpage': 'team', 'newspage': 'news',
            'newsindexpage': 'news', 'projectpage': 'network', 'projectsindexpage': 'models'}.get(model, 'book')
