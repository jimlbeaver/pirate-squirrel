# Assets: inventory and style guide

Blender scripts in `tools/blender/` build every asset, render a preview to `art/previews/` (gitignored) and export `art/exports/<name>.glb`. The game loads a GLB with `swapIn(name, parent, standIn, wire)` over a primitive stand-in and keeps the stand-in if anything fails. All stand-in references are to sections of `v2/index.html`.

`blender -b -P tools/blender/lineup.py` renders every exported asset side by side at game scale, in a 3/4 view and from the follow camera. Run it after changing any asset. `blender -b -P tools/blender/samples.py` renders the shading and foliage sample sheets behind the decisions below; it exports nothing.

## Decisions

| Question | Decision |
|---|---|
| Crab eyes | **Settled:** small beady eyes, no stalks, lids or glints (crab and Captain Pinch) |
| Captain Pinch | **Settled:** tricorne plus one oversized claw (`ClawR` 1.35×) |
| Hero squirrel | **Settled:** scripted in Blender, low-poly, one skinned mesh on a simple armature, with baked glTF clips (see *Squirrel rig and clips*). In the game since v2.3. Tail sits lower and further back (v2.3) so the hat and gear read from the follow camera |
| Character shading, faceted or smooth | **Settled:** characters (squirrel, crabs, Captain Pinch) are smooth-shaded; the world stays faceted |
| Nuts | **Settled:** each nut reads apart at a glance, even from the follow camera. Sea nuts are faceted world props: a pinched, pitted peanut, a scaly-capped acorn, a wrinkled walnut with a seam. The Chestnut prize is the one smooth, glossy nut, bigger and redder, with a pale base patch and a tip tuft |
| Leaves and wear | **Settled:** option A from `art/previews/sample_foliage.png`, flat colours with boat-level moss (not B's heavier moss and weathering, nor C's vertex-colour gradients). The tree kit gets built to this in a later version |

## Style guide

**The rule:** every asset must read clearly when it sits next to the twig boat (the approved anchor), and none may be busier than the boat. If a detail can't be seen from the follow camera (6.2 behind and 2.5 above the squirrel, 58° vertical field of view), leave it out.

**Shape language.** Chunky, rounded and slightly wonky, as if hand-made from things a squirrel could find: twigs, bark, leaves, rope, shells. Exaggerate the silhouette: big claws, big eyes, big hat corners. No straight factory edges on natural things. Small random jitter in position, angle and thickness, seeded so rebuilds are repeatable.

**Detail level.** Only detail you can see from 6–9 m behind the squirrel: big shapes, two or three colour blocks per part, and a few accents (rope ties, moss tufts, spots). No greebles, no fine texture carved into geometry, no thin parts under about 0.015 wide.

**Shading.** Flat (faceted) shading for the world and its props, sea nuts included. Characters and the Chestnut prize are smooth-shaded. Principled BSDF with base colour and roughness only (metallic only for gold). No textures, with two exceptions where the game already draws canvas textures: sign text and plaque symbols. Those assets expose a named material slot (`SignFace`, `PlaqueFace`) that the game fills in. No emissive; glows stay in code.

**Palette.** Author colours as the game's hex values (`materials` section, `MAT`). The core 12:

| | | | |
|---|---|---|---|
| bark `6a4a31` | bark dark `3b2618` | twig `7d5a36` | rope `d9bf86` |
| leaf gold / sail `e2a73c` | moss `7c9a3b` | fur `d4622a` | cream `f5e6cf` |
| crab shell `d2502c` | ink `151012` | gold `e8b23d` | rock `8e8474` |

The other `MAT` values (deck `d8b17a`, plank `9b6c42`/`6d4a2c`, coat `7a3421`, leather `4a2c1a`, red `b3261e`, white `f3f0e6`, nut `7a4220`/`cfa46a`, the leaf set `d9872a e8b441 c0602a 9aa23f e39a37`, sand `e8d3a1`, water `2a8a93`) are fine too. A new colour is allowed only as one darker or lighter partner of an existing one (e.g. twig dark `684828`, crab shell dark `a33a20`, crab pale `f1b27a` = `tailTip`).

**Triangle budgets.** Pieces placed many times (hedge bushes, tree kit pieces) 100–800 each. Sea nuts up to 1.5k each, since there are only 27 and the walnut's wrinkles need the geometry. Props 500–3k. Characters 3–8k. Hero squirrel 8–12k including gear. The twig boat (7.3k tris, 554 KB) is the ceiling for a single prop. Flat shading splits vertices, so expect about 75 KB per 1k tris.

**Scale and orientation.** 1 Blender unit = 1 game unit (the squirrel is 0.9 tall). Blender is Z-up; the glTF exporter converts to game Y-up. Game forward (+z) is Blender -Y. The origin sits where the stand-in group's origin is, usually on the ground under the centre. Scripts write geometry in game coordinates via a `G(x, y, z)` helper, so numbers can be copied straight from the stand-in code.

**Moving parts.** Every part the game animates is its own named node. Its origin is the stand-in group's pivot and its rotation is identity, so the game's existing `rotation.x/y` code works unchanged (see the crab's `ClawL`/`ClawR`). Parts that could plausibly pop off (hats) get a node too.

**Naming.** Files are snake_case (`captain_pinch.glb`). Nodes and materials are PascalCase (`ClawL`, `CrabShell`). L/R means the character's own left/right; the character's left is game +x.

## Inventory

Status: **done** (approved by Jim), **style-check** (built, awaiting Jim), **todo**. The "Anim" column says who moves it: *code* means the game moves nodes; *clips* means skinned animation, not built yet.

### (a) Biggest visual impact per effort

| # | Asset | Stand-in (section) | Match: size, origin, facing | Tris | Style notes | Anim | Status |
|---|---|---|---|---|---|---|---|
| 1 | `twig_boat` | `boat` | hull 1.48 × 2.9, rim 0.34, deck 0.2, bow +z, rider 0.25 aft | 7,316 | woven twigs, rope lashings, oak-leaf sail, pinecone masthead | code (bob/roll) | **done** |
| 2 | `chest` | `treasure tree nest, flag, chest` (`chest` group) | 0.62 × 0.36 × 0.42, origin bottom centre, lock on +z; `Lid` node pivots at (0, 0.36, -0.21); lock in `ChestLock` | 916 | planked wood, chunky gold bands, corner caps and lock, dark lining with a few coins | code (lid, lock glow) | **style-check** (`tools/blender/chest.py`) |
| 3 | `chestnut` (final prize, #14) | chestnut stand-in in `prize` | 0.5 across, origin at centre (the reveal grows it 0.8× → 2.2×); `Chestnut` in `ChestnutShell`, husk petals `HuskA`–`HuskD` hinged at their bases | 2,005 with husk | glossy red-brown, pale flat hilum, tuft tip, spiky green husk. The only glossy nut in the game | code (husk opens, rise, spin, glow) | **style-check** (`tools/blender/nuts.py`) |
| 4 | `peanut`, `acorn`, `walnut` (#15) | `peanutModel`, `nutModel(g, 2.4)`, `walnutModel` in `voyage: nuts and hazards`; crab drops reuse `acorn` at 2/2.4 | authored at game size (peanut 0.6 long, acorn 0.75 tall, walnut 1.0 across), origin centre | 864 / 661 / 1,504 | pale pinched peanut with a pitted net; dark glossy acorn under a scaly cap; big deeply wrinkled walnut with a raised seam | code (bob, spin) | **style-check** (`tools/blender/nuts.py`) |
| 5 | Tree kit: `trunk`, `root_flare`, `branch`, `canopy_a/b/c`, `leaf_tuft`, `rope_wrap`, `moss_patch`, `sign_plaque` | `trees` (`TREES`, `addBranch`, `leafCluster`, `mossBand`, `addTag`) | trunk r 0.44–0.62, 6–12 tall (authored as a unit section, scaled per tree); branch tapers 0.27→0.15, walkable top 0.21 above its axis, 0.68 wide; canopy ~1.75 radius at top+0.95; plaque stick 0.5 plus a 0.56 disc at 0.66 | 100–800 each, instanced | bark with a few chunky vertical ridges; lobed oak-leaf clumps in the 5 leaf colours; moss patches with a bright rim on every edge (#5, #16); plaque symbol from the game's canvas texture | none | todo |
| 6 | `dock` kit, `pirates_gate` | `pier + Pirates Only gate` | plank 1.7 × 0.1 × 0.38, posts r 0.1 × 2.4; gate origin on the pier centre line at deck height; `GateLeafL/R` hinge at x ±0.92; sign board 2.3 × 0.68 at y 2.05 | 2–3k gate | weathered planks `9b6c42`/`6d4a2c`, rope-lashed posts, skull finial; `SignFace` slot for the game's text | code (gate leaves) | todo |
| 7 | `nest` | `treasure tree nest` | walkable disc r 1.45 at the treasure-tree top (flat top); bowl 1.58 → 1.15, 0.42 deep; rim r 1.5 | 3–5k | same twig weave as the boat, rope ties, a few leaves; flag stays in code | none | todo |
| 8 | `rock_a/b/c`, `drift_log` | `voyage` (`ROCKS`, `LOGS`), `Treasure Island` barricade | rock unit radius (scaled 1.1–2.4) with moss cap; log r 0.36 × 4.4 along x | 150–600 | rounded chunky rock, moss on top; log with bark, 2 broken stubs, a moss tuft. The barricade reuses the log | code (log drift, barricade collapse) | todo |

### (b) Enemies and characters

| # | Asset | Stand-in (section) | Match: size, origin, facing | Tris | Style notes | Anim | Status |
|---|---|---|---|---|---|---|---|
| 9 | `crab` | `buildCrab(1)` in `Treasure Island` | origin on the ground, body centred at y 0.24 (half-extents 0.42 × 0.2 × 0.32), +z forward; `Body`, `ClawL` (0.3, 0.26, 0.2), `ClawR` (-0.3, 0.26, 0.2) | 2,048 | smooth dome shell with dark spots and rim spikes, pale pincer tips, small beady eyes, smile | code (claws, hop, flip, hit flash) | **done** (in the game since v2.3) |
| 10 | `captain_pinch` | `buildCrab(1.45)` | as the crab, authored at 1× (the game scales `inner` by 1.45); plus a `Hat` node at (0, 0.46, -0.05); `ClawR` 1.35× | 3,084 | black tricorne with gold trim and skull, one oversized claw, beady eyes | code (the hat could pop off; the game doesn't do that yet) | **done** (in the game since v2.3) |
| 11 | `squirrel` + gear | `squirrel` (`buildSquirrel`, `equip`) | 0.9 tall, origin between the feet, +z forward; skinned `SquirrelBody` on a 17-bone rig; gear `Ears`, `Patch` (left eye, +x), `Hat`, `Coat` + `CoatSleeveL/R`, `Map` | 5,624 (body 2,748) | smooth red fur, cream belly and muzzle, huge dark eyes, giant puffy tail carried low and back; rust coat with belt and brass buckle; tricorne with red band and skull; scroll map | clips: `Idle`, `Run`, `Jump`, `Glide`, `Climb`, `Swipe`, `Celebrate` | **style-check** (in the game since v2.3; new tail) |
| 12 | `komodo` (#11) | `buildKomodo` in `Komodo dragon (grove floor)` | suggest ~2.0 long, ~0.45 at the shoulder, origin on the ground under the chest, +z forward | 3–6k | low, long and lumpy; grey-olive with a pale belly; big dopey-mean eyes; forked tongue as its own node | code (body segments, tongue) or clips | todo |
| 13 | `hawk` (#12) | `buildHawk` in `hawk (Treasure Island branches)` | suggest ~1.8 wingspan, origin at the body centre, +z forward | 2–4k | brown/cream with a yellow hooked beak; `WingL/R` and `Tail` nodes | code (flap, dive) | todo |

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

The tree kit (#5, designed for #13's extra plaques and #16's moss patches, in foliage option A), the dock and gate (#6), the Komodo dragon (#12, over the game's current stand-in), a search clip for the squirrel, and Captain Pinch's hat tumbling off in the defeat flip.

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
| `Glide` | 1.00 s, loop | spread-eagle like a flying squirrel, with a gentle limb sway; the game tilts the model forward on top |
| `Climb` | 0.50 s, loop | facing the trunk, diagonal pairs reach and push; its speed follows the climb speed |
| `Swipe` | 0.29 s (7 frames), play once | a crouched tail whip (keys at f0, f2, f5, f7), under the game's 0.3 s spin |
| `Celebrate` | 1.00 s, loop | arms up and bouncing, for the win |

The game (`squirrelClip`, `animateGlb` in the `animation` section) picks a clip from the movement state and crossfades over 0.15 s (0.06 s into `Swipe`). `Jump` and `Swipe` play once with `clampWhenFinished`. The body comes in as 7 `SkinnedMesh` primitives (one per material).

**Adding a clip.** Add a pose function to `CLIPS` in `squirrel.py`. It returns game-axis euler rotations per bone plus an optional `Hips` lift; the script converts them to bone space. Keep clips in place and loopable where the game loops them.

## Wiring notes

Done in v2.3:

- **Shared materials.** `GLTFLoader` shares one material instance between every mesh that uses it, so the loader converts each material from linear to sRGB once (a `Set` of seen materials), not once per mesh.
- **One load per file.** `loadAsset` caches a promise per GLB. The first `swapIn` caller gets `gltf.scene`, later callers get `scene.clone(true)`. Clones share materials and geometry, so anything that animates a material clones it first.
- **Crabs.** The stand-in parts live in a `standIn` group inside `inner`. `claws` points at `ClawR` and `ClawL` (that order matches `s = -1, 1`), and each crab clones its materials into `c.mats` for the hit flash.
- **Squirrel.** The stand-in stays as the fallback. `equip()` shows the matching gear nodes (`GEAR_NODES`), `Ears` hide under the hat, and an `AnimationMixer` plays the clips above. The code-driven bob and tail sway only run on the stand-in.
- **Chest and Chestnut.** The game opens the GLB's `Lid` and glows `ChestLock`; the reveal animates `ChestnutShell`'s emissive and swings `HuskA`–`HuskD` open about their hinges.

Still to do:

- **Captain Pinch's hat.** The `Hat` node could tumble off in the defeat flip; the game doesn't do that yet.
- **Tree kit.** Every kit mesh must go into `occluders` with the same `userData.leaf` / `fr` / `plat` fields as the stand-ins, or the camera fade breaks.
- **Colour.** The loader converts material colours only, which is all foliage option A needs. If an asset ever uses vertex colours (as option C would have), the loader must convert those too. The exporter writes `COLOR_0` as unnormalized float RGB, so this is all that's needed (checked in r128 on the sample GLB):

```js
const col = o.geometry.attributes.color, c = new THREE.Color();
if (col) { for (let i = 0; i < col.count; i++) { c.fromBufferAttribute(col, i).convertLinearToSRGB(); col.setXYZ(i, c.r, c.g, c.b); } col.needsUpdate = true; }
```

  `GLTFLoader` already sets `vertexColors` on those materials. Keep the material colour white in Blender, because the two multiply.
- **Size.** GLBs are uncompressed. Draco or meshopt would need extra decoders for r128, so revisit only if `art/exports` passes ~5 MB.
