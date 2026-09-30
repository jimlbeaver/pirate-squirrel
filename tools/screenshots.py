"""In-game screenshots of the art for review, via the page's window.__psq test hook.

  python3 tools/screenshots.py            # -> art/previews/ingame/*.png

Home Isle in the plain and full-gear looks, the squirrel's clip states, sailing past the three sea-nut
types, the crab guards and Captain Pinch, and the Chestnut reveal through to the win card.
"""
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright
from smoke_test import ROOT, VENDOR, serve

OUT = ROOT / "art" / "previews" / "ingame"


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    httpd = serve()
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        for pattern, path in VENDOR.items():
            await page.route(pattern, lambda route, _req=None, path=path: route.fulfill(path=str(path), content_type="application/javascript"))
        await page.goto(f"http://127.0.0.1:{httpd.server_address[1]}/v2/index.html")
        await page.wait_for_timeout(3000)
        E = page.evaluate
        print("assets:", await E("window.__psq.assets()"))
        await E("document.getElementById('startBtn').click()")
        await page.wait_for_timeout(800)

        async def step(n): await E(f"window.__psq.stepNR({n})")
        async def key(code, down): await E(f"window.__psq.key('{code}',{str(down).lower()})")
        async def shot(name):
            await E("window.__psq.step(1)")
            await page.screenshot(path=str(OUT / f"{name}.png"))
            print("saved", OUT / f"{name}.png")

        # Home Isle, on open sand facing the dock gate: plain, then the full kit (follow cam and a front view)
        g = await E("window.__psq.gate()")
        home = f"{g['pdx'] * (g['shoreD'] - 5)},3,{g['pdz'] * (g['shoreD'] - 5)}"
        face = f"Math.atan2({g['pdx']},{g['pdz']})"
        async def front(name):
            await E(f"window.__psq.view({face},0.15,2.6)"); await step(50); await shot(name)
            await key("KeyC", True); await key("KeyC", False); await E(f"window.__psq.face({face})"); await step(30)
        await E(f"window.__psq.tp({home},'air')"); await E(f"window.__psq.face({face})"); await step(90); await shot("01_home_plain")
        await front("02_home_plain_front")
        await E("window.__psq.giveAll()"); await step(60); await shot("03_home_gear")
        await front("04_home_gear_front")
        await key("KeyW", True); await step(20); await shot("04b_home_gear_run"); await key("KeyW", False); await step(30)

        # clip states: climb, glide, swipe
        t = await E("window.__psq.tree('h2')")
        x, z = t["x"] + 1.6, t["z"]
        await E(f"window.__psq.tp({x},{t['base']+1.5},{z},'air')"); await E(f"window.__psq.face(Math.atan2({t['x']-x},{t['z']-z}))"); await step(40)
        await key("KeyW", True); await step(50); await shot("05_climb"); await key("KeyW", False)
        await E("window.__psq.tp(0,9,-4,'air')"); await E("window.__psq.face(0.8)"); await step(20)
        await key("Space", True); await step(20); await shot("06_glide"); await key("Space", False); await step(80)
        await key("KeyF", True); await step(2); await key("KeyF", False); await step(6); await shot("07_swipe"); await step(40)

        # sailing: from a few boat-lengths behind each of the safest peanuts, facing up the lane
        nuts = (await E("window.__psq.nuts()"))["list"]
        for i, n in enumerate(sorted((n for n in nuts if n["type"] == "peanut"), key=lambda n: -n["d"])[:3]):
            await E(f"window.__psq.tp({n['x']},0.2,{n['z'] - 5},'boat',0)"); await step(60); await shot(f"08_sailing_nuts_{i}")

        # Treasure Island: the crab guards from the beach, then Captain Pinch up close
        c = await E("window.__psq.crabs()")
        cx = sum(k["x"] for k in c) / len(c); cz = sum(k["z"] for k in c) / len(c)
        await E(f"window.__psq.tp({cx},3,{cz - 3.2},'air')"); await E("window.__psq.face(0)"); await step(30); await shot("09_crabs")
        cap = c[3]
        await E(f"window.__psq.tp({cap['x'] + 1.2},3,{cap['z'] - 4.5},'air')"); await E("window.__psq.face(-0.25)"); await step(4); await shot("10_captain_pinch")

        # the Chestnut reveal
        t = await E("window.__psq.tree('T')"); lb = t["branches"][0]
        await E(f"window.__psq.tp({lb['cx']},{lb['top']+0.3},{lb['cz']},'air')"); await E(f"window.__psq.face(Math.atan2({-lb['ux']},{-lb['uz']}))"); await step(12)
        await key("KeyW", True)
        for _ in range(40):
            await step(10)
            if (await E("window.__psq.info()"))["platform"] == "nest": break
        await key("KeyW", False); await step(20)
        await key("KeyE", True); await step(1); await key("KeyE", False)
        for frames, name in ((50, "11_reveal_husk"), (85, "12_reveal_peak"), (140, "13_reveal_deez"), (180, "14_win")):
            await step(frames); await shot(name)
        print("page errors:", errors or "none")
        await browser.close()
    httpd.shutdown()

asyncio.run(main())
