import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
const b = await chromium.launch(); const p = await b.newPage({viewport:{width:1584,height:396}});
await p.goto('file:///home/user/tantra-enterprise-webinar-workspace/deliverables/29-linkedin-profile-branding/v2/.build/adi-cover-1584x396.html');
console.log(await p.evaluate(()=>[...document.querySelectorAll('.logos')].map(e=>[e.clientWidth,e.scrollWidth])));
await p.goto('file:///home/user/tantra-enterprise-webinar-workspace/deliverables/29-linkedin-profile-branding/v2/.build/featured-workshop-1200x627.html');
console.log(await p.evaluate(()=>[...document.querySelectorAll('.logos')].map(e=>[e.clientWidth,e.scrollWidth])));
await b.close();
