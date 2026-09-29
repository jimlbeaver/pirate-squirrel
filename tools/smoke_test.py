"""Headless smoke test for the pirate squirrel game.

Drives v2 through the full loop using the page's window.__psq test hook:
spawn -> hollow search -> gate -> board -> sail -> ashore -> crabs -> branch
puzzle leaps -> rotten branch -> nest -> chest -> win. Prints each step and
any page errors, and saves screenshots to tools/out/.

The page is served from a local HTTP server (GLB assets can't load over file://).
Any asset whose GLB exists in art/exports/ but fell back to its stand-in is reported.

Usage:
  pip install playwright && playwright install chromium
  python3 tools/smoke_test.py                  # v2
  python3 tools/smoke_test.py v1/index.html --screens-only
"""
import asyncio, functools, json, sys, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "out"
VENDOR = {"**/three.min.js": ROOT / "vendor" / "three.r128.min.js",
          "**/GLTFLoader.js": ROOT / "vendor" / "GLTFLoader.r128.js"}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


def serve():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(ROOT)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    page_rel = (args[0] if args else "v2/index.html").replace("\\", "/")
    screens_only = "--screens-only" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    httpd = serve()
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        page = await browser.new_page(viewport={"width": 1280, "height": 760})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        # serve CDN scripts from vendor/ so the test works offline
        def from_vendor(path):
            return lambda route: route.fulfill(path=str(path), content_type="application/javascript")
        for pattern, path in VENDOR.items():
            await page.route(pattern, from_vendor(path))
        await page.goto(f"http://127.0.0.1:{httpd.server_address[1]}/{page_rel}")
        await page.wait_for_timeout(1500)
        assets = {}
        if await page.evaluate("!!(window.__psq && window.__psq.assets)"):
            for _ in range(50):
                assets = await page.evaluate("window.__psq.assets()")
                if "loading" not in assets.values(): break
                await page.wait_for_timeout(200)
        fell_back = [n for n, s in assets.items() if s != "glb" and (ROOT / "art" / "exports" / f"{n}.glb").exists()]
        print("assets:", assets or "none", "| fell back to stand-in:", fell_back or "none")
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

        # 0. Home Isle climbing: walk into each tree from 8 directions. C = climbed, . = refused.
        #    Slick (mossy) trees refuse from the ground but can be climbed from their own branch.
        probe = await E("""(()=>{ const Q=window.__psq, out={};
          for(const id of ['h0','h1','h2','h3','h4','h5']){ const t=Q.tree(id); let row='';
            for(let k=0;k<8;k++){ const a=k/8*Math.PI*2, x=t.x+Math.cos(a)*1.6, z=t.z+Math.sin(a)*1.6;
              Q.tp(x,t.base+1.5,z,'air'); Q.face(Math.atan2(t.x-x,t.z-z)); Q.stepNR(40);
              Q.key('KeyW',true); Q.stepNR(40); Q.key('KeyW',false); row+=Q.info().mode==='climb'?'C':'.'; }
            let fromBranch='-';
            if(t.slick){ const b=t.branches.find(b=>b.to); const al=b.start+0.4;
              Q.tp(t.x+b.ux*al,b.top+0.3,t.z+b.uz*al,'air'); Q.stepNR(20); Q.face(Math.atan2(-b.ux,-b.uz));
              Q.key('KeyW',true); Q.stepNR(30); Q.key('KeyW',false); fromBranch=Q.info().mode==='climb'?'C':'.'; }
            out[id]={slick:!!t.slick,ground:row,fromBranch}; }
          Q.reset(); return out; })()""")
        for tid, r in probe.items():
            print(f"climb probe {tid:<3} {'slick' if r['slick'] else 'bare '} ground {r['ground']} from branch {r['fromBranch']}")
            if r["slick"]: assert r["ground"] == "." * 8 and r["fromBranch"] == "C", f"{tid}: slick tree should refuse from the ground and allow from its branch"
            else: assert r["ground"] == "C" * 8, f"{tid}: climbable tree refused a climb"

        # 1. first hollow: walk to the trunk and search
        await key("KeyW", True); await step(30); await key("KeyW", False)
        await press("KeyE"); await step(60)
        i = await info(); show("first hollow", i)
        assert i["gear"].get("patch"), "first hollow should give the eye patch"

        # 2. with the full kit and map, the gate opens and the boat can be boarded
        await E("window.__psq.giveAll()")
        assert await E("window.__psq.map()") == "map", "map should open once the squirrel has it"
        await page.screenshot(path=str(OUT / "02_map.png"))
        await E("window.__psq.map()")
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
        await E("window.__psq.step(1)")
        await page.screenshot(path=str(OUT / "03_sailing.png"))
        await E("window.__psq.tp(6,0.2,176,'boat')"); await E("window.__psq.face(0)")
        await key("KeyW", True); await step(150); await key("KeyW", False); await step(20)
        await press("KeyE"); await step(30)
        i = await info(); show("ashore", i)
        await page.screenshot(path=str(OUT / "04_beach.png"))

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
        seq = await E("window.__psq.seq()")
        for k in range(4):
            t = await E(f"window.__psq.tree('{chain[k]}')")
            launches = [b for b in t["branches"] if b["sym"] and b["to"] and b["chain"] == k or b["rotten"]]
            true = [b for b in launches if not b["rotten"]]
            assert 3 <= len(launches) <= 4 and len(true) == 1 and true[0]["sym"] == seq[k], f"{chain[k]}: want 3-4 signed launches, one true"
            assert any(b["sym"] in seq and b["sym"] != seq[k] for b in launches if b["rotten"]), f"{chain[k]}: no right-sign-wrong-tree decoy"
        for tid in ("D", "E"):
            br = (await E(f"window.__psq.tree('{tid}')"))["branches"]
            assert len(br) >= 2 and all(b["rotten"] and b["sym"] for b in br), f"{tid}: want signed rotten branches"
        assert not (await E("window.__psq.komodo()"))["awake"], "the dragon should doze until the squirrel is up in the grove"
        t = await E("window.__psq.tree('T')")
        await E(f"window.__psq.tp({t['x']},{t['base']+10.8},{t['z']},'air')"); await E("window.__psq.face(3.6)"); await step(40)
        await page.screenshot(path=str(OUT / "04b_grove.png"))
        for k in range(4):
            t = await E(f"window.__psq.tree('{chain[k]}')")
            br = [b for b in t["branches"] if b["chain"] == k][0]
            a = br["hl"] - 0.4
            await E(f"window.__psq.tp({br['cx']+br['ux']*a},{br['top']+0.3},{br['cz']+br['uz']*a},'air')"); await step(10)
            await E(f"window.__psq.face(Math.atan2({br['ux']},{br['uz']}))")
            await key("KeyW", True); await key("Space", True); await step(4); await key("KeyW", False); await step(70); await key("Space", False); await step(20)
            i = await info(); show(f"leap {chain[k]} -> {chain[k+1]}", i)
            assert (i["platform"] or "").startswith(chain[k+1] + ">"), f"leap from {chain[k]} should land on {chain[k+1]}"

        # 6. a rotten branch should snap
        s = await E("window.__psq.tree('S')")
        rb = [b for b in s["branches"] if b["rotten"]][0]
        await E(f"window.__psq.tp({rb['cx']},{rb['top']+0.3},{rb['cz']},'air')"); await step(40)
        show("stood on rotten branch", await info())

        # 6b. the fall wakes the Komodo dragon's chase; a swipe stuns it, a branch ends it
        k = await E("window.__psq.komodo()"); print(f"{'komodo after the fall':<28} {k}")
        assert k["awake"] and k["chasing"], "a fall to the grove floor should start the chase"
        i = await info()
        await E("window.__psq.face(0)"); await E(f"window.__psq.komodo({i['x']+0.3},{i['z']+2.8},1.5708)"); await step(2)
        await page.screenshot(path=str(OUT / "04c_komodo.png"))
        await E(f"window.__psq.komodo({i['x']},{i['z']+1.4},3.1416)"); await step(2)
        await press("KeyF"); await step(3)
        k = await E("window.__psq.komodo()"); print(f"{'komodo swiped':<28} {k}")
        assert k["stun"] > 0, "a tail-swipe should stun the dragon"
        s = await E("window.__psq.tree('S')"); br = [b for b in s["branches"] if b["chain"] == 0][0]
        await E(f"window.__psq.tp({br['cx']},{br['top']+0.3},{br['cz']},'air')"); await step(20)
        k = await E("window.__psq.komodo()"); print(f"{'back on a branch':<28} {k}")
        assert not k["chasing"], "the dragon should give up once the squirrel is off the ground"

        # 7. treasure tree: climb to the nest and open the chest
        t = await E("window.__psq.tree('T')"); lb = t["branches"][0]
        await E(f"window.__psq.tp({lb['cx']},{lb['top']+0.3},{lb['cz']},'air')"); await E(f"window.__psq.face(Math.atan2({-lb['ux']},{-lb['uz']}))"); await step(12)
        await key("KeyW", True)
        for _ in range(40):
            await step(10)
            if (await info())["platform"] == "nest": break
        await key("KeyW", False)
        await press("KeyE"); await step(130)
        assert await E("!document.getElementById('gag').hidden && document.getElementById('gag2').hidden"), "the 'all D's' line should show first"
        await step(120)
        assert await E("!document.getElementById('gag2').hidden"), "DEEZ NUTS should follow two seconds later"
        await page.screenshot(path=str(OUT / "05_deez.png"))
        await step(160)
        i = await info(); show("chest", i)
        assert await E("document.getElementById('gag').hidden"), "the pop-up should clear for the tally"
        await E("window.__psq.step(1)")
        await page.screenshot(path=str(OUT / "05_win.png"))

        print("\nresult:", "WIN" if i["state"] == "win" else "did not reach win", "| page errors:", errors or "none")
        if fell_back: print("WARNING: these GLBs exist but did not load:", fell_back)
        await browser.close()
    httpd.shutdown()

asyncio.run(main())
