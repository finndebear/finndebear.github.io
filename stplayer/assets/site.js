(() => {
  'use strict';
  // Keep old, language-specific policy links working.
  if (new URLSearchParams(location.search).has('lang')) {
    location.replace(`/stplayer/privacy/${location.search}${location.hash}`);
    return;
  }
  const repo = 'finndebear/finndebear.github.io';
  async function latest() {
    try {
      const response = await fetch('assets/latest-release.json', {
        signal: AbortSignal.timeout(8000), cache: 'no-cache'
      });
      if (!response.ok) return;
      const release = await response.json();
      if (release.draft || release.prerelease || !Array.isArray(release.assets)) return;
      const apk = release.assets.find(asset => {
        try {
          const url = new URL(asset.browser_download_url);
          return /\.apk$/i.test(asset.name) && url.origin === 'https://github.com'
            && url.pathname.startsWith(`/${repo}/releases/download/`);
        } catch { return false; }
      });
      if (!apk) return;
      document.querySelectorAll('[data-apk-download]').forEach(link => { link.href = apk.browser_download_url; });
      document.querySelectorAll('[data-version-label]').forEach(label => {
        label.textContent = `v${release.tag_name.replace(/^v/i, '')} · Android 8.0+ · ${(apk.size / 1048576).toFixed(1)} MB`;
      });
    } catch { /* Static links still open the permanent latest-release page. */ }
  }
  latest();
})();
