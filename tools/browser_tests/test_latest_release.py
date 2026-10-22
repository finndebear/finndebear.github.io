"""Browser coverage: serve the real pages and intercept only GitHub's release response."""
import copy
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import unittest

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
API = 'https://api.github.com/repos/finndebear/finndebear.github.io/releases/latest'


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


class LatestReleaseBrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.context = self.browser.new_context()
        self.addCleanup(self.context.close)
        # No analytics or other external traffic during these deterministic tests.
        self.context.route('https://**/*', lambda route: route.abort())
        self.release = json.loads((ROOT / 'stplayer/assets/latest-release.json').read_text())
        tag = self.release['tag_name']
        self.release['tag_name'] = '9.8.7'
        self.release['body'] = '## English\n- New release <script>window.injected = true</script>\n\n### Details\nMore & better.\n\n## Русский\n- Новая версия\n\n### Подробности\nЕщё лучше.'
        for asset in self.release['assets']:
            asset['name'] = asset['name'].replace(tag, '9.8.7')
            asset['browser_download_url'] = asset['browser_download_url'].replace(tag, '9.8.7')

    def open(self, path, release=None, status=200, width=1280, javascript=True):
        if not javascript:
            context = self.browser.new_context(java_script_enabled=False)
            self.addCleanup(context.close)
            page = context.new_page()
        else:
            self.context.route(API, lambda route: route.fulfill(
                status=status, json=release or self.release,
                headers={'Access-Control-Allow-Origin': '*'}))
            page = self.context.new_page()
        page.set_viewport_size({'width': width, 'height': 900})
        page.goto(self.base + path, wait_until='networkidle')
        return page

    def test_homepages_update_both_downloads_version_labels_and_schema(self):
        for path in ('/stplayer/', '/stplayer/ru/'):
            with self.subTest(path=path):
                page = self.open(path)
                labels = page.locator('[data-version-label]').all_text_contents()
                self.assertEqual(2, len(labels))
                self.assertTrue(all(label.startswith('v9.8.7 · Android 8.0+') for label in labels))
                self.assertEqual([self.release['assets'][0]['browser_download_url']] * 2,
                                 page.locator('[data-apk-download]').evaluate_all('(links) => links.map(link => link.href)'))
                schema = json.loads(page.locator('script[type="application/ld+json"]').text_content())
                app = next(node for node in schema['@graph'] if node['@type'] == 'SoftwareApplication')
                self.assertEqual('9.8.7', app['softwareVersion'])
                self.assertEqual(self.release['assets'][0]['browser_download_url'], app['downloadUrl'])
                page.close()

    def test_release_pages_update_files_localized_notes_and_metadata_on_mobile(self):
        for path, present, absent in (('/stplayer/latest/', 'New release', 'Новая версия'),
                                      ('/stplayer/ru/latest/', 'Новая версия', 'New release')):
            with self.subTest(path=path):
                page = self.open(path, width=390)
                self.assertIn('9.8.7', page.title())
                self.assertIn('9.8.7', page.locator('#release-title').text_content())
                self.assertIn('9.8.7', page.locator('meta[name="description"]').get_attribute('content'))
                self.assertEqual(2, page.locator('.release-download-card').count())
                notes = page.locator('#release-notes').text_content()
                self.assertIn(present, notes)
                self.assertNotIn(absent, notes)
                self.assertEqual('https://github.com/finndebear/finndebear.github.io/releases/tag/9.8.7',
                                 page.locator('#release-notes .release-source a').get_attribute('href'))
                self.assertIsNone(page.evaluate('window.injected'))
                self.assertEqual(0, page.locator('#release-notes script').count())
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                self.assertEqual(1, page.locator('#release-notes details').count())
                page.close()

    def test_apk_only_release_removes_old_zip_and_uses_localized_missing_notes(self):
        self.release['assets'] = self.release['assets'][:1]
        self.release['body'] = '## English\n- English only'
        page = self.open('/stplayer/ru/latest/')
        self.assertEqual(1, page.locator('.release-download-card').count())
        self.assertEqual(0, page.locator('.format-zip').count())
        self.assertNotIn('ZIP', page.locator('meta[name="description"]').get_attribute('content'))
        self.assertIn('пока недоступны', page.locator('#release-notes').text_content())
        self.assertNotIn('English only', page.locator('#release-notes').text_content())

    def test_stable_asset_aliases_are_preferred_without_duplicate_cards(self):
        for asset in list(self.release['assets']):
            stable = copy.deepcopy(asset)
            stable['name'] = stable['name'].replace('-9.8.7', '')
            stable['browser_download_url'] = stable['browser_download_url'].replace('-9.8.7', '')
            self.release['assets'].append(stable)
        page = self.open('/stplayer/latest/')
        self.assertEqual(2, page.locator('.release-download-card').count())
        self.assertTrue(page.locator('.format-apk a').get_attribute('href').endswith('/latest/download/stplayer.apk'))
        self.assertTrue(page.locator('.format-zip a').get_attribute('href').endswith('/latest/download/stplayer.zip'))

    def test_unavailable_or_invalid_release_preserves_complete_static_fallback(self):
        variants = [(self.release, 403), (dict(self.release, draft=True), 200),
                    (dict(self.release, prerelease=True), 200)]
        foreign = copy.deepcopy(self.release)
        foreign['assets'][0]['browser_download_url'] = 'https://evil.example/stplayer.apk'
        variants.append((foreign, 200))
        for release, status in variants:
            with self.subTest(release=release['tag_name'], status=status):
                page = self.open('/stplayer/latest/', release=release, status=status)
                self.assertNotIn('9.8.7', page.locator('#release-title').text_content())
                self.assertEqual(2, page.locator('.release-download-card').count())
                self.assertIn('https://github.com/finndebear/finndebear.github.io/releases/latest',
                              page.locator('#release-fallback a').get_attribute('href'))
                self.assertNotIn('evil.example', page.content())
                page.close()

    def test_javascript_disabled_keeps_downloads_and_release_notes_usable(self):
        page = self.open('/stplayer/latest/', javascript=False)
        self.assertEqual(2, page.locator('.release-download-card a').count())
        self.assertGreater(page.locator('#release-notes li').count(), 0)
        self.assertTrue(page.locator('#release-fallback a').is_visible())

    def test_homepage_illustration_has_equal_dimensions_in_both_languages(self):
        for width in (320, 390, 768, 900, 1024, 1050, 1051, 1280, 1440):
            dimensions = []
            for path in ('/stplayer/', '/stplayer/ru/'):
                with self.subTest(path=path, width=width):
                    page = self.open(path, width=width)
                    dimensions.append(page.locator('.hero-art').evaluate('''art =>
                        [art, ...art.querySelectorAll('.hero-icon, .soundwave, .sound-ring')]
                            .map(element => {
                                const bounds = element.getBoundingClientRect();
                                return [bounds.width, bounds.height];
                            })'''))
                    self.assertGreater(page.locator('.hero-icon').evaluate('image => image.naturalWidth'), 0)
                    self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                    page.close()
            with self.subTest(width=width):
                self.assertEqual(dimensions[0], dimensions[1])

    def test_store_badges_are_localized_svg_and_rustore_follows_google_only_in_russian(self):
        for language, path in (('en', '/stplayer/latest/'), ('ru', '/stplayer/ru/latest/')):
            for width in (320, 390, 1280):
                with self.subTest(language=language, width=width):
                    page = self.open(path, width=width)
                    google = page.locator('.play-store-link img')
                    self.assertIn(f'google-play-badge-{language}.svg', google.get_attribute('src'))
                    self.assertTrue(google.is_visible())
                    self.assertGreater(google.evaluate('image => image.naturalWidth'), 0)
                    self.assertEqual(40, google.bounding_box()['height'])
                    stores = page.locator('.store-links a')
                    self.assertIn('play.google.com/store/apps/details?id=com.st.player', stores.nth(0).get_attribute('href'))
                    self.assertEqual(2 if language == 'ru' else 1, stores.count())
                    if language == 'ru':
                        self.assertEqual('https://www.rustore.ru/catalog/app/com.st.player', stores.nth(1).get_attribute('href'))
                        self.assertIn('rustore-badge.svg', stores.nth(1).locator('img').get_attribute('src'))
                        self.assertEqual(40, stores.nth(1).locator('img').bounding_box()['height'])
                    self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                    page.close()


if __name__ == '__main__':
    unittest.main()
