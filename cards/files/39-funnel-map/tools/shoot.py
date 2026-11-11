"""Screenshot every funnel page for the map's cover cards. Usage: python3 -I tools/shoot.py <out_dir> <bonus_password>"""
import sys, asyncio
from playwright.async_api import async_playwright
OUT, PW = sys.argv[1], sys.argv[2]
B = "https://webinar.sellwithtantra.com"
PAGES = {
  "registration": B + "/?v=map",
  "survey": B + "/thank-you/?v=map",
  "upsell": B + "/funnelos/?v=map",
  "confirmation": B + "/confirmation/?v=map",
  "calculator": B + "/calculator/?v=map",
  "replay": B + "/recording/?v=map",
  "checkout": "https://checkout.dodopayments.com/buy/pdt_0NrT0uZn0wxHm3nE0KBY5?quantity=1",
}
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1280, "height": 1600}, device_scale_factor=1)
        pg = await ctx.new_page()
        for k, u in PAGES.items():
            try:
                await pg.goto(u, wait_until="networkidle", timeout=45000)
                await pg.wait_for_timeout(1800)
                await pg.screenshot(path=f"{OUT}/{k}.png")
                print("ok", k)
            except Exception as e:
                print("fail", k, e)
        await pg.goto("https://bonuses.sellwithtantra.com/", wait_until="networkidle")
        await pg.screenshot(path=f"{OUT}/bonus-gate.png"); print("ok bonus-gate")
        await pg.fill("#pw", PW); await pg.keyboard.press("Enter"); await pg.wait_for_load_state("networkidle"); await pg.wait_for_timeout(1200)
        await pg.screenshot(path=f"{OUT}/bonus-hub.png"); print("ok bonus-hub", pg.url)
        for k, path in (("playbook", "/playbook/?funnel=webinar"), ("library", "/library/#t=landing_page")):
            await pg.goto("https://bonuses.sellwithtantra.com" + path, wait_until="networkidle"); await pg.wait_for_timeout(1500)
            await pg.screenshot(path=f"{OUT}/{k}.png"); print("ok", k)
        await b.close()
asyncio.run(main())
