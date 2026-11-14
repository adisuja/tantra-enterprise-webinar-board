/* ===================== chrome: dock · bar · drawers · palette · motion ===================== */
const VIEWFN = {overview:vOverview,webinars:vWebinars,acquisition:vAcquisition,audience:vAudience,engagement:vEngagement,commercial:vCommercial,intelligence:vIntelligence,next:vNext};
const VIEW_L = {overview:'Overview',webinars:'Webinars',acquisition:'Acquisition',audience:'Audience',engagement:'Engagement',commercial:'Commercial',intelligence:'Insights',next:'Next webinar'};
const VIEW_Q = {overview:'The big picture',webinars:'Compare every webinar',acquisition:'Where did people come from?',audience:'Who joined?',engagement:'What did they do?',commercial:'What did it earn?',intelligence:'What needs attention?',next:'What are we doing for the next one?'};
const VIEW_S = {overview:'Overview',webinars:'Webinars',acquisition:'Sources',audience:'Audience',engagement:'Engage',commercial:'Revenue',intelligence:'Insights',next:'Next'};
const VIEW_G = {overview:'Start here',webinars:'Past webinars',intelligence:'Decide'};
const WTAB_Q = {overview:'This webinar at a glance',acquisition:'Where its people came from',audience:'Who joined it',engagement:'What they did',commercial:'What it earned',content:'What was said and sent',timeline:'What happened, when'};
const VIEW_D = ['overview','next','webinars','acquisition','audience','engagement','commercial','intelligence'];
const FILTERED = ['overview','webinars','acquisition','audience','engagement','commercial'];
const I = {
  overview:'<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="2.6"/>', webinars:'<circle cx="7" cy="15.5" r="3"/><circle cx="14" cy="9" r="4.4"/><circle cx="19" cy="16.5" r="2"/>',
  acquisition:'<path d="M5 19L19 5"/><path d="M10 5h9v9"/>', audience:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  engagement:'<path d="M12 3l8 9-8 9-8-9z"/><path d="M12 8.5l3.5 3.5-3.5 3.5L8.5 12z"/>', commercial:'<path d="M16.5 6.5A4 4 0 0 0 8.5 8v3.2H6.5m2 0V16c0 1.4-.9 2.4-2 3h12m-10-7.8h6"/>',
  intelligence:'<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M18.5 15.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"/>',
  next:'<path d="M4 12h15"/><path d="M13 6l6 6-6 6"/>', data:'<path d="M12 3l7 3v5.2c0 4.6-3 7.6-7 9.8-4-2.2-7-5.2-7-9.8V6z"/><path d="M9 12l2.2 2.2L15.5 10"/>',
  theme:'<circle cx="12" cy="12" r="8"/><path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor"/>', content:'<path d="M5 6h14M5 11h14M5 16h9"/>', timeline:'<path d="M3 12h18"/><circle cx="7" cy="12" r="2"/><circle cx="14" cy="12" r="2"/><circle cx="19" cy="12" r="1"/>',
  back:'<path d="M15 5l-7 7 7 7"/>', guide:'<circle cx="12" cy="12" r="9"/><path d="M9.6 9.5a2.6 2.6 0 1 1 3.6 2.4c-.8.4-1.2.9-1.2 1.8"/><circle cx="12" cy="17" r=".6" fill="currentColor"/>'};
const ico = k => `<svg viewBox="0 0 24 24" aria-hidden="true">${I[k]||''}</svg>`;
const mark = `<svg viewBox="0 0 30 30" width="30" height="30" aria-label="__KIT_BRAND_NAME__"><circle cx="15" cy="15" r="12" fill="none" stroke="var(--ink)" stroke-width="1.4"/><path d="M15 3a12 12 0 0 1 0 24" fill="var(--gold)" opacity=".9"/><circle cx="15" cy="15" r="4" fill="var(--ink)"/></svg>`;

function dockHtml(){ const inW=S.w!=null;
  const items=inW ? WTABS.map(([k,l])=>[k,l,k,S.wtab===k,'wtab',WTAB_Q[k]||'',l]) : VIEW_D.map(k=>[k,VIEW_L[k],k,S.view===k,'view',VIEW_Q[k],VIEW_S[k]]);
  const btn=([k,l,ic,on,t,q,sh])=>`<button class="dk${on?' on':''}" data-dock="${k}" data-dt="${t}" aria-label="${l}: ${q}" ${on?'aria-current="page"':''}>${ico(ic)}<span class="tag">${l}</span><span class="tg"><b>${inW?l:l}</b><small>${q}</small></span></button>`;
  const body=items.map(it=>(!inW&&VIEW_G[it[0]]?`<div class="grp">${VIEW_G[it[0]]}</div>`:'')+btn(it)).join('');
  return `<div class="brand">${mark}<span class="bw"><b>__KIT_BRAND_NAME__</b><small>Webinar Analytics</small></span></div>${inW?`<button class="exit" data-exit="1" aria-label="Back to the programme">← All webinars</button>`:''}${body}
   <div class="gap"></div><button class="dk aux" id="themeBtn" aria-label="Light or dark">${ico('theme')}<span class="tag">Light / dark</span><span class="tg"><b>Light / dark</b></span></button>
   <button class="dk aux" data-health="1" aria-label="Data quality">${ico('data')}${MODEL.health.conflicts?'<i class="dot"></i>':''}<span class="tag">Data quality</span><span class="tg"><b>Data quality</b><small>What is complete, what is missing</small></span></button>`; }

const filtLabel = {
  webinars:()=>S.pick?plural(S.pick.length,'webinar'):'All webinars',
  channels:()=>S.ch==='all'?'All channels':S.ch==='cold'?'With cold email':'Calendar only',
  outcomes:()=>{ const p=[]; if(S.tier!=='all') p.push(TIER_L[S.tier]); if(S.rev!=='all') p.push(S.rev==='has'?'Earned revenue':'No revenue'); if(S.att!=='all') p.push(S.att==='high'?'Attendance above avg':'Attendance below avg'); return p.length?p.join(' · '):'All outcomes'; },
  dates:()=>`${dfmt(byN(S.from).date)} → ${dfmt(byN(S.to).date)}`
};
const filtOn = k => k==='webinars'?!!S.pick : k==='channels'?S.ch!=='all' : k==='outcomes'?(S.tier!=='all'||S.rev!=='all'||S.att!=='all') : (S.from!==W_ALL[0].n||S.to!==LAST.n);
function barHtml(){ const inW=S.w!=null, t=inW?`Webinar ${S.w}`:VIEW_L[S.view];
  const toks=(!inW&&FILTERED.includes(S.view))?['webinars','channels','outcomes','dates'].map(k=>`<button class="tok${filtOn(k)?' on':''}" data-filt="${k}" aria-haspopup="dialog">${esc(filtLabel[k]())}</button>`).join('')+(filtersOn()||S.from!==W_ALL[0].n||S.to!==LAST.n?'<button class="tok clr" data-reset="1">Clear</button>':''):'';
  return `<div class="crumb"><b>__KIT_BRAND_NAME__</b><span>${inW?`<button class="link" data-exit="1">All webinars</button> / ${t}`:t}${S.debug?' · debug':''}</span></div><div class="toks">${toks}</div><button class="guide-btn" data-guide="1" aria-label="How to read this dashboard"><b>?</b>Guide</button><button class="kbd" id="palBtn" aria-label="Search and jump"><b aria-hidden="true" style="font-size:16px;font-weight:400">⌕</b><span>Search</span><kbd>⌘K</kbd></button>`; }

/* ---------- tooltips ---------- */
const TIP=()=>$('#tip'); let tipFor=null;
function tipHtml(el){
  if(el.dataset.stage) return stageTip(el.dataset.stage);
  if(el.classList.contains('bub')&&el.dataset.w) return bubTip(byN(el.dataset.w));
  return el.dataset.tip?`<span>${esc(el.dataset.tip)}</span>`:null; }
function stageTip(k){ if(k==='visits') return '<span class="tl">Visits</span><span class="tv">\u2014</span>Website visits are not tracked, so the journey starts at the people we contacted.';
  if(k==='clicks') return `<span class="tl">Clicks</span><span class="tv">${f0(sum(MODEL.email_campaigns,c=>c.clicks))}</span>Clicks on links in cold emails only. Calendar-invitation replies have no click to count.`;
  const s=STAGE(k), list=ws(), v=s.money?totalsOf(list).rev:stageTotal(s,list), r=stageRank(s,list), rt=stageRate(s,list);
  const kinds=[...new Set(list.map(w=>w.m[k]&&w.m[k].k).filter(Boolean))].join(' · ');
  const row=(a,b)=>`<div class="tr2"><span>${a}</span><span>${b}</span></div>`;
  return `<span class="tl">${s.l}</span><span class="tv">${s.money?gbp(v):f0(v)}</span>${s.rate&&nn(rt)?row('Step rate',`${s.rf(rt)} ${s.rl}`):''}${r?row('Per-webinar average',s.rf(r.avg))+row('Strongest',`W${r.best.n} · ${s.rf(s.rate(r.best))}`)+row('Weakest',`W${r.worst.n} · ${s.rf(s.rate(r.worst))}`):''}${kinds?row('Status',kinds):''}<div style="opacity:.6;margin-top:6px">Click for the full breakdown</div>`; }
function bubTip(w){ const k=S.lm, g=MET[k], v=metVal(w,k), st=statsOf(W_ALL,k), d=pchg(v,st.avg);
  const row=(a,b)=>`<div class="tr2"><span>${a}</span><span>${b}</span></div>`;
  return `<span class="tl">W${w.n} · ${dfull(w.date)}</span><span class="tv">${nn(v)?g.f(v):'\u2014'}</span>${nn(d)?row('vs average',`${d>0?'+':'−'}${Math.abs(d).toFixed(0)}%`):''}${row('Overall',f1(w.score.total)+(w.mature?'':'†'))}${row('Registered',f0(w.m.registrations.v))}${row('Attended',f0(w.m.attended.v)+' · '+pc(w.r.attend_pct,0))}${row('Revenue',nn(w.m.revenue.v)?gbp(w.m.revenue.v)+(w.mature?'':'*'):'\u2014')}<div style="opacity:.6;margin-top:6px">Click to open · shift-click to compare</div>`; }
function showTip(el,e){ const h=tipHtml(el); if(!h){ hideTip(); return; } const t=TIP(); t.innerHTML=h; t.classList.add('on'); tipFor=el; moveTip(e); }
function moveTip(e){ const t=TIP(), r=t.getBoundingClientRect(); let x=e.clientX+16,y=e.clientY+16; if(x+r.width>innerWidth-8) x=e.clientX-r.width-16; if(y+r.height>innerHeight-8) y=e.clientY-r.height-16; t.style.left=Math.max(8,x)+'px'; t.style.top=Math.max(8,y)+'px'; }
function hideTip(){ TIP().classList.remove('on'); tipFor=null; }
function hot(n,on){ $$(`[data-w="${n}"]`).forEach(x=>x.classList.toggle('hot',on)); const l=$('#land'); if(l) l.classList.toggle('dim',on); }

/* ---------- drawers ---------- */
function openDrawer(html){ const d=$('#drawer'); d.innerHTML=`<button class="x" data-close="1" aria-label="Close">✕</button>${html}`; d.classList.add('on'); $('#scrim').classList.add('on'); d.scrollTop=0; d.querySelector('.x').focus(); }
function closeDrawer(){ $('#drawer').classList.remove('on'); $('#scrim').classList.remove('on'); }
const kindChip = k => `<span class="sv">${k}</span>`;
function downstream(s,list){ const T=totalsOf(list), i=STAGES.indexOf(s); const rows=[]; const defs={attended:['Attended',T.att],calls:['Booked a call',T.calls],customers:['Became a customer',T.cust],revenue:['Revenue credited to a webinar',T.rev]};
  STAGES.slice(i+1).forEach(n=>{ if(n.k==='registrations') return; const d=defs[n.k]; if(d) rows.push({k:d[0],v:n.money?T.rev:d[1],t:n.money?gbp(T.rev):f0(d[1])+(s.k==='registrations'&&T.reg?` · ${pc(d[1]/T.reg*100,n.k==='attended'?1:2)}`:'')}); });
  return rows; }
function drawerStage(k){ const list=ws(), T=totalsOf(list);
  if(k==='visits'||k==='clicks'){ const E=MODEL.email_campaigns; return openDrawer(`<span class="lbl">${k==='visits'?'Website visits':'Clicks'}</span><h2 class="num">${k==='visits'?'\u2014':f0(sum(E,c=>c.clicks))}</h2><p class="sub">${k==='visits'?'Website visits are not tracked, so the journey starts at the people contacted. Nothing is estimated.':'Clicks are counted on links in cold emails only. Calendar invitations have no link to click, and opens are not measured.'}</p>${k==='clicks'?`<h4 class="lbl">By campaign</h4>${rowsOf(E.filter(c=>c.clicks).map(c=>({k:esc(c.name),v:c.clicks,w:c.mapped_webinar||null})),{})}`:''}`); }
  const s=STAGE(k), v=s.money?T.rev:stageTotal(s,list), rt=stageRate(s,list), r=stageRank(s,list), kinds=[...new Set(list.map(w=>w.m[k]&&w.m[k].k).filter(Boolean))];
  let h=`<span class="lbl">${s.l} · ${esc(scopeLabel())}</span><h2 class="num">${s.money?gbp(v):f0(v)}</h2>${s.rate&&nn(rt)?`<p class="sub"><b>${s.rf(rt)}</b> ${s.rl}</p>`:''}<p class="sub" style="margin-top:8px">${kinds.map(kindChip).join(' ')} ${esc(DEF[s.def]||'')}</p>`;
  if(s.com&&list.some(w=>!w.mature)) h+=`<p class="sub" style="margin-top:8px">* Includes ${list.filter(w=>!w.mature).map(w=>'W'+w.n).join(', ')} \u2014 ${esc(MAT().toLowerCase())}.</p>`;
  if(r) h+=`<h4 class="lbl">Strongest and weakest</h4><div class="rows"><div class="row" data-w="${r.best.n}"><span class="k">Strongest · W${r.best.n}</span><span></span><span class="vv up">${s.rf(s.rate(r.best))}</span></div><div class="row" data-w="${r.worst.n}"><span class="k">Weakest · W${r.worst.n}</span><span></span><span class="vv dn">${s.rf(s.rate(r.worst))}</span></div></div>`;
  h+=`<h4 class="lbl">Which webinars</h4>${rowsOf(list.map(w=>({k:`W${w.n} · ${dfmt(w.date)}`,v:s.get(w)||0,t:(nn(s.get(w))?(s.money?gbp(s.get(w)):f0(s.get(w))):'\u2014')+(s.com&&!w.mature?'*':''),w:w.n})),{gold:s.money})}`;
  if(k==='registrations'){ const parts=REG_METHODS.map(([kk,l])=>({k:l,v:sum(list,w=>w.m[kk].v)})); h+=`<h4 class="lbl">Where they came from</h4>${rowsOf(parts,{})}<div class="states">${stateOf('Website / LinkedIn / paid','Not tracked')}</div>`;
    const E=campaignsFor(list); h+=`<h4 class="lbl">Which campaigns</h4>${E.length?rowsOf(E.map(c=>({k:`${esc(c.name)}`,v:c.sent,t:f0(c.sent)+' sent',w:c.mapped_webinar})),{}):'<div class="states">'+stateOf('Campaigns','None attributed')+'</div>'}`; }
  if(k==='outreach') h+=`<h4 class="lbl">How they were contacted</h4>${rowsOf([{k:'Calendar invitations',v:sum(list,w=>w.m.calendar.v)},{k:'Cold email as well',v:sum(list,w=>w.m.cold_email.v)}],{})}`;
  if(k==='attended') h+=`<h4 class="lbl">Registered but did not attend</h4><p class="sub"><b>${f0(T.noshow)}</b> people. Live and replay viewers overlap, so they are never added.</p>`;
  const dn=downstream(s,list); if(dn.length) h+=`<h4 class="lbl">${k==='registrations'?'What those registrations led to':'What happened next'}</h4>${rowsOf(dn,{gold:true})}`;
  if(s.money) h+=`<p class="sub" style="margin-top:14px"><button class="link" data-prov="revenue">Revenue provenance →</button></p>`;
  openDrawer(h); }
function drawerSource(k){ const list=ws(), p=REG_METHODS.find(x=>x[0]===k), tot=sum(list,w=>w.m[k].v);
  openDrawer(`<span class="lbl">Sign-up method</span><h2 class="num">${f0(tot)}</h2><p class="sub"><b>${esc(p[1])}</b></p><h4 class="lbl">By webinar</h4>${rowsOf(list.map(w=>({k:`W${w.n} · ${dfmt(w.date)}`,v:w.m[k].v||0,w:w.n,t:f0(w.m[k].v)})),{})}<p class="sub" style="margin-top:14px">${esc(DEF['Registration']||'')}</p>`); }
function drawerRevenue(){ const C=MODEL.commercial, list=ws();
  openDrawer(`<span class="lbl">Revenue provenance</span><h2 class="num" style="color:var(--gold-t)">${gbp(C.total.revenue)}</h2><p class="sub">Total paid by ${plural(C.total.customers,'customer')}.</p>
   <h4 class="lbl">How it splits</h4>${rowsOf([{k:'Credited to a webinar',v:C.webinar_attributed.revenue,t:gbp(C.webinar_attributed.revenue)+' · '+C.webinar_attributed.customers+' customers'},{k:'Paid without attending any webinar',v:C.unattributed.revenue,t:gbp(C.unattributed.revenue)+' · '+C.unattributed.customers+' buyers'}],{gold:true})}
   <p class="sub" style="margin-top:12px">The buyers in the second line never attended a webinar. Where they came from is not recorded \u2014 it is not assumed to be LinkedIn or any other channel.</p>
   <h4 class="lbl">How credit is given</h4><p class="sub">${esc(C.attribution_rule)}. ${esc(scrub(C.channel_attribution))}</p>
   <h4 class="lbl">By webinar</h4>${list.map(w=>`<div class="row" style="display:grid;grid-template-columns:90px 1fr auto auto;gap:10px;padding:6px 0;align-items:center;cursor:pointer" data-w="${w.n}"><span class="k" style="font-size:14.5px">W${w.n}</span><span class="sub">${plural(w.m.customers.v||0,'customer')}${w.mature?'':' · maturing'}</span><span class="vv" style="font-weight:600">${nn(w.m.revenue.v)?gbp(w.m.revenue.v):'\u2014'}</span>${provBtn(w,'revenue','Revenue',gbp)}</div>`).join('')}
   <p class="sub" style="margin-top:14px">${gbp(C.committed_not_received)} more is committed but not yet received.</p>`); }
function drawerPM(id){ const p=PROVS[id]; if(!p) return; const m=p.m, w=byN(p.w), f=({gbp,f0})[p.fmt]||(v=>String(v));
  openDrawer(`<span class="lbl">W${p.w} · ${esc(p.label)}</span><h2 class="num">${nn(m.v)?f(m.v)+(p.imm?'*':''):'\u2014'}</h2><p class="sub">${kindChip(m.k)} ${esc(DEF[m.k]||'')}</p>
   <h4 class="lbl">Where this number comes from</h4><p class="sub">${esc(scrub(m.s))}</p>${p.imm?`<p class="sub" style="margin-top:8px">* ${esc(MAT())} \u2014 shown as recorded so far.</p>`:''}${m.note?`<h4 class="lbl">Note</h4><p class="sub">${esc(scrub(m.note))}</p>`:''}
   ${m.alts&&m.alts.length?`<h4 class="lbl">Other sources report</h4><div class="ledger">${m.alts.map(a=>`<div class="li"><span>${esc(scrub(a.s))}</span><span><b>${f(a.v)}</b></span><span></span></div>`).join('')}</div><p class="sub" style="margin-top:8px">${m.conflict?'These sources disagree by more than 5%. The first value is the one shown.':'These agree within tolerance.'}</p>`:''}`); }
function drawerGuide(){
  openDrawer(`<span class="lbl">How to read this</span><h2 style="font-size:clamp(30px,4vw,42px);letter-spacing:-.03em">Three steps</h2>
   <ol class="steps"><li><span><b>Start on Overview.</b> The snapshot shows how the programme is doing, the chart shows the direction, and "What deserves attention" lists what stands out.</span></li>
   <li><span><b>Pick a question in the left menu.</b> Acquisition, Audience, Engagement and Commercial each answer one plain question. Hover a menu item for what it covers.</span></li>
   <li><span><b>Click anything.</b> Every ribbon stage, bubble, bar and number opens its detail. Click a webinar bubble to open that webinar on its own; use "All webinars" to come back.</span></li></ol>
   <h4 class="lbl">Colours</h4><div class="key"><i style="background:var(--ocean)"></i><span>Blue means people</span><i style="background:var(--gold)"></i><span>Gold means money only</span><i style="background:var(--good)"></i><span>Green means better than average</span><i style="background:var(--bad)"></i><span>Red means worse than average</span></div>
   <h4 class="lbl">Good to know</h4><div class="ledger"><div class="li"><span><b>A dash is not zero</b><small>It means that figure is not recorded. Nothing is guessed or filled in.</small></span><span></span><span></span></div><div class="li"><span><b>* = still maturing</b><small>Recent webinars have not finished producing calls and sales yet, so their totals will rise.</small></span><span></span><span></span></div><div class="li"><span><b>Ribbon width is a square root</b><small>That is how 20 customers stay visible next to 357K people contacted. The taper is the drop-off.</small></span><span></span><span></span></div><div class="li"><span><b>Shortcuts</b><small>Press ⌘K (or /) to search any webinar or view. Press Esc to close panels.</small></span><span></span><span></span></div></div>
   <button class="btn" style="margin-top:22px" data-close="1">Got it</button>`); }
function drawerHealth(){ const H=MODEL.health, cs=H.conflict_register, open=cs.filter(c=>/^OPEN/.test(c.status)); const stale=H.stale_feeds||[];
  openDrawer(`<span class="lbl">Data quality</span><h2 class="num">${f0(H.completeness_pct)}%</h2><p class="sub"><b>${H.completeness_pct>=99.5?'All data is complete.':'Some data is incomplete.'}</b> ${f0(H.completeness_pct)}% of the figures this dashboard expects are available. Anything missing is shown as a dash, never as zero.</p><p class="sub" style="margin-top:8px">Revenue figures are available for ${statsOf(W_ALL,'revenue').n} of the ${W_ALL.filter(w=>w.mature).length} webinars old enough to have complete sales.</p>
   <h4 class="lbl">Figures that differ between sources</h4><p class="sub"><b>${open.length}</b> still being checked · ${cs.length-open.length} already confirmed against the underlying records.</p>
   <div class="ledger">${open.slice(0,8).map(c=>`<div class="li" data-w="${c.n}" style="cursor:pointer"><span><b>W${c.n}</b> · ${esc(c.metric)}<small>${esc(c.a.s)} reports ${f0(c.a.v)}; ${c.others.map(o=>esc(o.s)+' '+f0(o.v)).join(', ')}</small></span><span></span><span></span></div>`).join('')}</div>
   <h4 class="lbl">Not available yet</h4><div class="ledger">${H.missing_by_field.slice(0,7).map(f=>`<div class="li"><span>${esc(f.field.replace(/_/g,' '))}<small>${esc(f.reason)}</small></span><span class="sv">${f.webinars.length===W_ALL.length?'all':f.webinars.length+' webinars'}</span><span></span></div>`).join('')}</div>
   <h4 class="lbl">What cannot be traced</h4><div class="ledger">${H.attribution_gaps.map(g=>`<div class="li"><span><b>${esc(g.gap)}</b><small>${esc(scrub(g.detail))}</small></span><span></span><span></span></div>`).join('')}</div>
   ${S.debug&&stale.length?`<h4 class="lbl">Stale feeds (debug)</h4><div class="ledger">${stale.map(f=>`<div class="li"><span>${esc(f.what)}<small>${esc(f.updated||'')} ${esc(f.note||'')}</small></span><span></span><span></span></div>`).join('')}</div>`:''}`); }
function drawerEvidence(s){ openDrawer(`<span class="lbl">${KIND_L[s.kind]||s.kind}</span><p class="h2" style="margin:14px 0 18px;font-size:28px">${s.text}</p><h4 class="lbl">Evidence</h4><p class="sub">${esc(scrub(s.ev||''))}</p><div style="margin-top:20px;display:flex;gap:8px"><button class="btn" data-fsig-obj="1">Explore</button></div>`); window._evSig=s; }
function drawerQ(cat){ const qs=MODEL.questions.items.filter(q=>q.cats.includes(cat)).sort((a,b)=>b.up-a.up).slice(0,12);
  openDrawer(`<span class="lbl">Questions · ${esc(cat.toLowerCase())}</span><h2 class="num">${qs.length}</h2><div class="ledger">${qs.map(q=>`<div class="li" ${q.n?`data-w="${q.n}" data-wtab="content"`:''} style="cursor:pointer"><span>${esc(q.q)}<small>${q.n?'W'+q.n:'Webinar unknown'}</small></span><span class="sv">▲ ${q.up}</span><span></span></div>`).join('')}</div><p class="sub" style="margin-top:12px">${esc(MODEL.questions.caveat||'')}</p>`); }
function act(s){ closeDrawer(); if(s.lm&&MET[s.lm]) { nav({view:'webinars',lm:s.lm}); return; } if(s.prov==='revenue'&&!s.w) { nav({view:s.view||'commercial'}); return; } if(s.w) openW(s.w,s.tab); else if(s.stage) { nav({view:s.view||'overview'}); drawerStage(s.stage); } else nav({view:s.view||'overview'}); }

/* ---------- fullscreen focus (charts get the whole screen) ---------- */
function openFS(kind){ let el=$('#fsv'); if(!el){ el=document.createElement('div'); el.id='fsv'; el.className='fs-on'; document.body.appendChild(el); }
  const list=ws(); el.innerHTML=`<button class="x ico-btn" data-closefs="1" style="position:fixed;top:18px;right:22px;font-size:15px" aria-label="Close">✕ Close</button>${kind==='river'?`<span class="lbl">The journey · ${esc(scopeLabel())}</span><div style="margin-top:22px;max-width:1500px">${flow({list,W:Math.min(innerWidth*.9,1400),h:420,hmax:200,cy:160})}</div>`:`<span class="lbl">Webinar landscape</span><div style="margin-top:14px">${landMetricChips()}</div><div style="margin-top:18px">${landscape({W:Math.min(innerWidth*.9,1500),H:Math.max(380,innerHeight-260)})}</div>`}`;
  S.fs=kind; }
function closeFS(){ const el=$('#fsv'); if(el) el.remove(); S.fs=null; }

/* ---------- filter popovers ---------- */
function openPop(kind,anchor){ const p=$('#pop'); let h='';
  if(kind==='webinars') h=`<div class="grp lbl">Webinars</div>${W_ALL.map(w=>`<label><input type="checkbox" data-pk="${w.n}" ${(!S.pick||S.pick.includes(w.n))?'checked':''}> <b>W${w.n}</b> <span class="na">${dfmt(w.date)}</span> ${tierPill(w)}</label>`).join('')}<div style="display:flex;gap:8px;padding:8px"><button class="btn q" data-pall="1">All</button><button class="btn q" data-pnone="1">Top performers</button></div>`;
  if(kind==='channels') h=`<div class="grp lbl">Channels</div>${[['all','All channels'],['cal','Calendar invitations only'],['cold','Calendar + cold email']].map(([v,l])=>`<label><input type="radio" name="ch" data-ch="${v}" ${S.ch===v?'checked':''}> ${l}</label>`).join('')}`;
  if(kind==='outcomes') h=`<div class="grp lbl">Result</div><select data-sel="tier" aria-label="Result"><option value="all">Any result</option>${Object.entries(TIER_L).map(([k,l])=>`<option value="${k}" ${S.tier===k?'selected':''}>${l}</option>`).join('')}</select><div class="grp lbl">Revenue</div><select data-sel="rev" aria-label="Revenue"><option value="all">Any</option><option value="has" ${S.rev==='has'?'selected':''}>Earned revenue</option><option value="none" ${S.rev==='none'?'selected':''}>Mature, no revenue</option></select><div class="grp lbl">Attendance</div><select data-sel="att" aria-label="Attendance"><option value="all">Any</option><option value="high" ${S.att==='high'?'selected':''}>At or above average</option><option value="low" ${S.att==='low'?'selected':''}>Below average</option></select>`;
  if(kind==='dates') h=`<div class="grp lbl">From</div><select data-sel="from" aria-label="From">${W_ALL.map(w=>`<option value="${w.n}" ${S.from===w.n?'selected':''}>W${w.n} · ${dfmt(w.date)}</option>`).join('')}</select><div class="grp lbl">To</div><select data-sel="to" aria-label="To">${W_ALL.map(w=>`<option value="${w.n}" ${S.to===w.n?'selected':''}>W${w.n} · ${dfmt(w.date)}</option>`).join('')}</select>`;
  p.innerHTML=h; const r=anchor.getBoundingClientRect(); p.style.left=Math.max(8,Math.min(r.left,innerWidth-350))+'px'; p.style.top=(r.bottom+8)+'px'; p.dataset.kind=kind; p.classList.add('on'); }
function closePop(){ $('#pop').classList.remove('on'); }
function resetFilters(){ S.pick=null; S.ch='all'; S.tier='all'; S.rev='all'; S.att='all'; S.from=W_ALL[0].n; S.to=LAST.n; S.sel=[]; }

/* ---------- command palette ---------- */
let PAL=[], palI=0;
function palItems(){ const it=[], v=(t,go,kw)=>it.push({t,go,kw:(kw||'')+' '+t,tag:'View'});
  v('Overview',{view:'overview'},'home command centre summary revenue'); v('Webinars',{view:'webinars'},'explorer landscape compare ranking table'); v('Acquisition',{view:'acquisition'},'source email linkedin organic paid traffic clicks visits channel registration sources campaigns');
  v('Audience',{view:'audience'},'geography country seniority company size titles uk decision maker'); v('Engagement',{view:'engagement'},'attendance questions chat polls watch drop-off attention'); v('Commercial',{view:'commercial'},'revenue money customers calls sales attribution');
  v('Insights',{view:'intelligence'},'insights signals recommendations anomalies trends'); v('Next webinar',{view:'next'},'upcoming w12 readiness campaign');
  W_ALL.forEach(w=>{ it.push({t:`Webinar ${w.n}`,go:{w:w.n},kw:`w${w.n} webinar ${w.n} ${dfull(w.date)}`,tag:dfmt(w.date),sub:`${tierPill(w).replace(/<[^>]+>/g,'')}`}); WTABS.slice(1).forEach(([k,l])=>it.push({t:`Webinar ${w.n} · ${l}`,go:{w:w.n,tab:k},kw:`w${w.n} ${l}`,tag:'Workspace'})); });
  it.push({t:'Strongest webinar',go:{w:BEST.n},kw:'best top winner highest',tag:'W'+BEST.n}); it.push({t:'Weakest webinar',go:{w:WORST.n},kw:'worst lowest',tag:'W'+WORST.n});
  it.push({t:'Revenue',go:{view:'commercial'},kw:'money sales __KIT_CURRENCY_SYMBOL__',tag:'Metric'}); it.push({t:'Revenue by source',go:{view:'commercial'},kw:'attribution channel unlinked',tag:'Metric'}); it.push({t:'Unlinked revenue',go:{prov:1},kw:'unattributed never attended',tag:'Metric'});
  it.push({t:'Registrations',go:{stage:'registrations'},kw:'registered sign ups',tag:'Metric'}); it.push({t:'Attendance',go:{view:'engagement'},kw:'attended no show',tag:'Metric'}); it.push({t:'Attendees',go:{stage:'attended'},kw:'attended',tag:'Metric'}); it.push({t:'Calls',go:{stage:'calls'},kw:'booked',tag:'Metric'}); it.push({t:'Customers',go:{stage:'customers'},kw:'buyers paid',tag:'Metric'});
  it.push({t:'Email',go:{view:'acquisition'},kw:'cold email campaigns instantly',tag:'Source'}); it.push({t:'LinkedIn',go:{view:'acquisition'},kw:'social',tag:'Source'}); it.push({t:'Questions',go:{view:'engagement'},kw:'asked q&a topics',tag:'Metric'});
  it.push({t:'Data reliability',go:{health:1},kw:'quality conflicts missing confidence',tag:'Data'}); it.push({t:'Table view of webinars',go:{view:'webinars',tbl:true},kw:'spreadsheet exact numbers',tag:'View'}); it.push({t:'Toggle light / dark',go:{theme:1},kw:'theme mode',tag:'Action'}); it.push({t:'Clear all filters',go:{reset:1},kw:'reset',tag:'Action'});
  return it; }
function palRender(){ const q=$('#palq').value.trim().toLowerCase(), toks=q.split(/\s+/).filter(Boolean);
  PAL=palItems().map(i=>{ const hay=(i.kw+' '+i.t).toLowerCase(); if(!toks.every(t=>hay.includes(t))) return null; const sc=toks.reduce((s,t)=>s+(i.t.toLowerCase().startsWith(t)?3:i.t.toLowerCase().includes(t)?2:1),0); return {...i,sc}; }).filter(Boolean).sort((a,b)=>b.sc-a.sc).slice(0,q?10:9);
  palI=Math.min(palI,Math.max(PAL.length-1,0));
  $('#pall').innerHTML=PAL.map((i,n)=>`<li role="option" data-pi="${n}" class="${n===palI?'on':''}"><span>${esc(i.t)}</span>${i.sub?`<em>${esc(i.sub)}</em>`:''}<small>${i.tag||''}</small></li>`).join('')||'<li><em>Nothing matches \u2014 try “revenue”, “W5” or “email”.</em></li>'; }
function palOpen(){ $('#pal').classList.add('on'); $('#palq').value=''; palI=0; palRender(); setTimeout(()=>$('#palq').focus(),10); }
function palClose(){ $('#pal').classList.remove('on'); }
function palGo(i){ const it=PAL[i]; if(!it) return; palClose(); const g=it.go;
  if(g.theme){ toggleTheme(); return; } if(g.reset){ resetFilters(); render({}); return; } if(g.health){ drawerHealth(); return; } if(g.prov){ nav({view:'commercial'}); drawerRevenue(); return; }
  if(g.stage){ nav({view:'overview'}); drawerStage(g.stage); return; } if(g.w){ openW(g.w,g.tab); return; } if(g.tbl){ S.tbl=true; } nav({view:g.view}); }

/* ---------- routing ---------- */
const depth = () => S.w!=null?1:0;
function writeHash(){ const p=[]; if(S.w!=null){ p.push('w='+S.w); if(S.wtab!=='overview') p.push('tab='+S.wtab); } else if(S.view!=='overview') p.push('view='+S.view); if(S.noanim) p.push('anim=0'); if(S.debug) p.push('debug=1'); try{ history.replaceState(null,'','#'+p.join('&')); }catch(e){} }
function nav(o){ const d0=depth(); if('view' in o){ S.w=null; S.view=o.view; } Object.keys(o).forEach(k=>{ if(!['view'].includes(k)) S[k]=o[k]; }); closeDrawer(); closePop(); closeFS(); writeHash(); render({dive:true,z:depth()>d0?.975:depth()<d0?1.02:.99}); window.scrollTo(0,0); }
function openW(n,tab){ const d0=depth(); S.w=+n; S.wtab=tab||'overview'; closeDrawer(); closePop(); closeFS(); writeHash(); render({dive:true,z:depth()>d0?.975:.99}); window.scrollTo(0,0); }
function applyHash(){ try{ const h=Object.fromEntries((location.hash||'').replace(/^#/,'').split('&').filter(Boolean).map(p=>p.split('=')));
  if(h.anim==='0'||(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)){ S.noanim=true; document.documentElement.classList.add('noanim'); } if(h.debug==='1') S.debug=true;
  if(h.w&&byN(h.w)){ S.w=+h.w; S.wtab=WTABS.some(t=>t[0]===h.tab)?h.tab:'overview'; } else { S.w=null; if(h.view&&VIEWFN[h.view]) S.view=h.view; } }catch(e){} }

/* ---------- theme ---------- */
function setTheme(t){ S.theme=t; document.documentElement.dataset.theme=t; try{ localStorage.setItem('wi-theme',t); }catch(e){} }
function toggleTheme(){ setTheme(S.theme==='dark'?'light':'dark'); render({}); }
function initTheme(){ let t=null; try{ t=localStorage.getItem('wi-theme'); }catch(e){} if(t!=='dark') t='light'; setTheme(t); }

/* ---------- debug (only with #debug=1) ---------- */
function debugBlock(){ const H=MODEL.health, q=MODEL.qa; const L=[];
  L.push('DEBUG \u2014 internal information, hidden from the client view'); L.push(`build ${MODEL.build} · model generated ${MODEL.generated} · today ${MODEL.today}`); L.push('');
  L.push('PIPELINE'); L.push(H.pipeline.last_run_text||''); L.push('SOURCES'); MODEL.sources.forEach(s=>L.push(`  ${s.kind.padEnd(9)} ${s.name} \u2014 ${s.file} (${s.updated})`));
  L.push(''); L.push(`DATA QUALITY completeness ${H.completeness_pct}% · conflicts ${H.conflicts} · stale feeds ${(H.stale_feeds||[]).length}`);
  (H.stale_feeds||[]).forEach(f=>L.push(`  stale: ${f.what} ${f.updated||''} ${f.note||''}`));
  L.push(''); L.push('ATTENDANCE DEFINITION'); L.push('  '+(MODEL.config.attendance_definition.canonical||''));
  L.push(''); L.push('READINESS / DEPLOYMENT'); L.push('  authentication: '+JSON.stringify(MODEL.config.authentication.status)+' · cloudflare access: '+JSON.stringify(MODEL.config.cloudflare_access.status));
  if(q){ L.push(''); L.push(`QA (run ${q.ran}${q.stale?' \u2014 STALE':''})`); Object.entries(q.checks).forEach(([k,v])=>L.push(`  ${v.status.padEnd(5)} ${k} \u2014 ${v.detail}`)); }
  return `<div class="dbg">${esc(L.join('\n'))}</div>`; }

/* ---------- brand footer + data freshness (turns amber when the data is old) ---------- */
function footHtml(){ const g=MODEL.generated||'', m=/(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})/.exec(g); let age=null;
  if(m){ const t=Date.UTC(+m[1],+m[2]-1,+m[3],+m[4],+m[5])-5.5*3600e3; age=(Date.now()-t)/3600e3; }
  const old=age!=null&&age>26, ago=age==null?'':age<1?'less than an hour ago':age<48?`${Math.round(age)} hours ago`:`${Math.round(age/24)} days ago`;
  return `<footer class="foot${old?' old':''}"><b>__KIT_BRAND_NAME__</b> · Webinar Analytics<span class="sp"></span><span>${old?`Not refreshed for ${ago} \u2014 figures may be out of date. `:''}Data as of ${esc(asOf(g))}${ago&&!old?` (${ago})`:''}</span></footer>`; }
/* ---------- render + motion ---------- */
const PREV={}; const SEEN={};
const FM={f0,gbp:f0,k1:v=>(v/1000).toFixed(1),f1};
function render(o){ o=o||{}; const cv=$('#canvas'), fl={};
  if(!o.dive&&!S.noanim) $$('[data-flip]').forEach(e=>{ const r=e.getBoundingClientRect(); fl[e.dataset.flip]=r; });
  Object.keys(PROVS).forEach(k=>delete PROVS[k]);
  $('#dock').innerHTML=dockHtml(); $('#bar').innerHTML=barHtml();
  let html; try{ html=(S.w!=null?vWorkspace():VIEWFN[S.view]())+(S.debug?debugBlock():''); }catch(err){ console.error(err); html=`<div class="rise" style="padding:50px 0"><div class="h2">This view could not be drawn.</div><p class="sub" style="margin-top:8px">${esc(String(err.message||err))}</p><button class="btn" style="margin-top:14px" data-reset="1">Reset and reload</button></div>`; }
  cv.innerHTML=html+footHtml(); cv.classList.toggle('still',!o.dive);
  if(o.dive){ cv.style.setProperty('--z',o.z||.985); cv.classList.remove('dive'); void cv.offsetWidth; cv.classList.add('dive'); }
  document.title=(S.w!=null?`Webinar ${S.w}`:VIEW_L[S.view])+' · __KIT_BRAND_NAME__ Dashboard';
  afterRender(fl,o); }
function afterRender(fl,o){
  $$('[data-ck]').forEach(el=>{ const key=el.dataset.ck, to=parseFloat(el.dataset.v), f=FM[el.dataset.f]||f0, tgt=el.querySelector('.cv')||el; if(Number.isNaN(to)){ return; }
    const from=(key in PREV)?PREV[key]:0; PREV[key]=to; if(S.noanim||from===to||(!o.dive&&!(key in PREV)&&false)) { tgt.textContent=f(to); return; }
    if(o.dive&&SEEN[key]) { tgt.textContent=f(to); return; } SEEN[key]=1;
    const t0=performance.now(), dur=o.dive?650:420; const step=t=>{ const k=Math.min(1,(t-t0)/dur), e=1-Math.pow(1-k,3); tgt.textContent=f(from+(to-from)*e); if(k<1) requestAnimationFrame(step); else tgt.textContent=f(to); }; requestAnimationFrame(step); });
  if(!S.noanim&&!o.dive&&Object.keys(fl).length){ $$('[data-flip]').forEach(e=>{ const a=fl[e.dataset.flip]; if(!a) return; const b=e.getBoundingClientRect(); if(!b.width||!a.width) return;
      const dx=a.left-b.left, dy=a.top-b.top, sx=a.width/b.width, sy=a.height/b.height; if(Math.abs(dx)+Math.abs(dy)<1&&Math.abs(sx-1)<.01&&Math.abs(sy-1)<.01) return;
      try{ e.animate([{transformOrigin:'0 0',transform:`translate(${dx}px,${dy}px) scale(${sx},${sy})`},{transformOrigin:'0 0',transform:'none'}],{duration:380,easing:'cubic-bezier(.2,.8,.2,1)'}); }catch(x){} }); }
  const snap=$('#snap'); if(snap&&innerWidth<=760){ snap.onscroll=()=>{ const i=Math.round(snap.scrollLeft/snap.clientWidth); if(i!==S.pane){ S.pane=i; $$('#pager button').forEach((b,n)=>b.classList.toggle('on',n===i)); } }; snap.scrollLeft=S.pane*snap.clientWidth; }
}

/* ---------- events ---------- */
function bind(){
  const D=document;
  D.addEventListener('click',e=>{ const t=e.target, c=s=>t.closest(s);
    let x;
    if(c('[data-close]')||t.id==='scrim'){ closeDrawer(); return; } if(c('[data-closefs]')){ closeFS(); return; }
    if(!c('.pop')&&!c('[data-filt]')) closePop();
    if((x=c('[data-pm]'))){ drawerPM(x.dataset.pm); return; }
    if((x=c('[data-prov]'))){ drawerRevenue(); return; }
    if((x=c('[data-stage]'))){ drawerStage(x.dataset.stage); return; } if((x=c('[data-src]'))){ drawerSource(x.dataset.src); return; }
    if((x=c('[data-sig]'))){ act(worth()[+x.dataset.sig]); return; } if((x=c('[data-fsig]'))){ act(feed()[+x.dataset.fsig]); return; } if((x=c('[data-evid]'))){ drawerEvidence(feed()[+x.dataset.evid]); return; } if(c('[data-fsig-obj]')){ act(window._evSig); return; }
    if((x=c('[data-qcat]'))){ drawerQ(x.dataset.qcat); return; }
    if((x=c('[data-tm]'))){ S.tm=x.dataset.tm; render({}); return; }
    if((x=c('[data-lm]'))){ S.lm=x.dataset.lm; render({}); if(S.fs) { openFS(S.fs); } return; }
    if(c('[data-selmode]')){ S.selMode=!S.selMode; render({}); return; } if(c('[data-selclear]')){ S.sel=[]; render({}); return; }
    if((x=c('[data-cmp]'))){ nav({view:'webinars'}); return; }
    if((x=c('[data-tbl]'))){ S.tbl=x.dataset.tbl==='1'; render({}); return; }
    if((x=c('[data-sort]'))){ const k=x.dataset.sort; if(S.sort===k) S.dir*=-1; else { S.sort=k; S.dir=-1; } render({}); return; }
    if((x=c('[data-filt]'))){ const p=$('#pop'); if(p.classList.contains('on')&&p.dataset.kind===x.dataset.filt){ closePop(); } else openPop(x.dataset.filt,x); return; }
    if(c('[data-reset]')){ resetFilters(); closePop(); render({}); return; }
    if((x=c('[data-fs]'))){ openFS(x.dataset.fs); return; }
    if((x=c('[data-pane]'))){ const sn=$('#snap'); S.pane=+x.dataset.pane; if(sn) sn.scrollTo({left:S.pane*sn.clientWidth,behavior:S.noanim?'auto':'smooth'}); $$('#pager button').forEach((b,n)=>b.classList.toggle('on',n===S.pane)); return; }
    if(c('[data-exit]')){ nav({view:S.view}); return; }
    if((x=c('[data-dock]'))){ const k=x.dataset.dock; if(x.dataset.dt==='wtab'){ S.wtab=k; writeHash(); render({dive:true,z:.995}); } else nav({view:k}); return; }
    if(c('[data-guide]')){ drawerGuide(); return; }
    if(c('[data-health]')){ drawerHealth(); return; }
    if(c('#themeBtn')){ toggleTheme(); return; } if(c('#palBtn')){ palOpen(); return; }
    if((x=c('[data-pi]'))){ palGo(+x.dataset.pi); return; } if(t.id==='pal'){ palClose(); return; }
    if((x=c('[data-wtab]'))&&c('.wtabs')){ S.wtab=x.dataset.wtab; writeHash(); render({dive:true,z:.995}); return; }
    if((x=c('[data-go]'))&&!c('[data-w]')){ nav({view:x.dataset.go}); return; }
    if((x=c('.bub[data-w]'))){ const n=+x.dataset.w; if(S.selMode||e.shiftKey||e.metaKey||e.ctrlKey){ S.sel=S.sel.includes(n)?S.sel.filter(v=>v!==n):[...S.sel,n].slice(-3); render({}); return; } openW(n); return; }
    if((x=c('[data-w]'))){ openW(x.dataset.w,x.dataset.wtab); return; }
  });
  D.addEventListener('change',e=>{ const t=e.target; let ch=false;
    if(t.dataset.pk){ const on=$$('[data-pk]').filter(i=>i.checked).map(i=>+i.dataset.pk); S.pick=on.length===W_ALL.length?null:on; ch=true; }
    if(t.dataset.ch){ S.ch=t.dataset.ch; ch=true; }
    if(t.dataset.sel){ const k=t.dataset.sel; S[k]=(k==='from'||k==='to')?+t.value:t.value; if(S.from>S.to){ if(k==='from') S.to=S.from; else S.from=S.to; } ch=true; }
    if(ch){ const kind=$('#pop').dataset.kind; render({}); const a=$(`[data-filt="${kind}"]`); if(a&&$('#pop').classList.contains('on')) { const r=a.getBoundingClientRect(); $('#pop').style.left=Math.max(8,Math.min(r.left,innerWidth-350))+'px'; $('#pop').style.top=(r.bottom+8)+'px'; } } });
  D.addEventListener('click',e=>{ const t=e.target; if(t.dataset&&t.dataset.pall){ S.pick=null; render({}); openPop('webinars',$('[data-filt="webinars"]')||t); } if(t.dataset&&t.dataset.pnone){ S.pick=W_ALL.filter(w=>tierOf(w)==='top').map(w=>w.n); render({}); openPop('webinars',$('[data-filt="webinars"]')||t); } });
  D.addEventListener('mouseover',e=>{ const t=e.target.closest('[data-tip],[data-stage],.bub[data-w]'); if(t&&t!==tipFor) showTip(t,e); else if(!t) hideTip(); const b=e.target.closest('.bub[data-w],.row[data-w]'); if(b) hot(b.dataset.w,true); });
  D.addEventListener('mouseout',e=>{ const b=e.target.closest('.bub[data-w],.row[data-w]'); if(b) hot(b.dataset.w,false); if(!e.relatedTarget||!e.relatedTarget.closest||!e.relatedTarget.closest('[data-tip],[data-stage],.bub')) hideTip(); });
  D.addEventListener('mousemove',e=>{ if(tipFor) moveTip(e); });
  D.addEventListener('focusin',e=>{ const t=e.target.closest&&e.target.closest('[data-stage],.bub[data-w]'); if(t){ const r=t.getBoundingClientRect(); showTip(t,{clientX:r.left+r.width/2,clientY:r.top}); } });
  D.addEventListener('focusout',hideTip);
  D.addEventListener('keydown',e=>{ const t=e.target;
    if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){ e.preventDefault(); $('#pal').classList.contains('on')?palClose():palOpen(); return; }
    if(e.key==='/'&&!/INPUT|SELECT|TEXTAREA/.test(t.tagName)){ e.preventDefault(); palOpen(); return; }
    if(e.key==='Escape'){ if($('#pal').classList.contains('on')) palClose(); else if(S.fs) closeFS(); else if($('#drawer').classList.contains('on')) closeDrawer(); else closePop(); return; }
    if($('#pal').classList.contains('on')){ if(e.key==='ArrowDown'){ e.preventDefault(); palI=Math.min(palI+1,PAL.length-1); palRender(); } else if(e.key==='ArrowUp'){ e.preventDefault(); palI=Math.max(palI-1,0); palRender(); } else if(e.key==='Enter'){ e.preventDefault(); palGo(palI); } return; }
    if((e.key==='Enter'||e.key===' ')&&t.matches&&t.matches('[role=button],[role=link],tr[data-w]')&&!/INPUT|SELECT|TEXTAREA|BUTTON/.test(t.tagName)){ e.preventDefault(); t.dispatchEvent(new MouseEvent('click',{bubbles:true,shiftKey:e.shiftKey})); } });
  $('#palq').addEventListener('input',()=>{ palI=0; palRender(); });
  /* landscape drag-to-select (brush) */
  D.addEventListener('pointerdown',e=>{ const svg=e.target.closest&&e.target.closest('#land svg'); if(!svg||e.target.closest('.bub')||e.button!==0) return; const r=svg.getBoundingClientRect(), x0=e.clientX-r.left, b=svg.querySelector('#brush'); let drag=false;
    const mv=ev=>{ const x1=ev.clientX-r.left; if(Math.abs(x1-x0)>8) drag=true; if(!drag) return; b.style.display='block'; b.setAttribute('x',Math.min(x0,x1)); b.setAttribute('width',Math.abs(x1-x0)); };
    const up=ev=>{ removeEventListener('pointermove',mv); removeEventListener('pointerup',up); const x1=ev.clientX-r.left; if(!drag) return; const lo=Math.min(x0,x1), hi=Math.max(x0,x1), g=S._geo;
      S.sel=W_ALL.filter((w,i)=>g.x(i)>=lo&&g.x(i)<=hi&&inScope(w)).map(w=>w.n).slice(0,3); render({}); };
    addEventListener('pointermove',mv); addEventListener('pointerup',up); });
  let rt, lastW=innerWidth; addEventListener('resize',()=>{ clearTimeout(rt); rt=setTimeout(()=>{ if(Math.abs(innerWidth-lastW)>40){ lastW=innerWidth; if(S.fs) openFS(S.fs); render({}); } },160); });
  addEventListener('hashchange',()=>{ const w0=S.w, v0=S.view; applyHash(); render({dive:true,z:.985}); });
}
