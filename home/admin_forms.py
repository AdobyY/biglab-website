"""Small form helpers for editorial input, without changing publication rules."""
import re

from django import forms
from wagtail.admin.forms import WagtailAdminModelForm


class PublicationLinkField(forms.URLField):
    def to_python(self, value):
        value = (value or "").strip()
        match = re.fullmatch(r"(?:doi:\s*)?(10\.\d{4,9}/\S+)", value, flags=re.IGNORECASE)
        if match:
            value = "https://doi.org/" + match.group(1)
        return super().to_python(value)


class PublicationAdminForm(WagtailAdminModelForm):
    doi_or_url = PublicationLinkField(
        required=False,
        label="Publication URL or DOI",
        help_text="Enter a publication URL or a DOI such as 10.1234/example. DOI values are saved as https://doi.org/ links.",
    )


def contrast_ratio(first, second):
    def luminance(color):
        values = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
        return sum(v * weight for v, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)
