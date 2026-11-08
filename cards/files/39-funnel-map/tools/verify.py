"""Log in to the live funnel map and screenshot each view. Usage: python3 tools/verify.py <out_dir>"""
import os, sys, asyncio
from pathlib import Path
from playwright.async_api import async_playwright
OUT = sys.argv[1]; U = "https://tantra-funnel-map.growthcluborg.workers.dev"
pw = dict(l.split("=", 1) for l in (Path.home() / ".config/tantra/keys/funnel-map.env").read_text().split())["MAP_PASSWORD"]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1500, "height": 950})
        pg = await ctx.new_page(); errs = []
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text)); pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(U + "/?v=1"); await pg.fill("#pw", pw); await pg.keyboard.press("Enter")
        await pg.wait_for_load_state("networkidle"); await pg.wait_for_timeout(1500)
        print("chips", await pg.locator(".chip").count(), "rows", await pg.locator(".row").count(), "paths", await pg.locator("svg.wires path").count())
        await pg.screenshot(path=f"{OUT}/1-top.png")
        await pg.screenshot(path=f"{OUT}/2-full.png", full_page=True)
        await pg.click('.chip[data-m="E1"]'); await pg.wait_for_timeout(600); await pg.screenshot(path=f"{OUT}/3-panel-E1.png")
        await pg.click('.chip[data-m="W-1D"]'); await pg.wait_for_timeout(600)
        await pg.locator('.chip[data-m="W-1D"]').scroll_into_view_if_needed(); await pg.wait_for_timeout(400); await pg.screenshot(path=f"{OUT}/4-panel-W1D.png")
        await pg.click('.cover[data-s="confirm"]'); await pg.wait_for_timeout(600); await pg.screenshot(path=f"{OUT}/5-panel-stage.png")
        await pg.click('#close'); await pg.click('[data-v="timeline"]'); await pg.wait_for_timeout(400); await pg.screenshot(path=f"{OUT}/6-timeline.png", full_page=True)
        await pg.click('[data-v="bonuses"]'); await pg.wait_for_timeout(400); await pg.screenshot(path=f"{OUT}/7-bonuses.png", full_page=True)
        await pg.goto(U + "/#m=E-P1"); await pg.wait_for_timeout(1500); await pg.screenshot(path=f"{OUT}/8-deeplink.png")
        m = await b.new_context(viewport={"width": 390, "height": 844}, storage_state=await ctx.storage_state()); mp = await m.new_page()
        await mp.goto(U + "/"); await mp.wait_for_timeout(1500); await mp.screenshot(path=f"{OUT}/9-mobile.png")
        print("errors", errs)
        await b.close()
asyncio.run(main())
