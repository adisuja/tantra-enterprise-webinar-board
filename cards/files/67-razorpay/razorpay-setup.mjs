/**
 * Push catalogue.json to Razorpay as subscription Plans (one per currency).
 *
 *   node razorpay-setup.mjs            -> dry run: shows what it would create
 *   node razorpay-setup.mjs --apply    -> creates the missing plans
 *
 * Keys come from ~/.config/tantra/keys/razorpay.env (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET).
 * Idempotent: every plan carries notes.catalogue_key + notes.currency, and an existing
 * plan with the same pair and amount is reused. Razorpay plans are immutable, so a price
 * change creates a new plan; the old one stays for existing subscribers.
 * Writes the resulting plan ids to plan-ids.json (no secrets) for the checkout routes.
 * USD plans need international payments approved on the account (ticket #21821390).
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const envFile = join(homedir(), ".config/tantra/keys/razorpay.env");
if (existsSync(envFile)) {
  for (const line of readFileSync(envFile, "utf8").split("\n")) {
    const m = line.match(/^\s*([A-Z_]+)\s*=\s*(.*)\s*$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
}
const { RAZORPAY_KEY_ID: ID, RAZORPAY_KEY_SECRET: SECRET } = process.env;
if (!ID || !SECRET) {
  console.error("Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in " + envFile);
  process.exit(1);
}
const APPLY = process.argv.includes("--apply");
const AUTH = "Basic " + Buffer.from(`${ID}:${SECRET}`).toString("base64");

async function rzp(method, path, body) {
  const r = await fetch("https://api.razorpay.com/v1" + path, {
    method,
    headers: { Authorization: AUTH, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const j = await r.json();
  if (!r.ok) throw new Error(`${method} ${path} ${r.status}: ${JSON.stringify(j.error ?? j)}`);
  return j;
}

async function allPlans() {
  const out = [];
  for (let skip = 0; ; skip += 100) {
    const { items } = await rzp("GET", `/plans?count=100&skip=${skip}`);
    out.push(...items);
    if (items.length < 100) return out;
  }
}

const cat = JSON.parse(readFileSync(join(here, "catalogue.json"), "utf8"));
const existing = await allPlans();
const ids = {};

for (const s of cat.subscriptions) {
  for (const [cur, amount] of [["USD", s.usd], ["INR", s.inr]]) {
    if (!amount) continue;
    const hit = existing.find(
      (p) => p.notes?.catalogue_key === s.key && p.item.currency === cur && p.item.amount === amount,
    );
    if (hit) {
      ids[`${s.key}:${cur}`] = hit.id;
      console.log(`ok      ${s.key} ${cur} ${amount} -> ${hit.id}`);
      continue;
    }
    if (!APPLY) {
      console.log(`create  ${s.key} ${cur} ${amount} (${s.period})`);
      continue;
    }
    const p = await rzp("POST", "/plans", {
      period: s.period,
      interval: s.interval,
      item: { name: s.name, amount, currency: cur, description: s.name },
      notes: { catalogue_key: s.key, currency: cur, trial_days: String(s.trial_days ?? 0) },
    });
    ids[`${s.key}:${cur}`] = p.id;
    console.log(`created ${s.key} ${cur} ${amount} -> ${p.id}`);
  }
}

if (APPLY) {
  writeFileSync(join(here, "plan-ids.json"), JSON.stringify(ids, null, 2) + "\n");
  console.log("wrote plan-ids.json");
}
