from django import template
from django.utils.translation import get_language
from wagtail.models import Locale

from home.models import InterfaceText
from home.ui import default_ui_text

register = template.Library()
_CACHE_KEY = "home.ui.overrides"


@register.simple_tag(takes_context=True)
def ui(context, key):
    """Resolve an editor's localized label, loading overrides once per render."""
    page = context.get("page") or context.get("self")
    locale = getattr(page, "locale", None) or context.get("locale")
    request = context.get("request")
    language = getattr(locale, "language_code", None) or getattr(request, "LANGUAGE_CODE", None) or get_language() or "en"
    # Includes push their own render frame. Share the outermost render's cache,
    # not the persistent base frame, so subsequent renders fetch fresh overrides.
    frames = context.render_context.dicts
    render_frame = frames[1] if len(frames) > 1 else frames[0]
    cache = render_frame.setdefault(_CACHE_KEY, {})
    locale_key = (getattr(locale, "pk", None), language)
    if locale_key not in cache:
        if locale is None:
            locale = Locale.objects.filter(language_code=language).first()
        cache[locale_key] = dict(
            InterfaceText.objects.filter(locale=locale).values_list("key", "text")
        ) if locale else {}
    return cache[locale_key].get(key, default_ui_text(key, language))
