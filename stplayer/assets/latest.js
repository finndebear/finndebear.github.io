(async () => {
  'use strict';
  const repo = 'finndebear/finndebear.github.io';
  const files = document.getElementById('download-files');
  try {
    const response = await fetch('../assets/latest-release.json', {
      signal: AbortSignal.timeout(8000), cache: 'no-cache'
    });
    if (!response.ok) throw new Error('Release unavailable');
    const release = await response.json();
    if (release.draft || release.prerelease || !Array.isArray(release.assets)) throw new Error('No stable release');
    document.getElementById('release-title').textContent = `Version ${release.tag_name} · Android 8.0+`;
    document.title = `Stream Transport Player ${release.tag_name} — Latest release`;
    const fragment = document.createDocumentFragment();
    const formats = {apk: ['Android installer', 'Install on your phone or tablet.'], zip: ['ZIP archive', 'The archive supplied with this release.']};
    for (const [extension, [title, description]] of Object.entries(formats)) {
      for (const asset of release.assets.filter(item => item.name.toLowerCase().endsWith(`.${extension}`))) {
        const url = new URL(asset.browser_download_url);
        if (url.origin !== 'https://github.com' || !url.pathname.startsWith(`/${repo}/releases/download/`)) continue;
        const card = document.createElement('article');
        card.className = `release-download-card format-${extension}`;
        const format = document.createElement('span');
        format.className = 'download-format';
        format.textContent = extension.toUpperCase();
        const heading = document.createElement('h2');
        heading.textContent = title;
        const text = document.createElement('p');
        text.textContent = description;
        const button = document.createElement('a');
        button.className = 'button primary';
        button.href = url.href;
        button.textContent = `↓ Download ${extension.toUpperCase()}`;
        const size = document.createElement('p');
        size.className = 'small';
        size.textContent = `${asset.name} · ${(asset.size / 1048576).toFixed(1)} MB`;
        card.append(format, heading, text, button, size);
        fragment.append(card);
      }
    }
    if (!fragment.childNodes.length) throw new Error('No download files');
    files.replaceChildren(fragment);
    // Render release text as DOM text, never as remote HTML.
    const notes = document.createDocumentFragment();
    let list;
    for (const line of (release.body || 'No release notes were provided.').split('\n')) {
      const bullet = line.match(/^\s*[-*]\s+(.+)/);
      if (bullet) {
        if (!list) { list = document.createElement('ul'); notes.append(list); }
        const item = document.createElement('li');
        item.textContent = bullet[1];
        list.append(item);
      } else {
        list = null;
        if (!line.trim()) continue;
        const heading = line.match(/^#{1,6}\s+(.+)/);
        const element = document.createElement(heading ? 'h3' : 'p');
        element.textContent = heading ? heading[1] : line;
        notes.append(element);
      }
    }
    document.getElementById('release-notes').replaceChildren(notes);
  } catch {
    files.replaceChildren();
    const message = document.createElement('p');
    message.textContent = 'Download details could not be loaded. Use the GitHub link below to get the latest files.';
    files.append(message);
  }
})();
