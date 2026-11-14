/* ===================== visual primitives (inline SVG / HTML, no libraries) ===================== */
let UID = 0;
const cw = () => Math.max(320, Math.min(((document.getElementById('canvas')||document.body).clientWidth||innerWidth) - 68, 1900));
const sq = (v,mx) => (nn(v)&&mx>0) ? Math.sqrt(Math.max(v,0)/mx) : 0;

/* ---------- THE JOURNEY RIVER ----------
   Ribbon thickness ∝ √count (so 20 customers stay visible next to 190k contacted); the legend says so.
   The taper between two nodes IS the drop-off. Revenue is a different unit, drawn in gold. */
function flow(o){
  const list=o.list, T=totalsOf(list), C=MODEL.commercial, auto=!o.vertical&&!o.W&&cw()<720, V=!!o.vertical||auto, id='f'+(++UID), full=list.length===W_ALL.length;
  // A stage no connected source measures is drawn as a ghost ("not connected"), never as a zero.
  const noOut=list.every(w=>!nn(w.m.outreach.v));
  const real=STAGES.filter(s=>(!o.skip||!o.skip.includes(s.k))&&!(s.k==='outreach'&&noOut)).map(s=>({s,v:s.money?T.rev:stageTotal(s,list)}));
  const ghosts=o.ghosts===false?[]:[{ghost:1,k:'visits',l:'Visits',v:null,note:'Tracking not connected'},(MODEL.email_campaigns||[]).length?{ghost:1,k:'clicks',l:'Clicks',v:sum(MODEL.email_campaigns,c=>c.clicks),note:'email links only'}:{ghost:1,k:'clicks',l:'Clicks',v:null,note:'Email tracking not connected'}];
  if(noOut&&(!o.skip||!o.skip.includes('outreach'))) ghosts.push({ghost:1,k:'contacted',l:'Contacted',v:null,note:'Outreach not connected'});
  const nodes=[...ghosts,...real], N=nodes.length;
  const W=o.W||(V?360:cw()), H=auto?N*(o.step||74)+10:(o.H||(V?N*(o.step||74)+10:o.h||340));
  const padA=V?22:30, spanA=(V?H:W)-padA*2-(V?62:96), nw=V?7:8;
  const sp=spanA/(N-1), wrapTxt=(s,max)=>{ const w=String(s).split(' '), out=['']; w.forEach(x=>{ const l=out[out.length-1]; if(l&&(l+' '+x).length>max) out.push(x); else out[out.length-1]=l?l+' '+x:x; }); return out.slice(0,3); }, tsp=(lines,x,dy)=>lines.map((l,i)=>`<tspan x="${x}" ${i?`dy="${dy}"`:''}>${l}</tspan>`).join('');
  const A=i=>padA+spanA*i/(N-1), c0=V?64:(o.cy||132);
  const hmax=o.hmax||(V?96:150), mxPeople=Math.max(...real.filter(r=>!r.s.money).map(r=>r.v||0),1);
  const unl=(full&&o.unlinked!==false)?C.unattributed.revenue:0, revTot=T.rev+unl;
  const th=r=>r.s.money ? Math.max(14,hmax*.92) : Math.max(5,hmax*sq(r.v,mxPeople));
  const P=(a,c)=>V?`${c.toFixed(1)},${a.toFixed(1)}`:`${a.toFixed(1)},${c.toFixed(1)}`;
  let rib='', nd='', pulse='';
  const rev=real.find(r=>r.s.money), revI=nodes.indexOf(rev), tRev=rev?th(rev):0, tAtt=rev&&revTot?tRev*(T.rev/revTot):0;
  real.forEach((r,j)=>{ const i=nodes.indexOf(r); r.i=i; r.t=th(r); });
  for(let j=1;j<real.length;j++){ const a=real[j-1], b=real[j]; const a1=A(a.i)+nw, a2=A(b.i), d=(a2-a1)*.5, money=b.s.money;
    const t1=a.t, c1=c0; let t2=b.t, c2=c0;
    if(money){ t2=Math.max(6,tAtt); c2=c0-tRev/2+t2/2; }
    rib+=`<path class="rb${money?' rbm':''}" fill="url(#${id}${money?'m':'p'})" d="M${P(a1,c1-t1/2)} C${P(a1+d,c1-t1/2)} ${P(a2-d,c2-t2/2)} ${P(a2,c2-t2/2)} L${P(a2,c2+t2/2)} C${P(a2-d,c2+t2/2)} ${P(a1+d,c1+t1/2)} ${P(a1,c1+t1/2)}Z"/>`;
    pulse+=`<path class="pulse${money?' m':''}" d="M${P(a1,c1)} C${P(a1+d,c1)} ${P(a2-d,c2)} ${P(a2,c2)}"/>`; }
  if(unl&&rev){ const a2=A(revI), cU=c0+tRev/2-(tRev-tAtt)/2, tU=tRev-tAtt, a1=a2-(V?44:96);
    rib+=`<path d="M${P(a1,cU-tU/2)} C${P(a1+30,cU-tU/2)} ${P(a2-30,cU-tU/2)} ${P(a2,cU-tU/2)} L${P(a2,cU+tU/2)} C${P(a2-30,cU+tU/2)} ${P(a1+30,cU+tU/2)} ${P(a1,cU+tU/2)}Z" fill="url(#${id}h)" stroke="var(--gold)" stroke-dasharray="3 3" stroke-width="1"/>`; }
  nodes.forEach((n,i)=>{ const a=A(i);
    if(n.ghost){ const lx=V?150:a-6, ly=V?a-2:c0+hmax/2+34;
      nd+=`<g class="nd ghost" ${n.k==='contacted'?'':n.k==='clicks'?'data-stage="clicks"':'data-stage="visits"'} tabindex="0" role="button" aria-label="${n.l}: ${n.note}">
        <rect class="hit" x="${V?0:a-34}" y="${V?a-26:c0-hmax/2}" width="${V?W:68}" height="${V?52:hmax+90}"/>
        <circle class="bar" cx="${V?c0:a+4}" cy="${V?a:c0}" r="${V?9:11}"/>
        <text class="n" x="${V?150:a+4}" y="${V?a-10:c0+hmax/2+18}" text-anchor="${V?'start':'middle'}">${n.l}</text>
        <text class="v" x="${V?150:a+4}" y="${V?a+14:c0+hmax/2+60}" text-anchor="${V?'start':'middle'}">${n.l==='Clicks'&&nn(n.v)?compact(n.v):'\u2014'}</text>
        <text class="r" x="${V?150:a+4}" y="${V?a+30:c0+hmax/2+79}" text-anchor="${V?'start':'middle'}">${V?n.note:tsp(wrapTxt(n.note,Math.floor((sp-6)/7)),a+4,15)}</text></g>`; return; }
    const r=n, t=r.t, money=r.s.money, x=V?c0-t/2:a, y=V?a:c0-t/2;
    let barSvg;
    if(money){ const ta=tAtt; barSvg=`<rect class="bar" x="${V?c0-tRev/2:a}" y="${V?a:c0-tRev/2}" width="${V?ta:nw}" height="${V?nw:ta}" rx="2"/>${unl?`<rect x="${V?c0-tRev/2+ta:a}" y="${V?a:c0-tRev/2+ta}" width="${V?tRev-ta:nw}" height="${V?nw:tRev-ta}" rx="2" fill="url(#${id}h)" stroke="var(--gold)" stroke-dasharray="3 2"/>`:''}`; }
    else barSvg=`<rect class="bar" x="${x}" y="${y}" width="${V?t:nw}" height="${V?nw:t}" rx="2"/>`;
    const ov=r.s.com&&list.some(w=>!w.mature)?'*':'';
    const rate=r.s.rate?(r.s.k==='revenue'?(T.att?r.s.rf(stageRate(r.s,list))+' '+r.s.rl:''):(r.s.rf(stageRate(r.s,list))+' '+r.s.rl)):'';
    const lx=V?150:a+4, ta=V?'start':'middle';
    const ly=V?a:c0+hmax/2+(money?0:0);
    const base=V?a:c0+hmax/2+18;
    const valTxt=money?gbpk(r.v):compact(r.v)+ov;
    nd+=`<g class="nd${money?' m':''}" data-stage="${r.s.k}" tabindex="0" role="button" aria-label="${r.s.l}: ${money?gbp(r.v):f0(r.v)}. Open details">
      <rect class="hit" x="${V?0:a-52}" y="${V?a-26:c0-hmax/2-8}" width="${V?W:104}" height="${V?58:hmax+84}"/>${barSvg}
      <text class="n" x="${lx}" y="${V?a-9:base}" text-anchor="${ta}">${V?r.s.l:tsp(wrapTxt(r.s.l,Math.max(8,Math.floor((sp-6)/8.4))),lx,14)}</text>
      <text class="v" x="${lx}" y="${V?a+17:base+44}" text-anchor="${ta}">${valTxt}</text>
      <text class="r" x="${lx}" y="${V?a+34:base+63}" text-anchor="${ta}">${V?esc(rate):tsp(wrapTxt(esc(rate),Math.max(10,Math.floor((sp-6)/7))),lx,15)}</text></g>`; });
  // unlinked label
  let unlTxt='';
  if(unl&&rev) unlTxt=V?`<text class="loss" x="150" y="${A(revI)+52}">+ ${gbpk(unl)} not linked to a webinar</text>`:`<text class="loss" x="${A(revI)-8}" y="${c0+tRev/2+86}" text-anchor="end">+ ${gbpk(unl)} paid without attending a webinar</text>`;
  const defs=`<defs><linearGradient id="${id}p" gradientUnits="objectBoundingBox" x1="0" y1="0" x2="${V?0:1}" y2="${V?1:0}"><stop offset="0" stop-color="var(--ocean)" stop-opacity=".38"/><stop offset="1" stop-color="var(--ocean)" stop-opacity=".12"/></linearGradient>
    <linearGradient id="${id}m" x1="0" y1="0" x2="${V?0:1}" y2="${V?1:0}"><stop offset="0" stop-color="var(--gold)" stop-opacity=".25"/><stop offset="1" stop-color="var(--gold)" stop-opacity=".55"/></linearGradient>
    <pattern id="${id}h" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" fill="none"/><line x1="0" y1="0" x2="0" y2="6" stroke="var(--gold)" stroke-opacity=".5" stroke-width="2"/></pattern></defs>`;
  const note=`<div class="legend" style="margin-top:2px"><span>Ribbon width ∝ √count \u2014 the taper is the drop-off.${list.some(w=>!w.mature)&&real.some(r=>r.s.com)?' * includes still-maturing webinars.':''}</span></div>`;
  return `<svg class="flow${V?' vert':''}" viewBox="0 0 ${W} ${H}" role="group" aria-label="Journey from people contacted to revenue">${defs}<g class="rv">${rib}${pulse}</g>${nd}${unlTxt}</svg>${o.legend===false?'':note}`; }

/* ---------- THE WEBINAR LANDSCAPE ---------- */
function landscape(o){
  o=o||{}; const k=o.metric||S.lm, g=MET[k], list=W_ALL, W=o.W||cw(), H=o.H||(W<640?300:360), L=54,R=(W<640?30:96),T=34,B=64, n=list.length;
  const X=i=>L+(n>1?i/(n-1):.5)*(W-L-R-40)+20, vals=list.map(w=>metVal(w,k)).filter(nn), mx=(Math.max(...vals,1e-9))*1.18, Y=v=>T+(1-v/mx)*(H-T-B);
  const regMax=Math.max(...list.map(w=>w.m.registrations.v||0),1), revMax=Math.max(...list.map(w=>w.m.revenue.v||0),1);
  const st=statsOf(list,k), money=o.money, rad=w=>(W<640?5:7)+sq(w.m.registrations.v,regMax)*(W<640?18:26);
  let s='';
  for(let i=0;i<=3;i++){ const v=mx*i/3.18, y=Y(v); s+=`<line class="gridl" x1="${L}" x2="${W-R}" y1="${y}" y2="${y}"/><text x="${L-8}" y="${y+4}" text-anchor="end">${g.f(v)}</text>`; }
  if(nn(st.avg)) s+=`<line x1="${L}" x2="${W-R}" y1="${Y(st.avg)}" y2="${Y(st.avg)}" stroke="var(--gold)" stroke-dasharray="5 4"/><text x="${W-R+8}" y="${Y(st.avg)-3}" text-anchor="start" style="fill:var(--gold-t);font-weight:600">average</text><text x="${W-R+8}" y="${Y(st.avg)+13}" text-anchor="start" style="fill:var(--gold-t);font-weight:600">${g.f(st.avg)}</text>`;
  list.forEach((w,i)=>{ const v=metVal(w,k), x=X(i), inS=inScope(w), sel=S.sel.includes(w.n)||o.hl===w.n;
    const cls=`bub${inS?'':' out'}${sel?' sel':''}`;
    s+=`<text x="${x}" y="${H-B+22}" text-anchor="middle" style="font:600 12.5px var(--mono);fill:var(--ink2)">W${w.n}</text><text x="${x}" y="${H-B+37}" text-anchor="middle">${dfmt(w.date)}</text>`;
    if(!nn(v)){ s+=`<g class="${cls}" data-w="${w.n}" data-flip="b${w.n}" tabindex="0" role="button" aria-label="W${w.n}: no data"><rect x="${x-18}" y="${T}" width="36" height="${H-T-B}" fill="transparent"/><text x="${x}" y="${Y(0)-8}" text-anchor="middle" class="vv">\u2014</text></g>`; return; }
    const y=Y(v), r=rad(w), tier=tierOf(w), fillC=money?'var(--gold)':'var(--ocean)';
    const fillOp=tier==='top'?.92:tier==='avg'?.55:tier==='low'?.12:.08, dashed=(!w.mature)||tier==='prov';
    const ring=(w.m.revenue.v>0&&!money)?`<circle cx="${x}" cy="${y}" r="${r+4+sq(w.m.revenue.v,revMax)*7}" fill="none" stroke="var(--gold)" stroke-width="${1.4+sq(w.m.revenue.v,revMax)*3.4}" opacity=".95"/>`:'';
    s+=`<g class="${cls}" data-w="${w.n}" data-flip="b${w.n}" tabindex="0" role="button" aria-label="W${w.n}, ${g.l} ${g.f(v)}. Open workspace"><line class="stem" x1="${x}" x2="${x}" y1="${y}" y2="${H-B}"/>${ring}
      <circle class="c" cx="${x}" cy="${y}" r="${r}" fill="${fillC}" fill-opacity="${fillOp}" stroke="${fillC}" stroke-width="1.6" ${dashed?'stroke-dasharray="3 3"':''}/>
      <text x="${x}" y="${y+4}" text-anchor="middle" style="fill:${tier==='top'?'var(--bg)':'var(--ink)'}">${r>14?'W'+w.n:''}</text>
      <text class="vv" x="${x}" y="${y-r-(w.m.revenue.v>0&&!money?12+sq(w.m.revenue.v,revMax)*7:7)}" text-anchor="middle">${g.f(v)}${g.com&&!w.mature?'*':''}</text></g>`; });
  S._geo={x:X,L,R,W,n,T,H,B};
  return `<div class="land" id="land"><svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="group" aria-label="Webinars over time by ${esc(g.l)}">${s}<rect class="brush" id="brush" x="0" y="${T}" width="0" height="${H-T-B}" style="display:none"/></svg></div>
  <div class="legend"><span><i style="background:var(--ocean)"></i>Bubble size = registrations</span>${money?'':'<span><i style="background:none;box-shadow:inset 0 0 0 2px var(--gold)"></i>Gold ring = revenue credited</span>'}<span><i style="background:none;box-shadow:inset 0 0 0 1.5px var(--ocean)"></i>Solid = top performer · faint = needs attention</span><span>Dashed = still maturing / provisional</span></div>`; }

/* ---------- ranked strip (score) ---------- */
function rankStrip(){ const mx=100; return `<div class="rows dim-others">${RANKED.map(w=>`<div class="row" data-w="${w.n}" data-flip="r${w.n}" tabindex="0" role="button"><span class="k"><b>W${w.n}</b> · ${dfmt(w.date)}</span><div class="bar2"><i style="width:${w.score.total/mx*100}%"></i></div><span class="vv">${f1(w.score.total)}</span></div>`).join('')}${W_ALL.filter(w=>!w.rank).map(w=>`<div class="row" data-w="${w.n}" tabindex="0" role="button"><span class="k"><b>W${w.n}</b> · ${dfmt(w.date)}</span><span class="na" style="font-size:14px">Not ranked yet \u2014 ${esc(MAT().toLowerCase())}</span><span class="vv">${f1(w.score.total)}†</span></div>`).join('')}</div>`; }

/* ---------- compact rows (bars) ---------- */
function rowsOf(items,o){ o=o||{}; const mx=Math.max(...items.map(i=>i.v||0),1e-9);
  return `<div class="rows dim-others">${items.map(i=>`<div class="row${o.gold?' gold':''}" ${i.w?`data-w="${i.w}"`:''} ${i.attr||''} tabindex="0" role="button" ${i.tip?`data-tip="${esc(i.tip)}"`:''}><span class="k">${i.k}</span><div class="bar2"><i style="width:${(i.v||0)/mx*100}%"></i></div><span class="vv">${i.t!=null?i.t:(nn(i.v)?(o.fmt||f0)(i.v):'\u2014')}</span></div>`).join('')}</div>`; }

/* ---------- strip plot: where does this webinar sit among all? ---------- */
function strips(w,keys){ return keys.map(k=>{ const g=MET[k]; const pool=W_ALL.filter(x=>(!g.com||x.mature)&&nn(metVal(x,k))); if(!pool.length||!nn(metVal(w,k))) return `<div class="li" style="display:grid;grid-template-columns:150px 1fr;gap:12px;padding:9px 0;border-top:1px solid var(--hair)"><span class="k" style="font-size:14.5px;color:var(--ink2)">${g.l}</span><span class="na" style="font-size:14.5px">${g.com&&!w.mature?'recorded so far \u2014 '+esc(MAT()):'Not available'}</span></div>`;
    const mn=Math.min(...pool.map(x=>metVal(x,k))), mx=Math.max(...pool.map(x=>metVal(x,k))), rg=(mx-mn)||1, pos=v=>Math.min(100,Math.max(0,(v-mn)/rg*100)), a=avg(pool.map(x=>metVal(x,k)));
    return `<div class="li" style="display:grid;grid-template-columns:150px 1fr 92px;gap:12px;align-items:center;padding:9px 0;border-top:1px solid var(--hair)"><span class="k" style="font-size:14.5px;color:var(--ink2)">${g.l}</span>
      <div style="position:relative;height:18px"><div style="position:absolute;left:0;right:0;top:8px;height:1px;background:var(--line)"></div>
      ${pool.map(x=>`<i data-w="${x.n}" data-tip="W${x.n}: ${g.f(metVal(x,k))}" style="position:absolute;left:calc(${pos(metVal(x,k))}% - 3px);top:6px;width:6px;height:6px;border-radius:50%;background:${x===w?'transparent':'var(--ghost)'};cursor:pointer"></i>`).join('')}
      <i style="position:absolute;left:${pos(a)}%;top:2px;width:1px;height:14px;background:var(--gold)" data-tip="Programme average ${g.f(a)}"></i>
      <i style="position:absolute;left:calc(${pos(metVal(w,k))}% - 7px);top:2px;width:14px;height:14px;border-radius:50%;background:var(--ocean);box-shadow:0 0 0 4px var(--ocean-soft)"></i></div>
      <span class="num" style="text-align:right;font-weight:600">${g.f(metVal(w,k))}${g.com&&!w.mature?'*':''}</span></div>`; }).join('')+`<div class="legend"><span><i style="background:var(--ocean)"></i>this webinar</span><span><i style="background:var(--ghost)"></i>other webinars</span><span><i style="background:var(--gold);width:2px;border-radius:0"></i>average</span></div>`; }

/* ---------- attention ladder: what share of attendees went on to each step ---------- */
function attention(list,opt){ opt=opt||{}; const A=sum(list,w=>w.m.attended.v); if(!A) return '<div class="state"><b>Attention</b>No attendees in view</div>';
  const step=(l,v,man)=>({l,v,man}), rows=[step('Attended',A), step('Clicked the offer',sum(list,w=>w.m.cta.v),1), step('Applied',sum(list,w=>w.m.applications.v),1), step('Booked a call',sum(list,w=>w.m.calls.v)), step('Became a customer',sum(list,w=>w.m.customers.v))];
  const W=opt.W||Math.min(cw(),760), H=210, L=10, Rr=10, T=26, B=46, pts=rows.map((r,i)=>({...r,p:nn(r.v)?r.v/A*100:null,x:L+i/(rows.length-1)*(W-L-Rr)}));
  const sc=p=>Math.sqrt(p/100); const Y=p=>T+(1-sc(p))*(H-T-B);
  const ok=pts.filter(p=>nn(p.p)); let drop=null; for(let i=1;i<ok.length;i++){ const d=ok[i-1].p-ok[i].p; if(!drop||d>drop.d) drop={d,a:ok[i-1],b:ok[i]}; }
  const path=ok.map((p,i)=>(i?'L':'M')+p.x.toFixed(1)+','+Y(p.p).toFixed(1)).join('');
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Share of attendees reaching each step"><defs><linearGradient id="atg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="var(--ocean)" stop-opacity=".34"/><stop offset="1" stop-color="var(--ocean)" stop-opacity="0"/></linearGradient></defs>
    <path d="${path}L${ok[ok.length-1].x},${H-B}L${ok[0].x},${H-B}Z" fill="url(#atg)"/><path d="${path}" fill="none" stroke="var(--ocean)" stroke-width="2.4" stroke-linejoin="round"/>
    ${pts.map(p=>`<g><text x="${Math.min(Math.max(p.x,48),W-48)}" y="${H-24}" text-anchor="middle" style="fill:var(--ink2)">${p.l}</text><text x="${Math.min(Math.max(p.x,48),W-48)}" y="${H-9}" text-anchor="middle" style="font:600 12px var(--mono)">${nn(p.v)?f0(p.v):'\u2014'}${p.man?' ✎':''}</text>${nn(p.p)?`<circle cx="${p.x}" cy="${Y(p.p)}" r="5" fill="var(--bg)" stroke="var(--ocean)" stroke-width="2.2" data-tip="${p.l}: ${f0(p.v)} · ${pc(p.p,p.p<10?1:0)} of attendees${p.man?' · typed in by the team':''}"/><text x="${p.x}" y="${Y(p.p)-12}" text-anchor="${p.x<30?'start':p.x>W-30?'end':'middle'}" style="fill:var(--ink);font-weight:600">${pc(p.p,p.p<10?1:0)}</text>`:''}</g>`).join('')}
    ${drop?`<text x="${(drop.a.x+drop.b.x)/2}" y="${Y((drop.a.p+drop.b.p)/2)+30}" text-anchor="middle" style="fill:var(--bad);font-weight:600">attention falls most here</text>`:''}</svg>
    <div class="legend"><span>Share of attendees (√ scale). ✎ = typed in by the team; the web-form click has no automatic source.</span></div>`; }

/* ---------- ring arcs for single percentages ---------- */
function arc(v,label,tip){ if(!nn(v)) return `<div class="bn"><div class="v na">\u2014</div><span class="lbl">${label}</span><div class="s">Not recorded</div></div>`;
  const r=34,c=2*Math.PI*r,off=c*(1-Math.min(v,100)/100);
  return `<div class="bn" data-tip="${esc(tip||'')}"><svg width="86" height="86" viewBox="0 0 86 86" role="img" aria-label="${label} ${pc(v,0)}"><circle cx="43" cy="43" r="${r}" fill="none" stroke="var(--hair)" stroke-width="7"/><circle class="arc" cx="43" cy="43" r="${r}" fill="none" stroke="var(--ocean)" stroke-width="7" stroke-linecap="round" stroke-dasharray="${c.toFixed(1)}" stroke-dashoffset="${off.toFixed(1)}" transform="rotate(-90 43 43)"/><text x="43" y="48" text-anchor="middle" style="font:300 20px var(--sans);fill:var(--ink);letter-spacing:-.03em">${pc(v,0)}</text></svg><span class="lbl" style="display:block;margin-top:6px">${label}</span></div>`; }

const stateOf = (label,text) => `<span class="state"><b>${label}</b>${text||'Not recorded'}</span>`;
const bigNum = (v,label,sub,o) => `<div class="bn"><div class="v num${o&&o.gold?' gold-t':''}" ${o&&o.ck?`data-ck="${o.ck}" data-v="${nn(v)?v:''}" data-f="${o.f||'f0'}"`:''} style="${o&&o.gold?'color:var(--gold-t)':''}">${nn(v)?((o&&o.fmt)||f0)(v):'\u2014'}</div><span class="lbl">${label}</span>${sub?`<div class="s">${sub}</div>`:''}</div>`;
