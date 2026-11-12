"""Verify the approved November document and the reusable timeline/import workflow."""
from datetime import date
from io import StringIO
import json
from pathlib import Path
import re
import tempfile
from unittest.mock import patch
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from bs4 import BeautifulSoup
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase
from wagtail.blocks import StructBlockValidationError

from home.blocks import TimelineBlock
from home.content_snapshot import load_bundle


class SuppliedContentTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data, _ = load_bundle()

    def test_every_supplied_prose_paragraph_is_transferred_in_full(self):
        source = Path(__file__).parent / 'seed_assets/supplied/CONTENT.docx'
        with ZipFile(source) as document:
            paragraphs = ET.fromstring(document.read('word/document.xml')).findall(
                './/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body//'
                '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')
        def normalize(value):
            plain = BeautifulSoup(value, 'html.parser').get_text() if '<' in value else value
            return re.sub(r'\s+', ' ', plain).strip()
        # Lists, biographies, linked text and every audience-specific paragraph are included.
        indices = [29,31,33,40,42,44,56,62,67,73,79,85,91,97,101,103,
                   125,127,132,134,139,142,145,148,150,153,158,161,165,168,
                   233,234,237,240,242,244,247,249,250,251,252,255,256,257,258,260,
                   266,268,270,271,272,274,275,276,277,278,280,281,282,283,284,
                   292,293,296,299,301,302,303,304,306,308,311,
                   317,320,323,325,326,327,328,330,332,335,
                   343,344,347,350,352,355,362,365,368,370,373,
                   377,379,381,396,398,400,422,433]
        def strings(value):
            if isinstance(value, dict):
                for child in value.values():
                    yield from strings(child)
            elif isinstance(value, list):
                for child in value:
                    yield from strings(child)
            elif isinstance(value, str):
                yield normalize(value)
        public_text = '\n'.join(strings(self.data))
        for index in indices:
            expected = re.sub(r'\[[^\]]*\]', '', ''.join(paragraphs[index].itertext())).strip()
            with self.subTest(paragraph=index):
                self.assertIn(normalize(expected), public_text)

    def test_bilingual_pages_contacts_visibility_and_news_dates(self):
        for code in ('en', 'cs'):
            pages = [p for p in self.data['pages'] if p['locale'] == code]
            team = [p for p in pages if p['model'] == 'home.personpage']
            self.assertEqual(len(team), 8)
            self.assertTrue(all(p['fields']['email'] for p in team))
            self.assertIsNone(next(p for p in team if p['fields']['slug']=='adela-frankova')['fields']['portrait'])
            news = [p for p in pages if p['model'] == 'home.newspage']
            self.assertEqual(len(news), 6)
            self.assertEqual(max(p['fields']['date'] for p in news), '2026-09-24')
            for slug in ('about-the-project','for-schools','for-parents','for-students','timeline'):
                self.assertTrue(next(p for p in pages if p['fields']['slug']==slug)['live'])
            self.assertFalse(next(p for p in pages if p['fields']['slug']=='results')['live'])
            self.assertFalse(any(s['value']['is_visible'] for p in pages for s in p['fields']['sections']
                                 if s['type']=='project_list' and s['value']['status']=='finished'))
        contact = next(s['fields'] for s in self.data['settings'] if s['model']=='home.contactsettings')
        self.assertEqual(contact['email'], 'biglab@muni.cz')
        self.assertIn('2.53', contact['address'])
        self.assertIn('218/10', contact['address'])
        for snippet in self.data['snippets']:
            if snippet['model']=='home.publication':
                self.assertEqual(snippet['fields']['publication_type'], '')

    def test_check_uses_no_database_and_reports_broken_references(self):
        output = StringIO()
        call_command('seed_biglab', check=True, stdout=output)
        self.assertIn('70 pages', output.getvalue())
        data = json.loads(json.dumps(self.data))
        data['pages'][0]['fields']['hero_image'] = {'ref':'wagtailimages.image','id':999999}
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'content.json').write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaisesMessage(CommandError, 'Invalid content snapshot'):
                load_bundle(directory)


class TimelineTests(SimpleTestCase):
    def setUp(self):
        self.block = TimelineBlock()
        self.value = self.block.to_python({'title':'Timeline','current_label':'Current period','milestones':[
            {'starts_on':'2026-03-01','period':'Spring 2026','text':'<p>Preparation</p>'},
            {'starts_on':'2026-09-01','period':'Autumn 2026','text':'<p>Pilot interviews</p>'},
            {'starts_on':'2027-03-01','period':'Spring 2027','text':'<p>Questionnaire</p>'},
        ]})

    def test_current_period_advances_at_date_boundary_and_works_without_javascript(self):
        for today, expected in ((date(2026,2,28),None),(date(2026,3,1),'Spring 2026'),
                                (date(2026,11,12),'Autumn 2026'),(date(2027,3,1),'Spring 2027')):
            with self.subTest(today=today), patch('home.blocks.timezone.localdate', return_value=today):
                soup = BeautifulSoup(self.block.render(self.value), 'html.parser')
                current = soup.select('li[aria-current="step"]')
                self.assertEqual(len(current), 1 if expected else 0)
                if expected:
                    self.assertEqual(current[0].time.text, expected)
                self.assertEqual(len(soup.select('.timeline-item')), 3)

    def test_editor_rejects_duplicate_or_unsorted_dates(self):
        self.block.clean(self.value)
        for dates in (['2026-09-01','2026-03-01','2027-03-01'], ['2026-03-01']*3):
            raw = self.block.get_prep_value(self.value)
            for item, day in zip(raw['milestones'], dates):
                item['value']['starts_on'] = day
            with self.assertRaises(StructBlockValidationError):
                self.block.clean(self.block.to_python(raw))
