"use strict";
/* __KIT_BRAND_NAME__ Dashboard \u2014 presentation layer only.
   Reads MODEL (model.json) read-only. No calculation, attribution or business rule is defined here:
   every figure is a model field, a sum of model fields, or a ratio of two model fields that the
   previous UI already showed. Unknown stays unknown ("\u2014"), never zero. */
const MODEL = JSON.parse(document.getElementById('model').textContent);
const W_ALL = MODEL.webinars;
const LAST = W_ALL[W_ALL.length-1];
const RANKED = W_ALL.filter(w=>w.rank).sort((a,b)=>a.rank-b.rank);
const BEST = RANKED[0], WORST = RANKED[RANKED.length-1];
const S = {view:'overview', w:null, wtab:'overview', lm:'attend_pct', from:W_ALL[0].n, to:LAST.n, pick:null, ch:'all', tier:'all', rev:'all', att:'all',
  sel:[], selMode:false, tbl:false, sort:'score', dir:-1, debug:false, noanim:false, theme:null, pane:0, fs:null, tm:'attend_pct'};
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const nn = x => x!=null && !Number.isNaN(x);
const f0 = x => nn(x)?Math.round(x).toLocaleString('__KIT_LOCALE__'):'\u2014';
const f1 = x => nn(x)?x.toLocaleString('__KIT_LOCALE__',{maximumFractionDigits:1,minimumFractionDigits:1}):'\u2014';
const f2 = x => nn(x)?x.toLocaleString('__KIT_LOCALE__',{maximumFractionDigits:2,minimumFractionDigits:2}):'\u2014';
const gbp = x => nn(x)?'__KIT_CURRENCY_SYMBOL__'+Math.round(x).toLocaleString('__KIT_LOCALE__'):'\u2014';
const gbpk = x => !nn(x)?'\u2014':(Math.abs(x)>=1000?'__KIT_CURRENCY_SYMBOL__'+(x/1000).toLocaleString('__KIT_LOCALE__',{maximumFractionDigits:1})+'K':'__KIT_CURRENCY_SYMBOL__'+Math.round(x));
const pc = (x,d=1) => nn(x)?x.toLocaleString('__KIT_LOCALE__',{maximumFractionDigits:d,minimumFractionDigits:d})+'%':'\u2014';
const compact = x => !nn(x)?'\u2014':(x>=10000?(x/1000).toLocaleString('__KIT_LOCALE__',{maximumFractionDigits:1})+'K':f0(x));
const sum = (a,f)=>a.reduce((s,x)=>s+(f(x)||0),0);
const avg = a => { const x=a.filter(nn); return x.length? x.reduce((s,y)=>s+y,0)/x.length : null; };
const dfmt = d => new Date(d+'T00:00').toLocaleDateString('__KIT_LOCALE__',{day:'numeric',month:'short'});
const dfull = d => new Date(d+'T00:00').toLocaleDateString('__KIT_LOCALE__',{day:'numeric',month:'short',year:'numeric'});
const plural = (n,s,p) => f0(n)+' '+(n===1?s:(p||s+'s'));
const byN = n => W_ALL.find(w=>w.n===+n);
const DEF = Object.fromEntries(MODEL.dictionary);
const MAT = () => MODEL.maturity_label;
const pchg = (a,b) => (nn(a)&&nn(b)&&b!==0) ? (a-b)/Math.abs(b)*100 : null;
const firstSent = t => String(t||'').split(/(?<=[.!?])\s/)[0];

/* ---- metric catalogue (same getters as the previous UI) ---- */
const MET = {
  score:{l:'Overall result',get:w=>w.score.total,f:f1,hb:1,unit:'/100'},
  attend_pct:{l:'Attendance rate',get:w=>w.r.attend_pct,f:v=>pc(v,1),hb:1},
  registrations:{l:'Registrations',get:w=>w.m.registrations.v,f:f0,hb:1},
  attended:{l:'Attendees',get:w=>w.m.attended.v,f:f0,hb:1},
  calls:{l:'Calls',get:w=>w.m.calls.v,f:f0,hb:1,com:1},
  call_pct:{l:'Calls per 100 attendees',get:w=>w.r.call_pct,f:f1,hb:1,com:1},
  customers:{l:'Customers',get:w=>w.m.customers.v,f:f0,hb:1,com:1},
  revenue:{l:'Revenue',get:w=>w.m.revenue.v,f:gbp,hb:1,com:1},
  reg_pct:{l:'Registered per contacted',get:w=>w.r.reg_pct,f:v=>pc(v,2),hb:1},
  q_per_att:{l:'Questions per attendee',get:w=>w.r.q_per_att,f:f2,hb:1},
  rev_per_att:{l:'Revenue per attendee',get:w=>w.r.rev_per_att,f:gbp,hb:1,com:1},
  outreach:{l:'People contacted',get:w=>w.m.outreach.v,f:f0,hb:1},
  interest_pct:{l:'Interest rate',get:w=>w.r.interest_pct,f:v=>pc(v,2),hb:1},
  company_known_pct:{l:'Company known',get:w=>w.m.company_known_pct.v,f:v=>pc(v,1),hb:1}
};
const LAND_METRICS = ['attend_pct','score','revenue','registrations','call_pct','reg_pct'];
const metVal = (w,k) => MET[k].get(w);
const statsOf = (list,k) => { const c=MET[k].com||k==='score'; const xs=list.filter(w=>!c||w.mature).map(w=>metVal(w,k)).filter(nn); return {avg:avg(xs), n:xs.length, max:xs.length?Math.max(...xs):null, min:xs.length?Math.min(...xs):null}; };

/* ---- tiers = the approved badge, no new scoring ---- */
function tierOf(w){ const b=w.badge||''; if(!w.rank||b==='PROVISIONAL') return 'prov'; if(b==='BEST'||b==='TOP 3') return 'top'; if(b==='UNDERPERFORMING'||b==='CRITICAL') return 'low'; return 'avg'; }
const TIER_L = {top:'Top performer',avg:'Average',low:'Needs attention',prov:'Provisional'};
const tierPill = w => `<span class="pill ${tierOf(w)}" data-tip="Approved Performance Score badge: ${esc(w.badge||'\u2014')}${w.rank?' · rank '+w.rank+' of '+RANKED.length:' · not ranked'}">${TIER_L[tierOf(w)]}</span>`;

/* ---- scope: the filter set ---- */
const ATT_AVG = () => avg(W_ALL.map(w=>w.r.attend_pct));
const inScope = w => w.n>=S.from && w.n<=S.to && (!S.pick || S.pick.includes(w.n))
  && (S.ch==='all' || (S.ch==='cold' ? (w.m.cold_email.v||0)>0 : (w.m.cold_email.v||0)===0))
  && (S.tier==='all' || tierOf(w)===S.tier)
  && (S.rev==='all' || (S.rev==='has' ? (w.m.revenue.v||0)>0 : (w.mature && w.m.revenue.v===0)))
  && (S.att==='all' || (nn(w.r.attend_pct) && (S.att==='high' ? w.r.attend_pct>=ATT_AVG() : w.r.attend_pct<ATT_AVG())));
const ws = () => W_ALL.filter(inScope);
const isAll = () => ws().length===W_ALL.length;
const filtersOn = () => !isAll() || S.ch!=='all' || S.tier!=='all' || S.rev!=='all' || S.att!=='all';
const totalsOf = list => { const t=k=>sum(list,w=>w.m[k].v); return {n:list.length,out:t('outreach'),reg:t('registrations'),att:t('attended'),calls:t('calls'),cust:t('customers'),rev:t('revenue'),noshow:t('noshow')}; };

/* ---- the journey: one definition used by the river, the tooltips and the drawers ---- */
const STAGES = [
  {k:'outreach',  l:'Contacted',        get:w=>w.m.outreach.v,       rate:null,                 prev:null,          def:'Outreach',    unit:'people'},
  {k:'registrations',l:'Registered',    get:w=>w.m.registrations.v,  rate:w=>w.r.reg_pct,      prev:'outreach',    def:'Registration',unit:'people', rf:v=>pc(v,2), rl:'of people contacted'},
  {k:'attended',  l:'Attended',         get:w=>w.m.attended.v,       rate:w=>w.r.attend_pct,   prev:'registrations',def:'Attendance', unit:'people', rf:v=>pc(v,1), rl:'of registered'},
  {k:'calls',     l:'Booked a call',    get:w=>w.m.calls.v,          rate:w=>w.r.call_pct,     prev:'attended',    def:'Call',        unit:'calls',  rf:v=>f1(v),   rl:'per 100 attendees', com:1},
  {k:'customers', l:'Became a customer',get:w=>w.m.customers.v,      rate:w=>w.r.cust_pct,     prev:'attended',    def:'Customer',    unit:'customers',rf:v=>pc(v,1),rl:'of attendees', com:1},
  {k:'revenue',   l:'Revenue',          get:w=>w.m.revenue.v,        rate:w=>w.r.rev_per_att,  prev:'attended',    def:'Revenue',     unit:'__KIT_CURRENCY_SYMBOL__',      rf:gbp,        rl:'per attendee', com:1, money:1}
];
const STAGE = k => STAGES.find(s=>s.k===k);
function stageTotal(s,list){ return sum(list,w=>s.get(w)); }
function stageRate(s,list){ // programme-level rate for a stage = ratio of the two summed fields the model already holds
  const T=totalsOf(list); const A=T.att; switch(s.k){
    case 'registrations': return T.out?T.reg/T.out*100:null; case 'attended': return T.reg?T.att/T.reg*100:null;
    case 'calls': return A?T.calls/A*100:null; case 'customers': return A?T.cust/A*100:null; case 'revenue': return A?T.rev/A:null; default: return null; } }
// per-webinar step rate → strongest & weakest (commercial stages: mature webinars only, the approved rule)
function stageRank(s,list){ if(!s.rate) return null; const pool=list.filter(w=>(!s.com||w.mature)&&nn(s.rate(w))); if(pool.length<2) return null;
  const sorted=[...pool].sort((a,b)=>s.rate(b)-s.rate(a)); return {best:sorted[0],worst:sorted[sorted.length-1],avg:avg(pool.map(w=>s.rate(w))),n:pool.length}; }
const REG_METHODS = [['reg_calendar','Replied to a calendar invitation','var(--ocean)'],['reg_manual','Added by the team (bulk import)','var(--navy)'],['reg_wg_page','Signed up on the webinar page','var(--ocean-2)']];
const DIM_PLAIN = {'Revenue':'earning revenue','Commercial conversion':'turning attendees into customers','Registration':'getting people to register','Attendance':'getting people to attend','Audience quality':'who joined','Engagement':'engagement','Outreach efficiency':'how well it was promoted'};

/* ---- "worth looking at" and the intelligence feed: deterministic, assembled from model numbers only ---- */
function signals(){
  const out=[], C=MODEL.commercial, T=totalsOf(W_ALL), SU=MODEL.superlatives;
  if(SU.commercial){ const w=byN(SU.commercial.n), a=statsOf(W_ALL,'revenue').avg, x=a?SU.commercial.v/a:null;
    out.push({kind:'REVENUE SIGNAL',cls:'rev',head:`Strongest revenue \u2014 W${w.n}`,text:x?`W${w.n} generated <b>${x.toFixed(1)}×</b> the programme average revenue.`:`W${w.n} earned the most webinar-attributed revenue.`,
      ev:`${gbp(SU.commercial.v)} from ${plural(w.m.customers.v,'customer')}, against ${gbp(a)} on average across ${statsOf(W_ALL,'revenue').n} mature webinars. ${MODEL.executive.find(e=>e.label==='Strongest commercial').text.split('. ')[0]}.`,why:`Shows what a strong webinar can deliver, and what is worth repeating.`,w:w.n,tab:'commercial'}); }
  if(SU.worst){ const w=byN(SU.worst.n), d=Object.entries(w.score.dims).filter(([k,x])=>nn(x.v)).sort((a,b)=>a[1].v-b[1].v)[0];
    out.push({kind:'WEAKEST WEBINAR',cls:'',head:`Weakest result \u2014 W${w.n}`,text:`W${w.n} has the lowest overall result at <b>${f1(w.score.total)}</b> out of 100${d?`, weakest at ${DIM_PLAIN[d[0]]||d[0].toLowerCase()}`:''}.`,
      ev:(MODEL.executive.find(e=>e.label==='Weakest overall')||{}).text||'',why:`This is where the next webinar has the most room to improve.`,w:w.n,tab:'overview'}); }
  if(T.reg) out.push({kind:'ATTENDANCE SIGNAL',cls:'',head:'Attendance \u2014 the programme-wide drop-off',text:`${f0(T.reg)} registered, ${f0(T.att)} attended: <b>${pc(T.att/T.reg*100,1)}</b>. ${f0(T.noshow)} registered people never joined.`,
      ev:`Registered → attended is the biggest people-loss before the sales steps. Definition: ${DEF['Attendance']||''}`,why:`Most people who register never join, so this is the biggest loss before any sale.`,stage:'attended',view:'engagement'});
  out.push({kind:'COMMERCIAL SIGNAL',cls:'rev',head:'Unlinked revenue',text:`<b>${gbpk(C.unattributed.revenue)}</b> of ${gbpk(C.total.revenue)} came from ${plural(C.unattributed.customers,'buyer')} who never attended a webinar.`,
    ev:`No webinar is credited for it, and the dashboard does not know where those buyers came from. Rule applied: ${C.attribution_rule}.`,why:`${pc(C.unattributed.revenue/C.total.revenue*100,0)} of revenue cannot be tied to a webinar, so the programme's impact may be understated.`,view:'commercial',prov:'revenue'});
  const parts=REG_METHODS.map(([k,l])=>({l,v:sum(W_ALL,w=>w.m[k].v)})), tot=sum(parts,p=>p.v), top=parts.slice().sort((a,b)=>b.v-a.v)[0];
  if(tot) out.push({kind:'ACQUISITION SIGNAL',cls:'',head:'Where sign-ups come from',text:`<b>${top.l}</b> accounts for ${pc(top.v/tot*100,0)} of sign-ups where the method is recorded.`,
    ev:`Website, LinkedIn, organic and paid traffic are not tracked, so they cannot be compared.`,why:`Knowing which route works shows where promotion effort should go.`,view:'acquisition'});
  MODEL.recommendations.filter(r=>r.pri>=1).slice(0,2).forEach(r=>{ const m=/\bW(\d+)\b/.exec(r.title+' '+r.why), n=m?+m[1]:null, up=MODEL.upcoming&&n===MODEL.upcoming.n;
    out.push({kind:'ACTION',cls:'act',head:r.title,text:`${esc(r.title)}.`,ev:firstSent(r.why)+' Evidence: '+r.evidence+'.',why:firstSent(r.why),...(up?{view:'next'}:(n&&byN(n))?{w:n,tab:'overview'}:{view:'webinars'})}); });
  return out; }
const worth = () => signals().slice(0,5);
const KIND_L = {'REVENUE SIGNAL':'Revenue','WEAKEST WEBINAR':'Weakest webinar','ATTENDANCE SIGNAL':'Attendance','COMMERCIAL SIGNAL':'Commercial','ACQUISITION SIGNAL':'Promotion','ACTION':'What to do next','TREND SIGNAL':'Trend','OUTLIER SIGNAL':'Stands out'};

/* ---- email campaigns attributed by documented ID only ---- */
const campaignsFor = list => MODEL.email_campaigns.filter(c=>c.mapped_webinar && list.some(w=>w.n===c.mapped_webinar));
