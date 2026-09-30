# Assets: inventory and style guide

Blender scripts in `tools/blender/` build every asset, render a preview to `art/previews/` (gitignored) and export `art/exports/<name>.glb`. The game loads a GLB with `swapIn(name, parent, standIn)` over a primitive stand-in and keeps the stand-in if anything fails. All stand-in references are to sections of `v2/index.html`.

`blender -b -P tools/blender/lineup.py` renders every exported asset side by side at game scale, in a 3/4 view and from the follow camera. Run it after changing any asset. `blender -b -P tools/blender/samples.py` renders the two open-question sheets below; it exports nothing.

## Decisions

| Question | Decision |
|---|---|
| Crab eyes | **Settled:** small beady eyes, no stalks, lids or glints (crab and Captain Pinch) |
| Captain Pinch | **Settled:** tricorne plus one oversized claw (`ClawR` 1.35×) |
| Hero squirrel | **Settled:** scripted in Blender, low-poly, one skinned mesh on a simple armature, with baked glTF clips (see *Squirrel rig and clips*). Not wired into the game yet |
| Character shading, faceted or smooth | **Pending** Jim's pick from `art/previews/sample_shading.png` (crab and squirrel each way, next to faceted world pieces) |
| Leaves and wear | **Pending** Jim's pick from `art/previews/sample_foliage.png`: A flat colours with boat-level moss, B flat with more moss and weathering, C vertex-colour gradients (needs the loader change in the wiring notes) |

## Style guide

**The rule:** every asset must read clearly when it sits next to the twig boat (the approved anchor), and none may be busier than the boat. If a detail can't be seen from the follow camera (6.2 behind and 2.5 above the squirrel, 58° vertical field of view), leave it out.

**Shape language.** Chunky, rounded and slightly wonky, as if hand-made from things a squirrel could find: twigs, bark, leaves, rope, shells. Exaggerate the silhouette: big claws, big eyes, big hat corners. No straight factory edges on natural things. Small random jitter in position, angle and thickness, seeded so rebuilds are repeatable.

**Detail level.** Only detail you can see from 6–9 m behind the squirrel: big shapes, two or three colour blocks per part, and a few accents (rope ties, moss tufts, spots). No greebles, no fine texture carved into geometry, no thin parts under about 0.015 wide.

**Shading.** Flat (faceted) shading for the world. Characters are faceted for now, pending the shading decision. Principled BSDF with base colour and roughness only (metallic only for gold). No textures, with two exceptions where the game already draws canvas textures: sign text and plaque symbols. Those assets expose a named material slot (`SignFace`, `PlaqueFace`) that the game fills in. No emissive; glows stay in code.

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
| 9 | `crab` | `buildCrab(1)` in `Treasure Island` | origin on the ground, body centred at y 0.24 (half-extents 0.42 × 0.2 × 0.32), +z forward; `Body`, `ClawL` (0.3, 0.26, 0.2), `ClawR` (-0.3, 0.26, 0.2) | 2,048 | dome shell with dark spots and rim spikes, pale pincer tips, small beady eyes, smile | code (claws, hop, flip) | **style-check** (eyes settled; shading pending) |
| 10 | `captain_pinch` | `buildCrab(1.45)` | as the crab, authored at 1× (the game scales `inner` by 1.45); plus a `Hat` node at (0, 0.46, -0.05); `ClawR` 1.35× | 3,084 | black tricorne with gold trim and skull, one oversized claw, beady eyes | code (+ hat can pop off) | **style-check** (design settled; shading pending) |
| 11 | `squirrel` + gear | `squirrel` (`buildSquirrel`, `equip`) | 0.9 tall, origin between the feet, +z forward; skinned `SquirrelBody` on a 17-bone rig; gear `Ears`, `Patch` (left eye, +x), `Hat`, `Coat` + `CoatSleeveL/R`, `Map` | 4,964 (body 2,088) | red fur, cream belly and muzzle, huge dark eyes, giant puffy tail; rust coat with belt and brass buckle; tricorne with red band and skull; scroll map | clips: `Idle`, `Run`, `Jump` (glide, climb, swipe, search, celebrate later) | **style-check** (scripted, rigged, animated; not wired in) |
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

Jim's shading and foliage picks, then the chest and final Chestnut (#2, #3), the sea nuts (#4), the tree kit (#5, designed for #13's extra plaques and #16's moss patches, and built to the foliage pick), the dock and gate (#6), more squirrel clips, and the Komodo dragon (#12) once its gameplay stand-in exists.

## Squirrel rig and clips

`blender -b -P tools/blender/squirrel.py` builds, rigs, animates and exports `squirrel.glb`, and renders contact sheets and MP4s to `art/previews/` (`-- --quick` renders one still only).

**Nodes.** Armature `Squirrel` (origin between the feet, +z forward) with one skinned mesh `SquirrelBody`. Gear is rigid meshes parented to bones, so the game toggles `visible` by name, as `equip()` does today:

| Node | Bone | Notes |
|---|---|---|
| `Ears` | `Head` | hide while the hat is on (they poke through it) |
| `Patch` | `Head` | over the left eye (+x); the strap runs diagonally round the head |
| `Hat` | `Head` | tricorne, red band, skull |
| `Coat`, `CoatSleeveL`, `CoatSleeveR` | `Hips`, `ArmL`, `ArmR` | one piece of gear: toggle all three together |
| `Map` | `Hips` | scroll on the right hip |

**Bones (17).** `Hips` (root) → `Spine` → `Chest` → `Head`, `ArmL/R`; `Hips` → `ThighL/R` → `ShinL/R` → `FootL/R`; `Hips` → `Tail1`…`Tail5`. Rotation keys are quaternions. Weights are painted by script (rigid per part, blended across the torso and tail), with no automatic weights, so rebuilds are repeatable.

**Clips.** 24 fps, every bone keyed (51 channels). All clips play in place: the game already moves, turns and arcs the squirrel.

| Clip | Length | Use |
|---|---|---|
| `Idle` | 2.00 s (48 frames), loop | breathing, head look, tail sway |
| `Run` | 0.50 s (12 frames), loop | one stride per loop; `timeScale = hs * 3.2 / (4 * Math.PI)` keeps the stride rate the game's `walkPhase` uses |
| `Jump` | 0.67 s (16 frames), play once, `clampWhenFinished` | crouch (f3), launch (f6), apex tuck (f10), reach to land (f16). Start on jump; crossfade back to `Idle`/`Run` on landing |

```js
const mixer = new THREE.AnimationMixer(gltf.scene);             // tick with mixer.update(dt)
const act = (n) => mixer.clipAction(THREE.AnimationClip.findByName(gltf.animations, n));
act('Run').play();
const jump = act('Jump'); jump.setLoop(THREE.LoopOnce); jump.clampWhenFinished = true;
```

Checked in three.js r128 (`GLTFLoader` plus `AnimationMixer`): all three clips load by name and move the bones, and all gear nodes are found by name. The body comes in as 7 `SkinnedMesh` primitives (one per material).

**Adding a clip.** Add a pose function to `CLIPS` in `squirrel.py`. It returns game-axis euler rotations per bone plus an optional `Hips` lift; the script converts them to bone space. Keep clips in place and loopable where the game loops them.

## Wiring notes (for whoever swaps these in; not done on this branch)

- **Shared materials (fix before the first multi-node GLB goes in).** `GLTFLoader` shares one material instance between every mesh that uses it. The loader's per-mesh `convertLinearToSRGB` therefore runs once per mesh, and shared colours wash out: the crab's shell (body and both claws) and the squirrel's fur and coat come out pale. The twig boat is one mesh, so it never showed. Convert each material once:

```js
const seen = new Set();
m.traverse(o => { if (!o.isMesh) return; [].concat(o.material).forEach(q => { if (seen.has(q)) return; seen.add(q); /* existing conversion */ }); });
```

- **Crabs.** Build the stand-in parts into a `standIn` group inside `inner`, load each GLB once and `clone()` it per crab (`swapIn` currently loads per call, so add a small cache). Point `claws` at the `ClawR` and `ClawL` nodes (that order matches `s = -1, 1`). The hit flash sets `c.m.emissive`, so clone the GLB's materials per crab and flash all of them. Captain Pinch's `Hat` can tumble off in the defeat flip.
- **Tree kit.** Every kit mesh must go into `occluders` with the same `userData.leaf` / `fr` / `plat` fields as the stand-ins, or the camera fade breaks.
- **Colour.** The loader converts material colours only. If Jim picks foliage option C (vertex-colour gradients), the loader must convert vertex colours too. The exporter writes `COLOR_0` as unnormalized float RGB, so this is all that's needed (checked in r128 on the sample GLB):

```js
const col = o.geometry.attributes.color, c = new THREE.Color();
if (col) { for (let i = 0; i < col.count; i++) { c.fromBufferAttribute(col, i).convertLinearToSRGB(); col.setXYZ(i, c.r, c.g, c.b); } col.needsUpdate = true; }
```

  `GLTFLoader` already sets `vertexColors` on those materials. Keep the material colour white in Blender, because the two multiply.
- **Squirrel.** Keep the current stand-in as the fallback. On load, hide the stand-in's parts, map `equip()` onto the gear node names above, and drive the clips from the existing movement state (grounded plus speed gives `Idle` or `Run`; take-off plays `Jump`). The code-driven tail sway (`rig.tail.rotation`) goes away, because the clips do it. Glide and swipe tail poses need their own clips.
- **Size.** GLBs are uncompressed. Draco or meshopt would need extra decoders for r128, so revisit only if `art/exports` passes ~5 MB.
- The old `chestnut_demo.py` export is off-style (linear RGB rather than palette hex, smooth-shaded, raw `bpy`) and will be replaced by the #14 chestnut.
