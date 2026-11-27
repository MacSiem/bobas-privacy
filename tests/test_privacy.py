import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = ('pl', 'en', 'de', 'es', 'fr', 'it', 'pt', 'uk', 'ja', 'ko', 'zh')


class PrivacyPage(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.sections = {}
        self.language_links = []
        self.language = None
        self.in_switcher = False
        self.heading = None
        self.feed(path.read_text(encoding='utf-8'))
        self.close()

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'nav' and attrs.get('class') == 'lang-switcher':
            self.in_switcher = True
        if self.in_switcher and tag == 'a' and attrs['href'].startswith('#'):
            self.language_links.append((attrs['href'], attrs.get('lang')))
        if tag == 'section':
            self.language = attrs['id']
            if self.language in self.sections:
                raise ValueError(f'Duplicate language section: {self.language}')
            self.sections[self.language] = {
                'lang': attrs.get('lang'), 'contents': {'intro': []}, 'links': [],
            }
            self.heading = 'intro'
        if self.language is None:
            return
        section = self.sections[self.language]
        if tag == 'h2':
            self.heading = f'heading-{len(section["contents"])}'
            section['contents'][self.heading] = []
        section['contents'][self.heading].append((tag, attrs.get('href')))
        if tag == 'a':
            section['links'].append(attrs['href'])

    def handle_endtag(self, tag):
        if tag == 'section':
            self.language = None
        if tag == 'nav':
            self.in_switcher = False

    def handle_data(self, data):
        if self.language is not None and data.strip():
            self.sections[self.language]['contents'][self.heading].append(('text', data.strip()))


class PrivacyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = PrivacyPage(ROOT / 'index.html')
        cls.deletion = PrivacyPage(ROOT / 'delete-account/index.html')

    def test_language_navigation_targets_all_eleven_sections(self):
        self.assertEqual(tuple(self.policy.sections), LANGUAGES)
        self.assertEqual(self.policy.language_links, [(f'#{code}', code) for code in LANGUAGES])
        for code in LANGUAGES:
            with self.subTest(language=code):
                self.assertEqual(self.policy.sections[code]['lang'], code)

    def test_each_translation_covers_all_fifteen_policy_sections(self):
        content_tags = {'p', 'li', 'ul', 'strong', 'a'}
        source = list(self.policy.sections['en']['contents'].values())[1:]
        for code, locale in self.policy.sections.items():
            with self.subTest(language=code):
                intro, *chapters = locale['contents'].values()
                self.assertIn(('h1', None), intro)
                self.assertTrue(any('2026-11-23' in text for tag, text in intro if tag == 'text'))
                self.assertEqual(len(chapters), 15)

                for number, (chapter, source_chapter) in enumerate(zip(chapters, source), start=1):
                    with self.subTest(chapter=number):
                        self.assertEqual(
                            [tag for tag, _ in chapter if tag in content_tags],
                            [tag for tag, _ in source_chapter if tag in content_tags],
                        )
                        title = next(text for tag, text in chapter if tag == 'text')
                        self.assertRegex(title, rf'^{number}\. \S')

                for chapter, terms in {
                    1: ('Maciej Siemiński', 'LICENCEPRO POLSKA Sp. z o.o.'),
                    3: ('MMKV', 'SecureStore', 'Android Keystore'),
                    4: ('bobas://join', 'JSON', 'CSV', 'PDF', 'Premium', 'Google Drive', 'iCloud', 'CloudKit', 'Apple Private Relay'),
                    5: ('Live Activity', 'Expo Push', 'Cloudflare Worker', 'APNs', 'Firebase Cloud Messaging'),
                    6: ('Sentry',),
                    7: ('Unity Ads', 'AD_ID', 'ATT'),
                    12: ('V1', 'V2', '30', 'Sentry', 'Unity Ads'),
                    14: ('UODO',),
                }.items():
                    addressable = locale['contents'][f'heading-{chapter}']
                    text = ' '.join(value for tag, value in addressable if tag == 'text')
                    for term in terms:
                        self.assertIn(term, text)

    def test_every_locale_links_to_its_deletion_page_and_public_contacts(self):
        for code, locale in self.policy.sections.items():
            with self.subTest(language=code):
                target = f'delete-account/#{code}'
                self.assertIn(('a', target), locale['contents']['heading-14'])
                self.assertEqual(self.deletion.sections[code]['lang'], code)
                self.assertEqual(locale['links'].count('mailto:mail@macsiem.dev'), 4)
                self.assertIn('https://uodo.gov.pl/', locale['links'])
