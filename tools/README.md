# Static website maintenance

Edit `tools/templates/*.html.in` and `stplayer/assets/locales.json` in this
repository’s `docs/` directory. The public GitHub Pages repository is a generated
snapshot; edits to generated HTML are replaced on the next render/publication.
The site has English, German, Spanish, Finnish, French, Japanese, Dutch,
Portuguese, Russian, Swedish and Turkish translations, plus Simplified Chinese.
All 12 languages have static home, guide and download pages, with reciprocal
language links and a generated sitemap. English retains `/stplayer/`; other
languages use `/stplayer/<code>/`. The existing privacy page supports all 12 via
`?lang=<code>`; its policy text remains at its original owner.

From the directory containing `stplayer/` (`docs/` in this checkout, or the root
of the public snapshot), run:

```sh
python3 tools/render_site.py
python3 tools/render_site.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/tests -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/browser_tests -v
```

Browser tests require Python Playwright and its Chromium browser. They serve real
local files and intercept GitHub release responses, including failures. Coverage
includes all languages, mobile and desktop layout, theme controls, language
navigation, new releases, APK-only releases, stable aliases, unsafe responses,
JavaScript-disabled fallback and privacy-page navigation.

`stplayer/assets/latest-release.json` is the verified public-release snapshot.
The renderer updates downloads, localized captions, release notes, application
structured data and local asset fingerprints. It runs offline, validates before
writing, and does not publish or modify Git state. `--check` writes nothing.

At runtime `site.js` checks GitHub’s latest stable release with an eight-second
limit. It rejects drafts, prereleases, foreign asset URLs and invalid sizes.
Stable `stplayer.apk` / `stplayer.zip` aliases are preferred without duplicate
cards. Static downloads and notes remain usable without JavaScript or the API.

English and Russian release notes come from the release body. Translated summaries
for the other ten languages live in `stplayer/assets/release-translations.json`.
They are bound to the release tag and SHA-256 of the exact UTF-8 release body;
changing either shows a localized missing-translation message, never stale notes.
Update the summaries and digest when publishing another release. Full original
notes are linked on GitHub. Untrusted release text is rendered as text.

The hero uses the app icon and decorative sound waves. The icon is served as a
smaller WebP; the original PNG remains available for external links and social
references. Social previews use `stplayer-social.png`, the existing STPlayer
store feature graphic (1024 × 500), with explicit Open Graph dimensions and a
large Twitter card. It is metadata only and is not downloaded to render the page.
After changing a shared image, use the Facebook Sharing Debugger to refresh its
cached preview; fetching with a crawler User-Agent does not refresh Meta's cache.
Language flags match STPlayer Settings (including UK English and
Portuguese from Portugal). No external fonts or UI framework are required.

Publication remains a separate step. The mirror publisher exports only tracked
public files, writes metadata after asset verification and runs the renderer.
Local previews and test results do not establish deployment or search ranking.

After publishing new or changed pages, notify IndexNow participants (including
Bing and Yandex) once for the entire generated sitemap:

```sh
python3 tools/notify_indexnow.py
python3 tools/notify_indexnow.py --submit
```

The first command is an offline dry run. Submission checks the deployed sitemap
and public ownership challenge (`indexnow.txt`) before sending. HTTP 200 means
received, and 202 means ownership validation is pending; neither proves indexing.
Google uses Search Console and the sitemap separately. Do not repeatedly submit
unchanged pages. See the [IndexNow protocol](https://www.indexnow.org/documentation).

Google Play badges are unmodified localized SVGs from the official
[Partner Marketing Hub digital SVG collection](https://partnermarketinghub.withgoogle.com/brands/google-play/google-play/lockups-icons-badges/?folder=86718).
The site uses the Portugal and Simplified Chinese variants, matching its language
choices. All badges are served locally at a 40 px height; RuStore follows Google
Play on the Russian download page. Download pages omit the redundant header
link to themselves; home and guide pages retain the download link.
