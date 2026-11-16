"""Indexable pages, local navigation and security work without JavaScript."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASE = 'https://finndebear.github.io'


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tags = []
        self.feed(source)

    def handle_starttag(self, tag, attributes):
        self.tags.append((tag, dict(attributes)))

    def find(self, tag, **attributes):
        return [a for t, a in self.tags if t == tag and all(a.get(k) == v for k, v in attributes.items())]


class SiteContractTest(unittest.TestCase):
    def test_site_identity_is_declared_at_the_domain_root_and_shared_by_the_homepage(self):
        def schemas(filename):
            return [json.loads(raw) for raw in re.findall(
                r'<script type="application/ld\+json">(.*?)</script>', (ROOT / filename).read_text(), re.S)]
        root = next(node for node in schemas('index.html') if node['@type'] == 'WebSite')
        self.assertEqual(BASE + '/', root['url'])
        self.assertEqual('STPlayer', root['name'])
        home = next(node for schema in schemas('stplayer/index.html') for node in schema['@graph']
                    if node['@type'] == 'WebSite')
        self.assertEqual({key: value for key, value in root.items() if key != '@context'}, home)

    def test_sitemap_pages_are_indexable_and_have_unique_titles_and_descriptions(self):
        titles, descriptions = set(), set()
        for loc in ET.parse(ROOT / 'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
            with self.subTest(url=loc.text):
                path = ROOT / urlsplit(loc.text).path.lstrip('/') / 'index.html'
                source = path.read_text()
                page = Page(source)
                self.assertEqual([{'rel': 'canonical', 'href': loc.text}], page.find('link', rel='canonical'))
                self.assertEqual(1, len(page.find('h1')))
                self.assertFalse(any('noindex' in a.get('content', '').lower() for a in page.find('meta', name='robots')))
                title = source.split('<title>', 1)[1].split('</title>', 1)[0]
                description = page.find('meta', name='description')[0]['content']
                self.assertNotIn(title, titles)
                self.assertNotIn(description, descriptions)
                titles.add(title); descriptions.add(description)
                if '/privacy/' not in loc.text:
                    alternates = {a['hreflang']: a['href'] for a in page.find('link', rel='alternate')}
                    self.assertEqual({'en', 'de', 'es', 'fi', 'fr', 'ja', 'nl', 'pt', 'ru', 'sv', 'tr', 'zh', 'x-default'}, alternates.keys())
                    for language in ('en', 'de', 'es', 'fi', 'fr', 'ja', 'nl', 'pt', 'ru', 'sv', 'tr', 'zh'):
                        other = ROOT / urlsplit(alternates[language]).path.lstrip('/') / 'index.html'
                        other_page = Page(other.read_text())
                        self.assertEqual(alternates, {a['hreflang']: a['href'] for a in other_page.find('link', rel='alternate')})
                        self.assertEqual(language, other_page.find('html')[0]['lang'])
        self.assertEqual(37, len(titles))
        self.assertIn('Sitemap: ' + BASE + '/sitemap.xml', (ROOT / 'robots.txt').read_text())

    def test_every_local_link_and_image_has_a_destination(self):
        for path in ROOT.rglob('*.html'):
            page = Page(path.read_text())
            for tag, attrs in page.tags:
                for key in ('href', 'src'):
                    if key not in attrs: continue
                    url = urlsplit(attrs[key])
                    if url.scheme or url.netloc: continue
                    target = (ROOT / unquote(url.path).lstrip('/')) if url.path.startswith('/') else path.parent / unquote(url.path)
                    if not url.path: target = path
                    if target.is_dir(): target /= 'index.html'
                    with self.subTest(page=str(path.relative_to(ROOT)), link=attrs[key]):
                        self.assertTrue(target.is_file(), str(target))
                        if url.fragment and target.suffix == '.html':
                            ids = {a['id'] for _, a in Page(target.read_text()).tags if 'id' in a}
                            self.assertIn(unquote(url.fragment), ids)

    def test_security_policy_precedes_scripts_and_language_controls_include_visible_labels(self):
        for path in (ROOT / 'stplayer').rglob('*.html'):
            source = path.read_text(); page = Page(source)
            with self.subTest(page=str(path.relative_to(ROOT))):
                self.assertLess(source.index('Content-Security-Policy'), source.index('<script'))
                for control in page.find('a', **{'class': 'language-switch'}):
                    self.assertIn(control['hreflang'].upper(), control['aria-label'])
