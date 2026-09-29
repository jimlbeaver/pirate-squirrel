# Pirate Squirrel — Browser Game Plan

**Working title:** *Pirate Squirrel: Quest for the Chest Nuts* (interactive)

**Pitch:** Third-person browser game. Play as the pirate squirrel hopping tree → tree, searching for the Chestnut, while avoiding ground dangers.

**Relation to the short film:** Same character world / Look B pirate squirrel energy. Film stays as cinematic canon; this is a playable spin-off, not a film remake.

---

## 1. Is it possible?

**Yes.** Two realistic paths:

| Path | How it works | Pros | Cons |
|------|----------------|------|------|
| **A — Browser-native (recommended start)** | Blender (or AI mesh tools) → export GLB → **Godot 4 Web** or **Three.js / PlayCanvas** | Runs in a normal browser tab; cheap to host; fast iteration | Visuals “game-good,” not Unreal cinematic |
| **B — Unreal → browser** | Blender → Unreal → **Pixel Streaming** | Highest look / lighting | Needs a GPU server streaming video; cost + latency; harder to share casually |

**Recommendation:** Ship a playable loop with **Path A**. Revisit Unreal/Pixel Streaming only if Jim wants film-quality lighting and accepts hosting cost.

---

## 2. Game pieces (what we need)

### Core loop
1. Spawn on a tree / branch safe zone.
2. Move / jump / climb to other trees.
3. **Search** a tree (hold / interact) — may find nothing, bait, or **the Chestnut**.
4. Touching **ground hazards** = fail / respawn (or lose a life).
5. Find Chestnut = win (short victory beat; optional wink callback).

### Player
- Third-person camera (over-shoulder / follow)
- Controllable pirate squirrel (start with capsule/stand-in mesh; swap Look B later)
- Actions: move, jump (tree-to-tree), climb (optional v2), search/interact, pause

### World
- Small **forest clearing** arena (not open world for v1)
- **3–5 searchable trees** with distinct silhouettes
- Safe branch / nest platforms
- Ground = danger zone (mud, fox shadow, lawnmower vibe, or simple “lava” stand-in)
- Optional: nest-ship prop as landmark (visual only in v1)

### Hazards (v1 keep simple)
- Fall-to-ground = damage/fail
- 1 moving ground threat (patrol path)
- Optional: timed “Mom calling” humor beat later (not required for prototype)

### Win / lose
- **Win:** Chestnut found (random among trees or fixed “final” tree after N searches)
- **Lose:** fall / hit hazard (retry from last tree)

### UI
- Minimal: search prompt, “trees searched,” win/lose screens
- Title card energy: *Quest for the Chest Nuts* + Sloppy Beaver end joke optional

### Audio
- Soft bed (reuse film theme snippet under license we already control) or silent prototype
- SFX: jump, land, search rustle, fail, win

---

## 3. Tech stack (proposed)

| Layer | Choice | Why |
|-------|--------|-----|
| Art / modeling | **Blender** (+ optional Meshy/Tripo for draft meshes) | Industry-standard; GLB export |
| Engine (prototype) | **Godot 4** export to HTML5 **or** Three.js + Rapier/Cannon | Browser-friendly; one person can iterate |
| Character anim | Mixamo / Blender rig (later) | Stand-in first |
| Hosting | Static host (GitHub Pages / Cloudflare / simple VPS) | No game server for v1 |
| Later optional | Unreal 5 + Pixel Streaming | Only if we outgrow look quality |

**Explicit non-goals for v1:** multiplayer, inventory RPG, open world, Unreal streaming.

---

## 4. Asset pipeline

1. **Blockout** — greybox trees + capsule squirrel in engine (no art polish).
2. **Hero mesh** — Blender pirate squirrel (Look B: bicorne, LEFT-eye patch, coat) → decimate for web → GLB.
3. **Trees / props** — low-poly oaks, nest platforms, chestnut prop.
4. **Textures** — simple PBR; bake where needed for web perf.
5. **Animations** — idle, run, jump, search dig, celebrate (can start with 2–3).
6. **Swap** stand-in → hero without changing gameplay code.

Film stills/clips are **reference**, not direct game assets (different topology / polycount).

---

## 5. Phased plan

### Phase 0 — Design lock (½ day)
- Confirm Path A (browser-native)
- Lock arena size, tree count, win rule, fail rule
- One-page control map (keyboard + optional touch)

### Phase 1 — Greybox prototype (few days)
- Empty scene + third-person controller
- 3 trees with jump pads / gaps
- Search interact → random loot table (empty / chestnut)
- Ground kill volume
- Win / lose screens
- **Success = fun to hop and search**, ugly OK

### Phase 2 — Art pass 1
- Pirate squirrel hero GLB in-game
- Readable trees + chestnut prop
- Basic lighting / sky
- Jump + search SFX

### Phase 3 — Feel & content
- 5 trees, 1 patrol hazard
- Camera polish, coyote time / jump forgiveness
- Short intro line or title splash
- Shareable web build

### Phase 4 — Optional stretch
- Climbing on trunks
- Nest-ship set piece
- “Sloppy Beaver” end card gag
- Mobile touch controls
- Unreal path evaluation (only if Jim wants)

---

## 6. How we start (first concrete steps)

1. Create project folder: `/workspace/pirate-squirrel-game/` (this file lives here).
2. Pick engine: **Godot 4 Web** (recommended default) *or* Three.js if Jim prefers pure web code.
3. Greybox Phase 1 in engine — no Blender required yet.
4. Parallel track: Blender squirrel draft from film Look B refs in `/workspace/pirate-squirrel/refs/`.
5. Weekly playable drop Jim can open in Chrome.

**Day-1 checklist**
- [ ] Engine choice locked
- [ ] Empty third-person scene runs locally
- [ ] One tree mesh + jump
- [ ] Search key opens “Searching…” then result toast
- [ ] Ground = restart

---

## 7. Risks & decisions

| Risk | Mitigation |
|------|------------|
| Scope creep (Unreal too early) | Greybox in browser first |
| Web performance | Low-poly, few lights, baked where possible |
| Character look ≠ film | Stylized readable silhouette > frame-perfect Pixar |
| Jumping feel hard | Iterate coyote time / sticky landings early |
| Hosting Unreal | Don’t until Path A is fun |

**Open decisions for Jim**
1. Godot vs Three.js for prototype?
2. Win = random Chestnut among trees, or fixed final tree after searching others?
3. Tone: kid-friendly cozy, or slightly slapstick-dangerous?

---

## 8. Folder layout (proposed)

```
pirate-squirrel-game/
  PLAN.md                 ← this file
  DESIGN.md               ← controls, win/lose (later)
  godot/ or web/          ← engine project
  art/
    blender/
    exports/              ← GLB
  refs/                   ← links/copies from film refs
  builds/                 ← web export drops
```

---

## 9. Definition of “done” for first playable

A stranger can open a URL, move the squirrel, jump between at least 3 trees, search trees, die on the ground, and find the Chestnut once — without reading a manual.

---

*Drafted 2026-09-29 for Jim · Pixel*
