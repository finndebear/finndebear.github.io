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

    def test_homepage_icon_and_waves_keep_equal_dimensions_without_overflow(self):
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
                    self.assertEqual(1, page.locator('.soundwave').count())
                    self.assertEqual(2, page.locator('.sound-ring').count())
                    self.assertEqual(0, page.locator('.player-screen').count())
                    self.assertEqual(3, page.locator('#features article.feature').count())
                    self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                    page.close()
            with self.subTest(width=width):
                self.assertEqual(dimensions[0], dimensions[1])

    def test_store_badges_are_localized_svg_and_rustore_follows_google_only_in_russian(self):
        for language in json.loads((ROOT / 'stplayer/assets/locales.json').read_text()):
            path = '/stplayer/' + ('' if language == 'en' else language + '/') + 'latest/'
            for width in (320, 390, 768, 900, 1024, 1280):
                with self.subTest(language=language, width=width):
                    page = self.open(path, width=width)
                    google = page.locator('.play-store-link img')
                    self.assertIn(f'google-play-badge-{language}.svg', google.get_attribute('src'))
                    self.assertEqual(0, page.locator('header .nav-download').count())
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

    def test_all_twelve_languages_work_on_mobile_and_desktop_without_javascript(self):
        locales = json.loads((ROOT / 'stplayer/assets/locales.json').read_text())
        context = self.browser.new_context(java_script_enabled=False)
        self.addCleanup(context.close)
        for language, text in locales.items():
            prefix = '/stplayer/' + ('' if language == 'en' else language + '/')
            for suffix in ('', 'audiobooks/', 'latest/'):
                for width in (320, 1280):
                    with self.subTest(language=language, suffix=suffix, width=width):
                        page = context.new_page()
                        page.set_viewport_size({'width': width, 'height': 900})
                        page.goto(self.base + prefix + suffix)
                        self.assertEqual(language, page.locator('html').get_attribute('lang'))
                        self.assertEqual(1, page.locator('h1').count())
                        self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                        navigation = page.locator('header nav:not(.language-options)')
                        self.assertEqual(1, navigation.locator('a[href="/stplayer/privacy/?lang=' + language + '"]').count())
                        self.assertEqual(0, navigation.locator('a[href$="audiobooks/"]').count())
                        picker = page.locator('.language-picker')
                        picker.locator('summary').click()
                        self.assertEqual(12, picker.locator('a').count())
                        self.assertEqual(12, picker.locator('a span[aria-hidden="true"]').count())
                        self.assertEqual(text['flag'], picker.locator('summary span').text_content())
                        self.assertEqual(text['flag'], picker.locator('summary').inner_text().strip())
                        self.assertIn(text['name'], picker.locator('summary').get_attribute('aria-label'))
                        self.assertTrue(picker.locator('[aria-current="page"]').is_visible())
                        for link in picker.locator('a').all():
                            code = link.get_attribute('hreflang')
                            expected = '/stplayer/' + ('' if code == 'en' else code + '/') + suffix
                            self.assertEqual(expected, link.get_attribute('href'))
                            self.assertIn(locales[code]['name'], link.inner_text())
                        self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                        if suffix == 'latest/':
                            self.assertEqual(2, page.locator('#download-files a').count())
                            self.assertIn(text['notesTitle'], page.locator('#notes-heading').text_content())
                            self.assertGreater(page.locator('#release-notes li').count(), 0)
                        page.close()

    def test_latest_release_metadata_remains_localized_in_every_language(self):
        locales = json.loads((ROOT / 'stplayer/assets/locales.json').read_text())
        for language, text in locales.items():
            with self.subTest(language=language):
                prefix = '/stplayer/' + ('' if language == 'en' else language + '/')
                page = self.open(prefix + 'latest/')
                self.assertEqual(text['downloadPageTitle'].format(version='9.8.7'), page.title())
                self.assertIn(text['apkTitle'], page.locator('.format-apk h2').text_content())
                self.assertIn(text['version'].format(version='9.8.7'), page.locator('#release-title').text_content())
                if language not in ('en', 'ru'):
                    self.assertIn(text['missingNotes'], page.locator('#release-notes').text_content())
                page.close()

    def test_translated_notes_are_bound_to_both_version_and_original_body(self):
        current = json.loads((ROOT / 'stplayer/assets/latest-release.json').read_text())
        locales = json.loads((ROOT / 'stplayer/assets/locales.json').read_text())
        for language in set(locales) - {'en', 'ru'}:
            for altered in (False, True):
                with self.subTest(language=language, altered=altered):
                    release = dict(current, body=current['body'] + (' edited' if altered else ''))
                    page = self.open('/stplayer/' + language + '/latest/', release=release)
                    notes = page.locator('#release-notes')
                    if altered:
                        self.assertIn(locales[language]['missingNotes'], notes.text_content())
                        self.assertEqual(0, notes.locator('li').count())
                    else:
                        self.assertIn(locales[language]['translatedSummary'], notes.text_content())
                        self.assertEqual(7, notes.locator('li').count())
                    page.close()

    def test_theme_and_privacy_navigation_follow_each_selected_language(self):
        locales = json.loads((ROOT / 'stplayer/assets/locales.json').read_text())
        for language, text in locales.items():
            prefix = '/stplayer/' + ('' if language == 'en' else language + '/')
            for path in (prefix, '/stplayer/privacy/?lang=' + language):
                with self.subTest(language=language, path=path):
                    page = self.open(path)
                    toggle = page.locator('[data-theme-toggle]')
                    for _ in range(2):
                        dark = page.locator('html').get_attribute('data-theme') == 'dark'
                        self.assertEqual(text['themeLight' if dark else 'themeDark'], toggle.get_attribute('aria-label'))
                        toggle.click()
                        self.assertEqual('light' if dark else 'dark', page.locator('html').get_attribute('data-theme'))
                    if '/privacy/' in path:
                        self.assertEqual(language, page.locator('html').get_attribute('lang'))
                        self.assertEqual(prefix, page.locator('.policy-brand').get_attribute('href'))
                        self.assertEqual(1, page.locator('section.on').count())
                        self.assertIn(text['flag'], page.locator('#lang option:checked').text_content())
                    page.close()


if __name__ == '__main__':
    unittest.main()
