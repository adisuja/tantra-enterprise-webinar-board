#!/usr/bin/env python3
"""Create the Google Sheet "Tantra Enterprise CRM" in Adi's own Drive from the xlsx template, unshared,
then read it back through the Sheets API and check tabs, headers, dropdowns, formatting and Summary formulas.

usage: python3 deliverables/23-crm/create_gsheet.py [--update SHEET_ID | --verify-only SHEET_ID]
Token: /Users/adithyamurali/CEO/.secrets/token.json (needs drive.file and spreadsheets). No token value is printed or saved.
The refreshed access token stays in memory; token.json is not rewritten.
"""
import json
import pathlib
import sys

from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2.credentials import Credentials

HERE = pathlib.Path(__file__).resolve().parent
TOKEN = "/Users/adithyamurali/CEO/.secrets/token.json"
XLSX = HERE / "Tantra_Enterprise_CRM_template.xlsx"
NAME = "Tantra Enterprise CRM"
TABS = ["Summary", "Contacts", "Webinar", "Pipeline", "Events", "Sequences", "Lists"]


def session():
    c = Credentials.from_authorized_user_file(TOKEN)
    need = {"https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/spreadsheets"}
    if not need <= set(c.scopes or []):
        sys.exit("token lacks drive.file or spreadsheets scope: import the xlsx by hand (README, Adi steps)")
    c.refresh(Request())
    return AuthorizedSession(c)


def create(s):
    meta = {"name": NAME, "mimeType": "application/vnd.google-apps.spreadsheet"}
    boundary = "tantra-crm-boundary"
    body = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{json.dumps(meta)}\r\n"
            f"--{boundary}\r\nContent-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n").encode()
    body += XLSX.read_bytes() + f"\r\n--{boundary}--".encode()
    r = s.post("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,owners(emailAddress),shared",
               data=body, headers={"Content-Type": f"multipart/related; boundary={boundary}"})
    r.raise_for_status()
    sid = r.json()["id"]
    # A Workspace default may add "anyone at the domain with the link". The CRM stays owner only.
    perms = s.get(f"https://www.googleapis.com/drive/v3/files/{sid}/permissions?fields=permissions(id,type)").json()
    for p in perms.get("permissions", []):
        if p["type"] in ("domain", "anyone"):
            s.delete(f"https://www.googleapis.com/drive/v3/files/{sid}/permissions/{p['id']}").raise_for_status()
    return sid


def update(s, sid):
    """Replace the sheet's content with the current template, keeping the same file id and sharing."""
    r = s.patch(f"https://www.googleapis.com/upload/drive/v3/files/{sid}?uploadType=media",
                data=XLSX.read_bytes(),
                headers={"Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"})
    r.raise_for_status()


def verify(s, sid):
    out = []
    f = s.get(f"https://www.googleapis.com/drive/v3/files/{sid}?fields=name,shared,mimeType").json()
    perms = s.get(f"https://www.googleapis.com/drive/v3/files/{sid}/permissions?fields=permissions(role,type)").json()
    out.append(("name", f.get("name") == NAME, f.get("name")))
    out.append(("unshared (owner only)", not f.get("shared") and [p["role"] for p in perms.get("permissions", [])] == ["owner"],
                f"shared={f.get('shared')} roles={[p['role'] for p in perms.get('permissions', [])]}"))
    meta = s.get(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}?fields=sheets(properties(title),conditionalFormats)").json()
    titles = [x["properties"]["title"] for x in meta["sheets"]]
    out.append(("tabs", titles == TABS, titles))
    cf = {x["properties"]["title"]: len(x.get("conditionalFormats", [])) for x in meta["sheets"]}
    out.append(("conditional formats", cf.get("Pipeline", 0) >= 7 and cf.get("Sequences", 0) >= 4, cf))
    heads = s.get(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}/values:batchGet",
                  params={"ranges": [f"{t}!1:1" for t in TABS[1:6]]}).json()
    hv = {r["range"].split("!")[0].strip("'"): r.get("values", [[]])[0] for r in heads["valueRanges"]}
    sys.path.insert(0, str(HERE))
    from build import TABS as WANT
    out.append(("headers match the template", all(hv.get(t) == WANT[t] for t in WANT), {k: len(v) for k, v in hv.items()}))
    dv = s.get(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}",
               params={"ranges": "Pipeline!E2", "fields": "sheets(data(rowData(values(dataValidation))))"}).json()
    rule = dv["sheets"][0]["data"][0]["rowData"][0]["values"][0].get("dataValidation", {})
    out.append(("stage dropdown", rule.get("condition", {}).get("type") == "ONE_OF_RANGE", rule.get("condition", {})))
    summ = s.get(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/Summary!A1:F60").json().get("values", [])
    flat = [c for row in summ for c in row]
    out.append(("Summary formulas compute", not any(str(c).startswith("#") for c in flat) and any(r[:1] == ["9 Nurture"] for r in summ),
                [c for c in flat if str(c).startswith("#")][:5] or "no errors"))
    lists = s.get(f"https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/Lists!A1:A11").json().get("values", [])
    out.append(("stage list", [r[0] for r in lists[1:]][:1] == ["1 New Lead"] and len(lists) == 11, len(lists)))
    ok = True
    for name, good, detail in out:
        ok &= bool(good)
        print(("PASS " if good else "FAIL ") + name + ": " + str(detail))
    return ok


if __name__ == "__main__":
    s = session()
    if len(sys.argv) == 3 and sys.argv[1] == "--verify-only":
        sid = sys.argv[2]
    elif len(sys.argv) == 3 and sys.argv[1] == "--update":
        sid = sys.argv[2]
        update(s, sid)
        print("updated sheet id:", sid)
    else:
        sid = create(s)
        print("created sheet id:", sid)
    sys.exit(0 if verify(s, sid) else 1)
