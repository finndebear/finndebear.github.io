# Static website updates

`stplayer/assets/site.js` looks up the latest published stable release from the
public GitHub API on the English and Russian home/download pages. It refreshes APK
links, version and size captions, download cards, localized release notes and
application metadata. Publishing a new release needs no HTML or version-label
edits. When a release includes stable `stplayer.apk` / `stplayer.zip` aliases, those
are preferred without duplicating the versioned downloads.

The lookup is bounded to eight seconds. Invalid releases, drafts, prereleases and
foreign download URLs are rejected before updating the page. The checked-in release
snapshot remains available without JavaScript, offline or if GitHub rate-limits the
request. The download page also links directly to GitHub's latest release.

`stplayer/assets/latest-release.json` supplies that static fallback. To refresh the
fallback snapshot, regenerate and check the tracked HTML from this repository:

```sh
python3 tools/render_site.py
python3 tools/render_site.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/tests -v
```

The renderer updates the English and Russian download pages, homepage APK links
and version labels, application structured data, and changed CSS/JS fingerprints.
It runs offline and does not publish, fetch releases, or modify Git state.
The generated HTML is served directly by GitHub Pages. `--check` writes nothing and
fails when the snapshot and HTML differ. Content outside the marked generated
regions remains editable in the HTML files.

Release notes keep the main changes visible immediately; additional sections use a
native HTML disclosure to keep the page compact. Both the static renderer and the
runtime lookup render release-note markup as text.

Browser regression tests serve the real site locally and intercept the GitHub API.
With Python Playwright and its Chromium browser installed, run:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/browser_tests -v
```

These cover both languages, mobile layout, new releases, APK-only releases, stable
aliases, unsafe response data, unavailable GitHub and JavaScript-disabled fallback.
