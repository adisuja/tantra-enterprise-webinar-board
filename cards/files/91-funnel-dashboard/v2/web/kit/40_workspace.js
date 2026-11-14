/* ===================== the webinar workspace: you are "inside" one webinar ===================== */
const WTABS = [['overview','Overview'],['acquisition','Acquisition'],['audience','Audience'],['engagement','Engagement'],['commercial','Commercial'],['content','Content'],['timeline','Timeline']];
const PROVS = {};  // provenance payloads for clickable status badges, keyed by id
function provBtn(w,key,label,fmt){ const m=w.m[key]; if(!m) return ''; const id='p'+Object.keys(PROVS).length;
  PROVS[id]={w:w.n,key,label,m,fmt:fmt?fmt.name:null,imm:!!(!w.mature&&['calls','customers','revenue','outreach_customers','outreach_revenue'].includes(key))};
  return `<button class="sv" data-pm="${id}" data-tip="${esc(m.k)} \u2014 click for the source">${m.k}${PROVS[id].imm?'*':''}</button>`; }
function wLabel(w){ if(w.rank===1) return 'Strongest webinar'; if(w.rank&&w.rank===RANKED.length) return 'Weakest ranked webinar'; if(!w.mature) return 'Still maturing'; return w.rank?`Ranked ${w.rank} of ${RANKED.length}`:'Not ranked'; }
function wHeader(w){ const imm=!w.mature, rev=w.m.revenue.v, cu=w.m.customers.v;
  return `<div class="wh rise"><div class="meta"><span class="lbl">Webinar ${w.n} · ${dfull(w.date)}</span>${tierPill(w)}<span class="lbl" style="color:var(--gold-t)">${wLabel(w)}</span></div>
   <div style="display:flex;gap:56px;flex-wrap:wrap;align-items:flex-end">
     <div><div class="hero-n gold" style="font-size:clamp(54px,7vw,104px)" data-ck="wrev${w.n}" data-v="${nn(rev)?rev:''}" data-f="gbp"><sup>__KIT_CURRENCY_SYMBOL__</sup><span class="cv">${nn(rev)?f0(rev):'\u2014'}</span></div><span class="lbl" style="display:block;margin-top:10px">${imm?'Revenue recorded so far*':'Attributed revenue'} ${provBtn(w,'revenue','Revenue',gbp)}</span></div>
     ${bigNum(cu,imm?'Customers so far*':'Customers','',{ck:'wc'+w.n})}${bigNum(w.m.attended.v,'Attended','of '+f0(w.m.registrations.v)+' registered')}${bigNum(w.score.total,'Overall result',w.rank?'rank '+w.rank+' of '+RANKED.length:'not ranked yet',{fmt:f1})}
   </div>${imm?`<p class="sub" style="margin-top:14px">* ${esc(MAT())}. Sales figures for this webinar are still arriving; they are shown as recorded so far and it is not ranked.</p>`:''}</div>
   <div class="wtabs rise" style="--d:1" role="tablist">${WTABS.map(([k,l])=>`<button role="tab" class="${S.wtab===k?'on':''}" data-wtab="${k}" aria-selected="${S.wtab===k}">${l}</button>`).join('')}</div>`; }

function wOverview(w){ const dims=Object.entries(w.score.dims);
  const good=w.why_won.slice(0,2), bad=w.what_wrong.filter(x=>x.sev!=='low').slice(0,2);
  return `<div class="cols sec" style="margin-top:34px">${rise(2,`<span class="lbl">This webinar's journey</span>${flow({list:[w],H:340,h:340,hmax:118,cy:112,legend:true})}`)}
     ${rise(3,`<span class="lbl">What happened</span><div class="verdict" style="margin-top:14px">${good.length?`<p><b>Strongest part.</b> ${good.map(x=>esc(scrub(x.title+': '+x.text))).join(' ')}</p>`:''}${bad.length?`<p><b>Watch.</b> ${bad.map(x=>esc(scrub(x.title+': '+x.text))).join(' ')}</p>`:''}${w.bottleneck&&w.bottleneck.largest_drop?`<p><b>Largest drop.</b> ${esc(w.bottleneck.largest_drop.from)} → ${esc(w.bottleneck.largest_drop.stage)} lost ${pc(w.bottleneck.largest_drop.drop*100,0)} of people.</p>`:''}</div>`)}</div>
   <div class="cols c2 sec">${rise(4,`<span class="lbl">Where it sits among all webinars</span><div style="margin-top:10px">${strips(w,['score','registrations','attend_pct','call_pct','revenue'])}</div>`)}
     ${rise(5,`<span class="lbl">Result by dimension</span><div style="margin-top:14px">${rowsOf(dims.map(([k,d])=>({k:esc(k),v:nn(d.v)?d.v:0,t:nn(d.v)?f0(d.v)+' / 100':'<span class="na">withheld</span>',tip:DEF[k]||''})),{})}</div><p class="sub" style="margin-top:10px">A withheld dimension has no data for this webinar; it is left out, never scored as zero.${w.score.provisional?' This score is provisional.':''}</p>`)}</div>
   <div class="cols c2 sec">${rise(6,`<span class="lbl">Worth repeating</span><div class="ledger" style="margin-top:10px">${(w.lessons.repeat||[]).map(t=>`<div class="li"><span>${esc(scrub(t))}</span><span></span><span></span></div>`).join('')||'<div class="na" style="padding:10px 0">Nothing stands out.</div>'}</div>`)}${rise(7,`<span class="lbl">Worth changing</span><div class="ledger" style="margin-top:10px">${(w.lessons.change||[]).map(t=>`<div class="li"><span>${esc(scrub(t))}</span><span></span><span></span></div>`).join('')||'<div class="na" style="padding:10px 0">Nothing stands out.</div>'}</div>`)}</div>`; }

function wAcquisition(w){ const m=w.m, parts=REG_METHODS.map(([k,l])=>({k:l,v:m[k].v||0})), E=campaignsFor([w]);
  return `<div class="h2 rise" style="margin-top:34px">Where did people come from?</div>
   <div class="cols c2 sec">${rise(1,`<span class="lbl">How the ${f0(m.registrations.v)} registered</span><div style="margin-top:14px">${rowsOf(parts,{})}</div><div class="states">${stateOf('Website visits')}${stateOf('LinkedIn')}${stateOf('Organic')}${stateOf('Paid')}${m.reg_other.v==null?stateOf('Other sources','UTM tags are empty'):''}</div>`)}
     ${rise(2,`<span class="lbl">Invitation replies · ${f0(m.outreach.v)} contacted ${provBtn(w,'outreach','Contacted',f0)}</span><div style="margin-top:14px">${rowsOf([{k:'Said yes',v:m.rsvp_yes.v},{k:'Said maybe',v:m.rsvp_maybe.v},{k:'Said no',v:m.rsvp_no.v},{k:'No reply yet',v:m.rsvp_pending.v}],{})}</div><p class="sub" style="margin-top:10px">${pc(w.r.reg_pct,2)} of people contacted registered · ${f1(w.r.reg_per_1k)} per 1,000.</p>`)}</div>
   <div class="sec">${rise(3,`<span class="lbl">Email campaigns attributed to this webinar</span>${E.length?`<div class="tw" style="margin-top:12px"><table><thead><tr><th class="l">Campaign</th><th>Sent</th><th>Delivered</th><th>Clicks</th><th>Replies</th><th>Bounce</th></tr></thead><tbody>${E.map(c=>`<tr><td class="l">${esc(c.name)}</td><td>${f0(c.sent)}</td><td>${f0(c.delivered)}</td><td>${f0(c.clicks)}</td><td>${f0(c.replies)}</td><td>${pc(c.bounce_rate,2)}</td></tr>`).join('')}</tbody></table></div>`:`<div class="states">${stateOf('Cold email',m.cold_email.v?'Campaign not attributed by ID':'No cold email for this webinar')}</div>`}`)}</div>`; }

function wAudience(w){ const m=w.m;
  return `<div class="h2 rise" style="margin-top:34px">Who joined?</div>
   ${rise(1,`<div class="big3" style="margin-top:28px">${arc(m.decision_maker_pct.v,'Senior titles')}${arc(m.uk_pct.v,'In __KIT_HOME_MARKET_LABEL__')}${arc(m.company_known_pct.v,'Company known')}</div><div class="states">${stateOf('Audience type')}${stateOf('Industry')}${stateOf('Job function')}${stateOf('New vs returning')}</div>`)}
   <div class="sec">${rise(2,`<span class="lbl">Against the other webinars</span><div style="margin-top:10px;max-width:760px">${strips(w,['reg_pct'])}</div>`)}</div>`; }

function wEngagement(w){ const m=w.m;
  return `<div class="h2 rise" style="margin-top:34px">Attention, after people joined</div>
   ${rise(1,`<div style="margin-top:20px;max-width:880px">${attention([w])}</div>`)}
   <div class="cols c2 sec">${rise(2,`<span class="lbl">How they watched</span><div class="big3" style="margin-top:14px">${bigNum(m.live_viewers.v,'Live')}${bigNum(m.replay_viewers.v,'Replay')}${bigNum(m.watch_both.v,'Both','overlap \u2014 never added')}${bigNum(m.public_replay.v,'Public replay','anonymous, not counted as attendance')}</div>`)}
     ${rise(3,`<span class="lbl">Questions</span><div class="big3" style="margin-top:14px">${bigNum(m.questions.v,'Asked')}${bigNum(m.answered.v,'Answered')}${bigNum(m.upvotes.v,'Upvotes')}${bigNum(w.r.q_per_att,'Per attendee','',{fmt:f2})}</div>`)}</div>
   <div class="states sec">${stateOf('Watch time')}${stateOf('Drop-off minute')}${stateOf('Polls')}${stateOf('Chat')}</div>`; }

function wCommercial(w){ const m=w.m, imm=!w.mature;
  return `<div style="margin-top:34px" class="rise"><span class="lbl">Customers, calls and what each attendee was worth</span>
    <div class="big3" style="margin-top:20px">${bigNum(m.customers.v,'Customers',provBtn(w,'customers','Customers',f0))}${bigNum(m.calls.v,'Calls',provBtn(w,'calls','Calls',f0))}${bigNum(m.attended.v,'Attendees')}${bigNum(w.r.rev_per_att,'Per attendee','',{fmt:gbp})}</div>${imm?`<p class="sub" style="margin-top:14px">* ${esc(MAT())}. Figures are recorded so far.</p>`:''}</div>
   ${rise(2,`<div class="sec"><span class="lbl">Attendee → call → customer → revenue</span>${flow({list:[w],ghosts:false,skip:['outreach','registrations'],h:290,hmax:92,cy:104})}</div>`)}
   <div class="cols c2 sec">${rise(3,`<span class="lbl">Reached by our outreach</span><div class="big3" style="margin-top:12px">${bigNum(m.outreach_customers.v,'Customers')}${bigNum(m.outreach_revenue.v,'Revenue','',{fmt:gbp})}</div><p class="sub" style="margin-top:10px">Customers who were also on this webinar's outreach list. Credit rule for all revenue: ${esc(MODEL.commercial.attribution_rule)}.</p>`)}
     ${rise(4,`<span class="lbl">Funnel steps</span><div style="margin-top:6px">${strips(w,['call_pct','rev_per_att'])}</div>`)}</div>`; }

function wContent(w){ const qs=MODEL.questions.items.filter(q=>q.n===w.n).sort((a,b)=>b.up-a.up), bw=MODEL.questions.by_webinar[w.n]||{};
  return `<div class="h2 rise" style="margin-top:34px">Content</div>
   <div class="cols c2 sec">${rise(1,`<span class="lbl">Topic</span><p style="margin-top:10px;font-size:18px;max-width:34ch">${esc(w.title)}</p><p class="sub" style="margin-top:10px">Every webinar so far shares this one title, so topics cannot be compared.</p><div class="states">${stateOf('Presenter')}</div>`)}
     ${rise(2,`<span class="lbl">What people asked about</span><div style="margin-top:14px">${Object.keys(bw).length?rowsOf(Object.entries(bw).sort((a,b)=>b[1]-a[1]).map(([k,v])=>({k:k.charAt(0)+k.slice(1).toLowerCase(),v})),{}):'<div class="states">'+stateOf('Questions','None categorised for this webinar')+'</div>'}</div>`)}</div>
   <div class="sec">${rise(3,`<span class="lbl">Questions · ${qs.length} matched to this webinar</span><div class="ledger" style="margin-top:10px">${qs.map(q=>`<div class="li"><span>${esc(q.q)}<small>${q.cats.map(c=>esc(c.toLowerCase())).join(', ')}</small></span><span class="sv">▲ ${q.up}</span><span></span></div>`).join('')||'<div class="na" style="padding:10px 0">No matched questions.</div>'}</div><p class="sub" style="margin-top:10px">${esc(MODEL.questions.caveat||'')}</p>`)}</div>`; }

function addDays(d,n){ const x=new Date(d+'T00:00'); x.setDate(x.getDate()+n); return x.toISOString().slice(0,10); }
function wTimeline(w){ const i=W_ALL.indexOf(w), p=W_ALL[i-1], nx=W_ALL[i+1], mat=addDays(w.date,MODEL.mature_days);
  const nb=(x,l)=>x?`<div class="li" data-w="${x.n}" data-wtab="timeline" style="cursor:pointer"><span><b>${l} · W${x.n}</b> · ${dfull(x.date)}<small>${f0(x.m.registrations.v)} registered · ${f0(x.m.attended.v)} attended · ${pc(x.r.attend_pct,1)} attendance · ${x.m.revenue.v?gbp(x.m.revenue.v):'no revenue credited'}</small></span><span>→</span><span></span></div>`:'';
  return `<div class="h2 rise" style="margin-top:34px">Timeline</div>
   <div class="cols c2 sec">${rise(1,`<span class="lbl">Key dates</span><div class="ledger" style="margin-top:10px"><div class="li"><span>Webinar held<small>${w.days_since>=0?w.days_since+' days ago':''}</small></span><span><b>${dfull(w.date)}</b></span><span></span></div><div class="li"><span>Sales figures complete from<small>${MODEL.mature_days} days after the webinar</small></span><span><b>${dfull(mat)}</b></span><span class="sv">${w.mature?'done':'pending'}</span></div>${w.rsvp_scanned?`<div class="li"><span>Invitation replies last read</span><span><b>${dfull(w.rsvp_scanned)}</b></span><span></span></div>`:''}</div><div class="states">${stateOf('Per-day registrations','No dated sign-up events')}${stateOf('Email send dates')}</div>`)}
     ${rise(2,`<span class="lbl">In sequence</span><div class="ledger" style="margin-top:10px">${nb(p,'Before')}${nb(nx,'After')}</div>`)}</div>
   <div class="sec">${rise(3,`<span class="lbl">Where W${w.n} sits through time</span><div style="margin-top:10px">${landscape({hl:w.n})}</div>`)}</div>`; }

function vWorkspace(){ const w=byN(S.w); if(!w) return emptyScope(); S.wtab=WTABS.some(t=>t[0]===S.wtab)?S.wtab:'overview';
  const F={overview:wOverview,acquisition:wAcquisition,audience:wAudience,engagement:wEngagement,commercial:wCommercial,content:wContent,timeline:wTimeline}[S.wtab];
  return wHeader(w)+`<div id="wbody">${F(w)}</div>`; }
