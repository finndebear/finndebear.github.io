(() => {
  'use strict';
  const key = 'stplayer-theme';
  const preference = window.matchMedia('(prefers-color-scheme: dark)');
  let chosen;
  try { chosen = localStorage.getItem(key); } catch { /* Storage can be disabled. */ }
  if (chosen !== 'dark' && chosen !== 'light') chosen = null;
  const apply = () => {
    const theme = chosen || (preference.matches ? 'dark' : 'light');
    document.documentElement.dataset.theme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#071426' : '#f7fafc');
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      const label = `Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`;
      button.setAttribute('aria-label', label);
      button.title = label;
    });
  };
  // Run before styles load to avoid a flash of the wrong theme.
  apply();
  preference.addEventListener('change', apply);
  window.addEventListener('storage', event => {
    if (event.key === key || event.key === null) {
      chosen = event.newValue === 'dark' || event.newValue === 'light' ? event.newValue : null;
      apply();
    }
  });
  document.addEventListener('DOMContentLoaded', () => {
    apply();
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.addEventListener('click', () => {
        chosen = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
        try { localStorage.setItem(key, chosen); } catch { /* The current page still switches. */ }
        apply();
      });
    });
  });
})();
