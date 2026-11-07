// Writes 3-REVENUE-PLAN-MODEL.md from the model itself (src/assets/plan-model.js), so the card never drifts from the code.
// usage: node tools/model-doc.mjs
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const T = require(path.join(here, '../../13-15a-26-20-pages/src/assets/plan-model.js'));
const fmt = (x) => Math.round(x).toLocaleString('en-US');

let md = `# The Revenue Plan model: ten funnels, six stages, every KPI

Generated from the calculator's own code (src/assets/plan-model.js in the pages folder) by tools/model-doc.mjs. Change the code, then rerun it. Round 2 (Adi 2026-11-08): every rate is built on our own webinar data (7-OUR-WEBINAR-DATA.md) and set conservatively.

## How the plan is worked out

1. **Goal.** The 12-month revenue goal from the survey (blank: new revenue equal to today's yearly run rate, at least $120,000). On the plan it is the big number on the right, and it can be typed over.
2. **Revenue per sign-up.** Each funnel is a chain of stage rates from a sign-up (registrant, lead, application, half-watcher, member, commenter) to a paying customer. One sign-up's expected revenue is the chain's customers times the revenue per customer in the first 12 months, plus any low-ticket sales (OOO and SLO).
3. **Sign-ups needed a month.** The goal divided by the revenue per sign-up, spread over the funnel's cycles (52 webinars a year, 6 challenges, 3 launches, otherwise 12 months).
4. **Traffic.** Your own audience first, at a warm rate (2.5 times the cold page rate). The rest is split across the channels picked in the survey: the ad budget buys what it can, then calendar invites, cold email, LinkedIn, WhatsApp, content and partners share the remainder by weight (70, 10, 10, 5, 5, 5), or by the shares typed on the plan. Event funnels register people straight from a channel; the others send people to a page first. The plan shows how many invites, emails, connection requests and messages to send, and the ad spend.
5. **Revenue per customer.** One-time and annual offers: the price. Monthly offers: customers join evenly through the year and leave at the monthly churn (9% for a cold start down to 4% for the strongest profile), so the average customer pays for fewer than 12 months.
6. **Personalisation.** The survey answers place each KPI between 10% and 80% of the way from low to strong: conservative by design, never the top of a range. Close and buy-online rates move with the price (the whole range scales). Every KPI can be typed over on the plan; the arrow puts it back.
7. **The next 52 weeks.** A small line under the plan: extra customers from a year of nurture for the people who did not buy, never counted in the goal.

## Funnel fit (question 10)

Every funnel starts at 50 points; the answers add or take away points with a reason the person sees (price, sales motion, B2B or B2C, audience size, ad budget, hours, proof, funnels already built). Webinar and reverse squeeze page carry a priority boost of 12 (Adi 2026-11-08: prioritise them), workshop series 4, book a call and challenge 2. The top three are marked recommended.

## Traffic channels (stage 1)

| Channel | Event funnels: sign-ups per unit sent (low, typical, strong) | Other funnels: page visits per unit sent | Source |
| --- | --- | --- | --- |
`;
const rate = (k) => (!k ? 'not used' : k.fmt === 'usd' ? `$${k.ty} a click (B2C $0.75)` : `${k.lo}%, ${k.ty}%, ${k.hi}%`);
for (const c of Object.values(T.CH)) md += `| ${c.name} | ${c.ev ? rate(c.ev) : 'goes through the page'} | ${rate(c.pg)} | ${(c.ev || c.pg).src} |\n`;

md += '\n## The stages and every KPI\n\nLow, typical and strong are percentages unless marked as dollars. "call" KPIs apply only when clients buy after a call; "online" only when they buy without one. Stages: 1 Traffic, 2 Landing and sign-up, 3 Nurture, 4 Conversion, 5 Revenue and pipeline, 6 The next 52 weeks.\n';
for (const id of T.ORDER) {
  const f = T.FUNNELS[id];
  const notes = [`Sign-up: ${f.signup.toLowerCase()}.`, `${f.cadence.perYear} ${f.cadence.per}s a year.`, f.event ? 'Event funnel: channels register people directly.' : '', f.callOnly ? 'Always a call offer.' : '', f.adsOnly ? 'Traffic is paid ads only.' : '', f.organic ? 'Traffic is your own posts only.' : ''].filter(Boolean).join(' ');
  md += `\n### ${f.name}\n\n${f.blurb} ${notes}\n\n| Stage | KPI | Definition | Low | Typical | Strong | Applies | Source |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n`;
  f.kpis.forEach((k) => {
    const u = (x) => (k.fmt === 'usd' ? `$${x}` : `${x}%`);
    const applies = k.flags === 'call' ? 'call' : k.flags === 'checkout' ? 'online' : 'always';
    md += `| ${k.stage} | ${k.name} (${k.id}) | ${k.def} | ${u(k.lo)} | ${u(k.ty)} | ${u(k.hi)} | ${applies} | ${k.src} |\n`;
  });
}

const S = { offer_type: 'consulting', market: 'b2b', price: 9999, price_model: 'one_time', motion: 'call', revenue_now: 2, goal: 500000, revenue_built: 3, years: 3, clients: 2, case_studies: 2, brands: 1, funnel_exp: 1, revops: 1, email_list: 2000, followers: 3000, channels: ['calendar', 'linkedin', 'ads'], ad_budget: 2000, hours: 1, team_help: 1 };
md += '\n## Worked example (shown when no survey answers exist)\n\nA B2B consultant selling a $9,999 one-time offer after a call, $10K to $50K a month now, goal $500,000 in 12 months, 3 to 5 case studies, one funnel tried before, spreadsheets, 2,000 email subscribers, 3,000 followers, calendar invites, LinkedIn and $2,000 a month of ads, 5 to 10 hours a week. Every number is a month.\n\n| Funnel | Fit | Sign-ups | Outreach to send | Customers |\n| --- | --- | --- | --- | --- |\n';
for (const r of T.recommend(S)) {
  const p = T.plan(r.id, S);
  const out = p.lines.filter((l) => l.id !== 'owned').map((l) => (l.money ? `$${fmt(l.reach)} ads` : `${fmt(l.reach)} ${l.unit.replace(' to send', '')}`)).join('; ');
  md += `| ${r.name} | ${r.fit}% | ${fmt(p.signupsMonth)} ${p.signup.toLowerCase()} | ${out} | ${p.custMonth.toFixed(1)} |\n`;
}
if (/[–—]/.test(md)) throw new Error('dash in output');
fs.writeFileSync(path.join(here, '..', '3-REVENUE-PLAN-MODEL.md'), md);
console.log('wrote 3-REVENUE-PLAN-MODEL.md', md.length);
