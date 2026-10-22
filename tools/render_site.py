#!/usr/bin/env python3
"""Render the checked-in release snapshot into both language versions, offline."""

import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://finndebear.github.io/stplayer/"
PLAY_STORE = "https://play.google.com/store/apps/details?id=com.st.player"
RELEASE_PATH = "/finndebear/finndebear.github.io/releases/download/"
PAGES = (
    ("stplayer/index.html", "en", False),
    ("stplayer/ru/index.html", "ru", False),
    ("stplayer/latest/index.html", "en", True),
    ("stplayer/ru/latest/index.html", "ru", True),
)
COPY = {
    "en": {
        "version": "Version {version} · Android 8.0+",
        "title": "Download STPlayer {version} APK for Android",
        "description": "Download STPlayer {version} for Android 8.0+: {formats}. Free audiobook player for online catalogs, MP3, M4B and offline listening.",
        "subtitle": "The latest stable version. Free, with no ads or subscription.",
        "formats": {"apk": ("Android installer", "Install on your phone or tablet."), "zip": ("ZIP archive", "The archive supplied with this release.")},
        "download": "↓ Download",
        "more": "More release details",
        "no_notes": "No release notes were provided.",
        "missing_translation": "English release notes are not available for this version.",
        "source": "Source: GitHub release {version}",
    },
    "ru": {
        "version": "Версия {version} · Android 8.0+",
        "title": "Скачать STPlayer {version} APK для Android",
        "description": "Скачайте STPlayer {version} для Android 8.0+: {formats}. Бесплатный плеер аудиокниг: онлайн-каталоги, MP3, M4B и прослушивание без интернета.",
        "subtitle": "Последняя стабильная версия. Бесплатно, без рекламы и подписки.",
        "formats": {"apk": ("Установочный файл Android", "Установите на телефон или планшет."), "zip": ("ZIP-архив", "Архив из этого релиза.")},
        "download": "↓ Скачать",
        "more": "Подробности версии",
        "no_notes": "Описание версии не опубликовано.",
        "missing_translation": "Заметки на русском языке для этой версии пока недоступны.",
        "source": "Источник: релиз {version} на GitHub",
    },
}


def validate_release(release):
    if not isinstance(release, dict):
        raise ValueError("The release snapshot must be a JSON object")
    if release.get("draft") is not False or release.get("prerelease") is not False:
        raise ValueError("The snapshot must describe a published stable release")
    tag = release.get("tag_name", "")
    if not isinstance(tag, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", tag):
        raise ValueError("Invalid release tag")
    if (release.get("body") is not None and not isinstance(release["body"], str)) or not isinstance(release.get("assets"), list):
        raise ValueError("Invalid release body or asset list")
    assets = []
    for asset in release["assets"]:
        if not isinstance(asset, dict) or not isinstance(asset.get("name"), str):
            raise ValueError("Invalid release asset")
        name = asset.get("name", "")
        extension = Path(name).suffix.lower().lstrip(".")
        if extension not in ("apk", "zip"):
            continue
        url = urlsplit(asset.get("browser_download_url", ""))
        if (url.scheme != "https" or url.netloc != "github.com"
                or not url.path.startswith(RELEASE_PATH + tag + "/")
                or url.path.rsplit("/", 1)[-1] != name):
            raise ValueError("Download asset must belong to this public release: " + name)
        if type(asset.get("size")) is not int or asset["size"] <= 0:
            raise ValueError("Invalid asset size: " + name)
        assets.append(asset)
    if not any(asset["name"].lower().endswith(".apk") for asset in assets):
        raise ValueError("The stable release must contain an Android APK")
    return assets


def replace_once(source, pattern, replacement):
    result, count = re.subn(pattern, lambda match: replacement(match), source, flags=re.S)
    if count != 1:
        raise ValueError("Expected one editable region: " + pattern)
    return result


def replace_region(source, name, content):
    start, end = "<!-- BEGIN " + name + " -->", "<!-- END " + name + " -->"
    return replace_once(source, re.escape(start) + r".*?" + re.escape(end),
                        lambda _: start + "\n" + content + "\n" + end)


def language_notes(release, lang):
    lines = (release.get("body") or "").splitlines()
    languages = {"en": "english", "ru": "русский"}
    sections = [(i, match.group(1).lower()) for i, line in enumerate(lines)
                if (match := re.fullmatch(r"##\s+(English|Русский)\s*", line, re.I))]
    if not sections:
        return lines or [COPY[lang]["no_notes"]]
    for position, (start, language) in enumerate(sections):
        if language == languages[lang]:
            end = sections[position + 1][0] if position + 1 < len(sections) else len(lines)
            return lines[start + 1:end]
    return [COPY[lang]["missing_translation"]]


def render_markdown(lines):
    """Keep the release snapshot's existing heading/list/plain-text contract."""
    result, in_list = [], False
    for line in lines:
        bullet = re.match(r"^\s*[-*]\s+(.+)", line)
        if bullet:
            if not in_list:
                result.append("<ul>")
                in_list = True
            result.append("<li>" + html.escape(bullet.group(1)) + "</li>")
            continue
        if in_list:
            result.append("</ul>")
            in_list = False
        if not line.strip():
            continue
        heading = re.match(r"^#{1,6}\s+(.+)", line)
        tag, text = ("h3", heading.group(1)) if heading else ("p", line)
        result.append("<" + tag + ">" + html.escape(text) + "</" + tag + ">")
    if in_list:
        result.append("</ul>")
    return "\n".join(result)


def render_notes(release, lang):
    lines = language_notes(release, lang)
    first_heading = next((i for i, line in enumerate(lines) if re.match(r"^#{1,6}\s+", line)), len(lines))
    primary = render_markdown(lines[:first_heading])
    extra = render_markdown(lines[first_heading:])
    if primary and extra:
        notes = primary + '\n<details class="release-details"><summary>' + COPY[lang]["more"] + "</summary>\n" + extra + "\n</details>"
    else:
        notes = primary or extra or "<p>" + COPY[lang]["no_notes"] + "</p>"
    source = html.escape(COPY[lang]["source"].format(version=release["tag_name"]))
    url = "https://github.com/finndebear/finndebear.github.io/releases/tag/" + release["tag_name"]
    return notes + '\n<p class="small release-source"><a href="' + html.escape(url, quote=True) + '">' + source + '</a></p>'


def render_downloads(release, assets, lang):
    copy = COPY[lang]
    result = ['<p id="release-title" class="latest-subtitle" aria-live="polite">' + html.escape(copy["version"].format(version=release["tag_name"])) + "</p>",
              '<p class="muted">' + copy["subtitle"] + "</p>",
              '<div id="download-files" class="release-download-grid" aria-live="polite">']
    for extension, (title, description) in copy["formats"].items():
        for asset in assets:
            if not asset["name"].lower().endswith("." + extension):
                continue
            result.append('<article class="release-download-card format-' + extension + '">'
                          '<span class="download-format">' + extension.upper() + '</span>'
                          '<h2>' + title + '</h2><p>' + description + '</p>'
                          '<a class="button primary" href="' + html.escape(asset["browser_download_url"], quote=True) + '">'
                          + copy["download"] + " " + extension.upper() + '</a><p class="small">'
                          + html.escape(asset["name"]) + " · " + format(asset["size"] / 1048576, ".1f") + " MB</p></article>")
    return "\n".join(result + ["</div>"])


class Metadata(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.description = self.canonical = ""
        self.feed(source)

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if tag == "meta" and attributes.get("name") == "description":
            self.description = attributes["content"]
        if tag == "link" and attributes.get("rel") == "canonical":
            self.canonical = attributes["href"]


def render_schema(source, release, assets, lang, is_release):
    metadata = Metadata(source)
    expected_url = BASE + ("ru/" if lang == "ru" else "") + ("latest/" if is_release else "")
    if metadata.canonical != expected_url or not metadata.description:
        raise ValueError("Missing or inconsistent page metadata")
    apk = next(asset for asset in assets if asset["name"].lower().endswith(".apk"))
    app = {
        "@type": "SoftwareApplication", "@id": BASE + "#app",
        "name": "Stream Transport Player", "alternateName": "STPlayer",
        "description": metadata.description, "url": BASE,
        "image": BASE + "assets/stplayer-icon.png",
        "operatingSystem": "Android 8.0 or later", "applicationCategory": "MultimediaApplication",
        "softwareVersion": release["tag_name"].removeprefix("v"),
        "downloadUrl": apk["browser_download_url"], "installUrl": PLAY_STORE,
        "fileSize": str(apk["size"]) + " bytes",
        "releaseNotes": BASE + ("ru/" if lang == "ru" else "") + "latest/#notes-heading",
        "author": {"@type": "Person", "name": "Finn de Bear"}, "sameAs": PLAY_STORE,
        "offers": {"@type": "Offer", "price": 0, "priceCurrency": "USD", "url": PLAY_STORE},
    }
    graph = []
    if lang == "en" and not is_release:
        graph.append({"@type": "WebSite", "name": "STPlayer", "alternateName": "Stream Transport Player", "url": BASE})
    graph.extend([{"@type": "WebPage", "@id": expected_url + "#webpage", "url": expected_url,
                   "inLanguage": lang, "about": {"@id": app["@id"]}}, app])
    data = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2).replace("<", "\\u003c")
    return '<script type="application/ld+json">\n' + data + "\n</script>"


def render_site(root, check=False):
    release = json.loads((root / "stplayer/assets/latest-release.json").read_text(encoding="utf-8"))
    assets = validate_release(release)
    outputs = {}
    for filename, lang, is_release in PAGES:
        page = root / filename
        source = page.read_text(encoding="utf-8")
        if is_release:
            title = html.escape(COPY[lang]["title"].format(version=release["tag_name"]))
            has_zip = any(asset["name"].lower().endswith(".zip") for asset in assets)
            formats = ("APK installer or ZIP archive" if has_zip else "APK installer") if lang == "en" else ("APK или ZIP" if has_zip else "APK")
            description = html.escape(COPY[lang]["description"].format(version=release["tag_name"], formats=formats), quote=True)
            source = replace_once(source, r"<title>.*?</title>", lambda _: "<title>" + title + "</title>")
            for attribute, key, content in (("name", "description", description), ("property", "og:title", title), ("property", "og:description", description)):
                source = replace_once(source, r'<meta ' + attribute + '="' + key + r'" content="[^"]*">',
                                      lambda _, a=attribute, k=key, c=content: '<meta ' + a + '="' + k + '" content="' + c + '">')
            source = replace_region(source, "GENERATED RELEASE", render_downloads(release, assets, lang))
            source = replace_region(source, "GENERATED NOTES", render_notes(release, lang))
        else:
            apk = next(asset for asset in assets if asset["name"].lower().endswith(".apk"))
            source, count = re.subn(r'(<a\b[^>]*\bdata-apk-download\b[^>]*\bhref=")[^"]*(")',
                                    lambda m: m[1] + html.escape(apk["browser_download_url"], quote=True) + m[2], source)
            if count != 2:
                raise ValueError("Expected both homepage download links")
            label = "v" + release["tag_name"].removeprefix("v") + " · Android 8.0+ · " + format(apk["size"] / 1048576, ".1f") + " MB"
            source, count = re.subn(r'(<p\b[^>]*\bdata-version-label\b[^>]*>).*?(</p>)',
                                    lambda m: m[1] + html.escape(label) + m[2], source, flags=re.S)
            if count != 2:
                raise ValueError("Expected both homepage version labels")
        outputs[page] = replace_region(source, "GENERATED SCHEMA", render_schema(source, release, assets, lang, is_release))
    fingerprints = {name: hashlib.sha256((root / "stplayer/assets" / name).read_bytes()).hexdigest()[:12]
                    for name in ("site.css", "site.js")}
    for page in root.rglob("*.html"):
        source = outputs.get(page, page.read_text(encoding="utf-8"))
        for name, digest in fingerprints.items():
            source = re.sub(re.escape(name) + r"\?v=[a-f0-9]+", name + "?v=" + digest, source)
        outputs[page] = source
    changed = [page for page, content in outputs.items() if page.read_text(encoding="utf-8") != content]
    # Validate/render every page before the first write, so bad inputs leave all HTML intact.
    if not check:
        for page in changed:
            page.write_text(outputs[page], encoding="utf-8")
    return [str(page.relative_to(root)) for page in changed]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated HTML or asset fingerprints are stale; write nothing")
    args = parser.parse_args()
    try:
        changed = render_site(ROOT, check=args.check)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, "Site generation failed: " + str(error) + "\n")
    if args.check and changed:
        parser.exit(1, "Stale generated pages; run python3 tools/render_site.py:\n" + "\n".join(changed) + "\n")
    print(("Updated " + str(len(changed)) + " pages") if changed else "Static site is current")


if __name__ == "__main__":
    main()
