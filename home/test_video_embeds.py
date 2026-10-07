from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from home.blocks import VideoHomeSectionBlock


class VideoEmbedTests(SimpleTestCase):
    def test_nested_video_renders_provider_iframe_instead_of_escaped_html(self):
        block = VideoHomeSectionBlock()
        value = block.to_python({
            'is_visible': True,
            'title': 'Video tutorial',
            'video': 'https://www.youtube.com/watch?v=Ee6teO-RvAw',
            'theme': 'paper',
        })
        iframe = '<iframe src="https://www.youtube.com/embed/Ee6teO-RvAw" title="Tutorial"></iframe>'
        with patch('wagtail.embeds.embeds.get_embed', return_value=SimpleNamespace(html=iframe)):
            rendered = block.render(value)
        self.assertIn(iframe, rendered)
        self.assertNotIn('&lt;iframe', rendered)
        self.assertIn('responsive-embed', rendered)

    def test_hidden_video_does_not_fetch_the_external_provider(self):
        block = VideoHomeSectionBlock()
        value = block.to_python({'is_visible': False, 'video': 'https://www.youtube.com/watch?v=Ee6teO-RvAw'})
        with patch('wagtail.embeds.embeds.get_embed') as provider:
            self.assertNotIn('<iframe', block.render(value))
            provider.assert_not_called()
