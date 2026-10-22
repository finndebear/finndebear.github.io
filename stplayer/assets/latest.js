(async () => {
  'use strict';
  const repo = 'finndebear/finndebear.github.io';
  const files = document.getElementById('download-files');
  const russian = document.documentElement.lang === 'ru';
  try {
    const response = await fetch(new URL('latest-release.json', document.currentScript.src), {
      signal: AbortSignal.timeout(8000), cache: 'no-cache'
    });
    if (!response.ok) throw new Error('Release unavailable');
    const release = await response.json();
    if (release.draft || release.prerelease || !Array.isArray(release.assets)) throw new Error('No stable release');
    document.getElementById('release-title').textContent = russian
      ? `Версия ${release.tag_name} · Android 8.0+` : `Version ${release.tag_name} · Android 8.0+`;
    document.title = russian
      ? `Скачать STPlayer ${release.tag_name}: APK и ZIP | Android`
      : `Download STPlayer ${release.tag_name} APK & ZIP | Android`;
    const fragment = document.createDocumentFragment();
    const formats = russian
      ? {apk: ['Установочный файл Android', 'Установите на телефон или планшет.'], zip: ['ZIP-архив', 'Архив из этого релиза.']}
      : {apk: ['Android installer', 'Install on your phone or tablet.'], zip: ['ZIP archive', 'The archive supplied with this release.']};
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
        button.textContent = `${russian ? '↓ Скачать' : '↓ Download'} ${extension.toUpperCase()}`;
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
    const body = release.body || (russian ? 'Описание версии не опубликовано.' : 'No release notes were provided.');
    const allLines = body.split('\n');
    const languageHeading = /^##\s+(English|Русский)\s*$/i;
    const preferredLanguage = russian ? 'русский' : 'english';
    const sectionStart = allLines.findIndex(line => languageHeading.exec(line)?.[1].toLowerCase() === preferredLanguage);
    let noteLines = allLines;
    if (sectionStart >= 0) {
      const nextSection = allLines.findIndex((line, index) => index > sectionStart && /^##\s+/.test(line));
      noteLines = allLines.slice(sectionStart + 1, nextSection < 0 ? undefined : nextSection);
    } else if (allLines.some(line => languageHeading.test(line))) {
      noteLines = [russian
        ? 'Заметки на русском языке для этой версии пока недоступны.'
        : 'English release notes are not available for this version.'];
    }
    for (const line of noteLines) {
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
    message.textContent = russian
      ? 'Не удалось загрузить сведения о файлах. Откройте ссылку на GitHub ниже.'
      : 'Download details could not be loaded. Use the GitHub link below to get the latest files.';
    files.append(message);
  }
})();
