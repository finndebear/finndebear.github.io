(() => {
  'use strict';
  const repo = 'finndebear/finndebear.github.io';
  const api = `https://api.github.com/repos/${repo}`;
  const safeAsset = asset => {
    try {
      const url = new URL(asset.browser_download_url);
      return url.origin === 'https://github.com' && url.pathname.startsWith(`/${repo}/releases/download/`);
    } catch { return false; }
  };
  async function latest() {
    try {
      const response = await fetch(`${api}/releases/latest`, {signal: AbortSignal.timeout(8000), headers: {Accept: 'application/vnd.github+json'}});
      if (!response.ok) return;
      const release = await response.json();
      if (release.draft || release.prerelease || !Array.isArray(release.assets)) return;
      const apk = release.assets.find(asset => /\.apk$/i.test(asset.name) && safeAsset(asset));
      if (apk) {
        document.getElementById('apk-download').href = apk.browser_download_url;
        document.getElementById('download-label').textContent = 'Download APK';
        document.getElementById('version-label').textContent = `Version ${release.tag_name} · Android 8.0+ · ${(apk.size / 1048576).toFixed(1)} MB`;
      }
      const link = document.createElement('a');
      link.className = 'release-row';
      link.href = 'stplayer/latest/';
      for (const [className, text] of [['release-version', release.tag_name], ['release-name', release.name || 'STPlayer for Android'], ['release-date', 'APK · AAB · ZIP ↗']]) {
        const span = document.createElement('span');
        span.className = className;
        span.textContent = text;
        link.append(span);
      }
      document.getElementById('release-list').replaceChildren(link);
    } catch { /* The permanent latest-release page remains available without API access. */ }
  }
  if (new URLSearchParams(location.search).has('lang')) {
    location.replace(`privacy.html${location.search}${location.hash}`);
    return;
  }
  latest();
})();
