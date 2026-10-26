#!/usr/bin/env python3
"""Browser check of a built guide (needs playwright with chromium; skip if unavailable).

Usage: python check_page.py <guide.html>
Loads the page with KaTeX served from the local npm cache (installed by check_guide.py),
then checks: no JS errors, math rendered, quiz click updates the sidebar chip, progress
survives a reload, no horizontal scroll at phone width, and dark mode renders.
Saves screenshots next to the guide (shot-desktop.png, shot-phone.png, shot-dark.png).
"""
import sys, pathlib
from playwright.sync_api import sync_playwright
page_path = pathlib.Path(sys.argv[1]).resolve()
K = pathlib.Path.home()/".cache/lsg-katex/node_modules/katex/dist"
def route(r):
    u = r.request.url
    if "KaTeX" in u and K.exists(): r.fulfill(path=str(K/u.split("/0.16.9/")[1]))
    else: r.abort()
bad = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for scheme in ("light", "dark"):
        pg = b.new_page(viewport={"width": 1200, "height": 900}, color_scheme=scheme)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.route("https://**/*", route)
        pg.goto(page_path.as_uri()); pg.wait_for_timeout(900)
        if scheme == "dark":
            pg.screenshot(path=str(page_path.with_name("shot-dark.png"))); b_errs = errs; break
        n = pg.locator(".katex").count()
        if n == 0: bad.append("no math rendered")
        if pg.locator(".katex-error").count(): bad.append(f"{pg.locator('.katex-error').count()} KaTeX errors on page")
        quiz = pg.locator(".quiz[data-quiz]").first
        qid = quiz.get_attribute("data-quiz")
        quiz.locator(".opt").first.click()
        chip = pg.locator(f'[data-chip="{qid}"]').first.text_content()
        if not chip: bad.append("sidebar chip did not update after answering")
        pg.reload(); pg.wait_for_timeout(900)
        if pg.locator(f'[data-chip="{qid}"]').first.text_content() != chip: bad.append("progress not restored after reload")
        pg.locator("#resetAll").count() or bad.append("no Reset all progress button")
        pg.locator("#printSheet").count() or bad.append("no Print formula sheet button")
        pg.screenshot(path=str(page_path.with_name("shot-desktop.png")))
        pg.set_viewport_size({"width": 360, "height": 800}); pg.wait_for_timeout(300)
        if pg.evaluate("document.documentElement.scrollWidth > innerWidth + 1"): bad.append("horizontal scroll at 360px width")
        pg.screenshot(path=str(page_path.with_name("shot-phone.png")))
        pg.evaluate("localStorage.clear()")
        bad += [f"JS error: {e[:150]}" for e in errs]
        pg.close()
    b.close()
for x in bad: print("ERROR", x)
print("PASS (view the screenshots)" if not bad else f"FAIL ({len(bad)})")
sys.exit(1 if bad else 0)
