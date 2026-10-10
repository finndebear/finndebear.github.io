(() => {
  'use strict';
  const repo = 'finndebear/stplayer';
  const base = `https://github.com/${repo}`;
  const api = `https://api.github.com/repos/${repo}`;
  const releaseURL = tag => `${base}/releases/tag/${encodeURIComponent(tag)}`;
  const safeAsset = asset => {
    try {
      const url = new URL(asset.browser_download_url);
      return url.origin === 'https://github.com' && url.pathname.startsWith(`/${repo}/releases/download/`);
    } catch { return false; }
  };
  async function get(path) {
    const response = await fetch(`${api}${path}`, {signal: AbortSignal.timeout(8000), headers: {Accept: 'application/vnd.github+json'}});
    if (!response.ok) throw new Error('Release metadata unavailable');
    return response.json();
  }
  async function latest() {
    try {
      const release = await get('/releases/latest');
      if (release.draft || release.prerelease || !Array.isArray(release.assets)) return;
      const apk = release.assets.find(asset => /\.apk$/i.test(asset.name) && safeAsset(asset));
      if (!apk) return;
      document.getElementById('apk-download').href = apk.browser_download_url;
      document.getElementById('download-label').textContent = 'Download APK';
      document.getElementById('version-label').textContent = `Version ${release.tag_name} · Android 8.0+ · ${(apk.size / 1048576).toFixed(1)} MB`;
    } catch { /* The permanent GitHub Releases link also works without API access. */ }
  }
  async function history() {
    try {
      const releases = await get('/releases?per_page=10');
      const published = releases.filter(item => !item.draft && !item.prerelease).slice(0, 3);
      if (!published.length) return;
      const fragment = document.createDocumentFragment();
      for (const release of published) {
        const link = document.createElement('a');
        link.className = 'release-row';
        link.href = releaseURL(release.tag_name);
        const version = document.createElement('span');
        version.className = 'release-version';
        version.textContent = release.tag_name;
        const name = document.createElement('span');
        name.className = 'release-name';
        name.textContent = `${release.name || 'Release notes'} ↗`;
        const date = document.createElement('time');
        date.className = 'release-date';
        date.dateTime = release.published_at;
        date.textContent = new Date(release.published_at).toLocaleDateString('en-GB', {day: 'numeric', month: 'short', year: 'numeric'});
        link.append(version, name, date);
        fragment.append(link);
      }
      document.getElementById('release-list').replaceChildren(fragment);
    } catch { /* Keep the accessible static fallback, including when GitHub rate-limits. */ }
  }
  // Preserve existing privacy links such as /?lang=ru from the previous site.
  if (new URLSearchParams(location.search).has('lang')) {
    location.replace(`privacy.html${location.search}${location.hash}`);
    return;
  }
  latest();
  history();
})();
