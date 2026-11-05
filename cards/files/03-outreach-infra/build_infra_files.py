#!/usr/bin/env python3
"""Writes DOMAIN_SHORTLIST.md, DNS_RECORDS.md, sender-roster.csv and sender-roster.xlsx from the lists below.

usage: python3 build_infra_files.py        (xlsx needs openpyxl; without it the CSV and markdown are still written)

Edit WORKSPACE_DOMAINS or SPARES if a name is taken at registration, then rerun. The xlsx is gitignored.
Plan (Adi 2026-11-05): 100,000 invites a week / 7 days / 200 a sender a day = 71.4, so 72 senders on
12 domains x 6 mailboxes = 100,800 a week. 4 Workspaces x 3 domains x 18 senders.
"""
import csv, pathlib

HERE = pathlib.Path(__file__).resolve().parent
CHECKED = "2026-11-05"

# 12 primary domains, 3 per Workspace. Plain, company-like names from the list checked on 2026-11-04,
# rechecked "not found" at Verisign RDAP on CHECKED.
WORKSPACE_DOMAINS = {
    1: ["northgatesessions.com", "harborlineinsights.com", "brightfieldinsights.com"],
    2: ["ridgewayinsights.com", "cedarlineinsights.com", "stonebridgesessions.com"],
    3: ["larkspurinsights.com", "meridianwayinsights.com", "beaconfieldinsights.com"],
    4: ["juniperhillinsights.com", "alderpointinsights.com", "cobaltridgeinsights.com"],
}
SPARES = ["granitepeakinsights.com", "riverstonesessions.com", "slatehouseinsights.com", "keystonesessions.com"]
WORKSPACES = {1: "W1 strategywebinars (existing)", 2: "W2 new", 3: "W3 new", 4: "W4 new"}
PRIMARY = {1: "strategywebinars.com", 2: WORKSPACE_DOMAINS[2][0], 3: WORKSPACE_DOMAINS[3][0], 4: WORKSPACE_DOMAINS[4][0]}
# Six mailboxes a domain. Every sender is the webinar host, so no persona is invented.
USERS = [("adi", "Adi Murali"), ("adithya", "Adithya Murali"), ("adi.murali", "Adi Murali"),
         ("adithya.murali", "Adithya Murali"), ("a.murali", "Adi Murali"), ("adi.m", "Adi Murali")]
# Invites a sender a day for each webinar's send window (the 7 days before it), Day 0 = Mon 9 Nov 2026.
# CAPACITY_PLAN.md explains each step.
WEEKS = [("2026-11-12", "5 to 11 Nov", 0, 7), ("2026-11-19", "12 to 18 Nov", 0, 7), ("2026-11-26", "19 to 25 Nov", 0, 7),
         ("2026-12-03", "26 Nov to 2 Dec", 0, 7), ("2026-12-10", "3 to 9 Dec", 10, 7), ("2026-12-17", "10 to 16 Dec", 20, 7),
         ("2026-12-24", "17 to 23 Dec", 20, 7), ("2026-12-31", "24 to 30 Dec (no 25 Dec)", 20, 6),
         ("2027-01-07", "31 Dec to 6 Jan (no 1 Jan)", 20, 6), ("2027-01-14", "7 to 13 Jan", 20, 7),
         ("2027-01-21", "14 to 20 Jan", 50, 7), ("2027-01-28", "21 to 27 Jan", 75, 7), ("2027-02-04", "28 Jan to 3 Feb", 100, 7),
         ("2027-02-11", "4 to 10 Feb", 150, 7), ("2027-02-18", "11 Feb on", 200, 7)]
CAP_COLS = [f"daily_cap_{d}" for d, *_ in WEEKS[:-1]] + [f"daily_cap_{WEEKS[-1][0]}_on"]
COLS = ["domain", "mailbox_name", "display_name", "email", "workspace", "pool", "created", "warmup_start_day0",
        "service_account_project"] + CAP_COLS + ["tantra_service_account_connected", "tantra_max_per_day_set"]


def roster():
    rows = []
    for w, doms in WORKSPACE_DOMAINS.items():
        for d in doms:
            for u, name in USERS:
                rows.append({"domain": d, "mailbox_name": u, "display_name": name, "email": f"{u}@{d}",
                             "workspace": WORKSPACES[w], "pool": f"P{w}", "created": "FILL_DATE",
                             "warmup_start_day0": "FILL_DATE_100_USD_PAID", "service_account_project": f"cal-outreach-w{w}",
                             **dict(zip(CAP_COLS, [c for _, _, c, _ in WEEKS])),
                             "tantra_service_account_connected": "FILL_YES_NO", "tantra_max_per_day_set": "FILL"})
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
         "Written by `build_infra_files.py`: 12 sending domains and 4 spares. In the iFreeDomains panel: My Domains,",
         "Manage Domain, Manage iFreeDomains DNS. A Name of `@` means leave the Name field blank (the root of the domain).", "",
         "Two values come from Google Admin and replace the `FILL_` text: the verification TXT (when the domain is added,",
         "`ADI_STEPS.md` steps 3 and 4) and the DKIM key (step 6). Exactly one SPF record per domain: never add a second.",
         "DMARC reports go to `dmarc@<the same domain>`, an alias on the Workspace admin (step 5), so no outside domain",
         "has to consent.", ""]
    n = 0
    for w, doms in WORKSPACE_DOMAINS.items():
        for d in doms:
            n += 1
            L += block(n, d, f"Workspace {WORKSPACES[w]}, pool P{w}")
    for d in SPARES:
        n += 1
        L += block(n, d, "spare: add these records only when the spare is brought in")
    L += ["## Check What the World Sees (public DNS, no key)", "", "Replace the domain and run:", "", "```bash",
          "for t in TXT MX; do curl -s -H 'accept: application/dns-json' \"https://cloudflare-dns.com/dns-query?name=northgatesessions.com&type=$t\"; echo; done",
          "curl -s -H 'accept: application/dns-json' 'https://cloudflare-dns.com/dns-query?name=_dmarc.northgatesessions.com&type=TXT'; echo",
          "curl -s -H 'accept: application/dns-json' 'https://cloudflare-dns.com/dns-query?name=google._domainkey.northgatesessions.com&type=TXT'; echo",
          "```", "",
          "Pass: one `v=spf1` record, MX `smtp.google.com`, a `v=DMARC1` record, a DKIM key, nothing listed twice.",
          "After two clean weeks, change DMARC `p=none` to `p=quarantine`.", ""]
    return "\n".join(L)


def shortlist_md():
    L = ["# Domain Shortlist: 12 Sending Domains and 4 Spares", "",
         "Rules: `.com`, no hyphens, never growthclub.org, usetantra.com or a free Gmail address, nothing that reads as",
         "Tantra or GrowthClub, and none of the existing Tantra calendar names (strategywebinars, visionarywebinars,",
         "seminarvision, nextgenwebinars, signonline).", "",
         "12 domains x 6 mailboxes = 72 senders (`CAPACITY_PLAN.md`). 3 domains per Workspace, 18 senders each.", "",
         "**Why plain names.** The senders behind the master list used webinar-themed domains, and 156,018 of those",
         "recipients declined. A plain, company-like name (`northgatesessions.com`) does not repeat that pattern.", "",
         f"All 16 names came from the 90 checked on 2026-11-04 and returned \"not found\" again from the Verisign .com",
         f"registry (RDAP) on {CHECKED}. A name can still be taken before it is registered, or priced as \"Special\" at",
         "iFreeDomains: skip it and take the next spare. Checked for registration only: before registering, search each",
         "name to make sure no live company trades under it.", "",
         "| # | Domain | Workspace | Pool | Mailboxes |", "| --- | --- | --- | --- | --- |"]
    n = 0
    for w, doms in WORKSPACE_DOMAINS.items():
        for d in doms:
            n += 1
            tag = " (primary)" if d == PRIMARY[w] else ""
            L.append(f"| {n} | {d} | {WORKSPACES[w]}{tag} | P{w} | 6 |")
    L += ["", "## Spares (register now, leave parked so they age)", "",
          "A spare replaces a domain that is taken at registration, or one that runs hot later (Google warnings, high",
          "declines): move that domain's 6 mailboxes to the spare in the same Workspace.", "",
          "| # | Domain |", "| --- | --- |"]
    for d in SPARES:
        n += 1
        L.append(f"| {n} | {d} |")
    L += ["", "W1's primary domain is strategywebinars.com (registered 2026-09-27 at Cloudflare, nameservers on Cloudflare);",
          "it is not a sending domain.", "",
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
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ImportError:
        print(f"{len(rows)} senders; openpyxl missing, no xlsx"); return
    wb = Workbook(); ws = wb.active; ws.title = "Senders"
    ws.append(COLS)
    for r in rows:
        ws.append([r[c] for c in COLS])
    for c in ws[1]:
        c.font = Font(bold=True)
    ws.freeze_panes = "D2"
    plan = wb.create_sheet("Caps by week")
    plan.append(["Webinar (Thursday)", "Send window", "Invites a sender a day", "Senders", "Send days", "Week capacity"])
    for k, (d, win, cap, days) in enumerate(WEEKS):
        plan.append([d, win, cap, len(rows), days, f"=C{k + 2}*D{k + 2}*E{k + 2}"])
    for c in plan[1]:
        c.font = Font(bold=True)
    wb.save(HERE / "sender-roster.xlsx")
    print(f"{len(rows)} senders, {sum(map(len, WORKSPACE_DOMAINS.values()))} domains + {len(SPARES)} spares, xlsx")


if __name__ == "__main__":
    main()
