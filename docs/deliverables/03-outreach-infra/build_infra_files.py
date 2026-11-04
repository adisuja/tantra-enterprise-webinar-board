#!/usr/bin/env python3
"""Writes DOMAIN_SHORTLIST.md, DNS_RECORDS.md, sender-roster.csv and sender-roster.xlsx from the lists below.

usage: python3 build_infra_files.py        (xlsx needs openpyxl; without it the CSV and markdown are still written)

Edit WORKSPACE_DOMAINS or RESERVES if a name is taken at registration, then rerun. The xlsx is gitignored.
"""
import csv, pathlib

HERE = pathlib.Path(__file__).resolve().parent
CHECKED = "2026-11-04"

# 80 active domains, 20 per Workspace: 15 plain, company-like names (pairs share a name, as one firm with two
# domains would) and 5 webinar or strategy themed. Every name returned "not found" from Verisign RDAP on CHECKED.
WORKSPACE_DOMAINS = {
    1: ["northgatesessions.com", "northgatebriefings.com", "harborlineinsights.com", "harborlinesessions.com",
        "brightfieldinsights.com", "brightfieldsessions.com", "clearwatersessions.com", "clearwaterbriefings.com",
        "keystonesessions.com", "keystonebriefings.com", "lindenparkinsights.com", "fairhaveninsights.com",
        "westbrooksessions.com", "eastmereinsights.com", "oakhurstinsights.com", "strategyhourlive.com",
        "webinarbriefings.com", "founderbriefinghq.com", "revenuestrategylive.com", "b2bstrategyhour.com"],
    2: ["ridgewayinsights.com", "ridgewaysessions.com", "cedarlineinsights.com", "cedarlinesessions.com",
        "stonebridgesessions.com", "stonebridgebriefings.com", "granitepeakinsights.com", "granitepeaksessions.com",
        "birchwoodsessions.com", "birchwoodbriefings.com", "silverleafinsights.com", "bluecrestsessions.com",
        "hollowbrookinsights.com", "quarrystoneinsights.com", "thornburyinsights.com", "strategybriefinghq.com",
        "briefingroomlive.com", "foundersstrategyhour.com", "pipelinestrategylive.com", "weeklystrategylive.com"],
    3: ["larkspurinsights.com", "larkspursessions.com", "meridianwayinsights.com", "meridianwaysessions.com",
        "beaconfieldinsights.com", "beaconfieldsessions.com", "riverstonesessions.com", "riverstonebriefings.com",
        "lumenvaleinsights.com", "lumenvalesessions.com", "wrenfieldinsights.com", "foxgloveinsights.com",
        "copperbeechinsights.com", "kingsmereinsights.com", "mapleridgeinsights.com", "livestrategysessions.com",
        "operatorroundtable.com", "strategyforumlive.com", "airevenuebriefing.com", "executivestrategyhour.com"],
    4: ["juniperhillinsights.com", "juniperhillsessions.com", "alderpointinsights.com", "alderpointsessions.com",
        "cobaltridgeinsights.com", "cobaltridgesessions.com", "slatehouseinsights.com", "slatehousesessions.com",
        "amberlaneinsights.com", "amberlanesessions.com", "highmoorinsights.com", "greystonesessions.com",
        "ashcombeinsights.com", "pinecrestsessions.com", "willowmereinsights.com", "strategyroundtablehq.com",
        "strategysessionshq.com", "livewebinarseries.com", "strategyplaybooklive.com", "revenueroundtablehq.com"],
}
RESERVES = ["strategyinsightlive.com", "webinarroomhq.com", "liveroundtablehq.com", "foundersforumlive.com",
            "airevenuesessions.com", "revenuebriefinghq.com", "strategyseminarhq.com", "b2bwebinarseries.com",
            "executivebriefinglive.com", "aiwebinarseries.com"]
TAKEN = ["aistrategysessions.com", "pipelinebriefing.com", "thestrategyhour.com", "strategydeskhq.com"]
WORKSPACES = {1: "W1 strategywebinars (existing)", 2: "W2 new", 3: "W3 new", 4: "W4 new"}
PRIMARY = {1: "strategywebinars.com", 2: WORKSPACE_DOMAINS[2][0], 3: WORKSPACE_DOMAINS[3][0], 4: WORKSPACE_DOMAINS[4][0]}
# Every sender is the webinar host, so no persona is invented. Domains 1 to 10 of each Workspace get 6, 11 to 20 get 5:
# 110 senders a Workspace, 440 in all.
USERS = [("adi", "Adi Murali"), ("adithya", "Adithya Murali"), ("adi.murali", "Adi Murali"),
         ("adithya.murali", "Adithya Murali"), ("a.murali", "Adi Murali"), ("adi.m", "Adi Murali")]
# Invites a sender a day by plan week: weeks 1 to 3 none (days 0 to 20), 4 to 9 at 10 (days 21 to 62),
# 10 to 13 at 25 (days 63 to 90), 14 on at 50 (day 91 on). CAPACITY_PLAN.md explains the sources.
CAPS = [0, 0, 0, 10, 10, 10, 10, 10, 10, 25, 25, 25, 25, 50]
CAP_COLS = [f"daily_cap_wk{i:02d}" for i in range(1, 14)] + ["daily_cap_wk14_on"]
COLS = ["workspace", "pool", "domain", "user", "email", "display_name", "role", "created", "warmup_start_day0",
        "service_account_project"] + CAP_COLS + ["tantra_service_account_connected", "tantra_max_per_day_set", "notes"]


def roster():
    rows = []
    for w in (2, 3, 4):
        d = PRIMARY[w]
        rows.append({"workspace": WORKSPACES[w], "pool": f"P{w}", "domain": d, "user": "admin", "email": f"admin@{d}",
                     "display_name": "Workspace admin", "role": "admin (not a sender; holds the dmarc@ aliases)",
                     "created": "FILL_DATE", "warmup_start_day0": "FILL_DATE_100_USD_PAID", "service_account_project": "",
                     **{c: "" for c in CAP_COLS}, "tantra_service_account_connected": "", "tantra_max_per_day_set": "",
                     "notes": "primary domain"})
    for w, doms in WORKSPACE_DOMAINS.items():
        for i, d in enumerate(doms):
            for u, name in USERS[: 6 if i < 10 else 5]:
                rows.append({"workspace": WORKSPACES[w], "pool": f"P{w}", "domain": d, "user": u, "email": f"{u}@{d}",
                             "display_name": name, "role": "sender", "created": "FILL_DATE",
                             "warmup_start_day0": "FILL_DATE_100_USD_PAID",
                             "service_account_project": f"cal-outreach-w{w}{'a' if i < 10 else 'b'}",
                             **dict(zip(CAP_COLS, CAPS)), "tantra_service_account_connected": "FILL_YES_NO",
                             "tantra_max_per_day_set": "FILL", "notes": ""})
    return rows


def block(n, d, where):
    return [f"## {n}. {d}  ({where})", "", "```",
            "Type  Name               Priority  Value",
            "TXT   @                            FILL_WHOLE_VALUE_GOOGLE_SHOWS (starts google-site-verification=)",
            "MX    @                  1         SMTP.GOOGLE.COM",
            "TXT   @                            v=spf1 include:_spf.google.com ~all",
            "TXT   google._domainkey            FILL_WHOLE_VALUE_GOOGLE_SHOWS (starts v=DKIM1; k=rsa; p=)",
            f"TXT   _dmarc                       v=DMARC1; p=none; rua=mailto:dmarc@{d}; fo=1",
            "```", ""]


def dns_md():
    L = ["# DNS Records per Domain (copy-paste blocks)", "",
         "Written by `build_infra_files.py`. In the iFreeDomains panel: My Domains, Manage Domain, Manage iFreeDomains DNS.",
         "A Name of `@` means leave the Name field blank (the root of the domain).", "",
         "Two values come from Google Admin and replace the `FILL_` text: the verification TXT (when you add the domain)",
         "and the DKIM key (`ADI_STEPS.md` step 6). Exactly one SPF record per domain: never add a second.",
         "DMARC reports go to `dmarc@<the same domain>`, an alias on the Workspace admin (`ADI_STEPS.md` step 5), so no",
         "outside domain has to consent.", ""]
    n = 0
    for w, doms in WORKSPACE_DOMAINS.items():
        for d in doms:
            n += 1
            L += block(n, d, f"Workspace {WORKSPACES[w]}, pool P{w}")
    for d in RESERVES:
        n += 1
        L += block(n, d, "reserve")
    L += ["## Check What the World Sees (public DNS, no key)", "", "Replace the domain and run:", "", "```bash",
          "for t in TXT MX; do curl -s -H 'accept: application/dns-json' \"https://cloudflare-dns.com/dns-query?name=northgatesessions.com&type=$t\"; echo; done",
          "curl -s -H 'accept: application/dns-json' 'https://cloudflare-dns.com/dns-query?name=_dmarc.northgatesessions.com&type=TXT'; echo",
          "curl -s -H 'accept: application/dns-json' 'https://cloudflare-dns.com/dns-query?name=google._domainkey.northgatesessions.com&type=TXT'; echo",
          "```", "",
          "Pass: one `v=spf1` record, MX `smtp.google.com`, a `v=DMARC1` record, a DKIM key, nothing listed twice.",
          "After two clean weeks, change DMARC `p=none` to `p=quarantine`.", ""]
    return "\n".join(L)


def shortlist_md():
    L = ["# Domain Shortlist: 80 Active and 10 Reserves", "",
         "Rules: `.com`, no hyphens, never growthclub.org or usetantra.com, nothing that reads as Tantra or GrowthClub, and",
         "none of the existing Tantra calendar names (strategywebinars, visionarywebinars, seminarvision, nextgenwebinars, signonline).", "",
         "**Why most names are plain.** The senders behind the master list used webinar-themed domains, and 156,018 of",
         "those recipients declined. A plain, company-like name (`northgatesessions.com`) does not repeat that pattern.",
         "Each Workspace gets 15 plain names (pairs share a name, as one firm with two domains would) and 5 themed ones,",
         "so the two styles can be compared on decline rates in the first weeks.", "",
         f"Every name returned \"not found\" from the Verisign .com registry (RDAP) on {CHECKED}. A name can still be taken",
         "before Adi registers it, or be priced as \"Special\" at iFreeDomains: skip it and take a reserve. The plain names",
         "were checked for registration only: before buying, search each one to make sure no live company trades under it.", "",
         "| # | Domain | Style | Workspace | Senders |", "| --- | --- | --- | --- | --- |"]
    n = 0
    for w, doms in WORKSPACE_DOMAINS.items():
        for i, d in enumerate(doms):
            n += 1
            tag = " (primary)" if d == PRIMARY[w] else ""
            L.append(f"| {n} | {d} | {'plain' if i < 15 else 'themed'} | {WORKSPACES[w]}{tag} | {6 if i < 10 else 5} |")
    L += ["", "## Reserves (register now, leave parked so they age)", "", "| # | Domain |", "| --- | --- |"]
    for d in RESERVES:
        n += 1
        L.append(f"| {n} | {d} |")
    L += ["", "W1's primary domain is strategywebinars.com (registered 2026-09-27 at Cloudflare, nameservers on Cloudflare).", "",
          "Checked and already taken (do not use): " + ", ".join(TAKEN) + ", plus 60 plain combinations rejected in the same check.", "",
          "Recheck any name (public, no account): `curl -s -o /dev/null -w \"%{http_code}\\n\" https://rdap.verisign.com/com/v1/domain/northgatesessions.com`",
          "prints 404 when the name is free.", "",
          "If a name changes, edit `WORKSPACE_DOMAINS` in `build_infra_files.py` and rerun it: this file, `DNS_RECORDS.md` and the roster follow.", ""]
    return "\n".join(L)


def main():
    rows = roster()
    with open(HERE / "sender-roster.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
    (HERE / "DNS_RECORDS.md").write_text(dns_md())
    (HERE / "DOMAIN_SHORTLIST.md").write_text(shortlist_md())
    senders = sum(r["role"] == "sender" for r in rows)
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ImportError:
        print(f"{senders} senders; openpyxl missing, no xlsx"); return
    wb = Workbook(); ws = wb.active; ws.title = "Senders"
    ws.append(COLS)
    for r in rows:
        ws.append([r[c] for c in COLS])
    for c in ws[1]:
        c.font = Font(bold=True)
    ws.freeze_panes = "E2"
    plan = wb.create_sheet("Caps by week")
    plan.append(["Plan week", "Mon to Fri if Day 0 is Mon 9 Nov 2026", "Invites a sender a day", "Senders", "Send days", "Week capacity"])
    dates = ["9 to 13 Nov", "16 to 20 Nov", "23 to 27 Nov", "30 Nov to 4 Dec", "7 to 11 Dec", "14 to 18 Dec",
             "21 to 24 Dec", "28 to 31 Dec", "4 to 8 Jan 2027", "11 to 15 Jan", "18 to 22 Jan", "25 to 29 Jan",
             "1 to 5 Feb", "8 Feb 2027 on"]
    days = [5, 5, 5, 5, 5, 5, 4, 4, 5, 5, 5, 5, 5, 5]
    for k in range(14):
        plan.append([k + 1, dates[k], CAPS[k], senders, days[k], f"=C{k + 2}*D{k + 2}*E{k + 2}"])
    for c in plan[1]:
        c.font = Font(bold=True)
    wb.save(HERE / "sender-roster.xlsx")
    print(f"{len(rows)} roster rows ({senders} senders), {sum(map(len, WORKSPACE_DOMAINS.values())) + len(RESERVES)} DNS blocks, xlsx")


if __name__ == "__main__":
    main()
