"""Serve generated Wagtail images when the host has no media reverse proxy."""

from pathlib import PurePosixPath

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_safe
from wagtail.images import get_image_model


IMAGE_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".gif": "image/gif", ".webp": "image/webp", ".avif": "image/avif",
}


@require_safe
def public_image(request, filename):
    # Only registered raster renditions are public. Documents, originals and
    # arbitrary files in MEDIA_ROOT continue to use their existing access rules.
    content_type = IMAGE_TYPES.get(PurePosixPath(filename).suffix.lower())
    if not content_type or "/" in filename or "\\" in filename:
        raise Http404
    rendition = get_object_or_404(
        get_image_model().get_rendition_model(), file=f"images/{filename}",
    )
    try:
        image_file = rendition.file.open("rb")
    except FileNotFoundError as exc:
        raise Http404 from exc
    response = FileResponse(image_file, content_type=content_type)
    response["Cache-Control"] = "public, max-age=3600"
    response["X-Content-Type-Options"] = "nosniff"
    return response
