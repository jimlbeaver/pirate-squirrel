# Assets: inventory and style guide

Blender scripts in `tools/blender/` build every asset, render a preview to `art/previews/` (gitignored) and export `art/exports/<name>.glb`. The game loads a GLB with `swapIn(name, parent, standIn)` over a primitive stand-in and keeps the stand-in if anything fails. All stand-in references are to sections of `v2/index.html`.

`blender -b -P tools/blender/lineup.py` renders every exported asset side by side at game scale, in a 3/4 view and from the follow camera. Run it after changing any asset.

## Style guide

**The rule:** every asset must read clearly when it sits next to the twig boat (the approved anchor), and none may be busier than the boat. If a detail can't be seen from the follow camera (6.2 behind and 2.5 above the squirrel, 58° vertical field of view), leave it out.

**Shape language.** Chunky, rounded and slightly wonky, as if hand-made from things a squirrel could find: twigs, bark, leaves, rope, shells. Exaggerate the silhouette: big claws, big eyes, big hat corners. No straight factory edges on natural things. Small random jitter in position, angle and thickness, seeded so rebuilds are repeatable.

**Detail level.** Only detail you can see from 6–9 m behind the squirrel: big shapes, two or three colour blocks per part, and a few accents (rope ties, moss tufts, spots). No greebles, no fine texture carved into geometry, no thin parts under about 0.015 wide.

**Shading.** Flat (faceted) shading. Principled BSDF with base colour and roughness only (metallic only for gold). No textures, with two exceptions where the game already draws canvas textures: sign text and plaque symbols. Those assets expose a named material slot (`SignFace`, `PlaqueFace`) that the game fills in. No emissive; glows stay in code.

**Palette.** Author colours as the game's hex values (`materials` section, `MAT`). The core 12:

| | | | |
|---|---|---|---|
| bark `6a4a31` | bark dark `3b2618` | twig `7d5a36` | rope `d9bf86` |
| leaf gold / sail `e2a73c` | moss `7c9a3b` | fur `d4622a` | cream `f5e6cf` |
| crab shell `d2502c` | ink `151012` | gold `e8b23d` | rock `8e8474` |

The other `MAT` values (deck `d8b17a`, plank `9b6c42`/`6d4a2c`, coat `7a3421`, leather `4a2c1a`, red `b3261e`, white `f3f0e6`, nut `7a4220`/`cfa46a`, the leaf set `d9872a e8b441 c0602a 9aa23f e39a37`, sand `e8d3a1`, water `2a8a93`) are fine too. A new colour is allowed only as one darker or lighter partner of an existing one (e.g. twig dark `684828`, crab shell dark `a33a20`, crab pale `f1b27a` = `tailTip`).

**Triangle budgets.** Pieces placed many times (nuts, hedge bushes, tree kit pieces) 100–800 each. Props 500–3k. Characters 3–8k. Hero squirrel 8–12k including gear. The twig boat (7.3k tris, 554 KB) is the ceiling for a single prop. Flat shading splits vertices, so expect about 75 KB per 1k tris.

**Scale and orientation.** 1 Blender unit = 1 game unit (the squirrel is 0.9 tall). Blender is Z-up; the glTF exporter converts to game Y-up. Game forward (+z) is Blender -Y. The origin sits where the stand-in group's origin is, usually on the ground under the centre. Scripts write geometry in game coordinates via a `G(x, y, z)` helper, so numbers can be copied straight from the stand-in code.

**Moving parts.** Every part the game animates is its own named node. Its origin is the stand-in group's pivot and its rotation is identity, so the game's existing `rotation.x/y` code works unchanged (see the crab's `ClawL`/`ClawR`). Parts that could plausibly pop off (hats) get a node too.

**Naming.** Files are snake_case (`captain_pinch.glb`). Nodes and materials are PascalCase (`ClawL`, `CrabShell`). L/R means the character's own left/right; the character's left is game +x.

## Inventory

Status: **done** (approved by Jim), **style-check** (built, awaiting Jim), **todo**. The "Anim" column says who moves it: *code* means the game moves nodes; *clips* means skinned animation, not built yet.

### (a) Biggest visual impact per effort

| # | Asset | Stand-in (section) | Match: size, origin, facing | Tris | Style notes | Anim | Status |
|---|---|---|---|---|---|---|---|
| 1 | `twig_boat` | `boat` | hull 1.48 × 2.9, rim 0.34, deck 0.2, bow +z, rider 0.25 aft | 7,316 | woven twigs, rope lashings, oak-leaf sail, pinecone masthead | code (bob/roll) | **done** |
| 2 | `chest` | `treasure tree nest, flag, chest` (`chest` group) | 0.62 × 0.36 × 0.42, origin bottom centre, lock on +z; `Lid` node pivots at (0, 0.36, -0.21) | 1–1.5k | planked wood `7a4a26`, chunky gold bands and lock, a little wonky | code (lid) | todo |
| 3 | `chestnut` (final prize, #14) | `nutModel(chest, 1)` → `prize` | 0.35–0.45 across, origin at centre | ~1.5k with husk | glossy mahogany, pale flat hilum, tuft tip; optional green husk split into petal nodes. The only glossy nut in the game | code (rise, spin, husk opens) | todo (demo is off-style) |
| 4 | `peanut`, `acorn`, `walnut` (#15) | `nutModel(scene, 2.4)` in `voyage: nuts and hazards`; pickups `nutModel(scene, 2.0)` | today 0.77 across at 2.4×; peanut 0.75×, acorn 1×, walnut 1.3×; origin centre | 300–600 each | distinct silhouette and colour: pale lobed peanut, dark acorn with scaly cap, big wrinkled walnut with seam | code (bob, spin) | todo |
| 5 | Tree kit: `trunk`, `root_flare`, `branch`, `canopy_a/b/c`, `leaf_tuft`, `rope_wrap`, `moss_patch`, `sign_plaque` | `trees` (`TREES`, `addBranch`, `leafCluster`, `mossBand`, `addTag`) | trunk r 0.44–0.62, 6–12 tall (authored as a unit section, scaled per tree); branch tapers 0.27→0.15, walkable top 0.21 above its axis, 0.68 wide; canopy ~1.75 radius at top+0.95; plaque stick 0.5 plus a 0.56 disc at 0.66 | 100–800 each, instanced | bark with a few chunky vertical ridges; lobed oak-leaf clumps in the 5 leaf colours; moss patches with a bright rim on every edge (#5, #16); plaque symbol from the game's canvas texture | none | todo |
| 6 | `dock` kit, `pirates_gate` | `pier + Pirates Only gate` | plank 1.7 × 0.1 × 0.38, posts r 0.1 × 2.4; gate origin on the pier centre line at deck height; `GateLeafL/R` hinge at x ±0.92; sign board 2.3 × 0.68 at y 2.05 | 2–3k gate | weathered planks `9b6c42`/`6d4a2c`, rope-lashed posts, skull finial; `SignFace` slot for the game's text | code (gate leaves) | todo |
| 7 | `nest` | `treasure tree nest` | walkable disc r 1.45 at the treasure-tree top (flat top); bowl 1.58 → 1.15, 0.42 deep; rim r 1.5 | 3–5k | same twig weave as the boat, rope ties, a few leaves; flag stays in code | none | todo |
| 8 | `rock_a/b/c`, `drift_log` | `voyage` (`ROCKS`, `LOGS`), `Treasure Island` barricade | rock unit radius (scaled 1.1–2.4) with moss cap; log r 0.36 × 4.4 along x | 150–600 | rounded chunky rock, moss on top; log with bark, 2 broken stubs, a moss tuft. The barricade reuses the log | code (log drift, barricade collapse) | todo |

### (b) Enemies and characters

| # | Asset | Stand-in (section) | Match: size, origin, facing | Tris | Style notes | Anim | Status |
|---|---|---|---|---|---|---|---|
| 9 | `crab` | `buildCrab(1)` in `Treasure Island` | origin on the ground, body centred at y 0.24 (half-extents 0.42 × 0.2 × 0.32), +z forward; `Body`, `ClawL` (0.3, 0.26, 0.2), `ClawR` (-0.3, 0.26, 0.2) | 2,216 | dome shell with dark spots and rim spikes, pale pincer tips, eyes on stalks with grumpy lids, smile | code (claws, hop, flip) | **style-check** |
| 10 | `captain_pinch` | `buildCrab(1.45)` | as the crab, authored at 1× (the game scales `inner` by 1.45); plus a `Hat` node at (0, 0.46, -0.05); `ClawR` 1.35× | 3,252 | black tricorne with gold trim and skull, one oversized claw | code (+ hat can pop off) | **style-check** |
| 11 | `squirrel` + gear | `squirrel` (`buildSquirrel`, `equip`) | 0.9 tall, origin at the feet, +z forward; nodes `Body`, `Head` (0, 0.62, 0.04), `Ears`, `ArmL/R`, `Tail` (0, 0.2, -0.17); gear `Patch` (left eye, +x), `Coat`, `Hat`, `Map` | 8–12k | red fur, cream belly and muzzle, huge dark eyes, giant tail; rust coat with belt and brass buckle; tricorne with red band and skull; scroll map | code now; clips later (idle, run, jump, glide, climb, swipe, search, celebrate) | todo (**Jim to choose the approach**) |
| 12 | `komodo` (#11) | none yet (gameplay adds one) | suggest ~2.0 long, ~0.45 at the shoulder, origin on the ground under the chest, +z forward | 3–6k | low, long and lumpy; grey-olive with a pale belly; big dopey-mean eyes; forked tongue as its own node | code (body segments, tongue) or clips | todo |
| 13 | `hawk` (#12) | none yet | suggest ~1.8 wingspan, origin at the body centre, +z forward | 2–4k | brown/cream with a yellow hooked beak; `WingL/R` and `Tail` nodes | code (flap, dive) | todo |

### (c) Set dressing

| # | Asset | Stand-in (section) | Match | Tris | Notes | Status |
|---|---|---|---|---|---|---|
| 14 | `hollow` | `makeHollow` in `Home Isle hollows` | group on the trunk surface, +z out of the bark; hole 0.15 × 0.22 | ~300 | bark lip with a darker inside; the glint stays in code | todo |
| 15 | `shark_fin` | `SHARKS` in `voyage` | fin ~0.95 tall, base at the waterline, leading edge +z | ~150 | grey `46545d`, pale tip, small wake ring | todo |
| 16 | `hedge_bush` | `Treasure Island` hedge `InstancedMesh` | unit radius, ~180 instances, per-instance tint | 150–250 | bramble clump with a few thorns and berries; must stay instanced | todo |
| 17 | `cottage` | `scenery` | 3 × 2.2 × 2.6 box with a cone roof, seen at 150 m in fog | ~150 | white walls, terracotta roof, as in the concept backdrop | todo |
| 18 | `drift_leaf` | `scenery` `drift` planes | 0.15 × 0.1 | ~10 | a tiny oak-leaf outline | todo |

These stay in code: water, whirlpools, terrain, flag, clouds, particles and the SVG map.

### Next up, in order

The crab and Captain Pinch style check, then the chest and final Chestnut (#2, #3), the sea nuts (#4), the tree kit (#5, designed for #13's extra plaques and #16's moss patches), the dock and gate (#6), and the Komodo dragon (#12) once its gameplay stand-in exists. The hero squirrel (#11) is scheduled when Jim picks an approach.

## Wiring notes (for whoever swaps these in; not done on this branch)

- **Crabs.** Build the stand-in parts into a `standIn` group inside `inner`, load each GLB once and `clone()` it per crab (`swapIn` currently loads per call, so add a small cache). Point `claws` at the `ClawR` and `ClawL` nodes (that order matches `s = -1, 1`). The hit flash sets `c.m.emissive`, so clone the GLB's materials per crab and flash all of them. Captain Pinch's `Hat` can tumble off in the defeat flip.
- **Tree kit.** Every kit mesh must go into `occluders` with the same `userData.leaf` / `fr` / `plat` fields as the stand-ins, or the camera fade breaks.
- **Colour.** The loader converts material colours only. Vertex colours (if we ever use gradients) would need the same `convertLinearToSRGB`.
- **Size.** GLBs are uncompressed. Draco or meshopt would need extra decoders for r128, so revisit only if `art/exports` passes ~5 MB.
- The old `chestnut_demo.py` export is off-style (linear RGB rather than palette hex, smooth-shaded, raw `bpy`) and will be replaced by the #14 chestnut.
