"""Check the repeatable training command against the actual bilingual baseline."""
import json
from io import StringIO
from pathlib import Path
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from wagtail.models import Page, Site
from wagtail.images import get_image_model
from wagtail.documents import get_document_model

from home.blocks import HOME_SECTION_BLOCKS, CONTENT_BLOCKS
from home.content_snapshot import DEFAULT_BUNDLE, import_bundle
from home.models import ContentPage, HomePage, Publication, Collaboration, InterfaceText


class DemoContentTests(TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        override=self.settings(MEDIA_ROOT=Path(self.temp.name)/'media')
        override.enable()
        self.addCleanup(override.disable)
        import_bundle()
        self.output=StringIO()
        # Provider access is tested against the live local site separately.
        # Keep database/reset tests independent of YouTube or network access.
        provider=patch('wagtail.embeds.blocks.embed_to_frontend_html',return_value='<iframe title="Wagtail tutorial"></iframe>')
        provider.start()
        self.addCleanup(provider.stop)

    def run_demo(self):
        call_command('seed_biglab_demo',stdout=self.output)

    def test_all_blocks_translations_drafts_and_repeating_preserves_edits(self):
        self.run_demo()
        self.assertEqual(Page.find_problems(),([],[],[],[],[]))
        hubs=ContentPage.objects.filter(slug='wagtail-showcase')
        self.assertEqual(hubs.count(),2)
        en=hubs.get(locale__language_code='en')
        cs=hubs.get(locale__language_code='cs')
        self.assertEqual(en.translation_key,cs.translation_key)
        demos=Page.objects.filter(depth__gte=3).specific()
        sections=set()
        bodies=set()
        for page in demos:
            for item in page.sections:
                sections.add(item.block_type)
                for field,values in item.value.items():
                    if field.startswith('selected_'):
                        self.assertTrue(all(v.locale_id==page.locale_id for v in values or []))
            for field in (page.body,page.after_body):
                bodies.update(item.block_type for item in field)
        self.assertEqual(sections,set(dict(HOME_SECTION_BLOCKS)))
        # Simulation also exists in the section builder; content-block coverage
        # is checked separately once an article simulation example is present.
        self.assertEqual(bodies,set(dict(CONTENT_BLOCKS)))
        self.assertFalse(ContentPage.objects.get(slug='draft-exercise',locale__language_code='en').live)
        self.assertGreater(Page.objects.filter(depth__gte=6).count(),0)
        counts=(Page.objects.count(),get_image_model().objects.count(),get_document_model().objects.count(),Publication.objects.count(),Collaboration.objects.count(),InterfaceText.objects.count())
        edited=en.get_children().get(slug='editorial-layouts').specific
        edited.intro='<p>Manual edit survives another demo run.</p>'
        edited.save_revision().publish()
        self.run_demo()
        edited.refresh_from_db()
        self.assertIn('Manual edit survives',edited.intro)
        renamed=ContentPage.objects.get(slug='resources',locale__language_code='en')
        renamed.slug='renamed-resources'
        renamed.save_revision().publish()
        self.run_demo()
        renamed.refresh_from_db()
        self.assertEqual(renamed.slug,'renamed-resources')
        self.assertFalse(ContentPage.objects.filter(slug='resources',locale__language_code='en').exists())
        self.assertEqual(Page.find_problems(),([],[],[],[],[]))
        self.assertEqual(counts,(Page.objects.count(),get_image_model().objects.count(),get_document_model().objects.count(),Publication.objects.count(),Collaboration.objects.count(),InterfaceText.objects.count()))
        self.assertEqual(Page.find_problems(),([],[],[],[],[]))
        # A removed demo child can be added again without replacing its siblings.
        renamed.delete()
        self.run_demo()
        self.assertTrue(ContentPage.objects.filter(slug='resources',locale__language_code='en',live=True).exists())
        edited.refresh_from_db()
        self.assertIn('Manual edit survives',edited.intro)

    def test_reset_removes_demo_and_command_can_create_it_again(self):
        self.run_demo()
        site=Site.objects.get(is_default_site=True)
        domain=(site.hostname,site.port,site.root_page_id)
        user=get_user_model().objects.create_user('demo-editor',password='only-for-test')
        password=user.password
        call_command('seed_biglab',reset=True,stdout=self.output)
        payload=json.loads((DEFAULT_BUNDLE/'content.json').read_text(encoding='utf-8'))
        self.assertEqual(Page.objects.count(),len(payload['pages'])+1)
        self.assertFalse(ContentPage.objects.filter(slug='wagtail-showcase').exists())
        self.assertFalse(get_document_model().objects.filter(title__contains='навчальна').exists())
        site.refresh_from_db()
        user.refresh_from_db()
        self.assertEqual(domain,(site.hostname,site.port,site.root_page_id))
        self.assertEqual(password,user.password)
        self.run_demo()
        self.assertEqual(ContentPage.objects.filter(slug='wagtail-showcase',live=True).count(),2)

    def test_missing_baseline_does_not_create_half_a_demo(self):
        HomePage.objects.get(locale__language_code='cs',depth=2).delete()
        before=Page.objects.count()
        with self.assertRaisesMessage(CommandError,'Import initial content first'):
            self.run_demo()
        self.assertEqual(before,Page.objects.count())
