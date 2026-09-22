/* Shared by the site, editor shell, and same-origin guide iframe. */
(() => {
  const key = 'tryslang-theme';
  const read = () => {
    try { return localStorage.getItem(key) === 'dark' ? 'dark' : 'light'; }
    catch { return 'light'; }
  };
  const apply = (theme) => {
    document.documentElement.dataset.theme = theme;
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      const next = theme === 'dark' ? 'light' : 'dark';
      button.textContent = `${next === 'dark' ? 'Dark' : 'Light'} theme`;
      button.setAttribute('aria-label', `Switch to ${next} theme`);
    });
  };
  apply(read());
  document.addEventListener('DOMContentLoaded', () => {
    apply(read());
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.addEventListener('click', () => {
        const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
        try { localStorage.setItem(key, theme); } catch { /* Theme still works without storage. */ }
        apply(theme);
      });
    });
  });
  window.addEventListener('storage', event => {
    if (event.key === key || event.key === null) apply(read());
  });
})();
