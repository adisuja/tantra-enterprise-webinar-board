#!/usr/bin/env python3
"""Build the sales collateral: fill src/*.html from funnel-config.json, then render PDFs.

usage: python3 deliverables/25-sales-collateral/build.py

Tokens in src files: {{path.to.value}} with optional filters {{offer.price_usd|money}}, {{offer.includes|li}}.
A value that starts with FILL_ prints as a visible merge field, so an unknown never looks finished.
Needs Playwright with Chromium (pip install playwright; playwright install chromium).
"""
import html, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
CONFIG = HERE.parent / "_shared" / "funnel-config.json"
DOCS = {
    "case-study-deck": ["deck"],
    "enterprise-one-pager": ["a4", "letter"],
    "scope-and-pricing": ["a4", "letter"],
    "objections-faq": ["a4", "letter"],
}
MUST_FIT_ONE_PAGE = {"enterprise-one-pager", "scope-and-pricing"}
VIEW = {"a4": {"width": 794, "height": 1122}, "letter": {"width": 816, "height": 1056}}
PAGE = {"a4": "@page{size:A4}", "letter": "@page{size:Letter}", "deck": "@page{size:1280px 720px;margin:0}"}


def lookup(cfg, path):
    v = cfg
    for part in path.split("."):
        v = v[int(part)] if isinstance(v, list) else v[part]
    return v


def fill(cfg, text):
    def sub(m):
        path, _, flt = m.group(1).partition("|")
        v = lookup(cfg, path.strip())
        if isinstance(v, str) and v.startswith("FILL_"):
            return f'<span class="fill">{{{{{path.strip()}}}}}</span>'
        if flt == "money":
            return f"${int(v):,}"
        if flt == "li":
            return "".join(f"<li>{html.escape(x)}</li>" for x in v)
        return html.escape(str(v))
    out = re.sub(r"\{\{\s*([\w.|]+)\s*\}\}", sub, text)
    left = re.findall(r"\{\{[^}]*\}\}", re.sub(r'<span class="fill">\{\{[^}]*\}\}</span>', "", out))
    if left:
        sys.exit(f"unfilled tokens: {left}")
    return out


def main():
    from playwright.sync_api import sync_playwright
    import fitz
    cfg = json.loads(CONFIG.read_text())
    report = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, papers in DOCS.items():
            src = (HERE / "src" / f"{name}.html").read_text()
            for i, paper in enumerate(papers):
                page_html = fill(cfg, src).replace("/*PAGE*/", PAGE[paper])
                out_html = HERE / (f"{name}.html" if i == 0 else f".{name}-{paper}.tmp.html")
                out_html.write_text(page_html)
                pdf = HERE / (f"{name}.pdf" if paper == "deck" else f"{name}-{paper}.pdf")
                pg = browser.new_page()
                pg.goto(out_html.as_uri(), wait_until="networkidle")
                pg.emulate_media(media="print")
                if name in MUST_FIT_ONE_PAGE and paper in VIEW:
                    # .page clips overflow, so a page count of 1 can hide cut-off content: measure it
                    pg.set_viewport_size(VIEW[paper])
                    over = pg.evaluate("[...document.querySelectorAll('.body')].some(b => b.scrollHeight > b.clientHeight + 1)")
                    if over:
                        print(f"FAIL {name} ({paper}): content overflows the page and is clipped")
                pg.pdf(path=str(pdf), print_background=True, prefer_css_page_size=True)
                pg.close()
                if i > 0:
                    out_html.unlink()
                n = len(fitz.open(pdf))
                report.append((pdf.name, n))
                if name in MUST_FIT_ONE_PAGE and n != 1:
                    print(f"FAIL {pdf.name}: {n} pages, must be 1")
        browser.close()
    for f, n in report:
        print(f"{f}: {n} page(s)")


if __name__ == "__main__":
    main()
