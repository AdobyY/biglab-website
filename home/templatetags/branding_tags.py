"""One editable brand shared by public pages and every CMS screen."""

from django import template
from django.templatetags.static import static
from wagtail.models import Site

from home.models import ContactSettings


register = template.Library()


@register.simple_tag(takes_context=True)
def brand(context):
    request = context.get("request")
    site = Site.find_for_request(request) if request else Site.objects.filter(is_default_site=True).first()
    settings = ContactSettings.for_site(site) if site else None
    logo = settings.logo if settings else None
    fallback = static("images/biglab-logo.png")
    return {
        "name": settings.site_name if settings else "BIG Lab",
        "logo_url": logo.get_rendition("max-240x240").url if logo else fallback,
        "icon_url": logo.get_rendition("max-64x64").url if logo else fallback,
    }
