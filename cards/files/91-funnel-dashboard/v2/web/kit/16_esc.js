const esc = s => { let t=String(s==null?'':s); if(!S.debug) for(const [r,x] of SCRUB) t=t.replace(r,x); return t.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); };
// model sentences that contain our own <b> markup are built from numbers only; this strips internal names without escaping them
const scrub = s => { let t=String(s==null?'':s); if(!S.debug) for(const [r,x] of SCRUB) t=t.replace(r,x); return t; };
// vendor names read as plain descriptions in the client view (debug mode keeps the real names)
SCRUB.push([/WebinarGeek/g,'the webinar platform'],[/Tantra/g,'the invitation system'],[/Instantly/g,'the email tool'],[/\bGHL\b/g,'the CRM'],[/\bthe the\b/g,'the']);
SCRUB.push([/Spearman association with leave-one-out range/g,'pattern across webinars'],[/leave-one-out/gi,'checked without any single webinar'],[/Spearman/g,'rank-based']);
SCRUB.push([/[\w\-\/.']*\w\.(?:json|csv)'?/g,'the source file']);
SCRUB.push([/ by pipeline stage \w+ \(rc=\d+\)/g,''],[/pipeline stage/g,'update']);
