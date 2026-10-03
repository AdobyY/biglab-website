import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import RequestFactory, TestCase
from PIL import Image as PillowImage
from wagtail.images import get_image_model

from .public_images import public_image


class PublicImageTests(TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        media_settings = self.settings(MEDIA_ROOT=directory.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)
        # TestCase rolls back database rows; Wagtail's rendition cache survives
        # those rollbacks and must not reuse a previous test's image ID.
        get_image_model().get_rendition_model().cache_backend.clear()
        image_bytes = BytesIO()
        PillowImage.new("RGB", (20, 20), "navy").save(image_bytes, format="JPEG")
        self.image = get_image_model().objects.create(
            title="Public image",
            file=SimpleUploadedFile("portrait.jpg", image_bytes.getvalue(), "image/jpeg"),
        )
        self.rendition = self.image.get_rendition("width-10")
        self.factory = RequestFactory()

    def test_registered_rendition_is_served_with_image_headers(self):
        response = public_image(self.factory.get("/"), self.rendition.file.name.split("/")[-1])
        self.addCleanup(response.close)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertTrue(b"".join(response.streaming_content).startswith(b"\xff\xd8"))

    def test_arbitrary_files_originals_and_traversal_are_not_served(self):
        for name in ["../db.sqlite3", "..\\db.sqlite3", "upload.html", "missing.jpg", self.image.file.name]:
            with self.subTest(name=name), self.assertRaises(Http404):
                public_image(self.factory.get("/"), name)

    def test_missing_rendition_file_returns_not_found(self):
        self.rendition.file.storage.delete(self.rendition.file.name)
        with self.assertRaises(Http404):
            public_image(self.factory.get("/"), self.rendition.file.name.split("/")[-1])

    def test_post_requests_are_rejected(self):
        self.assertEqual(public_image(self.factory.post("/"), "portrait.jpg").status_code, 405)
