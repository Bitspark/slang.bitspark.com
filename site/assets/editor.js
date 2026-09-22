/* Presentation adapter for the pinned Angular 6 release. It adds shared recipes
 * and accessible names to native controls; Angular retains all app behavior. */
const iconNames = {
  'fa-save': 'Save', 'fa-download': 'Download operator',
  'fa-project-diagram': 'Visual graph', 'fa-code': 'YAML definition',
  'fa-play': 'Run', 'fa-stop': 'Stop', 'fa-plus-square': 'Create operator',
  'fa-upload': 'Import workspace', 'fa-trash': 'Remove',
  'fa-redo-alt': 'Rotate right', 'fa-undo-alt': 'Rotate left',
  'fa-arrows-alt-h': 'Mirror horizontally', 'fa-arrows-alt-v': 'Mirror vertically',
};

function decorate(root) {
  const elements = [root, ...root.querySelectorAll('button, input, select, textarea, a, iframe')];
  for (const element of elements) {
    if (!(element instanceof HTMLElement) || element.closest('.CodeMirror')) continue;
    if (element.matches('button')) {
      if (!element.classList.contains('sd-button')) {
        element.classList.add('sd-button', 'sd-button--small');
        if (element.matches('.btn-link')) element.classList.add('sd-button--quiet');
        else if (element.matches('.btn-outline-light, .btn-outline-secondary')) element.classList.add('sd-button--outline');
        else element.classList.add('sd-button--accent');
        // Remove Bootstrap color variants so hover/disabled states also use
        // the upstream recipes. Structural btn/btn-group classes stay intact.
        element.classList.remove('btn-primary', 'btn-light', 'btn-link', 'btn-outline-light', 'btn-outline-secondary');
      }
      if (!element.textContent.trim() && !element.hasAttribute('aria-label')) {
        const icon = element.querySelector('i');
        let label = Object.entries(iconNames).find(([name]) => icon?.classList.contains(name))?.[1];
        const operator = element.closest('.list-group-item')?.querySelector('.sl-operator-name')?.textContent.trim();
        if (operator) label = `${icon?.classList.contains('fa-plus') ? 'Add' : 'Open'} ${operator}`;
        if (!label && icon?.classList.contains('fa-plus')) label = 'Add';
        if (label) {
          element.setAttribute('aria-label', label);
          element.title = label;
        }
      }
    }
    if (element.matches('input:not([type="checkbox"]):not([type="radio"]), select, textarea')) {
      element.classList.add('sd-input');
      if (!element.hasAttribute('aria-label') && !element.labels?.length) {
        const label = element.getAttribute('placeholder') || element.getAttribute('title') ||
          (element.matches('input[type="file"]') ? 'Workspace ZIP file' : null);
        if (label) element.setAttribute('aria-label', label);
      }
    }
    if (element.matches('.sl-navbar-go-back')) {
      element.setAttribute('aria-label', 'Back to operators');
      element.title = 'Back to operators';
    }
    if (element.matches('iframe')) element.title = 'Slang quick start';
  }
}

const app = document.querySelector('app-root');
// The legacy <base href="/app/"> would otherwise turn a fragment link into
// navigation away from the open program. Keep the skip action in this document.
document.querySelector('.sd-skip')?.addEventListener('click', event => {
  event.preventDefault();
  document.querySelector('#playground')?.focus();
});
if (app) {
  decorate(app);
  new MutationObserver(records => {
    for (const record of records) {
      for (const node of record.addedNodes) {
        if (node instanceof HTMLElement) decorate(node);
      }
    }
  }).observe(app, { childList: true, subtree: true });
}

const operatorsToggle = document.querySelector('[data-operators-toggle]');
operatorsToggle?.addEventListener('click', () => {
  const shown = document.body.classList.toggle('show-operators');
  operatorsToggle.setAttribute('aria-expanded', String(shown));
});
