from io import BytesIO
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image as PILImage, ImageDraw
from wagtail.images import get_image_model
from django.template import Context, Template


class AnimatedImageTests(TestCase):
    def test_wagtail_keeps_frames_timing_and_loop_after_crop(self):
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            frames = [PILImage.new('RGB', (160, 100), color) for color in ('red', 'green', 'blue')]
            source = BytesIO()
            frames[0].save(source, format='GIF', save_all=True, append_images=frames[1:],
                           duration=[100, 200, 300], loop=2)
            image = get_image_model().objects.create(title='Animation', file=SimpleUploadedFile('test.gif', source.getvalue()))
            for spec in ('original', 'width-80', 'fill-60x60'):
                with self.subTest(spec=spec):
                    rendition = image.get_rendition(spec)
                    with rendition.file.open('rb') as file:
                        result = PILImage.open(file)
                        self.assertEqual(result.format, 'GIF')
                        self.assertEqual(result.n_frames, 3)
                        self.assertEqual(result.info['loop'], 2)
                        self.assertEqual([result.seek(i) or result.info['duration'] for i in range(3)], [100, 200, 300])
                        if spec == 'fill-60x60':
                            self.assertEqual(result.size, (60, 60))
            poster = image.get_rendition('width-80|format-png')
            with poster.file.open('rb') as file:
                self.assertEqual(PILImage.open(file).format, 'PNG')

    def test_transparent_animation_starts_directly_in_details_and_thumbnails(self):
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            frames = []
            for position in (15, 50):
                frame = PILImage.new('RGBA', (100, 100))
                ImageDraw.Draw(frame).rectangle((position, 20, position + 20, 40), fill='red')
                frames.append(frame)
            source = BytesIO()
            frames[0].save(source, format='GIF', save_all=True, append_images=frames[1:],
                           duration=150, loop=0, disposal=2)
            image = get_image_model().objects.create(title='Transparent', file=SimpleUploadedFile('transparent.gif', source.getvalue()))
            rendition = image.get_rendition('width-50')
            with rendition.file.open('rb') as file:
                result = PILImage.open(file)
                self.assertEqual(result.n_frames, 2)
                for index in range(2):
                    result.seek(index)
                    self.assertEqual(result.convert('RGBA').getpixel((0, 0))[3], 0)
            rendered = Template("{% load media_tags %}{% media_image image 'width-50' %}").render(Context({'image': image}))
            self.assertIn(rendition.url, rendered)
            self.assertNotIn('<button', rendered)
            self.assertNotIn('data-poster-src', rendered)
            thumbnail = Template("{% load media_tags %}{% media_image image 'width-50' controls=False %}").render(Context({'image': image}))
            self.assertNotIn('<button', thumbnail)
            self.assertIn(rendition.url, thumbnail)
