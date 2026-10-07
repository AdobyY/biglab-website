from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from home.ui import default_ui_text

register = template.Library()


@register.simple_tag(takes_context=True)
def media_image(context, image, spec, controls=True, **attrs):
    if not image:
        return ''
    rendition = image.get_rendition(spec)
    if not rendition.file.name.lower().endswith('.gif'):
        return rendition.img_tag(attrs)
    poster = image.get_rendition(spec + '|format-png')
    if not controls:
        # Linked thumbnails remain a single accessible link; the detail view has controls.
        return poster.img_tag(attrs)
    language = context.get('page').locale.language_code if context.get('page') else 'en'
    attrs['data-animation-src'] = rendition.url
    attrs['data-poster-src'] = poster.url
    return format_html('<span class="animated-media" data-animated-media>{}<button class="animation-toggle" type="button" aria-pressed="false" hidden>{}</button></span>',
                       mark_safe(poster.img_tag(attrs)), default_ui_text('play', language))
