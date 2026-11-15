/* ===================== shell: brands · funnels · themes · connect prompts · motion =====================
   Loaded after the kit's chrome, so these declarations replace dockHtml, setTheme, toggleTheme and
   initTheme. Everything else in the kit runs unchanged. TD (brand, funnels, missing sources) comes
   from the server in <script id="td">. */
const TD = (()=>{ try{ return JSON.parse(document.getElementById('td').textContent); }catch(e){ return {brands:[],brand:{},funnel:{},missing:[]}; } })();
const tdq = s => encodeURIComponent(s==null?'':s);
const tdInt = (cat) => `/integrations?b=${tdq(TD.brand.id)}${cat?'&cat='+tdq(cat):''}&from=${tdq(TD.funnel.id||'')}`;

/* ---------- the kit hid its vendors' names; here a vendor can be the brand itself (Tantra), so never
   rewrite the brand's own name ---------- */
for (let i = SCRUB.length - 1; i >= 0; i--) { const src = SCRUB[i][0].source; if (TD.brand && TD.brand.name && new RegExp(src).test(TD.brand.name)) SCRUB.splice(i, 1); }

/* ---------- vocabulary: a funnel whose events are not webinars renames them everywhere ---------- */
(function(){ const u=TD.funnel && TD.funnel.unit; if(!u || u.singular==='webinar') return;
  const cap=s=>s.charAt(0).toUpperCase()+s.slice(1);
  SCRUB.push([/\bWebinars\b/g,cap(u.plural)],[/\bwebinars\b/g,u.plural],[/\bWebinar\b/g,cap(u.singular)],[/\bwebinar\b/g,u.singular]);
  if(u.prefix && u.prefix!=='W') SCRUB.push([/\bW(\d+)\b/g,u.prefix+'$1']); })();

/* ---------- dock: brand and funnel switcher on top, Funnels and Integrations entries ---------- */
const tdIcon = {funnels:'<path d="M4 5h16l-6 7v6l-4 2v-8z"/>', integrations:'<circle cx="6" cy="6" r="2.4"/><circle cx="18" cy="6" r="2.4"/><circle cx="6" cy="18" r="2.4"/><circle cx="18" cy="18" r="2.4"/><path d="M8.4 6h7.2M6 8.4v7.2M18 8.4v7.2M8.4 18h7.2"/>', palette:'<path d="M12 3a9 9 0 1 0 0 18c1.2 0 1.8-.8 1.8-1.7 0-.5-.2-.9-.5-1.2-.3-.3-.5-.8-.5-1.2 0-1 .8-1.7 1.7-1.7H16a5 5 0 0 0 5-5c0-4.1-4-7.2-9-7.2z"/><circle cx="7.5" cy="11" r="1"/><circle cx="10.5" cy="7.5" r="1"/><circle cx="15" cy="7.5" r="1"/>', recap:'<rect x="4" y="3" width="16" height="18" rx="3"/><path d="M10 9l5 3-5 3z"/>'};
Object.assign(I, tdIcon);
const tdInitials = s => String(s||'?').split(/\s+/).filter(Boolean).slice(0,2).map(w=>w[0].toUpperCase()).join('');
function dockHtml(){ const inW=S.w!=null;
  const items=inW ? WTABS.map(([k,l])=>[k,l,k,S.wtab===k,'wtab',WTAB_Q[k]||'',l]) : VIEW_D.map(k=>[k,VIEW_L[k],k,S.view===k,'view',VIEW_Q[k],VIEW_S[k]]);
  const btn=([k,l,ic,on,t,q])=>`<button class="dk${on?' on':''}" data-dock="${k}" data-dt="${t}" aria-label="${esc(l)}: ${esc(q)}" ${on?'aria-current="page"':''}>${ico(ic)}<span class="tag">${esc(l)}</span><span class="tg"><b>${esc(l)}</b><small>${esc(q)}</small></span></button>`;
  const body=items.map(it=>(!inW&&VIEW_G[it[0]]?`<div class="grp">${VIEW_G[it[0]]}</div>`:'')+btn(it)).join('');
  const sw=`<button class="td-sw" id="tdSw" aria-haspopup="menu" aria-label="Switch brand or funnel: ${esc(TD.brand.name)}, ${esc(TD.funnel.name)}"><span class="td-mark">${esc(tdInitials(TD.brand.name))}</span><span class="bw"><b>${esc(TD.brand.name||'Brand')}</b><small>${esc(TD.funnel.name||'Funnel')}</small></span><span class="chev">▾</span></button>`;
  const funnels=`<a class="dk aux" href="/funnels?b=${tdq(TD.brand.id)}" aria-label="All funnels of ${esc(TD.brand.name)}">${ico('funnels')}<span class="tag">All funnels</span><span class="tg"><b>All funnels</b><small>Every funnel of this brand</small></span></a>`;
  return `<div class="brand">${sw}</div>${inW?`<button class="exit" data-exit="1" aria-label="Back to the programme">← All ${esc(TD.funnel.unit?TD.funnel.unit.plural:'webinars')}</button>`:funnels}${body}
   <div class="gap"></div>
   <a class="dk aux" href="/f/${tdq(TD.funnel.id)}/recap" aria-label="Animated recap">${ico('recap')}<span class="tag">Recap</span><span class="tg"><b>Recap</b><small>Animated summary to share</small></span></a>
   <a class="dk aux" href="${tdInt('')}" aria-label="Integrations">${ico('integrations')}${TD.missing&&TD.missing.length?'<i class="dot"></i>':''}<span class="tag">Integrations</span><span class="tg"><b>Integrations</b><small>${TD.connected||0} connected${TD.missing&&TD.missing.length?' · '+TD.missing.length+' to add':''}</small></span></a>
   <button class="dk aux" id="tdTheme" aria-label="Appearance">${ico('palette')}<span class="tag">Appearance</span><span class="tg"><b>Appearance</b><small>Light, dark and themes</small></span></button>
   <button class="dk aux" data-health="1" aria-label="Data quality">${ico('data')}${MODEL.health.conflicts?'<i class="dot"></i>':''}<span class="tag">Data quality</span><span class="tg"><b>Data quality</b><small>What is complete, what is missing</small></span></button>`; }

/* ---------- switcher menu ---------- */
function tdMenu(anchor){ let m=document.getElementById('tdMenu'); if(!m){ m=document.createElement('div'); m.id='tdMenu'; m.className='td-menu'; m.setAttribute('role','menu'); document.body.appendChild(m); }
  if(m.classList.contains('on')){ m.classList.remove('on'); return; }
  const rows=TD.brands.map(b=>`<div class="hd"><span>${esc(b.name)}</span><a href="/funnels?b=${tdq(b.id)}" style="padding:0;display:inline;width:auto;font:600 12px var(--sans);color:var(--ocean)">All funnels</a></div>`+
    (b.funnels.length?b.funnels.map(f=>`<a role="menuitem" class="${f.id===TD.funnel.id?'on':''}" href="/f/${tdq(f.id)}"><i class="dot ${f.status==='live'?'live':''}"></i><span><span>${esc(f.name)}</span><small>${esc(f.template_label||f.template)}</small></span></a>`).join(''):`<a role="menuitem" href="/funnels?b=${tdq(b.id)}&new=1"><span><span>Add the first funnel</span><small>Pick a template and its sources</small></span></a>`)).join('<div class="sep"></div>');
  m.innerHTML=rows+`<div class="sep"></div><a role="menuitem" href="/funnels?newbrand=1"><span><span>Add a brand</span><small>Its own funnels and integrations</small></span></a>`;
  const r=anchor.getBoundingClientRect(); m.style.left=Math.min(r.left, innerWidth-m.offsetWidth-12)+'px'; m.style.top=(innerWidth<=760? Math.max(12,r.top-Math.min(520,m.scrollHeight)-8) : r.bottom+6)+'px';
  m.classList.add('on'); const first=m.querySelector('a'); if(first) first.focus(); }
/* phones: the kit's bottom tab bar hides the brand and the extra entries, so they get a top strip */
function tdTopStrip(){ if(document.getElementById('tdTop')) return; const st=document.getElementById('stage'); if(!st) return;
  const d=document.createElement('div'); d.id='tdTop'; d.className='td-top';
  d.innerHTML=`<button class="td-sw" id="tdSwM" aria-haspopup="menu" aria-label="Switch brand or funnel"><span class="td-mark">${esc(tdInitials(TD.brand.name))}</span><span class="bw"><b>${esc(TD.brand.name)}</b><small>${esc(TD.funnel.name)}</small></span><span class="chev">▾</span></button><a class="td-ic" href="${tdInt('')}" aria-label="Integrations">${ico('integrations')}</a><a class="td-ic" href="/f/${tdq(TD.funnel.id)}/recap" aria-label="Recap">${ico('recap')}</a><button class="td-ic" id="tdThemeM" aria-label="Appearance">${ico('palette')}</button>`;
  st.insertBefore(d, st.firstChild); }
document.addEventListener('DOMContentLoaded',tdTopStrip);
document.addEventListener('click',e=>{ const sw=e.target.closest&&e.target.closest('#tdSw,#tdSwM'); const m=document.getElementById('tdMenu');
  if(sw){ e.stopPropagation(); tdMenu(sw); return; } if(m&&m.classList.contains('on')&&!e.target.closest('#tdMenu')) m.classList.remove('on');
  if(e.target.closest&&e.target.closest('#tdTheme,#tdThemeM')){ tdThemeDrawer(); } },true);
document.addEventListener('keydown',e=>{ if(e.key==='Escape'){ const m=document.getElementById('tdMenu'); if(m) m.classList.remove('on'); } });

/* ---------- themes: mode (light, dark, system) × palette × gradient ---------- */
const TD_PAL = [['classic','Classic','Gold and blue, the original',['#d4a72c','#1f6fdc']],['volt','Tantra Volt','Violet and teal',['#6d4aff','#22d3ee']],['aurora','Aurora','Teal and indigo',['#4f46e5','#06b6d4','#10b981']],['emerald','Emerald','Green and blue',['#059669','#84cc16']],['sunset','Sunset','Orange and violet',['#f97316','#e11d48']],['orchid','Orchid','Pink and blue',['#db2777','#8b5cf6']],['graphite','Graphite','Amber and steel',['#1e293b','#64748b']]];
const tdGet = (k,d) => { try{ const v=localStorage.getItem(k); return v==null?d:v; }catch(e){ return d; } };
const tdSet = (k,v) => { try{ localStorage.setItem(k,v); }catch(e){} };
function tdMode(){ const m=tdGet('td-mode', tdGet('wi-theme','system')); return m; }
function tdResolve(m){ if(m==='light'||m==='dark') return m; try{ return matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'; }catch(e){ return 'light'; } }
function setTheme(t){ S.theme=t; document.documentElement.dataset.theme=t; }
function tdApply(){ const de=document.documentElement; setTheme(tdResolve(tdMode())); de.dataset.palette=tdGet('td-palette',TD.brand.palette||'classic'); de.dataset.gradient=tdGet('td-grad','on'); }
function toggleTheme(){ tdSet('td-mode', S.theme==='dark'?'light':'dark'); tdApply(); render({}); }
function initTheme(){ tdApply(); try{ matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{ if(tdMode()==='system'){ tdApply(); render({}); } }); }catch(e){} }
function tdThemeDrawer(){ const m=tdMode(), p=document.documentElement.dataset.palette, g=document.documentElement.dataset.gradient==='on';
  openDrawer(`<span class="lbl">Appearance</span><h2 style="font-size:clamp(30px,4vw,42px);letter-spacing:-.03em;margin-bottom:18px">Make it yours</h2>
   <h4 class="lbl" style="margin:8px 0 10px">Mode</h4><div class="td-modes">${['light','dark','system'].map(x=>`<button data-tdmode="${x}" class="${m===x?'on':''}">${x[0].toUpperCase()+x.slice(1)}</button>`).join('')}</div>
   <h4 class="lbl" style="margin:26px 0 10px">Theme</h4><div class="td-sw-grid">${TD_PAL.map(([k,l,d,c])=>`<button class="td-swatch${p===k?' on':''}" data-tdpal="${k}"><i style="background:linear-gradient(120deg,${c.join(',')})"></i><span>${l}</span><small>${d}</small></button>`).join('')}</div>
   <label class="td-tgl" style="margin-top:22px"><span><b>Gradient glow</b><br><small style="color:var(--mute)">Soft colour behind the page and on headline money figures</small></span><input type="checkbox" data-tdgrad ${g?'checked':''}></label>
   <p class="sub" style="margin-top:14px;font-size:13.5px">Saved on this device. Money stays in the theme's first colour and people in its second, in every theme, so a chart reads the same whichever you pick.</p>`); }
document.addEventListener('click',e=>{ const t=e.target.closest&&e.target.closest('[data-tdmode],[data-tdpal]'); if(!t) return;
  if(t.dataset.tdmode){ tdSet('td-mode',t.dataset.tdmode); } if(t.dataset.tdpal){ tdSet('td-palette',t.dataset.tdpal); }
  tdApply(); render({}); tdThemeDrawer(); });
document.addEventListener('change',e=>{ if(e.target.matches&&e.target.matches('[data-tdgrad]')){ tdSet('td-grad',e.target.checked?'on':'off'); tdApply(); render({}); } });

/* ---------- connect prompts: every "not tracked / not recorded / not connected" gets a way to fix it ---------- */
const TD_ROLE = [
  [/contacted|outreach/i,'outreach','an outreach tool'],
  [/linkedin/i,'linkedin','LinkedIn outreach'],[/paid|spend|cost|\bads?\b|advert/i,'ads','ad accounts'],[/website|visit|organic|referr|traffic|search/i,'analytics','web analytics'],
  [/e-?mail|bounce|cold/i,'cold_email','cold email'],[/watch|drop-off|poll|chat|question|q&a|replay/i,'webinar','your webinar platform'],
  [/invitation|calendar|rsvp|invite/i,'tantra','the Tantra app'],[/content|post|impression|social/i,'content','content analytics'],
  [/call|book/i,'booking','a booking tool'],[/revenue|payment|customer|buyer|paid without/i,'payments','payments'],[/deal|pipeline|crm/i,'crm','a CRM']];
const tdRoleOf = txt => { for(const [r,cat,l] of TD_ROLE) if(r.test(txt)) return {cat,l}; return null; };
const tdMissingCat = cat => cat === 'outreach' ? !(TD.categories_connected || []).some(c => ['cold_email','linkedin','outreach'].includes(c)) : (!TD.categories_connected || !TD.categories_connected.includes(cat));
function tdDecorate(){ const cv=document.getElementById('canvas'); if(!cv) return;
  cv.querySelectorAll('.state, .li, .row, .wl, .tray span, .sub').forEach(el=>{
    if(el.dataset.tdcn) return; const txt=el.textContent||''; if(!/not (tracked|recorded|connected)|not connected yet|tracking not connected/i.test(txt)) return;
    const role=tdRoleOf(txt); if(!role||!tdMissingCat(role.cat)) return; el.dataset.tdcn='1';
    const a=document.createElement('a'); a.className='td-cn'; a.href=tdInt(role.cat); a.textContent='Connect '+role.l; el.appendChild(a); });
  cv.querySelectorAll('svg .nd.ghost').forEach(g=>{ if(g.dataset.tdcn) return; g.dataset.tdcn='1'; const role=tdRoleOf(g.textContent+' '+(g.getAttribute('data-tip')||'')+' visits'); if(!role) return;
    g.style.cursor='pointer'; g.setAttribute('role','link'); g.setAttribute('aria-label','Connect '+role.l); g.addEventListener('click',ev=>{ ev.stopPropagation(); location.href=tdInt(role.cat); }); });
  if(S.view==='overview'&&S.w==null&&TD.missing&&TD.missing.length&&!cv.querySelector('.td-setup')){ const h=cv.querySelector('.hero, .ov, h1'); if(h){ const box=document.createElement('div'); box.className='td-setup rise';
      box.innerHTML=`<div class="sub"><b>${TD.missing.length===1?'One source':TD.missing.length+' sources'} would complete this funnel.</b> Sections that need them say "not tracked" until they are connected. Each refresh is hourly and stays inside every provider's limits.</div><div class="roles">${TD.missing.slice(0,6).map(m=>`<a class="td-cn" href="${tdInt(m.category)}">${esc(m.label)}</a>`).join('')}</div>`;
      (h.closest('.ov')||h).insertAdjacentElement('afterend',box); } }
  tdChecks(cv); tdDash(cv); tdMotion(cv); }
/* ---------- weekly checks: the weekly cycle's runs for this funnel (GET /api/checks), on the Overview ---------- */
let tdCk=null, tdCkBusy=false;
const tdH = s => String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
// House rule: the product is never called "CRM" on screen; the cycle's report uses it as an area name.
const tdCkT = s => tdH(String(s==null?'':s).replace(/\bTantra CRM\b/g,'Tantra').replace(/(^|[^\w./-])CRM\b/g,'$1Tantra'));
const TD_CKS = {fail:'Fail',warn:'Warning',pass:'Pass',info:'Info'};
const TD_CKK = {check:'Check',roll:'Roll',e2e:'End to end'};
const tdCkPill = (st,n) => `<span class="pill tdc ${st}">${TD_CKS[st]||'Info'}${n!=null?` <b>${n}</b>`:''}</span>`;
const tdCkWhen = iso => { const t=Date.parse(iso); return Number.isNaN(t)?'':new Date(t).toLocaleString(undefined,{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'}); };
const tdCkDay = d => d&&/^\d{4}-\d{2}-\d{2}$/.test(d)?new Date(d+'T12:00:00').toLocaleDateString(undefined,{weekday:'short',day:'numeric',month:'short'}):(d||'n/a');
const tdCkShort = d => d&&/^\d{4}-\d{2}-\d{2}$/.test(d)?new Date(d+'T12:00:00').toLocaleDateString(undefined,{day:'numeric',month:'short'}):(d||'n/a');
function tdChecksHtml(){
  const head=`<div class="sec-h"><div class="h2">Weekly checks</div><span class="sp"></span><span class="na" style="font-size:14px">Pages, registration, offer and tracking, checked before each session</span></div>`;
  if(tdCk.error) return head+`<div class="state"><b>Weekly checks</b>Could not be loaded just now. Reload the page to try again.</div>`;
  const R=tdCk.runs||[]; if(!R.length) return head+`<div class="state"><b>No weekly checks yet</b>Each run of the weekly cycle shows here: what passed, what needs a look and what failed.</div>`;
  const L=R[0], bad=L.report.filter(r=>r.status==='fail'), wrn=L.report.filter(r=>r.status==='warn');
  const verdict=L.failed?`<b class="dn">${L.failed} failing</b>`:L.warned?`<b>No failures</b>, ${L.warned} to look at`:`<b class="up">All clear</b>`;
  const line=r=>`<div class="tdc-li">${tdCkPill(r.status)}<span class="a">${tdCkT(r.area)}</span><span class="t"><b>${tdCkT(r.name)}</b>${r.detail?`<small>${tdCkT(r.detail)}</small>`:''}</span></div>`;
  const lines=bad.concat(wrn), CAP=10;
  const list=lines.length?`<div class="tdc-list">${lines.slice(0,CAP).map(line).join('')}</div>${lines.length>CAP?`<details class="tdc-more"><summary>Show ${lines.length-CAP} more</summary><div class="tdc-list">${lines.slice(CAP).map(line).join('')}</div></details>`:''}`:`<p class="sub">Nothing failed or needs a look in the latest run.</p>`;
  const rows=R.map((r,i)=>`<tr${i===0?' class="on"':''}><td class="l">${tdH(tdCkWhen(r.at))}<small class="tdc-k">${tdH(TD_CKK[r.kind]||r.kind)}</small></td><td class="l tdc-kc">${tdH(TD_CKK[r.kind]||r.kind)}</td><td class="l">${tdH(tdCkShort(r.session))}</td><td>${r.failed?tdCkPill('fail',r.failed):'<span class="na">0 failed</span>'}</td><td>${r.warned?tdCkPill('warn',r.warned):'<span class="na">0 warnings</span>'}</td><td>${tdCkPill('pass',r.passed)}</td></tr>`).join('');
  return head+`<p class="q">Session of ${tdH(tdCkDay(L.session))}: ${verdict}.</p>
   <p class="q-sub">Latest run: ${tdH(TD_CKK[L.kind]||L.kind)}, ${tdH(tdCkWhen(L.at))}.</p>
   <div class="tdc-counts" role="group" aria-label="Latest run">${tdCkPill('fail',L.failed)}${tdCkPill('warn',L.warned)}${tdCkPill('pass',L.passed)}</div>
   <h3 class="lbl tdc-h">Failing and warning checks</h3>${list}
   <h3 class="lbl tdc-h">Last runs</h3><div class="tw"><table class="tdc-runs"><thead><tr><th class="l">Run</th><th class="l tdc-kc">Kind</th><th class="l">Session</th><th>Failed</th><th>Warnings</th><th>Passed</th></tr></thead><tbody>${rows}</tbody></table></div>`; }
function tdChecks(cv){ if(S.view!=='overview'||S.w!=null||!TD.funnel||!TD.funnel.id||cv.querySelector('.td-checks')) return;
  if(!tdCk){ if(!tdCkBusy){ tdCkBusy=true; fetch('/api/checks?funnel='+tdq(TD.funnel.id),{credentials:'same-origin'}).then(r=>r.ok?r.json():{error:true}).catch(()=>({error:true})).then(d=>{ tdCk=d||{error:true}; tdDecorate(); }); } return; }
  const all=cv.querySelectorAll('section.os'), at=all[all.length-1]; if(!at) return;
  const sec=document.createElement('section'); sec.className='os td-checks'; sec.setAttribute('aria-label','Weekly checks'); sec.innerHTML=tdChecksHtml(); at.insertAdjacentElement('afterend',sec); }
/* House copy rule: no em or en dashes anywhere a reader sees. The kit writes " \u2014 " between clauses and
   "\u2014" for a figure that is not recorded; both are rewritten as the page draws. */
function tdDash(root){ const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT); const fix=[]; let n; while((n=w.nextNode())) if(/[\u2013\u2014]/.test(n.nodeValue)) fix.push(n);
  fix.forEach(x=>{ let v=x.nodeValue; v=v.replace(/(\d)\s*\u2013\s*(\d)/g,'$1 to $2').replace(/^(\s*)[\u2013\u2014](\s+)/,'$1n/a$2').replace(/\s+[\u2013\u2014]\s+/g,': ').replace(/^[\u2014\u2013]$/,'n/a').replace(/[\u2014\u2013]/g,', '); x.nodeValue=v; });
  root.querySelectorAll('[data-tip],[aria-label]').forEach(e=>{ for(const a of ['data-tip','aria-label']){ const v=e.getAttribute(a); if(v&&/[\u2013\u2014]/.test(v)) e.setAttribute(a,v.replace(/\s+[\u2013\u2014]\s+/g,': ').replace(/[\u2014\u2013]/g,'n/a')); } }); }
/* footer: the kit assumed the model time was in India time; use the exact build time instead */
function footHtml(){ const g=MODEL.generated_iso?Date.parse(MODEL.generated_iso):NaN, age=Number.isNaN(g)?null:(Date.now()-g)/3600e3;
  const old=age!=null&&age>3, ago=age==null?'':age<1?'less than an hour ago':age<48?`${Math.round(age)} hours ago`:`${Math.round(age/24)} days ago`;
  const when=Number.isNaN(g)?'':new Date(g).toLocaleString(undefined,{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'});
  return `<footer class="foot${old?' old':''}"><b>${esc(TD.brand.name)}</b> · ${esc(TD.funnel.name)}<span class="sp"></span><span>${old?`Not refreshed for ${ago}, so figures may be out of date. `:''}Data as of ${esc(when)}${ago&&!old?` (${ago})`:''} · refreshed hourly</span></footer>`; }

/* ---------- motion: the content kit's timeline effects, played live on each view ---------- */
const tdEase=x=>1-Math.pow(1-x,3), tdBack=x=>{const c=1.70158;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)};
function tdFx(el,f,p,raw){ const s=el.style;
  if(f==='up'){s.opacity=p;s.transform=`translateY(${(1-p)*22}px)`} else if(f==='pop'){s.opacity=Math.min(1,raw*3);s.transform=`scale(${0.7+0.3*tdBack(raw)})`}
  else if(f==='blur'){s.opacity=p;s.filter=p>=1?'':`blur(${(1-p)*12}px)`} else if(f==='wipe'){s.clipPath=p>=1?'':`inset(0 ${(1-p)*100}% 0 0)`}
  else if(f==='grow'){s.transformOrigin='left center';s.transform=p>=1?'':`scaleX(${p})`} else if(f==='fade'){s.opacity=p} }
function tdMotion(root){ if(S.noanim) return; const els=[...root.querySelectorAll('[data-a]')].filter(e=>!e.dataset.tdDone); if(!els.length) return; const t0=performance.now();
  els.forEach(e=>{ e.dataset.tdDone='1'; const [f,at,d]=e.dataset.a.split(','); tdFx(e,f,0,0); });
  const step=t=>{ let busy=false; const bt=(t-t0)/1000; els.forEach(e=>{ const [f,at,d]=e.dataset.a.split(','); const raw=Math.max(0,Math.min(1,(bt-(+at||0))/(+d||.5))); tdFx(e,f,tdEase(raw),raw); if(raw<1) busy=true; }); if(busy) requestAnimationFrame(step); };
  requestAnimationFrame(step);
  root.querySelectorAll('.hero-n, .upc').forEach((h,i)=>{ if(h.dataset.tdSheen) return; h.dataset.tdSheen='1'; h.classList.add('td-sheen'); setTimeout(()=>h.classList.add('go'),500+i*180); }); }
// The kit redraws the canvas on every interaction; decorate after each draw.
new MutationObserver(()=>{ clearTimeout(window._tdT); window._tdT=setTimeout(tdDecorate,30); }).observe(document.getElementById('canvas'),{childList:true});
document.addEventListener('DOMContentLoaded',tdDecorate);
['drawer','tip','pop','pall'].forEach(id=>{ const el=document.getElementById(id); if(el) new MutationObserver(()=>tdDash(el)).observe(el,{childList:true,subtree:true,characterData:true}); });
