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
from django.test import SimpleTestCase, TestCase
from wagtail.blocks import StructBlockValidationError

from home.blocks import TimelineBlock
from home.content_snapshot import load_bundle, import_bundle
from home.models import ContactSettings, ContentPage, HomePage
from wagtail.models import Site


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

    def test_prose_and_headings_are_on_their_intended_pages_in_each_language(self):
        with ZipFile(Path(__file__).parent / 'seed_assets/supplied/CONTENT.docx') as document:
            paragraphs = ET.fromstring(document.read('word/document.xml')).findall(
                './/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body//'
                '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')
        targets = {
            'homepage': {'en':[39,40,42,44], 'cs':[28,29,31,33]},
            'petra-palickova': {'en':[62], 'cs':[56]},
            'michaela-krystofova': {'en':[73], 'cs':[67]},
            'adela-frankova': {'en':[85], 'cs':[79]},
            'olesja-nyjherova': {'en':[97], 'cs':[91]},
            'utku-caybas': {'en':[103], 'cs':[101]},
            'research-meeting-with-satis-lab': {'en':[131,132,134], 'cs':[124,125,127]},
            'tibor-zingora-interview': {'en':[141,142], 'cs':[138,139]},
            'new-team-members': {'en':[147,148], 'cs':[144,145]},
            'eusn2026': {'en':[152,153], 'cs':[149,150]},
            'ching-ting-ang-joins': {'en':[160,161], 'cs':[157,158]},
            'parta-pilot-school': {'en':[167,168], 'cs':[164,165]},
            'for-schools': {
                'en':[266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284],
                'cs':[231,233,234,236,237,239,240,242,244,246,247,249,250,251,252,254,255,256,257,258,260]},
            'for-parents': {
                'en':[315,317,319,320,322,323,325,326,327,328,330,332,334,335],
                'cs':[290,292,293,295,296,298,299,301,302,303,304,306,308,310,311]},
            'for-students': {'en':[360,362,364,365,367,368,370,372,373], 'cs':[341,343,344,346,347,349,350,352,354,355]},
            'timeline': {'en':[396,398,400,402], 'cs':[377,379,381,383]},
        }
        def normalize(value):
            return re.sub(r'\s+', ' ', BeautifulSoup(value, 'html.parser').get_text() if '<' in value else value).strip()
        def strings(value):
            if isinstance(value, dict):
                for child in value.values(): yield from strings(child)
            elif isinstance(value, list):
                for child in value: yield from strings(child)
            elif isinstance(value, str): yield normalize(value)
        for slug, languages in targets.items():
            for code, indices in languages.items():
                page = next(p for p in self.data['pages'] if p['locale']==code and
                            (p['model']=='home.homepage' if slug=='homepage' else p['fields']['slug']==slug))
                actual = '\n'.join(strings(page['fields']))
                for index in indices:
                    expected = re.sub(r'\[[^\]]*\]', '', ''.join(paragraphs[index].itertext())).strip()
                    expected = re.sub(r'\s+\d{1,2}\.\d{1,2}\.\d{4}$', '', expected)
                    with self.subTest(page=slug, locale=code, paragraph=index):
                        self.assertIn(normalize(expected), actual)
        for code, indices in [('en',range(406,413)),('cs',range(387,394))]:
            page = next(p for p in self.data['pages'] if p['locale']==code and p['fields']['slug']=='timeline')
            milestones = next(b['value']['milestones'] for b in page['fields']['body'] if b['type']=='timeline')
            for milestone, index in zip(milestones, indices):
                period, description = ''.join(paragraphs[index].itertext()).split(':',1)
                self.assertEqual(milestone['period'].casefold(), period.casefold())
                for sentence in description.split(';'):
                    self.assertIn(normalize(sentence), normalize(milestone['text']))

    def test_audience_tree_matches_document_order(self):
        for code in ('en','cs'):
            about = next(p for p in self.data['pages'] if p['locale']==code and p['fields']['slug']=='about-the-project')
            self.assertEqual([p['fields']['slug'] for p in self.data['pages'] if p['parent']==about['id']],
                             ['for-schools','for-parents','for-students'])

    def test_people_and_shared_records_match_the_document(self):
        with ZipFile(Path(__file__).parent / 'seed_assets/supplied/CONTENT.docx') as document:
            paragraphs = ET.fromstring(document.read('word/document.xml')).findall(
                './/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body//'
                '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')
        def source(index):
            return ''.join(paragraphs[index].itertext()).strip()
        people = {
            'petra-palickova': (61,55,64), 'michaela-krystofova': (72,66,75),
            'adela-frankova': (84,78,87), 'olesja-nyjherova': (96,90,99),
            'ching-ting-ang': (111,110,113), 'utku-caybas': (None,None,105),
            'tibor-zingora': (None,None,116), 'zhe-dong': (None,None,118),
        }
        for code in ('en','cs'):
            for slug, (en_role,cs_role,email) in people.items():
                fields = next(p['fields'] for p in self.data['pages'] if p['locale']==code and p['fields']['slug']==slug)
                self.assertEqual(fields['email'], source(email).removeprefix('Email: ').split()[0])
                role = en_role if code=='en' else cs_role
                if role:
                    self.assertEqual(fields['role'].casefold(), re.search(r'\(([^)]+)\)',source(role))[1].casefold())
                elif slug=='tibor-zingora':
                    self.assertEqual(fields['role'].casefold(), 'head' if code=='en' else 'vedoucí')
            publications = [s['fields'] for s in self.data['snippets'] if s['model']=='home.publication' and s['fields']['locale']['locale']==code]
            for title,authors,journal in [(184,185,186),(189,190,191)]:
                fields = next(p for p in publications if p['title']==source(title))
                self.assertEqual(fields['authors'],source(authors))
                self.assertEqual(fields['journal_or_publisher'],source(journal))
                self.assertEqual(fields['year'],2026)
                self.assertTrue(fields['doi_or_url'].startswith('https://doi.org/'))
            partners = [s['fields'] for s in self.data['snippets'] if s['model']=='home.collaboration' and s['fields']['locale']['locale']==code]
            indices = range(213,221,2) if code=='en' else range(199,207,2)
            for fields,index in zip(sorted(partners,key=lambda p:p['sort_order']),indices):
                self.assertEqual(fields['name'],source(index))
                self.assertEqual(fields['description'],source(index+1))
                self.assertTrue(fields['website'].startswith('https://'))

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


class SuppliedStructureRenderingTests(TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        media = self.settings(MEDIA_ROOT=Path(directory.name) / 'media')
        media.enable()
        self.addCleanup(media.disable)
        import_bundle()

    def test_news_media_and_collaborations_have_consistent_shared_layouts(self):
        for prefix, news_path, science_path in [('', '/news/', '/science/'), ('/cs', '/cs/novinky/', '/cs/vyzkum/')]:
            archive = BeautifulSoup(self.client.get(news_path).content, 'html.parser')
            cards = archive.select('.news-list-item')
            self.assertEqual(len(cards), 6)
            self.assertEqual(len(archive.select('.news-thumbnail')), 2)
            self.assertEqual(len(archive.select('.news-thumbnail img')), 2)
            self.assertFalse(archive.select('.news-thumbnail--placeholder'))
            for card in cards:
                self.assertIsNotNone(card.select_one('time[datetime]'))
                self.assertTrue(card.select_one('h2 a')['href'])
                self.assertLessEqual(len(card.select_one('.news-excerpt').text.split()), 33)
                if card.select_one('.news-thumbnail img'):
                    detail = BeautifulSoup(self.client.get(card.select_one('.news-title a')['href']).content, 'html.parser')
                    self.assertEqual(detail.select_one('.article-image img')['alt'], detail.select_one('main h1').get_text())
            for path in (prefix + '/', science_path):
                soup = BeautifulSoup(self.client.get(path).content, 'html.parser')
                self.assertEqual(len(soup.select('.collaboration-item')), 4)
                self.assertEqual(len(soup.select('.collaboration-symbol > svg')), 4)
                self.assertEqual(len(soup.select('.collaboration-copy h3 a[href]')), 4)
            parta = BeautifulSoup(self.client.get(prefix + '/parta/').content, 'html.parser')
            self.assertFalse(parta.select('[data-child-navigation]'))

    def test_document_navigation_and_contact_copy_in_both_languages(self):
        for code, root in [('en','/'),('cs','/cs/')]:
            response = self.client.get(root)
            self.assertEqual(response.status_code, 200)
            soup = BeautifulSoup(response.content, 'html.parser')
            menu = soup.select('header .site-nav > li')
            def titles(items):
                return [item.select_one(':scope > .nav-entry > a').get_text(strip=True) for item in items]
            self.assertEqual(titles(menu), ['About us','Science','PARTA'] if code=='en' else ['O nás','Výzkum','PARTA'])
            self.assertEqual(titles(menu[0].select(':scope > ul > li')),
                             ['BIG Lab','People','News'] if code=='en' else ['BIG Lab','Lidé','Novinky'])
            self.assertEqual(titles(menu[1].select(':scope > ul > li')),
                             ['Publications','Collaboration'] if code=='en' else ['Publikace','Spolupráce'])
            parta = menu[2].select(':scope > ul > li')
            self.assertEqual(titles(parta), ['About the project','Timeline'] if code=='en' else ['O projektu','Časová osa'])
            self.assertEqual(titles(parta[0].select(':scope > ul > li')),
                             ['For schools','For parents','For students'] if code=='en' else ['Pro školy','Pro rodiče','Pro studenty'])
            visit = ('or stop by the Faculty of Social Studies in person' if code=='en' else
                     'nebo se za námi zastavte osobně na Fakultu sociálních studií')
            team = ('You can find contact information for individual team members in the section' if code=='en' else
                    'Kontakty na jednotlivé členy týmu najdete v sekci')
            for path in (root+'?design=1', root+'contact/', root+'about/'):
                with self.subTest(path=path):
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200)
                    contact = BeautifulSoup(response.content, 'html.parser').select_one('.contact-surface, .builder-contact')
                    self.assertIsNotNone(contact)
                    self.assertIn(visit, contact.get_text(' ',strip=True))
                    self.assertEqual(contact.get_text(' ',strip=True).count(team), 1)
                    self.assertIsNotNone(contact.select_one('a[href="mailto:biglab@muni.cz"]'))
                    self.assertIn('2.53', contact.address.get_text())
                    self.assertIn('218/10', contact.address.get_text())
                    self.assertIsNotNone(contact.select_one('iframe'))

    def test_shared_address_stays_editable_without_changing_contact_copy(self):
        settings = ContactSettings.for_site(Site.objects.get(is_default_site=True))
        settings.address = 'Updated campus address\nOffice 9.99'
        settings.save()
        for root in ('/','/cs/'):
            for path in (root+'?design=1',root+'contact/'):
                contact = BeautifulSoup(self.client.get(path).content, 'html.parser').select_one('.contact-surface, .builder-contact')
                self.assertIn('Updated campus address',contact.address.get_text())
                self.assertNotIn('2.53',contact.get_text())

    def test_section_titles_do_not_repeat_the_page_title(self):
        for root in ('/','/cs/'):
            home = BeautifulSoup(self.client.get(root).content,'html.parser')
            self.assertIsNone(home.select_one('.updates-grid > div > h3'))
            self.assertTrue(home.select('.updates .news-list-item'))
            for suffix in ('parta/','parta/about-the-project/','contact/'):
                with self.subTest(path=root+suffix):
                    response = self.client.get(root+suffix)
                    soup = BeautifulSoup(response.content,'html.parser').select_one('main')
                    title = soup.h1.get_text(strip=True)
                    self.assertEqual(sum(h.get_text(strip=True)==title for h in soup.select('h1,h2,h3')),1)
                    for card in soup.select('.page-link-grid > a'):
                        self.assertIsNotNone(card.select_one('h2.page-link-title'))
                        self.assertTrue(card['href'])

    def test_existing_editor_contact_copy_is_not_duplicated(self):
        team = 'You can find contact information for individual team members in the section'
        for page in (HomePage.objects.get(locale__language_code='en'),
                     ContentPage.objects.get(locale__language_code='en',slug='contact')):
            for block in page.sections:
                if block.block_type=='contact':
                    block.value['text'] = block.block.child_blocks['text'].to_python(f'<p>{team}</p>')
            page.save()
        for path in ('/?design=1','/contact/'):
            contact = BeautifulSoup(self.client.get(path).content,'html.parser').select_one('.contact-surface, .builder-contact')
            self.assertEqual(contact.get_text(' ',strip=True).count(team),1)

    def test_audience_copy_and_buttons_render_in_both_languages(self):
        with ZipFile(Path(__file__).parent / 'seed_assets/supplied/CONTENT.docx') as document:
            paragraphs = ET.fromstring(document.read('word/document.xml')).findall(
                './/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body//'
                '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')
        for code,indices in [('en',{'for-schools':[266,268,270,271,272,274,275,276,277,278,280,281,282,283,284],
                                   'for-parents':[317,320,323,325,326,327,328,330,332,335],
                                   'for-students':[362,365,368,370,373]}),
                             ('cs',{'for-schools':[233,234,237,240,242,244,247,249,250,251,252,255,256,257,258,260],
                                   'for-parents':[292,293,296,299,301,302,303,304,306,308,311],
                                   'for-students':[343,344,347,350,352,355]})]:
            for slug,paragraph_indices in indices.items():
                page = ContentPage.objects.get(locale__language_code=code,slug=slug)
                response = self.client.get(page.url)
                self.assertEqual(response.status_code,200)
                main = BeautifulSoup(response.content,'html.parser').select_one('main')
                actual = re.sub(r'\s+',' ',main.get_text(' ',strip=True))
                for index in paragraph_indices:
                    expected = re.sub(r'\[[^\]]*\]','',''.join(paragraphs[index].itertext())).strip()
                    with self.subTest(page=page.url,paragraph=index):
                        self.assertIn(re.sub(r'\s+',' ',expected),actual)
                contact = ContentPage.objects.get(locale__language_code=code,slug='contact')
                self.assertTrue(any(a['href'].split('?')[0]==contact.url for a in main.select('a.button[href]')))
                if slug!='for-students':
                    timeline = ContentPage.objects.get(locale__language_code=code,slug='timeline')
                    self.assertTrue(any(a['href'].split('?')[0]==timeline.url for a in main.select('a.button[href]')))


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
