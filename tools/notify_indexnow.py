#!/usr/bin/env python3
"""Notify IndexNow participants of the published sitemap; dry-run by default."""
import argparse
import json
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from render_site import ROOT, SITE_ROOT


def payload(root=ROOT):
    key = (root / 'indexnow.txt').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'[a-zA-Z0-9-]{8,128}', key):
        raise ValueError('Invalid IndexNow key')
    urls = [node.text for node in ET.parse(root / 'sitemap.xml').iter(
        '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    if not 1 <= len(urls) <= 10000 or len(set(urls)) != len(urls):
        raise ValueError('Expected 1–10000 distinct sitemap URLs')
    for url in urls:
        parsed = urlsplit(url or '')
        if not url or not url.startswith(SITE_ROOT) or parsed.query or parsed.fragment:
            raise ValueError('Sitemap URLs must belong to this HTTPS site without query or fragment')
    return dict(host=urlsplit(SITE_ROOT).netloc, key=key,
                keyLocation=SITE_ROOT + 'indexnow.txt', urlList=urls)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--submit', action='store_true', help='Send after verifying the public key and sitemap')
    args = parser.parse_args()
    data = payload()
    if not args.submit:
        print(json.dumps(data, indent=2))
        return
    with urlopen(data['keyLocation'], timeout=20) as response:
        if response.read().decode('utf-8').strip() != data['key']:
            raise ValueError('Published IndexNow key does not match')
    with urlopen(SITE_ROOT + 'sitemap.xml', timeout=20) as response:
        published = [node.text for node in ET.fromstring(response.read()).iter(
            '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        if published != data['urlList']:
            raise ValueError('Published sitemap does not match; deploy before submitting')
    request = Request('https://api.indexnow.org/indexnow', data=json.dumps(data).encode('utf-8'),
                      headers={'Content-Type': 'application/json; charset=utf-8'})
    with urlopen(request, timeout=30) as response:
        if response.status not in (200, 202):
            raise RuntimeError(f'Unexpected IndexNow status: {response.status}')
        print(f'HTTP {response.status}: {len(published)} URLs received; indexing is not guaranteed.')
        if response.status == 202:
            print('Ownership validation is pending.')


if __name__ == '__main__':
    main()
