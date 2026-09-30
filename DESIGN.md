# Design notes: v2

Everything lives in `v2/index.html`: CSS and HUD markup at the top, then one script organized in commented sections (`/* ===== name ===== */`).

## How a run plays

1. **Home Isle.** You start on a branch of the home oak as a plain squirrel. Six tree hollows hold four items (eye patch, coat, hat, treasure map) and two junk finds. Contents are decided when you search: the first hollow always gives an item, and later ones use `items left / hollows left` odds, so you can never run out before finding everything. Items come in the order patch → coat → hat → map.
2. **Pirates Only gate.** The dock has a gate with a "Pirates ONLY" sign. It opens by itself when you arrive with all four items; otherwise it lists what's missing. While it's shut, the dock beyond it doesn't count as solid ground, so jumping or gliding around the gate just drops you in the sea. Boarding the boat also requires the map.
3. **Voyage.** Energy drains while sailing, faster at speed. Floating nuts refill it. Hazards cost energy: rocks, circling shark fins, drifting logs, and whirlpools that pull, spin and drain. At 0 energy the tide carries you back to the dock with energy full and the nuts restored. On first landfall, energy is topped up to at least 70.
4. **Crab guards.** A bramble hedge rings the island's grove, with one gap barricaded by four crabs (Captain Pinch has a hat and more HP). Crabs chase you on the ground and pinch for energy. Tail-swipe (F) or land on them. Beaten crabs drop nuts. When the last one falls, the barricade collapses. At 0 energy you wake up back on the beach at 70.
5. **Branch puzzle.** Only the rope-wrapped tree can be climbed from the ground. Mossy bark is too slick to climb. The path is rope tree → A → B → C → treasure tree, four leaps across three middle trees. Each tree has two or three launch branches with carved sign plaques (anchor, skull, star, moon, shell). The map shows which sign to take on each tree, reshuffled every game. The wrong branches are rotten and snap when you stand on them. Trunks can't be climbed above their highest branch, and later trees' branches are higher, so gliding can't skip steps.
6. **Treasure.** Climb the treasure tree to the nest, open the chest, and the Chestnut rises out. The win screen shows time, splashes, nuts eaten and crabs beaten.

## Movement rules

- Tank controls everywhere: W/S along the squirrel's facing, A/D turn. Follow cam sits behind him, and dragging switches to free cam.
- You can't walk off branches, the dock or the nest. Movement is clamped to the platform, so you leave only by jumping, or by climbing via the trunk.
- Leaps from a branch toward its partner branch on the next tree get aim assist (`assistFor`), active within about 40° of the right direction. Rotten decoys have no partner branch, so they get none.
- Anything between the camera and the squirrel fades to see-through (`updateOcclusion`). This covers leaves, trunks, branches, moss and rope.
- Grabbing trunks (`canGrab`): Home Isle trees from anywhere at or above their climb start. Grove trees only while standing on one of their own branches, or from the ground for the rope tree. Never from mid-air in the grove.

## Tuning knobs

| What | Value | Where |
|---|---|---|
| Run speed, glide speed | `RUN=5.2`, `GLIDE=6.2` | `game state` |
| Jump velocity, gravity | `JUMP_V=7.6`, `G=24` | `game state` |
| Glide fall speed, max glide time | `GLIDE_FALL=1.4`, `GLIDE_MAX=1.6` s | `game state` |
| Climb speed, turn rate | `CLIMB=2.8`, `TURN=3.0` rad/s | `game state` |
| Sailing energy drain | 4.6/s moving, 0.8/s idle | `stepBoat` |
| Floating nut | +12 | `stepBoat` |
| Rock / log / shark hit | −10 / −12 / −18 | `stepBoat` |
| Whirlpool | up to −11/s, pull 2.2 | `stepBoat` |
| Crab pinch | −15 (Captain −20) | `updateCrabs` |
| Crab HP | 2 (Captain 3) | `CRAB_DEF` |
| Island nut pickup | +15 | `updateCrabs` |
| Splash on Treasure Island | −10 | `doSplash` |
| Landfall / knockout energy | 70 | `goAshore`, `finishKO` |
| Voyage layout | lane curve `laneX(z)`, `ROCKS`, `SHARKS`, `LOGS`, `WHIRLS`, `SEA_NUTS` | `voyage` |
| Grove layout | `arcPt()` tree positions, `GROVE_LINKS` branch heights | `trees` |

Balance hasn't been play-tested by hand yet. The voyage energy budget is the first thing to tune.

## World layout

- Home Isle is centered at (0, 0), radius about 12.5. The dock points out at 60° from its center.
- Treasure Island is centered at `C = (6, 200)`, radius about 19. The hedge ring has radius 12, with its gap to the south facing the landing beach.
- Terrain is analytic (`islandH`, `terrainY`), so meshes and physics use the same function.

## Code map (section → what's in it)

`utils` · `renderer / scene` · `water` (animated plane that follows the camera) · `materials` · `assets` (`swapIn` loads `art/exports/<name>.glb` over a stand-in group and keeps the stand-in on any failure) · `symbols` (sign paths shared by the canvas plaques and the SVG map) · `islands / terrain` · `trees` (trees, branches as box platforms, moss bands) · `treasure tree nest, flag, chest` · `Home Isle hollows` · `pier + Pirates Only gate` · `voyage` · `Treasure Island` (hedge, barricade, crabs) · `boat` · `squirrel` (primitive rig; gear pieces toggle on) · `scenery` · `particles` · `audio` (WebAudio synthesized SFX) · `UI` · `game state` · `camera + input` · `the treasure map (SVG)` · `physics helpers` · `player step` · `crabs` · `interactions` · `objectives` · `animation` · `camera` (follow/free, occlusion fade) · `main loop` · `boot + hot-reload state`.

`window.__psq` at the bottom is a small test hook (teleport, step the simulation, press keys, read state) used by `tools/smoke_test.py`. It's harmless to ship, and easy to delete.

## Next steps

- **Assets.** Replace the primitive stand-ins with GLBs made in Blender. Done: the twig boat (`tools/blender/twig_boat.py`, oak-leaf sail, pinecone figurehead, crow's nest). Next: crab and Captain Pinch, then chest and chestnut, the tree kit (trunk, branch, canopy, moss, rope, sign plaque), dock and gate, then the hero squirrel. For the squirrel, the plan is an image-to-3D draft from `refs/`, cleaned up and cut down for the web, rigged, with gear pieces as separate meshes.
  - To swap an asset in: build the stand-in into its own group, then call `swapIn('<name>', parent, standInGroup)`. The GLB must share the stand-in's origin, size and facing (+z forward in game, -Y in Blender).
  - `GLTFLoader` r128 comes from jsdelivr with a fallback to `vendor/GLTFLoader.r128.js`. GLBs only load over HTTP; opened from `file://` the game quietly keeps the stand-ins.
  - Asset colours are authored as the game's hex values; the loader converts glTF's linear colours back so they match (the page has no colour management).
- **Music.** Add looping tracks (calm for the voyage, livelier on the islands) in the `audio` section, started after the first click, with the existing mute button.
- **Balance pass** on the voyage and crab fight.
- **Later:** split the single file into modules (Vite) once assets arrive, and add mobile tuning.
