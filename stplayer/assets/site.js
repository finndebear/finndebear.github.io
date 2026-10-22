(() => {
  'use strict';
  // Keep old, language-specific policy links working.
  if (/\/stplayer\/(?:index\.html)?$/.test(location.pathname) && new URLSearchParams(location.search).has('lang')) {
    location.replace(`/stplayer/privacy/${location.search}${location.hash}`);
    return;
  }
})();
