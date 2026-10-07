"""Small presentation helpers for the editable homepage content."""
import re
from django import template

register = template.Library()


@register.filter
def method_parts(value):
    source = getattr(value, 'source', str(value or ''))
    parts = [part for part in re.split(r'(?=<h3(?:\s|>))', source) if part.strip()]
    icons = ('network', 'models', 'experiment')
    return [{'html': part, 'icon': icons[index % len(icons)]} for index, part in enumerate(parts)]


@register.filter
def page_icon(page):
    model = getattr(getattr(page, 'content_type', None), 'model', '')
    return {'sciencepage': 'science', 'peopleindexpage': 'team', 'newspage': 'news',
            'newsindexpage': 'news', 'projectpage': 'network', 'projectsindexpage': 'models'}.get(model, 'book')
