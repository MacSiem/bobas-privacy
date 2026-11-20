import pathlib
import unittest
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
LANGUAGES = {'pl','en','de','es','fr','it','ja','ko','pt','uk','zh'}

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.current = None; self.sections = {}; self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'section':
            self.current = attrs.get('id'); self.sections[self.current] = {'lang': attrs.get('lang'), 'text': '', 'links': []}
        if tag == 'a':
            self.links.append(attrs.get('href'))
            if self.current: self.sections[self.current]['links'].append(attrs.get('href'))
    def handle_endtag(self, tag):
        if tag == 'section': self.current = None
    def handle_data(self, data):
        if self.current: self.sections[self.current]['text'] += data

class AccountDeletionPageTest(unittest.TestCase):
    def test_languages_have_contact_action_and_scope(self):
        page = Page(); page.feed((ROOT / 'delete-account/index.html').read_text(encoding='utf-8'))
        self.assertEqual(set(page.sections), LANGUAGES)
        for lang, section in page.sections.items():
            with self.subTest(lang=lang):
                self.assertEqual(section['lang'], lang)
                self.assertIn('#' + lang, page.links)
                self.assertGreater(len(section['text']), 200)
                for item in ('Bobas', 'Google Drive', 'iCloud', 'mail@macsiem.dev'):
                    self.assertIn(item, section['text'])
                urls = [urlparse(link) for link in section['links'] if link and link.startswith('mailto:')]
                self.assertTrue(any(url.path == 'mail@macsiem.dev' and parse_qs(url.query).get('subject') == ['Bobas account deletion'] for url in urls))
                self.assertIn('../', section['links'])
                self.assertIn('../terms/', section['links'])
        self.assertNotIn('<form', (ROOT / 'delete-account/index.html').read_text(encoding='utf-8').lower())

    def test_lost_email_or_apple_relay_has_a_fallback_in_each_language(self):
        page = Page(); page.feed((ROOT / 'delete-account/index.html').read_text(encoding='utf-8'))
        alternatives = {'pl':'dostępnego adresu', 'en':'address you can access', 'de':'erreichbaren Adresse',
                        'es':'dirección disponible', 'fr':'adresse accessible', 'it':'indirizzo accessibile',
                        'ja':'利用できるアドレス', 'ko':'사용할 수 있는 주소', 'pt':'endereço acessível',
                        'uk':'доступної адреси', 'zh':'仍可访问的邮箱'}
        for lang, text in alternatives.items():
            with self.subTest(lang=lang):
                self.assertIn('Apple', page.sections[lang]['text'])
                self.assertIn(text, page.sections[lang]['text'])

    def test_policy_links_directly_to_both_localized_deletion_paths(self):
        page = Page(); page.feed((ROOT / 'index.html').read_text(encoding='utf-8'))
        self.assertIn('delete-account/', page.links)
        self.assertIn('delete-account/#pl', page.sections['pl']['links'])
        self.assertIn('delete-account/#en', page.sections['en']['links'])
        self.assertTrue((ROOT / 'delete-account/index.html').is_file())

if __name__ == '__main__': unittest.main()
