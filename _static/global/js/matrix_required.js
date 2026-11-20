// Client-side "force response" for radio matrices: every radio group in every
// row must be answered; unanswered rows are highlighted.
function requireMatrix(tableId, errorId) {
  const table = document.getElementById(tableId);
  const err = document.getElementById(errorId);
  function rowComplete(tr) {
    const names = new Set(Array.from(tr.querySelectorAll('input[type=radio]')).map(i => i.name));
    return Array.from(names).every(n => tr.querySelector('input[name="' + n + '"]:checked'));
  }
  table.addEventListener('change', function (e) {
    const tr = e.target.closest('tr');
    if (tr && rowComplete(tr)) tr.classList.remove('missing');
  });
  document.getElementById('form').addEventListener('submit', function (e) {
    let first = null;
    table.querySelectorAll('tbody tr').forEach(function (tr) {
      if (!rowComplete(tr)) { tr.classList.add('missing'); if (!first) first = tr; }
    });
    if (first) {
      e.preventDefault();
      err.style.display = 'block';
      first.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  });
}
