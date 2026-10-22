# Static website updates

`stplayer/assets/latest-release.json` is the release snapshot used by the website.
After updating it, regenerate and check the tracked HTML from this repository:

```sh
python3 tools/render_site.py
python3 tools/render_site.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/tests -v
```

The renderer updates the English and Russian download pages, homepage APK links
and version labels, application structured data, and changed CSS/JS fingerprints.
It runs offline and does not publish, fetch releases, or modify Git state.
The generated HTML is served directly by GitHub Pages; run the renderer as part
of any release-snapshot update before publishing. `--check` writes nothing and
fails when the snapshot and HTML differ. Content outside the marked generated
regions remains editable in the HTML files.

Release notes stay in the original HTML. The main changes are visible immediately;
additional sections use a native HTML disclosure to keep the page compact.
