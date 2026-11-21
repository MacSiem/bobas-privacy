import pathlib
import unittest
from html.parser import HTMLParser

class Terms(HTMLParser):
    def __init__(self):
        super().__init__(); self.current = None; self.sections = {}; self.links = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'section': self.current = a['id']; self.sections[self.current] = {'lang': a.get('lang'), 'headings': 0, 'text': ''}
        if tag == 'h2' and self.current: self.sections[self.current]['headings'] += 1
        if tag == 'a': self.links.append(a.get('href'))
    def handle_endtag(self, tag):
        if tag == 'section': self.current = None
    def handle_data(self, data):
        if self.current: self.sections[self.current]['text'] += data

class TermsTest(unittest.TestCase):
    def test_all_supported_languages_have_complete_sections_and_public_contact(self):
        parser = Terms(); parser.feed(pathlib.Path('terms/index.html').read_text(encoding='utf-8'))
        langs = {'pl','en','de','es','fr','it','ja','ko','pt','uk','zh'}
        self.assertEqual(set(parser.sections), langs)
        for code, section in parser.sections.items():
            with self.subTest(language=code):
                self.assertEqual(section['lang'], code)
                self.assertEqual(section['headings'], 8)
                self.assertIn('mail@macsiem.dev', section['text'])
                self.assertIn('LICENCEPRO POLSKA', section['text'])
                self.assertIn('Maciej Siemiński', section['text'])
                self.assertIn('Google Drive', section['text'])
                self.assertIn('iCloud', section['text'])
                self.assertIn('Unity Ads', section['text'])
                self.assertIn('#' + code, parser.links)
                self.assertGreater(len(section['text']), 600)
        self.assertIn('https://www.apple.com/legal/internet-services/itunes/dev/stdeula/', parser.links)
        self.assertNotIn('macsiem.dev@gmail.com', pathlib.Path('terms/index.html').read_text(encoding='utf-8'))

    def test_all_translations_distinguish_csv_json_and_premium_pdf(self):
        parser = Terms(); parser.feed(pathlib.Path('terms/index.html').read_text(encoding='utf-8'))
        for code, section in parser.sections.items():
            with self.subTest(language=code):
                for term in ('CSV', 'JSON', 'PDF', 'Premium'):
                    self.assertIn(term, section['text'])

    def test_privacy_and_terms_cross_links_and_backup_boundaries(self):
        policy = Terms(); policy.feed(pathlib.Path('index.html').read_text(encoding='utf-8'))
        terms = Terms(); terms.feed(pathlib.Path('terms/index.html').read_text(encoding='utf-8'))
        self.assertIn('terms/', policy.links)
        self.assertIn('../', terms.links)
        for code in ('pl', 'en'):
            text = policy.sections[code]['text']
            for value in ('Maciej Siemiński', 'LICENCEPRO POLSKA', 'Google Drive', 'CloudKit', 'V1', 'V2', '30'):
                with self.subTest(language=code, value=value): self.assertIn(value, text)
            self.assertIn('#' + code, policy.links)

if __name__ == '__main__': unittest.main()
