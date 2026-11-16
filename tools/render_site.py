#!/usr/bin/env python3
"""Render the checked-in release snapshot into all supported language versions, offline."""

import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from string import Template


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://finndebear.github.io/stplayer/"
SITE_ROOT = BASE.removesuffix("stplayer/")
PLAY_STORE = "https://play.google.com/store/apps/details?id=com.st.player"
RELEASE_PATH = "/finndebear/finndebear.github.io/releases/download/"
LANGUAGES = ("en", "de", "es", "fi", "fr", "ja", "nl", "pt", "ru", "sv", "tr", "zh")
LOCALES = json.loads((ROOT / "stplayer/assets/locales.json").read_text())


def language_path(lang):
    return "" if lang == "en" else lang + "/"


PAGES = tuple(("stplayer/" + language_path(lang) + ("latest/" if latest else "") + "index.html", lang, latest)
              for lang in LANGUAGES for latest in (False, True))
COPY = {lang: dict(version=d["version"], title=d["downloadPageTitle"], description=d["downloadPageDescription"],
                   subtitle=d["downloadSubtitle"], formats={"apk": (d["apkTitle"], d["apkBody"]),
                   "zip": (d["zipTitle"], d["zipBody"])}, download=d["downloadVerb"], more=d["releaseMore"],
                   no_notes=d["noNotes"], missing_translation=d["missingNotes"], source=d["source"])
        for lang, d in LOCALES.items()}


def runtime_copy(lang):
    d = LOCALES[lang]
    return dict(version=d["version"], download=d["downloadVerb"], more=d["releaseMore"], source=d["source"],
                empty=d["noNotes"], missing=d["missingNotes"], apk=[d["apkTitle"], d["apkBody"]],
                zip=[d["zipTitle"], d["zipBody"]], title=d["downloadPageTitle"], description=d["downloadPageDescription"],
                summary=d["translatedSummary"])


def render_layouts(root):
    templates = {kind: Template((root / ("tools/templates/" + kind + ".html.in")).read_text())
                 for kind in ("base", "home", "guide", "latest")}
    analytics = (root / "tools/templates/analytics.html.in").read_text()
    release = json.loads((root / "stplayer/assets/latest-release.json").read_text())
    translated = json.loads((root / "stplayer/assets/release-translations.json").read_text())
    translation_matches = (release["tag_name"] == translated["tag"] and
                           hashlib.sha256((release.get("body") or "").encode()).hexdigest() == translated["bodySha256"])
    outputs = {}
    regions = {"en": "en_US", "de": "de_DE", "es": "es_ES", "fi": "fi_FI", "fr": "fr_FR", "ja": "ja_JP",
               "nl": "nl_NL", "pt": "pt_BR", "ru": "ru_RU", "sv": "sv_SE", "tr": "tr_TR", "zh": "zh_CN"}
    for lang in LANGUAGES:
        d = LOCALES[lang]
        if set(d) != set(LOCALES["en"]) or any(not isinstance(v, str) or not v.strip() for v in d.values()):
            raise ValueError("Incomplete locale: " + lang)
        for kind, suffix in (("home", ""), ("guide", "audiobooks/"), ("latest", "latest/")):
            base = "/stplayer/" + language_path(lang)
            canonical = BASE + language_path(lang) + suffix
            v = {k: html.escape(value, quote=True) for k, value in d.items()}
            v.update(lang=lang, homeUrl=base, guideUrl=base + "audiobooks/", latestUrl=base + "latest/",
                     assets="../" * ((lang != "en") + (kind != "home")) + "assets", canonical=canonical,
                     pageTitle=v[{"home": "homeTitle", "guide": "guideTitle", "latest": "downloadPageTitle"}[kind]],
                     pageDescription=v[{"home": "homeDescription", "guide": "guideDescription", "latest": "downloadPageDescription"}[kind]],
                     analytics=analytics, ogLocale=regions[lang], headerClass="release-header" if kind == "latest" else "")
            v["alternates"] = "\n".join('<link rel="alternate" hreflang="' + code + '" href="' + BASE + language_path(code) + suffix + '">'
                                         for code in LANGUAGES) + '\n<link rel="alternate" hreflang="x-default" href="' + BASE + suffix + '">'
            links = ''.join('<a href="/stplayer/' + language_path(code) + suffix + '" lang="' + code + '" hreflang="' + code + '"' +
                            (' aria-current="page"' if code == lang else '') + '>' + '<span aria-hidden="true">' + LOCALES[code]['flag'] + '</span> ' + html.escape(LOCALES[code]["name"]) + '</a>' for code in LANGUAGES)
            v["languagePicker"] = '<details class="language-picker"><summary aria-label="' + v["language"] + ' — ' + v["name"] + '">' + '<span aria-hidden="true">' + d['flag'] + '</span></summary><nav class="language-options" aria-label="' + v["language"] + '">' + links + '</nav></details>'
            v["extraStyles"] = '<link rel="stylesheet" href="' + v["assets"] + '/guide.css">' if kind == "guide" else ''
            v["downloadNavigation"] = ('<a class="nav-download" href="' + v["latestUrl"] + '">' + v["download"] + ' <span aria-hidden="true">↗</span></a>') if kind != "latest" else ''
            v["stores"] = ''
            if kind == "latest":
                badge = '<img src="' + v["assets"] + '/google-play-badge-' + lang + '.svg" height="40" alt="Google Play">'
                v["stores"] = '<div class="store-links"><a class="play-store-link" href="' + PLAY_STORE + '">' + badge + '</a>'
                if lang == "ru":
                    v["stores"] += '<a class="rustore-link" href="https://www.rustore.ru/catalog/app/com.st.player"><img src="' + v["assets"] + '/rustore-badge.svg" height="40" alt="RuStore"></a>'
                v["stores"] += '</div>'
            v["runtime"] = ''
            if kind != "guide":
                data = runtime_copy(lang)
                data["translation"] = dict(tag=translated["tag"], bodySha256=translated["bodySha256"],
                                           notes=translated["translations"][lang]) if translation_matches and lang not in ("en", "ru") else None
                v["runtime"] = '<script id="release-copy" type="application/json">' + json.dumps(data, ensure_ascii=False).replace('<', '\\u003c') + '</script>\n<script src="' + v["assets"] + '/site.js" defer></script>'
            v["body"] = templates[kind].substitute(v)
            outputs[root / ("stplayer/" + language_path(lang) + suffix + "index.html")] = templates["base"].substitute(v)
    return outputs



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
        expected_url = "https://github.com" + RELEASE_PATH + tag + "/" + name
        if (not re.fullmatch(r"[A-Za-z0-9._+-]+", name)
                or asset.get("browser_download_url") != expected_url):
            raise ValueError("Download asset must belong to this public release: " + name)
        if type(asset.get("size")) is not int or asset["size"] <= 0:
            raise ValueError("Invalid asset size: " + name)
        assets.append(asset)
    if not any(asset["name"].lower().endswith(".apk") for asset in assets):
        raise ValueError("The stable release must contain an Android APK")
    # Match the runtime picker: publish one card per format, preferring stable
    # aliases even when GitHub returns the versioned assets first. All static
    # consumers (cards, homepage links and schema) receive this same selection.
    selected = []
    for extension in ("apk", "zip"):
        matching = [asset for asset in assets if asset["name"].lower().endswith("." + extension)]
        if not matching:
            continue
        preferred = next((asset for asset in matching if asset["name"] == "stplayer." + extension), matching[0])
        if preferred["name"] == "stplayer." + extension:
            preferred = dict(preferred, browser_download_url=(
                "https://github.com/finndebear/finndebear.github.io/releases/latest/download/" + preferred["name"]))
        selected.append(preferred)
    return selected


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
    if lang not in ("en", "ru"):
        translated = json.loads((ROOT / "stplayer/assets/release-translations.json").read_text())
        digest = hashlib.sha256((release.get("body") or "").encode()).hexdigest()
        if release["tag_name"] == translated["tag"] and digest == translated["bodySha256"]:
            return [LOCALES[lang]["translatedSummary"]] + ["- " + note for note in translated["translations"][lang]]
        return [COPY[lang]["missing_translation"]]
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


def site_identity():
    return {"@type": "WebSite", "@id": SITE_ROOT + "#website", "name": "STPlayer",
            "alternateName": "Stream Transport Player", "url": SITE_ROOT}


def render_schema(source, release, assets, lang, is_release):
    metadata = Metadata(source)
    expected_url = BASE + language_path(lang) + ("latest/" if is_release else "")
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
        "releaseNotes": BASE + language_path(lang) + "latest/#notes-heading",
        "author": {"@type": "Person", "name": "Finn de Bear"}, "sameAs": PLAY_STORE,
        "offers": {"@type": "Offer", "price": 0, "priceCurrency": "USD", "url": PLAY_STORE},
    }
    graph = []
    if lang == "en" and not is_release:
        graph.append(site_identity())
    graph.extend([{"@type": "WebPage", "@id": expected_url + "#webpage", "url": expected_url,
                   "inLanguage": lang, "about": {"@id": app["@id"]}}, app])
    data = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2).replace("<", "\\u003c")
    return '<script type="application/ld+json">\n' + data + "\n</script>"


def render_site(root, check=False):
    release = json.loads((root / "stplayer/assets/latest-release.json").read_text(encoding="utf-8"))
    assets = validate_release(release)
    outputs = render_layouts(root)
    identity = json.dumps({"@context": "https://schema.org", **site_identity()}, ensure_ascii=False, indent=2)
    outputs[root / "index.html"] = replace_region((root / "index.html").read_text(), "GENERATED SITE IDENTITY",
                                                 '<script type="application/ld+json">\n' + identity + '\n</script>')
    for filename, lang, is_release in PAGES:
        page = root / filename
        source = outputs[page]
        if is_release:
            title = html.escape(COPY[lang]["title"].format(version=release["tag_name"]))
            has_zip = any(asset["name"].lower().endswith(".zip") for asset in assets)
            formats = "APK / ZIP" if has_zip else "APK"
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
    for page in (root / "stplayer").rglob("*.html"):
        outputs.setdefault(page, page.read_text(encoding="utf-8"))
    privacy = root / "stplayer/privacy/index.html"
    if privacy in outputs:
        source = outputs[privacy]
        controls = {code: {key: LOCALES[code][key] for key in ("themeLight", "themeDark")} for code in LANGUAGES}
        block = '<script id="privacy-copy" type="application/json">' + json.dumps(controls, ensure_ascii=False).replace('<', '\\u003c') + '</script>'
        source = re.sub(r'<script id="privacy-copy".*?</script>\n?', '', source, flags=re.S)
        outputs[privacy] = source.replace('</head>', block + '\n</head>')
    for page, source in list(outputs.items()):
        if "/audiobooks/" in str(page):
            url = Metadata(source).canonical
            graph = {"@context": "https://schema.org", "@type": "WebPage", "url": url,
                     "inLanguage": source.split('<html lang="', 1)[1].split('"', 1)[0], "about": {"@id": BASE + "#app"}}
            source = replace_region(source, "GENERATED SCHEMA", '<script type="application/ld+json">' + json.dumps(graph, ensure_ascii=False).replace('<', '\\u003c') + '</script>')
        def fingerprint(match):
            asset = (page.parent / match[2]).resolve()
            if not asset.is_relative_to(root.resolve()) or not asset.is_file():
                raise ValueError("Missing local asset: " + match[2])
            digest = hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
            return match[1] + match[2] + '?v=' + digest + '"'
        outputs[page] = re.sub(r'(\b(?:src|href)=")((?:\.\./)*assets/[^"?]+)(?:\?[^" ]*)?"', fingerprint, source)
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for lang in LANGUAGES:
        for suffix in ("", "audiobooks/", "latest/"):
            sitemap += '  <url><loc>' + BASE + language_path(lang) + suffix + '</loc></url>\n'
    outputs[root / "sitemap.xml"] = sitemap + '  <url><loc>' + BASE + 'privacy/</loc></url>\n</urlset>\n'
    changed = [page for page, content in outputs.items() if not page.is_file() or page.read_text(encoding="utf-8") != content]
    # Validate/render every page before the first write, so bad inputs leave all HTML intact.
    if not check:
        for page in changed:
            page.parent.mkdir(parents=True, exist_ok=True)
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
