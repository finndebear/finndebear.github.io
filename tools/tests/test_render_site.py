import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("render_site", ROOT / "tools/render_site.py")
site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(site)


class StaticSiteTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        files = [filename for filename, _, _ in site.PAGES]
        files += ["stplayer/assets/" + name for name in ("latest-release.json", "site.css", "site.js")]
        for filename in files:
            target = self.root / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / filename, target)
        self.snapshot = self.root / "stplayer/assets/latest-release.json"
        self.release = json.loads(self.snapshot.read_text())

    def write_release(self, release):
        self.snapshot.write_text(json.dumps(release, ensure_ascii=False))

    def page(self, lang="en", release=False):
        return self.root / ("stplayer/" + ("ru/" if lang == "ru" else "") + ("latest/" if release else "") + "index.html")

    def test_current_snapshot_is_rendered_and_idempotent(self):
        self.assertEqual([], site.render_site(self.root, check=True))
        self.assertEqual([], site.render_site(self.root))

    def test_new_release_updates_all_static_downloads_versions_and_schema(self):
        newer = copy.deepcopy(self.release)
        old_tag = newer["tag_name"]
        newer["tag_name"] = "9.8.7"
        for asset in newer["assets"]:
            asset["name"] = asset["name"].replace(old_tag, newer["tag_name"])
            asset["browser_download_url"] = asset["browser_download_url"].replace(old_tag, newer["tag_name"])
        self.write_release(newer)
        originals = {filename: (self.root / filename).read_bytes() for filename, _, _ in site.PAGES}
        self.assertEqual(4, len(site.render_site(self.root, check=True)))
        for filename, original in originals.items():
            self.assertEqual(original, (self.root / filename).read_bytes())
        self.assertEqual(4, len(site.render_site(self.root)))
        for lang in ("en", "ru"):
            for release_page in (False, True):
                source = self.page(lang, release_page).read_text()
                self.assertIn('"softwareVersion": "9.8.7"', source)
                self.assertIn(newer["assets"][0]["browser_download_url"], source)
                self.assertNotIn("latest.js", source)
                if release_page:
                    self.assertIn("9.8.7", source.split("</title>")[0])
                    self.assertEqual(2, source.count('class="release-download-card'))
                else:
                    self.assertEqual(2, source.count("v9.8.7 · Android 8.0+"))
        self.assertEqual([], site.render_site(self.root, check=True))

    def test_invalid_snapshot_never_overwrites_existing_html(self):
        for change in ({"draft": True}, {"prerelease": True}, {"tag_name": '<script>alert(1)</script>'}):
            with self.subTest(change=change):
                invalid = dict(self.release, **change)
                self.write_release(invalid)
                originals = {filename: (self.root / filename).read_bytes() for filename, _, _ in site.PAGES}
                with self.assertRaises(ValueError):
                    site.render_site(self.root)
                for filename, original in originals.items():
                    self.assertEqual(original, (self.root / filename).read_bytes())

    def test_foreign_or_wrong_version_downloads_are_rejected(self):
        for url in ("https://github.com.evil.example/file.apk", "https://github.com/elsewhere/repo/releases/download/1/file.apk", self.release["assets"][0]["browser_download_url"].replace(self.release["tag_name"], "0.0.1")):
            with self.subTest(url=url):
                invalid = copy.deepcopy(self.release)
                invalid["assets"][0]["browser_download_url"] = url
                with self.assertRaises(ValueError):
                    site.validate_release(invalid)

    def test_apk_and_positive_asset_sizes_are_required(self):
        invalid = copy.deepcopy(self.release)
        invalid["assets"][0]["size"] = 0
        with self.assertRaises(ValueError):
            site.validate_release(invalid)
        invalid["assets"] = [asset for asset in self.release["assets"] if asset["name"].endswith(".zip")]
        with self.assertRaises(ValueError):
            site.validate_release(invalid)

    def test_missing_region_leaves_other_pages_intact(self):
        page = self.page("ru", True)
        page.write_text(page.read_text().replace("<!-- END GENERATED NOTES -->", ""))
        originals = {filename: (self.root / filename).read_bytes() for filename, _, _ in site.PAGES}
        with self.assertRaises(ValueError):
            site.render_site(self.root)
        for filename, original in originals.items():
            self.assertEqual(original, (self.root / filename).read_bytes())

    def test_notes_are_localized_and_untrusted_markup_is_plain_text(self):
        release = dict(self.release, body='## English\n- <script>alert("x")</script>\n\n### Details\nText & more\n\n## Русский\n- Описание\n')
        english = site.render_notes(release, "en")
        russian = site.render_notes(release, "ru")
        self.assertIn("&lt;script&gt;", english)
        self.assertNotIn("<script>", english)
        self.assertNotIn("Описание", english)
        self.assertIn("Описание", russian)
        self.assertNotIn("alert", russian)
        self.assertIn('<details class="release-details"><summary>More release details</summary>', english)
        self.assertLess(english.index("<li>"), english.index("<details"))
        self.assertIn("Text &amp; more", english)

    def test_missing_translation_uses_a_localized_message(self):
        release = dict(self.release, body="## English\n- English only\n")
        russian = site.render_notes(release, "ru")
        self.assertIn(site.COPY["ru"]["missing_translation"], russian)
        self.assertNotIn("English only", russian)

    def test_empty_notes_use_a_localized_fallback(self):
        for body in (None, ""):
            for lang in ("en", "ru"):
                release = dict(self.release, body=body)
                site.validate_release(release)
                self.assertIn(site.COPY[lang]["no_notes"], site.render_notes(release, lang))

    def test_apk_only_release_does_not_advertise_a_zip(self):
        self.release["assets"] = [asset for asset in self.release["assets"] if asset["name"].endswith(".apk")]
        self.write_release(self.release)
        site.render_site(self.root)
        for lang in ("en", "ru"):
            source = self.page(lang, True).read_text()
            self.assertEqual(1, source.count('class="release-download-card'))
            self.assertNotIn('format-zip', source)
            self.assertNotIn("ZIP", site.Metadata(source).description)

    def test_main_headings_are_descriptive_and_language_links_remain_paired(self):
        for lang, heading in (("en", "Audiobook"), ("ru", "Плеер")):
            source = self.page(lang).read_text()
            self.assertIn('<h1 id="hero-title">' + heading, source)
            self.assertIn("Android.", source)
            self.assertIn('hreflang="en" href="' + site.BASE + '"', source)
            self.assertIn('hreflang="ru" href="' + site.BASE + 'ru/"', source)
            self.assertIn('"price": 0', source)
            self.assertNotIn('"aggregateRating"', source)


if __name__ == "__main__":
    unittest.main()
