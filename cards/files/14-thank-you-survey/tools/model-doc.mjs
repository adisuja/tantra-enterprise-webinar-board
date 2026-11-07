// Writes 3-REVENUE-PLAN-MODEL.md from the model itself (src/assets/plan-model.js), so the card never drifts from the code.
// usage: node tools/model-doc.mjs
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const T = require(path.join(here, '../../13-15a-26-20-pages/src/assets/plan-model.js'));
const pct = (x) => `${x}%`;
const fmt = (x) => Math.round(x).toLocaleString('en-US');

let md = `# The Revenue Plan model: ten funnels, six stages, every KPI

Generated from the calculator's own code (src/assets/plan-model.js in the pages folder) by tools/model-doc.mjs. Change the code, then rerun it.

## How the plan is worked out

1. **Goal.** The 12-month revenue goal from question 4 (blank: double today's run rate, at least $120,000), split across the funnel's cycles in a year (a webinar runs 52 times, a challenge 6, a launch 3, evergreen funnels 12 months).
Sources marked "self-reported; treat as a planning assumption" come from operator and agency reports, not audited data (grade B in 6-BENCHMARKS.md).

2. **Revenue per entry visit.** Every funnel is a chain of stage rates from the entry page to a paying customer. One visit's expected revenue is the chain's customers times the revenue per customer in the first 12 months, plus any low-ticket sales (OOO and SLO).
3. **Traffic needed.** Goal per cycle divided by revenue per visit. Plan from traffic instead: type the visits, and the revenue comes out.
4. **Where the traffic comes from.** The audience you own first (email list, followers, YouTube, community, site visitors, each with its own monthly rate), then the ad budget, then the outreach channels picked in question 9, split evenly. Each channel shows the outreach volume it needs (emails, connection requests, invites, ad spend) and, for cold email and LinkedIn, how many inboxes or accounts that takes.
5. **Revenue per customer.** One-time and annual offers: the price. Monthly offers: customers join evenly through the year and leave at the monthly churn (9% for a cold start down to 4% for the strongest profile, inside the sourced 4% to 9% range), so the average customer pays for fewer than 12 months.
6. **The next 52 weeks.** Everyone who joined the list and did not buy is worked for a year (weekly email, WhatsApp, check-in calls). The extra customers are tied to the funnel's own conversion (Nurture Recovery Rate, a planning figure), shown as a count only and never counted in the goal.
7. **Personalisation.** Each KPI sits between its low and strong value (never outside them), placed by the survey (2-SURVEY.md, "How the answers move each KPI"). Every KPI can be typed over; "Auto" puts it back.

## Funnel fit (question 10)

Every funnel starts at 50 points; the answers add or take away points with a reason the person sees (price, sales motion, B2B or B2C, audience size, ad budget, hours, proof, funnels already built). Webinar and reverse squeeze page carry a priority boost of 12 (Adi 2026-11-08: prioritise them), workshop series 4, book a call and challenge 2. The top three are marked recommended.

## The six stages and every KPI

Low, typical and strong are percentages. "call" KPIs apply only when clients buy after a call; "online" only when they buy without one. Stage numbers follow the playbook's FunnelOS canon: 1 Traffic, 2 Landing and sign-up, 3 Nurture, 4 Conversion, 5 Revenue and pipeline, 6 The next 52 weeks.
`;

for (const id of T.ORDER) {
  const f = T.FUNNELS[id];
  const notes = [
    `Entry: ${f.entry}.`,
    `Cadence: ${f.cadence.perYear} ${f.cadence.per}s a year.`,
    f.callOnly ? 'Always a call offer.' : '',
    f.adsOnly ? 'Traffic is paid ads only.' : '',
    f.organic ? 'Traffic is your own posts only.' : '',
    f.prices ? `Default prices: ${Object.entries(f.prices).map(([k, v]) => `${k} $${v}`).join(', ')} (the survey's entry price replaces the entry default).` : ''
  ].filter(Boolean).join(' ');
  md += `\n### ${f.name}\n\n${f.blurb} ${notes}\n\n| Stage | KPI | Definition | Low | Typical | Strong | Applies | Source |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n`;
  f.kpis.forEach((k) => {
    const applies = k.flags === 'call' ? 'call' : k.flags === 'checkout' ? 'online' : 'always';
    md += `| ${k.stage} | ${k.name} (${k.id}) | ${k.def} | ${pct(k.lo)} | ${pct(k.ty)} | ${pct(k.hi)} | ${applies} | ${k.src} |\n`;
  });
}

md += '\n## Traffic channels (stage 1)\n\n| Channel | Page visits per unit | How | Source |\n| --- | --- | --- | --- |\n';
for (const [id, c] of Object.entries(T.CHANNELS)) {
  const label = c.name + (id === 'ads_b2c' ? ' (B2C)' : id === 'ads' ? ' (B2B)' : '');
  const rate = c.vr ? `${(c.vr * 100).toFixed(2)}% of ${c.unit}` : `$${c.cpv.toFixed(2)} per visit`;
  md += `| ${label} | ${rate} | ${c.how} | ${c.src} |\n`;
}
md += '\n| Audience you own | Visits a month per person | How | Source |\n| --- | --- | --- | --- |\n';
for (const c of Object.values(T.OWNED)) md += `| ${c.name} | ${(c.per * 100).toFixed(2)}% | ${c.how} | ${c.src} |\n`;

const S = { offer_type: 'consulting', market: 'b2b', price: 9999, price_model: 'one_time', motion: 'call', cycle: 'weeks', revenue_now: 2, goal: 500000, revenue_built: 3, team_led: 1, years: 3, clients: 2, case_studies: 2, brands: 1, funnel_exp: 1, revops: 1, email_list: 2000, followers: 3000, channels: ['cold_email', 'linkedin', 'ads'], ad_budget: 2000, hours: 1, team_help: 1 };
md += '\n## Worked example (shown when no survey answers exist)\n\nA B2B consultant selling a $9,999 one-time offer after a call, $10K to $50K a month now, goal $500,000 in 12 months, 3 to 5 case studies, one funnel tried before, spreadsheets, 2,000 email subscribers, 3,000 followers, cold email, LinkedIn and $2,000 a month of ads, 5 to 10 hours a week.\n\n| Funnel | Fit | Visits a month for the goal | Customers a year | Calls held a month |\n| --- | --- | --- | --- | --- |\n';
for (const r of T.recommend(S)) {
  const p = T.plan(r.id, S);
  const held = (p.rows.find((x) => /held/i.test(x.label)) || { n: 0 }).n * p.cycles / 12;
  md += `| ${r.name} | ${r.fit}% | ${fmt(p.perMonth)} | ${fmt(p.customers * p.cycles)} | ${held ? held.toFixed(1) : 'none'} |\n`;
}
if (/[–—]/.test(md)) throw new Error('dash in output');
fs.writeFileSync(path.join(here, '..', '3-REVENUE-PLAN-MODEL.md'), md);
console.log('wrote 3-REVENUE-PLAN-MODEL.md', md.length);
