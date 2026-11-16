from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import notify_indexnow


class IndexNowTest(unittest.TestCase):
    def test_all_canonical_pages_are_in_one_notification(self):
        data = notify_indexnow.payload()
        self.assertEqual('finndebear.github.io', data['host'])
        self.assertEqual(37, len(data['urlList']))
        for language in ('en', 'de', 'es', 'fi', 'fr', 'ja', 'nl', 'pt', 'ru', 'sv', 'tr', 'zh'):
            path = '' if language == 'en' else language + '/'
            for suffix in ('', 'audiobooks/', 'latest/'):
                self.assertIn('https://finndebear.github.io/stplayer/' + path + suffix, data['urlList'])

    def test_invalid_key_and_foreign_urls_fail_before_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copy(ROOT / 'sitemap.xml', root / 'sitemap.xml')
            (root / 'indexnow.txt').write_text('invalid key')
            with self.assertRaisesRegex(ValueError, 'key'):
                notify_indexnow.payload(root)
            shutil.copy(ROOT / 'indexnow.txt', root / 'indexnow.txt')
            source = (root / 'sitemap.xml').read_text()
            for bad in ('https://finndebear.github.io.evil.example/', 'http://finndebear.github.io/',
                        'https://finndebear.github.io/?tracking=yes'):
                with self.subTest(url=bad):
                    (root / 'sitemap.xml').write_text(source.replace('https://finndebear.github.io/', bad, 1))
                    with self.assertRaises(ValueError):
                        notify_indexnow.payload(root)
