from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def media_image(context, image, spec, controls=True, **attrs):
    """Render animated renditions directly, including legacy thumbnail callers."""
    if not image:
        return ''
    return image.get_rendition(spec).img_tag(attrs)
