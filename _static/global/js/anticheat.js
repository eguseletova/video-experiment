// Anti-cheating measures (session config anti_cheat=True).
//
// - blocks copy / cut / paste, right-click menu, drag & drop, text selection,
//   and the usual shortcuts (copy/paste/select-all/print/save/view-source/devtools)
// - blurs the page whenever the study window loses focus (tab switch, other
//   app, screenshot tools that take focus) and while the macOS screenshot
//   modifier (Cmd+Shift) is held; PrintScreen briefly blurs the page and
//   tries to clear the clipboard
// - hides the page when printing
// - counts focus losses and copy/paste attempts; pages can record them by
//   including hidden inputs with data-ac="focus_lost" / data-ac="copy_paste"
//
// Browsers cannot truly prevent screenshots (or a phone camera); these
// measures make it harder and leave a trace.
//
// Per-page opt-out of paste blocking: set window.AC_ALLOW_PASTE = true
// (used on the Prolific ID page).
(function () {
  if (!window.ANTI_CHEAT) return;

  let focusLost = 0, copyPaste = 0;

  // ---------- styles + overlay ----------
  const style = document.createElement('style');
  style.textContent = `
    body { -webkit-user-select: none; user-select: none; }
    input, textarea, select { -webkit-user-select: text; user-select: text; }
    html.ac-hidden .otree-body { filter: blur(16px); }
    #acOverlay { display: none; position: fixed; inset: 0; z-index: 200000;
      align-items: center; justify-content: center; background: rgba(255,255,255,0.55);
      font-size: 22px; color: #111; text-align: center; padding: 20px; }
    html.ac-hidden #acOverlay { display: flex; }
    @media print { body { display: none !important; } }
  `;
  document.head.appendChild(style);

  function overlay() {
    let o = document.getElementById('acOverlay');
    if (!o) {
      o = document.createElement('div');
      o.id = 'acOverlay';
      o.textContent = 'Please keep this window active to continue the study.';
      document.body.appendChild(o);
    }
    return o;
  }
  function hide() { overlay(); document.documentElement.classList.add('ac-hidden'); }
  function show() { document.documentElement.classList.remove('ac-hidden'); }

  function record() {
    document.querySelectorAll('input[data-ac="focus_lost"]').forEach(function (i) { i.value = focusLost; });
    document.querySelectorAll('input[data-ac="copy_paste"]').forEach(function (i) { i.value = copyPaste; });
  }

  // ---------- focus / visibility ----------
  window.addEventListener('blur', function () { focusLost += 1; record(); hide(); });
  window.addEventListener('focus', show);
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') hide(); else if (document.hasFocus()) show();
  });

  // ---------- clipboard, context menu, drag ----------
  function block(e) { e.preventDefault(); copyPaste += 1; record(); }
  ['copy', 'cut'].forEach(function (t) { document.addEventListener(t, block, true); });
  document.addEventListener('paste', function (e) { if (!window.AC_ALLOW_PASTE) block(e); }, true);
  document.addEventListener('contextmenu', function (e) { e.preventDefault(); }, true);
  document.addEventListener('dragstart', function (e) { e.preventDefault(); }, true);
  document.addEventListener('drop', function (e) { e.preventDefault(); }, true);

  // ---------- keyboard ----------
  document.addEventListener('keydown', function (e) {
    const k = (e.key || '').toLowerCase();
    const mod = e.ctrlKey || e.metaKey;
    // macOS screenshot shortcuts start with Cmd+Shift: blur while held
    if (e.metaKey && e.shiftKey) hide();
    if (k === 'printscreen') { hide(); }
    if ((mod && ['c', 'x', 'a', 'p', 's', 'u'].includes(k)) ||
        (mod && k === 'v' && !window.AC_ALLOW_PASTE) ||
        (mod && e.shiftKey && ['i', 'j', 'c'].includes(k)) ||
        k === 'f12') {
      e.preventDefault();
      if (['c', 'x', 'v'].includes(k)) { copyPaste += 1; record(); }
    }
  }, true);
  document.addEventListener('keyup', function (e) {
    const k = (e.key || '').toLowerCase();
    if (k === 'printscreen') {
      try { navigator.clipboard && navigator.clipboard.writeText(''); } catch (err) {}
      setTimeout(show, 1500);
      return;
    }
    if (!(e.metaKey && e.shiftKey) && document.hasFocus()) show();
  }, true);

  document.addEventListener('DOMContentLoaded', record);
})();
