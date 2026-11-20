// Shared helpers for the Qualtrics reproduction.

// Qualtrics "Timing" question with MinSeconds: the Next button is hidden
// until the minimum time has elapsed.
function enforceMinSeconds(seconds) {
  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('NextButton');
    if (!btn) return;
    btn.style.visibility = 'hidden';
    setTimeout(function () { btn.style.visibility = 'visible'; }, seconds * 1000);
  });
}

// Mirror oTree's (hidden) page countdown into the fixed Qualtrics-style box.
document.addEventListener('DOMContentLoaded', function () {
  var box = document.getElementById('timerValue');
  if (!box) return;
  setInterval(function () {
    var src = document.querySelector('.otree-timer__time-left');
    if (src && src.textContent.trim()) box.textContent = src.textContent.trim();
  }, 250);
});

// Sliders: value is only recorded once the participant interacts with the
// handle (Qualtrics slider without custom start position).
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.q-slider').forEach(function (wrap) {
    var range = wrap.querySelector('input[type=range]');
    var hidden = wrap.querySelector('input[type=hidden]');
    var out = wrap.querySelector('.slider-value');
    if (hidden.value !== '') {
      range.value = hidden.value;
      range.classList.remove('untouched');
      out.textContent = hidden.value;
    }
    function update() {
      range.classList.remove('untouched');
      hidden.value = range.value;
      out.textContent = range.value;
    }
    range.addEventListener('input', update);
    range.addEventListener('change', update);
  });
});

// Prevent Enter in single-line inputs from submitting the page early.
document.addEventListener('keydown', function (e) {
  if (e.key === 'Enter' && e.target.tagName === 'INPUT' && e.target.type !== 'submit') {
    e.preventDefault();
  }
});
