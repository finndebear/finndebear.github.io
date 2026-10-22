(() => {
  'use strict';
  // Keep old, language-specific policy links working.
  if (/\/stplayer\/(?:index\.html)?$/.test(location.pathname) && new URLSearchParams(location.search).has('lang')) {
    location.replace(`/stplayer/privacy/${location.search}${location.hash}`);
    return;
  }
  if (!document.querySelector('[data-apk-download], #download-files')) return;

  const repository = 'finndebear/finndebear.github.io';
  const russian = document.documentElement.lang === 'ru';
  const copy = russian ? {
    version: 'Версия', download: '↓ Скачать', more: 'Подробности версии', source: 'Источник: релиз',
    empty: 'Описание версии не опубликовано.', missing: 'Заметки на русском языке для этой версии пока недоступны.',
    apk: ['Установочный файл Android', 'Установите на телефон или планшет.'],
    zip: ['ZIP-архив', 'Архив из этого релиза.']
  } : {
    version: 'Version', download: '↓ Download', more: 'More release details', source: 'Source: GitHub release',
    empty: 'No release notes were provided.', missing: 'English release notes are not available for this version.',
    apk: ['Android installer', 'Install on your phone or tablet.'],
    zip: ['ZIP archive', 'The archive supplied with this release.']
  };
  const element = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const size = asset => `${(asset.size / 1048576).toFixed(1)} MB`;

  function releaseAssets(release) {
    if (release.draft !== false || release.prerelease !== false || typeof release.tag_name !== 'string' ||
        !/^[A-Za-z0-9][A-Za-z0-9._+-]*$/.test(release.tag_name) ||
        !Array.isArray(release.assets) || (release.body != null && typeof release.body !== 'string')) {
      throw new Error('Invalid stable release');
    }
    const assets = release.assets.filter(asset => /\.(apk|zip)$/i.test(asset.name));
    for (const asset of assets) {
      const expected = `https://github.com/${repository}/releases/download/${release.tag_name}/${asset.name}`;
      if (asset.browser_download_url !== expected || !Number.isSafeInteger(asset.size) || asset.size <= 0 ||
          !/^[A-Za-z0-9._+-]+$/.test(asset.name)) throw new Error('Invalid release asset');
    }
    const formats = ['apk', 'zip'].map(format =>
      assets.find(asset => asset.name === `stplayer.${format}`) ||
      assets.find(asset => asset.name.toLowerCase().endsWith(`.${format}`))
    ).filter(Boolean);
    if (!formats.some(asset => asset.name.toLowerCase().endsWith('.apk'))) throw new Error('Missing APK');
    return formats.map(asset => /^stplayer\.(apk|zip)$/.test(asset.name)
      ? { ...asset, browser_download_url: `https://github.com/${repository}/releases/latest/download/${asset.name}` }
      : asset);
  }

  function releaseNotes(body) {
    let lines = (body || '').split(/\r?\n/);
    const sections = lines.flatMap((line, index) => {
      const match = /^##\s+(English|Русский)\s*$/i.exec(line);
      return match ? [{ index, language: match[1].toLowerCase() }] : [];
    });
    if (sections.length) {
      const index = sections.findIndex(section => section.language === (russian ? 'русский' : 'english'));
      lines = index < 0 ? [copy.missing] : lines.slice(sections[index].index + 1, sections[index + 1]?.index);
    }
    const fragment = document.createDocumentFragment();
    let parent = fragment, list = null, details = null;
    for (const line of lines) {
      if (!line.trim()) { list = null; continue; }
      const heading = /^#{1,6}\s+(.+)/.exec(line);
      if (heading && !details && fragment.childNodes.length) {
        details = element('details', undefined, 'release-details');
        details.append(element('summary', copy.more));
        fragment.append(details);
        parent = details;
      }
      const bullet = /^\s*[-*]\s+(.+)/.exec(line);
      if (bullet) {
        if (!list) { list = element('ul'); parent.append(list); }
        list.append(element('li', bullet[1]));
      } else {
        list = null;
        parent.append(element(heading ? 'h3' : 'p', heading ? heading[1] : line));
      }
    }
    if (!fragment.childNodes.length) fragment.append(element('p', copy.empty));
    return fragment;
  }

  function displayRelease(release, assets) {
    const apk = assets[0];
    document.querySelectorAll('[data-apk-download]').forEach(link => { link.href = apk.browser_download_url; });
    document.querySelectorAll('[data-version-label]').forEach(label => {
      label.textContent = `v${release.tag_name.replace(/^v/, '')} · Android 8.0+ · ${size(apk)}`;
    });
    const downloads = document.getElementById('download-files');
    if (downloads) {
      const cards = assets.map(asset => {
        const format = asset.name.split('.').pop().toLowerCase();
        const card = element('article', undefined, `release-download-card format-${format}`);
        const link = element('a', `${copy.download} ${format.toUpperCase()}`, 'button primary');
        link.href = asset.browser_download_url;
        card.append(element('span', format.toUpperCase(), 'download-format'), element('h2', copy[format][0]),
          element('p', copy[format][1]), link, element('p', `${asset.name} · ${size(asset)}`, 'small'));
        return card;
      });
      const notes = releaseNotes(release.body);
      const source = element('p', undefined, 'small release-source');
      const sourceLink = element('a', `${copy.source} ${release.tag_name}${russian ? ' на GitHub' : ''}`);
      sourceLink.href = `https://github.com/${repository}/releases/tag/${release.tag_name}`;
      source.append(sourceLink);
      notes.append(source);
      downloads.replaceChildren(...cards);
      document.getElementById('release-title').textContent = `${copy.version} ${release.tag_name} · Android 8.0+`;
      document.getElementById('release-notes').replaceChildren(notes);
      document.title = russian ? `Скачать STPlayer ${release.tag_name} APK для Android` : `Download STPlayer ${release.tag_name} APK for Android`;
      const formats = russian ? (assets.length > 1 ? 'APK или ZIP' : 'APK') : (assets.length > 1 ? 'APK installer or ZIP archive' : 'APK installer');
      const description = russian
        ? `Скачайте STPlayer ${release.tag_name} для Android 8.0+: ${formats}. Бесплатный плеер аудиокниг: онлайн-каталоги, MP3, M4B и прослушивание без интернета.`
        : `Download STPlayer ${release.tag_name} for Android 8.0+: ${formats}. Free audiobook player for online catalogs, MP3, M4B and offline listening.`;
      document.querySelector('meta[name="description"]').content = description;
      document.querySelector('meta[property="og:description"]').content = description;
      document.querySelector('meta[property="og:title"]').content = document.title;
    }
    document.querySelectorAll('script[type="application/ld+json"]').forEach(script => {
      const schema = JSON.parse(script.textContent);
      for (const node of schema['@graph'] || []) {
        if (node['@type'] !== 'SoftwareApplication') continue;
        node.softwareVersion = release.tag_name.replace(/^v/, '');
        node.downloadUrl = apk.browser_download_url;
        node.fileSize = `${apk.size} bytes`;
        node.description = document.querySelector('meta[name="description"]').content;
      }
      script.textContent = JSON.stringify(schema).replace(/</g, '\\u003c');
    });
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);
  fetch(`https://api.github.com/repos/${repository}/releases/latest`, { signal: controller.signal })
    .then(response => {
      if (!response.ok) throw new Error('Release lookup failed');
      return response.json();
    })
    .then(release => displayRelease(release, releaseAssets(release)))
    // The checked-in release remains usable offline or when GitHub rate-limits requests.
    .catch(() => {})
    .finally(() => clearTimeout(timeout));
})();
