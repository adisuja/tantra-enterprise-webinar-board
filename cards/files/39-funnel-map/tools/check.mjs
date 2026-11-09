// Card 39 build check and export. Fails on: an unknown {{field}}, a pre-live email or 1-to-1 WhatsApp without the
// WebinarJam {{join_url}}, a 1-to-1 WhatsApp with no template entry, a template body over Meta's 1024 characters,
// a template without the STOP line, a group post that does not point to the personal link. Writes site/templates/*.csv.
import fs from 'node:fs';
import path from 'node:path';
const site = process.argv[2];
const { MESSAGES, FIELDS, WA_TEMPLATES, EMAIL_TEMPLATES, metaOf } = await import(path.resolve(site, 'data.js'));
const PRE = new Set(['reg', 'survey', 'upsell', 'checkout', 'confirm', 'countdown']);
const errs = [];
for (const m of MESSAGES) {
  const all = [m.subject, m.preview, m.body, m.group].filter(Boolean).join('\n');
  for (const [, f] of all.matchAll(/\{\{([a-z_]+)\}\}/g)) if (!FIELDS[f]) errs.push(`${m.id}: unknown field {{${f}}}`);
  if (/[–—]/.test(all)) errs.push(`${m.id}: em or en dash`);
  const personal = m.ch === 'email' || m.ch === 'wa' || (m.ch === 'system' && m.id === 'E0');
  if (PRE.has(m.stage) && personal && !['STOP', 'START', 'REF-X', 'CAL'].includes(m.id) && !m.body.includes('{{join_url}}')) errs.push(`${m.id}: no {{join_url}} (WebinarJam link)`);
  if ((m.group || m.ch === 'group') && PRE.has(m.stage) && !/WebinarJam email/.test(m.group || m.body)) errs.push(`${m.id}: group post does not point to the personal link`);
  if (m.ch === 'wa') {
    const t = WA_TEMPLATES[m.id];
    if (!t) errs.push(`${m.id}: no WhatsApp template entry`);
    else if (t[0]) {
      if (metaOf(m.body).text.length > 1024) errs.push(`${m.id}: template body over 1024 characters`);
      if (!/Reply STOP to opt out\.$/.test(m.body)) errs.push(`${m.id}: template must end with the STOP line`);
      if (/^\{\{|\}\}$/.test(metaOf(m.body).text.trim())) errs.push(`${m.id}: template starts or ends with a variable`);
    }
  }
  if (m.ch === 'email' && !EMAIL_TEMPLATES[m.id]) errs.push(`${m.id}: no email template name`);
}
if (errs.length) { console.error('CHECK FAILED\n' + errs.join('\n')); process.exit(1); }
const csv = (rows) => rows.map((r) => r.map((v) => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')).join('\n') + '\n';
fs.mkdirSync(path.join(site, 'templates'), { recursive: true });
const em = MESSAGES.filter((m) => m.ch === 'email' || m.id === 'E0');
fs.writeFileSync(path.join(site, 'templates/emails.csv'), csv([['id', 'template_name', 'sends', 'trigger', 'audience', 'subject', 'preview', 'body'],
  ...em.map((m) => [m.id, EMAIL_TEMPLATES[m.id], m.when, m.trigger, m.audience, m.subject, m.preview, m.body])]));
const wa = MESSAGES.filter((m) => m.ch === 'wa' || m.ch === 'group' || m.group);
fs.writeFileSync(path.join(site, 'templates/whatsapp.csv'), csv([['id', 'template_name', 'category', 'language', 'sends', 'trigger', 'audience', 'body_with_fields', 'meta_body', 'meta_variables', 'group_post'],
  ...wa.map((m) => { const t = WA_TEMPLATES[m.id] || ['', m.ch === 'group' ? 'Group post' : '']; const mt = metaOf(m.body);
    return [m.id, t[0], t[1], t[0] ? 'en' : '', m.when, m.trigger, m.audience, m.ch === 'group' ? '' : m.body, t[0] ? mt.text : '', t[0] ? mt.vars.map((v) => `{{${v.n}}}=${v.field} (e.g. ${v.example})`).join(' | ') : '', m.group || (m.ch === 'group' ? m.body : '')]; })]));
console.log(`check ok: ${MESSAGES.length} messages, ${em.length} emails, ${wa.length} WhatsApp rows exported`);
