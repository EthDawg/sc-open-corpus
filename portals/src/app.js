// Shared helpers for the three portals. Data lives in ../data/ (written by portals/build.py).
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const host = u => { try { return new URL(u).host } catch { return u } };
const fmtBytes = n => n > 1e6 ? (n / 1e6).toFixed(1) + ' MB' : Math.max(1, Math.round(n / 1e3)) + ' KB';
async function getJSON(u) { const r = await fetch(u); if (!r.ok) throw new Error(u + ' ' + r.status); return r.json() }
async function initOrgs(app, load) {
  const idx = await getJSON('../data/index.json');
  const orgs = idx.orgs.filter(o => o.apps.includes(app));
  const sel = document.querySelector('#org');
  const want = new URLSearchParams(location.search).get('org') || localStorage.getItem(app + ':org') || orgs[0].slug;
  sel.innerHTML = orgs.map(o => `<option value="${o.slug}" ${o.slug === want ? 'selected' : ''}>${esc(o.name)}</option>`).join('');
  sel.onchange = () => { try { localStorage.setItem(app + ':org', sel.value) } catch {} ; history.replaceState(null, '', '?org=' + sel.value); load(sel.value) };
  load(orgs.some(o => o.slug === want) ? want : orgs[0].slug);
}
