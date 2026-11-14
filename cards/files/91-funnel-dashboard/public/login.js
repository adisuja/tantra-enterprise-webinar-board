// Sign-in form. Kept out of the HTML so the page can forbid inline scripts.
document.getElementById('f').addEventListener('submit', async function (e) {
  e.preventDefault();
  var msg = document.getElementById('msg');
  msg.textContent = '';
  var btn = this.querySelector('button');
  btn.disabled = true;
  try {
    var r = await fetch('/api/login', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ password: document.getElementById('pw').value }) });
    var d = await r.json();
    if (r.ok) { location.replace('/' + location.hash); return; }
    msg.textContent = d.error || 'Sign in failed.';
  } catch (err) { msg.textContent = 'Network error. Try again.'; }
  btn.disabled = false;
});
