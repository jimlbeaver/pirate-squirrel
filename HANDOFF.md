# Handoff: Pirate Squirrel browser game

You're picking up a browser game prototype, *Pirate Squirrel: Quest for the Chest Nuts*, a spin-off of Jim's animated short (OFWG Productions). Jim built v1 and v2 with Claude in a single session and has moved the code into this repo. Your job is to keep improving it without Jim present. Work in small, verifiable steps, and leave the game playable after every change.

## Read these first, in order

1. `README.md`: how to run it, controls, tools.
2. `DESIGN.md`: how v2 plays, the tuning-number table, the code-section map, next steps. **This is the source of truth for game rules.**
3. `CLAUDE.md`: short conventions.
4. `PLAN.md`: Jim's original plan (some of it is superseded by DESIGN.md).
5. `refs/Squirrel_Plain.png` and `refs/Pirate_Squirrel.png`: the concept art. This is the target look.

## Where things stand

- `v2/index.html` is the current game: one self-contained HTML file, three.js r128 loaded as a global (`THREE`), no build step. `v1/index.html` is a frozen reference. **Never edit v1.**
- Full loop works: Home Isle hollows (patch, coat, hat, map) → "Pirates ONLY" dock gate (needs all four) → voyage with energy, floating nuts and hazards → Treasure Island crab guards and barricade → branch-sign puzzle across three trees → treasure chest → win screen.
- All visuals are primitive stand-ins (spheres, cylinders, icosahedrons). Sound is synthesized WebAudio effects. There's no music yet.
- `tools/smoke_test.py` plays the whole loop headlessly through the `window.__psq` test hook and currently reports **WIN with no page errors**. Keep it that way.

## Decisions Jim has already made (don't undo these)

- **Controls are relative to the squirrel.** W/S forward and back, A/D turn, on the boat too. When climbing, A/D move to the squirrel's own left and right around the trunk. Don't reintroduce camera-relative movement.
- **Camera.** Follow cam behind the squirrel by default. Drag or arrow keys switch to free look, and C snaps back. Anything between the camera and the squirrel fades to see-through instead of the camera zooming in.
- **No accidental falls.** You can't walk off branches, the dock or the nest. You leave only by jumping or climbing. Leaps toward a partner branch get aim assist. Jim found falling off branches frustrating, so keep navigation forgiving.
- **Mossy bark means you can't climb.** Only the rope-wrapped tree can be climbed from the ground in the grove. Bare bark between moss bands is climbable from a branch.
- **Progression gates.** Gear and the map are all found on Home Isle. The gate needs the full kit plus the map. The voyage needs nuts to have enough energy. Crabs must be beaten to open the barricade. At least three trees must be crossed to reach the treasure tree.
- Tone: kid-friendly slapstick. Failures are funny and cheap: short respawns, no lives.

## Rules for working

1. **Verify every change.** Serve with `python3 -m http.server 8000` and check `/v2/`. After each change, run `python3 tools/smoke_test.py` and confirm it ends in `result: WIN | page errors: none`. If you change mechanics the test relies on, update the test in the same change.
2. **Keep `window.__psq` working.** It's how the game gets tested headlessly. Extend it if you need new probes.
3. **Update `DESIGN.md`** whenever you change a rule, a tuning number or the code layout. Numbers in the tuning table must match the code.
4. **Small commits** with clear messages, one topic each. Don't mix refactors with gameplay changes.
5. **Screenshots for visual work.** The smoke test saves them to `tools/out/`. For art changes, compare against `refs/` and describe what changed in the commit message.
6. **Network.** The page needs internet only for Google Fonts, and falls back to `vendor/three.r128.min.js` if the CDN is down. `pip install bpy` and `playwright install chromium` need internet once.
7. Don't add paid services, accounts or analytics. Don't publish or deploy anything. Jim decides when to share builds.

## Backlog, in priority order

Each item has what "done" means. Take them in order unless one is blocked.

### 1. Asset pipeline and first real assets (Blender, scripted)
- Use `tools/blender/chestnut_demo.py` as the template: scripts in `tools/blender/`, GLBs in `art/exports/`, previews in `art/previews/` (gitignored). Conventions: 1 Blender unit = 1 game unit, squirrel about 0.9 tall, branches about 0.6 wide, low-poly, Principled BSDF materials.
- Build a small loader in v2 with `GLTFLoader` for r128 (`https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js`; also vendor it in `vendor/`). **If a GLB fails to load, keep the primitive stand-in.** The game must never break because of a missing asset.
- Order: **twig boat with oak-leaf sail**, then **crab and Captain Pinch** (hat), **chest and chestnut**, **tree kit** (trunk, branch, canopy cluster, moss band, rope wrap, sign plaque), **dock and Pirates Only gate**.
- Done when each asset renders in game at the same size and position as its stand-in, the smoke test still wins, and a preview PNG exists for Jim to review.

### 2. Hero squirrel
- Match the concept art: red squirrel, big dark eyes, cream belly, huge bushy tail. Pirate gear is a tricorne with a red band and skull, an eye patch over the **left** eye, a rust-brown coat with belt and brass buckle, and the map as a rolled scroll.
- Gear pieces must be **separate meshes** that the game toggles on (`equip()` in the `squirrel` section).
- Rig and animate: idle, run, jump, glide (coat flares), climb, tail swipe, search (rummage), celebrate. Drive them from the existing player modes (`P.mode`, `P.gliding`, `P.attackT`, `state==='searching'`).
- If a scripted model can't get close to the concept art, say so in `NOTES_FOR_JIM.md` and recommend an image-to-3D draft from `refs/` for Jim to generate. Don't sign up for services yourself.

### 3. Balance pass
- Nobody has play-tested the numbers by hand. Build an autopilot in the smoke test (or a separate `tools/balance.py`) that sails the lane while collecting nuts and dodging hazards, and report energy at arrival across several runs.
- Target: a careful player arrives with about 20–50 energy. A player who ignores the nuts runs out around two-thirds of the way. The crab fight should cost about 20–40 energy.
- Tune only the values in the DESIGN.md tuning table, and record before/after numbers in the commit message.

### 4. Music hook (don't pick music)
- Jim has his own music and will supply it. Add a music system that loads `audio/voyage.mp3` and `audio/island.mp3` if they exist, crossfades by zone (Home Isle and Treasure Island vs at sea), starts only after the first click or keypress, respects the existing mute button, and stays silent if the files are missing.
- Done when the game behaves exactly as before with no audio files present.

### 5. Code structure (only after 1–4)
- Split `v2/index.html` into ES modules with Vite, following the existing section names, keep a working single-file build if feasible, and keep the smoke test passing. Leave `v1/` alone.

## When you're unsure

Jim is offline. Don't stop; make the most reasonable choice consistent with the decisions above. Write any open questions, trade-offs you picked, and things Jim should look at into `NOTES_FOR_JIM.md` at the repo root, newest first, one short entry per item. Examples: art direction calls, balance targets that felt off, anything you removed or couldn't finish.

Never make changes that are hard to reverse without writing them up there first. That means deleting assets, rewriting history, or changing core rules like the controls, the progression gates or the no-fall behavior.
