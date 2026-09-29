"""Headless smoke test for the pirate squirrel game.

Drives v2 through the full loop using the page's window.__psq test hook:
spawn -> hollow search -> gate -> board -> sail -> ashore -> crabs -> branch
puzzle leaps -> rotten branch -> nest -> chest -> win. Prints each step and
any page errors, and saves screenshots to tools/out/.

Usage:
  pip install playwright && playwright install chromium
  python3 tools/smoke_test.py                  # v2
  python3 tools/smoke_test.py v1/index.html --screens-only
"""
import asyncio, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "out"
THREE = ROOT / "vendor" / "three.r128.min.js"


async def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    page_path = ROOT / (args[0] if args else "v2/index.html")
    screens_only = "--screens-only" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        page = await browser.new_page(viewport={"width": 1280, "height": 760})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        # serve three.js from vendor/ so the test works offline
        async def serve_three(route):
            await route.fulfill(path=str(THREE), content_type="application/javascript")
        await page.route("**/three.min.js", serve_three)
        await page.goto(page_path.as_uri())
        await page.wait_for_timeout(1500)
        await page.screenshot(path=str(OUT / "01_title.png"))
        await page.evaluate("document.getElementById('startBtn').click()")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(OUT / "02_start.png"))
        if screens_only:
            print("screens saved to", OUT, "| page errors:", errors or "none")
            await browser.close(); return

        E = page.evaluate
        info = lambda: E("window.__psq.info()")
        step = lambda n: E(f"window.__psq.stepNR({n})")
        async def key(code, down): await E(f"window.__psq.key('{code}',{str(down).lower()})")
        async def press(code, n=3): await key(code, True); await step(n); await key(code, False)
        def show(tag, i):
            print(f"{tag:<28}", json.dumps({k: i[k] for k in ["state", "mode", "platform", "gateOpen", "visited", "guardsLeft", "energy", "prompt"]}))

        # 1. first hollow: walk to the trunk and search
        await key("KeyW", True); await step(30); await key("KeyW", False)
        await press("KeyE"); await step(60)
        i = await info(); show("first hollow", i)
        assert i["gear"].get("patch"), "first hollow should give the eye patch"

        # 2. with the full kit and map, the gate opens and the boat can be boarded
        await E("window.__psq.giveAll()")
        g = await E("window.__psq.gate()")
        x, z = g["pdx"] * (g["shoreD"] - 0.6), g["pdz"] * (g["shoreD"] - 0.6)
        await E(f"window.__psq.tp({x},1.5,{z},'air')"); await E(f"window.__psq.face(Math.atan2({g['pdx']},{g['pdz']}))"); await step(20)
        await key("KeyW", True); await step(90); await key("KeyW", False); await step(10)
        i = await info(); show("walked the dock", i)
        await press("KeyE"); await step(10)
        i = await info(); show("board", i)

        # 3. sail a little, then hop to Treasure Island's beach
        await key("KeyW", True); await step(240); await key("KeyW", False)
        i = await info(); show("sailing", i)
        await E("window.__psq.tp(6,0.2,176,'boat')"); await E("window.__psq.face(0)")
        await key("KeyW", True); await step(150); await key("KeyW", False); await step(20)
        await press("KeyE"); await step(30)
        i = await info(); show("ashore", i)
        await page.screenshot(path=str(OUT / "03_beach.png"))

        # 4. crabs: teleport next to each and tail-swipe
        for _ in range(12):
            alive = [c for c in await E("window.__psq.crabs()") if not c["dead"]]
            if not alive: break
            c = alive[0]
            await E(f"window.__psq.tp({c['x']+0.9},2,{c['z']},'air')"); await step(20)
            await press("KeyF"); await step(40)
        i = await info(); show("crabs beaten", i)

        # 5. puzzle: leap from each correct branch to the next tree
        chain = ["S", "A", "B", "Cc", "T"]
        for k in range(4):
            t = await E(f"window.__psq.tree('{chain[k]}')")
            br = [b for b in t["branches"] if b["chain"] == k][0]
            a = br["hl"] - 0.4
            await E(f"window.__psq.tp({br['cx']+br['ux']*a},{br['top']+0.3},{br['cz']+br['uz']*a},'air')"); await step(10)
            await E(f"window.__psq.face(Math.atan2({br['ux']},{br['uz']}))")
            await key("KeyW", True); await key("Space", True); await step(4); await key("KeyW", False); await step(70); await key("Space", False); await step(20)
            show(f"leap {chain[k]} -> {chain[k+1]}", await info())

        # 6. a rotten branch should snap
        s = await E("window.__psq.tree('S')")
        rb = [b for b in s["branches"] if b["rotten"]][0]
        await E(f"window.__psq.tp({rb['cx']},{rb['top']+0.3},{rb['cz']},'air')"); await step(40)
        show("stood on rotten branch", await info())

        # 7. treasure tree: climb to the nest and open the chest
        t = await E("window.__psq.tree('T')"); lb = t["branches"][0]
        await E(f"window.__psq.tp({lb['cx']},{lb['top']+0.3},{lb['cz']},'air')"); await E(f"window.__psq.face(Math.atan2({-lb['ux']},{-lb['uz']}))"); await step(12)
        await key("KeyW", True)
        for _ in range(40):
            await step(10)
            if (await info())["platform"] == "nest": break
        await key("KeyW", False)
        await press("KeyE"); await step(170)
        i = await info(); show("chest", i)
        await E("window.__psq.step(1)")
        await page.screenshot(path=str(OUT / "04_win.png"))

        print("\nresult:", "WIN" if i["state"] == "win" else "did not reach win", "| page errors:", errors or "none")
        await browser.close()

asyncio.run(main())
