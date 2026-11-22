// Optimization task UI (Weidmann & Deming). Guesses are sent to the server
// (oTree live_method), which returns the result; the function itself never
// reaches the browser.
//
// OptTask({practice, maxGuesses, prior, finalDone})
//   practice: unlimited guesses, no final answer
//   prior:    guesses already made ([[x, y], ...]) if the page is reloaded
(function () {
  window.OptTask = function (cfg) {
    const input = document.getElementById('optGuess');
    const enterBtn = document.getElementById('optEnter');
    const warning = document.getElementById('optWarning');
    const prompt = document.getElementById('optPrompt');
    const tbody = document.querySelector('#optHistory tbody');
    const modal = document.getElementById('optFinalModal');
    const max = cfg.maxGuesses;
    let n = 0, waiting = false, finalMode = false;

    function addRow(x, y) {
      n += 1;
      const tr = document.createElement('tr');
      const label = cfg.practice ? String(n) : n + ' of ' + max;
      [label, x, Number(y).toFixed(2)].forEach(function (v) {
        const td = document.createElement('td'); td.textContent = v; tr.appendChild(td);
      });
      tbody.appendChild(tr);
    }

    function enterFinalMode() {
      finalMode = true;
      prompt.textContent = 'Enter your final answer';
      if (modal) modal.style.display = 'flex';
    }

    (cfg.prior || []).forEach(function (g) { addRow(g[0], g[1]); });
    if (!cfg.practice && n >= max) enterFinalMode();
    if (cfg.finalDone) document.getElementById('form').submit();

    window.liveRecv = function (msg) {
      waiting = false;
      enterBtn.disabled = false;
      if (msg.type === 'result') {
        addRow(msg.guess, msg.result);
        if (cfg.practice) prompt.textContent = 'Try entering another number between 0 and 300';
        else if (n >= max) enterFinalMode();
      } else if (msg.type === 'final_saved' || msg.type === 'done') {
        document.getElementById('form').submit();
      } else {
        warning.style.display = 'block';
      }
      input.focus();
    };

    function submitGuess() {
      if (waiting) return;
      warning.style.display = 'none';
      const raw = input.value.trim();
      const x = Number(raw);
      if (raw === '' || isNaN(x) || x < 0 || x > 300) { warning.style.display = 'block'; return; }
      waiting = true;
      enterBtn.disabled = true;
      input.value = '';
      liveSend({ type: finalMode ? 'final' : 'guess', guess: x });
    }

    enterBtn.addEventListener('click', submitGuess);
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); submitGuess(); }
    });
    if (modal) {
      document.getElementById('optFinalOk').addEventListener('click', function () {
        modal.style.display = 'none';
        input.focus();
      });
    }
    return { count: function () { return n; } };
  };
})();
