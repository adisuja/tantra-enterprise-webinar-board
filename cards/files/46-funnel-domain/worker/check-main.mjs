// Runs before every `wrangler deploy` of this Worker (build.command in wrangler.jsonc).
// Several sessions deploy this one Worker. A deploy from a branch without the latest main silently undoes newer work
// (14 Nov: a card 72 deploy removed the date roll, CRM attribution, dedupe and the consent banner). This stops that.
// Emergency override: FUNNEL_DEPLOY_FORCE=1.
import { execSync } from 'node:child_process';
const sh = (c) => execSync(c, { stdio: ['ignore', 'pipe', 'pipe'] }).toString().trim();
if (process.env.FUNNEL_DEPLOY_FORCE === '1') { console.warn('check-main: FUNNEL_DEPLOY_FORCE=1, skipping the main check'); process.exit(0); }
try { sh('git fetch origin main --quiet'); } catch (e) {
  console.error('check-main: could not fetch origin/main, so I cannot prove this branch has the latest main. Fix the network or remote, then deploy again.');
  process.exit(1);
}
try { sh('git merge-base --is-ancestor origin/main HEAD'); } catch (e) {
  const behind = sh('git rev-list --count HEAD..origin/main');
  console.error(`check-main: this branch is ${behind} commit(s) behind origin/main. Deploying it would undo newer live work.\n` +
    'Run: git fetch origin && git merge origin/main, rebuild (node deliverables/13-15a-26-20-pages/build.mjs), commit, then deploy.');
  process.exit(1);
}
console.log('check-main: branch contains the latest origin/main');
