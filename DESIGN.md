# Design notes: v2

Everything lives in `v2/index.html`: CSS and HUD markup at the top, then one script organized in commented sections (`/* ===== name ===== */`). The version shown on the title screen and in the tab comes from `VERSION` (currently `2.2`) near the top of `init`.

## How a run plays

1. **Home Isle.** You start on a branch of the home oak as a plain squirrel. Six tree hollows hold four items (eye patch, coat, hat, treasure map) and two junk finds. Contents are decided when you search: the first hollow always gives an item, and later ones use `items left / hollows left` odds, so you can never run out before finding everything. Items come in the order patch → coat → hat → map. Two of the six trees (`h1`, `h4`, flagged `slick`) are mossy up to their lowest branch: you can't climb them from the ground, only by leaping onto one of their branches from a neighbouring tree and climbing from there. The other four climb from anywhere.
2. **Pirates Only gate.** The dock has a gate with a "Pirates ONLY" sign. It opens by itself when you arrive with all four items; otherwise it lists what's missing. While it's shut, the dock beyond it doesn't count as solid ground, so jumping or gliding around the gate just drops you in the sea. Boarding the boat also requires the map.
3. **Voyage.** Energy drains while sailing, faster at speed. Floating nuts refill it. Hazards cost energy: rocks, circling shark fins, drifting logs, and whirlpools that pull, spin and drain. At 0 energy the tide carries you back to the dock with energy full and the nuts restored. On first landfall, energy is topped up to at least 70.
4. **Crab guards.** A bramble hedge rings the island's grove, with one gap barricaded by four crabs (Captain Pinch has a hat and more HP). Crabs chase you on the ground and pinch for energy. Tail-swipe (F) or land on them. Beaten crabs drop nuts. When the last one falls, the barricade collapses. At 0 energy you wake up back on the beach at 70.
5. **Branch puzzle.** Only the rope-wrapped tree can be climbed from the ground. Mossy bark is too slick to climb. The path is rope tree → A → B → C → treasure tree, four leaps across three middle trees, running counterclockwise around the grove seen from above. Each chain tree has three or four launch branches with carved sign plaques, exactly one of them true. There are eight signs (anchor, skull, star, moon, shell, compass, parrot, key); the map shows which to take on each tree, reshuffled every game. The wrong launches are rotten and snap when you stand on them:
   - At least one decoy per tree wears another tree's true sign ("right sign, wrong tree"), so matching a sign isn't enough; you need the one for the tree you're on.
   - Some decoys skip ahead along the ring (S→B, A→Cc, B→T, Cc→A). Decoys aimed at the two off-path trees D and E meet a rotten signed branch there, so they look like real bridges. D and E stay unclimbable.
   - Arrival branches (where a true leap lands) carry their own tree's true sign. They hold.
   - Trunks can't be climbed above their highest branch, and later trees' branches are higher, so gliding can't skip steps.
6. **Komodo dragon.** It dozes at the treasure tree's base until you first get up into the grove, then prowls the floor below you, staying about 1.5 off. The first time you're on the grove floor after that (a rotten branch, a missed leap, the hawk), it chases after a 0.6 s grace: slower than you, but it hisses and lunges when close. A bite costs 20 energy and knocks you back, with a moment of invulnerability. A tail-swipe or a stomp stuns it for 1.5 s; it can't be stunned again for another second (it just flinches), and it can't be beaten. It never climbs, stays inside the brambles, and gives up as soon as you're on a branch or a trunk. The escape is running back to the rope tree. It resets on knockout. The map marks it: "Here be dragons".
7. **Hawk.** Stand still on a grove branch for 5 s (not moving, not turning) and a hawk screeches and circles in front of you, sinking as it winds up. 1.5 s later it makes one straight dive at where you are. A hit knocks you sideways off the branch with no glide (−5 energy, feathers), usually to the Komodo. Moving, leaping or climbing makes it miss, and a tail-swipe as it arrives bonks it away. Either way it leaves and the idle timer starts over. Never on the nest or Home Isle.
8. **Treasure.** Climb the treasure tree to the nest, open the chest, and the Chestnut rises out. A card reads "Congratulations on your efforts... you get all D's." Two seconds later "DEEZ NUTS!!!!" slams in, shaking (a gentle throb under reduced motion), then the win screen shows time, splashes, nuts eaten and crabs beaten.

## Skill levels

Easy or Normal, picked on the title card or the help card (H / ?). Normal is the default, and the choice is remembered in `localStorage` (`psq.skill`). The HUD shows the current level next to the timer. Everything comes from the `SKILL` table at the top of the `Komodo dragon` section:

| | Normal | Easy |
|---|---|---|
| Crab speed (chase 2.3, wander 1.0) | ×1 | ×0.6 |
| Komodo speed (prowl, chase, lunge) | ×1 (2.5, 4.0, 7.0) | ×0.6 (1.5, 2.4, 4.2) |
| Komodo bite | −20 | −10 |
| Hawk idle time before it comes | 5 s | 10 s |
| Hawk warning before the dive | 1.5 s | 2.2 s |
| Hawk dive speed | 13 | 7.5 |
| Sign hint | none | the true launch sign on each grove tree gets a soft gold glow and a slight warm tint |

The hint only marks the four true launches (`chain >= 0`). Decoys, D and E, and the arrival branches that carry the same sign stay plain, so you still check the map. Switching level mid-run takes effect at once.

## Movement rules

- Tank controls everywhere: W/S (or ↑/↓) along the squirrel's facing, A/D (or ←/→) turn. Shift + arrows looks around instead. Follow cam sits behind him, and dragging switches to free cam. H or ? opens a help card with the controls and pauses.
- You can't walk off branches, the dock or the nest. Movement is clamped to the platform, so you leave only by jumping, or by climbing via the trunk. The one deliberate exception is the hawk: a telegraphed knock-off with a clear way to avoid it (keep moving). Branch edge clamping itself is unchanged.
- Leaps from a branch toward its partner branch on the next tree get aim assist (`assistFor`), active within about 40° of the right direction. Rotten branches never get it, and it never steers toward one.
- Anything between the camera and the squirrel fades to see-through (`updateOcclusion`). This covers leaves, trunks, branches, moss and rope.
- Grabbing trunks (`canGrab`): Home Isle trees from anywhere at or above their climb start, except the slick ones, which only from their own branch. Grove trees only while standing on one of their own branches, or from the ground for the rope tree. Never from mid-air in the grove.
- The treasure map is north-up. Facing north (+z), the world's +x is on your left, so the map draws x right-to-left.

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
| Grove layout | `arcPt()` tree positions, `GROVE_LINKS` branch heights and decoys | `trees` |
| Komodo speeds | prowl 2.5, chase 4.0, lunge 7.0 for 0.4 s | `KOMODO` |
| Komodo lunge | within 3.2, 0.35 s hiss first, 0.6 s recovery, 2 s cooldown | `KOMODO` |
| Komodo grace, stun | 0.6 s after you land; stun 1.5 s, then 1 s before it can be stunned again | `KOMODO` |
| Komodo bite | −20 (Easy −10), knockback 6, 1.3 s between bites | `SKILL`, `KOMODO` |
| Hawk trigger | 5 s still on a grove branch; 1.5 s warning (Easy 10 s, 2.2 s) | `SKILL` |
| Hawk dive | speed 13 (Easy 7.5), hit radius 0.8, knock 5.5 sideways + 3.5 up, −5 | `SKILL`, `HAWK` |
| Hawk swipe window | within 2.2 of the squirrel during the dive | `HAWK` |
| Win pop-up | line at 1.6 s, DEEZ NUTS at 3.6 s, tally at 6.2 s | `GAG_AT` |

Balance hasn't been play-tested by hand yet. The voyage energy budget is the first thing to tune.

## World layout

- Home Isle is centered at (0, 0), radius about 12.5. The dock points out at 60° from its center.
- Treasure Island is centered at `C = (6, 200)`, radius about 19. The hedge ring has radius 12, with its gap to the south facing the landing beach.
- Terrain is analytic (`islandH`, `terrainY`), so meshes and physics use the same function.

## Code map (section → what's in it)

`utils` · `renderer / scene` · `water` (animated plane that follows the camera) · `materials` · `assets` (`swapIn` loads `art/exports/<name>.glb` over a stand-in group and keeps the stand-in on any failure) · `symbols` (sign paths shared by the canvas plaques and the SVG map) · `islands / terrain` · `trees` (trees, branches as box platforms, moss bands) · `treasure tree nest, flag, chest` · `Home Isle hollows` · `pier + Pirates Only gate` · `voyage` · `Treasure Island` (hedge, barricade, crabs) · `boat` · `squirrel` (primitive rig; gear pieces toggle on) · `scenery` · `particles` · `audio` (WebAudio synthesized SFX) · `UI` · `game state` · `camera + input` · `the treasure map (SVG)` · `physics helpers` · `player step` · `crabs` · `Komodo dragon (grove floor)` · `hawk (Treasure Island branches)` · `skill level` (Easy/Normal picker, sign glow) · `interactions` · `objectives` · `animation` · `camera` (follow/free, occlusion fade) · `main loop` · `boot + hot-reload state`.

`window.__psq` at the bottom is a small test hook (teleport, step the simulation, press keys, read state) used by `tools/smoke_test.py`. It's harmless to ship, and easy to delete.

## Next steps

- **Assets.** Replace the primitive stand-ins with GLBs made in Blender. Done: the twig boat (`tools/blender/twig_boat.py`, oak-leaf sail, pinecone masthead). Next: crab and Captain Pinch, then chest and chestnut, the tree kit (trunk, branch, canopy, moss, rope, sign plaque), dock and gate, the Komodo dragon and the hawk, then the hero squirrel. For the squirrel, the plan is an image-to-3D draft from `refs/`, cleaned up and cut down for the web, rigged, with gear pieces as separate meshes.
  - To swap an asset in: build the stand-in into its own group, then call `swapIn('<name>', parent, standInGroup)`. The GLB must share the stand-in's origin, size and facing (+z forward in game, -Y in Blender).
  - `GLTFLoader` r128 comes from jsdelivr with a fallback to `vendor/GLTFLoader.r128.js`. GLBs only load over HTTP; opened from `file://` the game quietly keeps the stand-ins.
  - Asset colours are authored as the game's hex values; the loader converts glTF's linear colours back so they match (the page has no colour management).
- **Music.** Add looping tracks (calm for the voyage, livelier on the islands) in the `audio` section, started after the first click, with the existing mute button.
- **Balance pass** on the voyage and crab fight.
- **Later:** split the single file into modules (Vite) once assets arrive, and add mobile tuning.
