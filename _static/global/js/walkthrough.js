// Walk-through mode: click through every page without answering anything.
// Only active when the session config has walkthrough=True (see walkthrough.py).
(function () {
  if (!window.WALKTHROUGH) return;

  // Always show / enable the Next button, even on pages that hide or disable it
  // (minimum page time, camera check, video recording, video choice).
  function freeNext() {
    const b = document.getElementById('NextButton');
    if (!b) return;
    b.disabled = false;
    b.style.display = '';
    b.style.visibility = 'visible';
  }

  document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('form');
    if (form) form.noValidate = true;
    freeNext();
    setInterval(freeNext, 250);

    const banner = document.createElement('div');
    banner.textContent = 'WALK-THROUGH MODE — no answers required';
    banner.style.cssText =
      'position:fixed; bottom:12px; left:12px; z-index:100000; background:#7c3aed; color:#fff;' +
      'padding:6px 12px; border-radius:6px; font-size:13px; font-weight:600; box-shadow:0 2px 8px rgba(0,0,0,.25);';
    document.body.appendChild(banner);
  });

  // Runs before the page's own submit handlers (capture phase on window) and
  // stops them, so page-level "please answer" checks never block submission.
  window.addEventListener('submit', function (e) {
    const form = e.target;
    // every radio group without an answer: pick the first option
    const groups = {};
    form.querySelectorAll('input[type=radio]').forEach(function (r) {
      (groups[r.name] = groups[r.name] || []).push(r);
    });
    Object.keys(groups).forEach(function (name) {
      const g = groups[name];
      if (!g.some(function (r) { return r.checked; })) g[0].checked = true;
    });
    // empty dropdowns: first real option
    form.querySelectorAll('select').forEach(function (s) {
      if (!s.value) {
        const o = Array.from(s.options).find(function (o) { return o.value !== ''; });
        if (o) s.value = o.value;
      }
    });
    // required hidden/text inputs declare a placeholder value via data-wt
    form.querySelectorAll('[data-wt]').forEach(function (el) {
      if (!el.value) el.value = el.dataset.wt;
    });
    e.stopImmediatePropagation();
  }, true);
})();
