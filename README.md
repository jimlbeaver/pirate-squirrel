# Pirate Squirrel: Quest for the Chest Nuts

Browser game prototype spun off from the OFWG Productions pirate squirrel short. Plain three.js, no build step. Each version is a single self-contained HTML file.

| Folder | What it is |
|---|---|
| `v2/` | **Current version.** Home Isle (gear, map, Pirates Only gate), the voyage (energy, nuts, hazards), Treasure Island (crab guards, branch-sign puzzle, treasure chest). |
| `v1/` | First playable greybox, kept as a reference. |
| `refs/` | Concept art: plain squirrel and full pirate gear. |
| `vendor/` | Local copy of three.js r128, used automatically if the CDN is unreachable. |
| `tools/` | Headless smoke test (Playwright) and a Blender asset-pipeline starter script. |
| `PLAN.md` | Original game plan. |
| `DESIGN.md` | How v2 plays, the tuning numbers, and a map of the code. |
| `CLAUDE.md` | Project notes for Claude Code if you continue there. |

## Run it

Opening `v2/index.html` straight from disk works. A local server is better, and you'll need one once GLB assets are loaded (browsers block `fetch` on `file://`):

```bash
cd pirate-squirrel-game
python3 -m http.server 8000
# then open http://localhost:8000/v2/
```

Needs internet for Google Fonts. three.js comes from cdnjs and falls back to `vendor/` offline.

## Put it in a repo

```bash
unzip pirate-squirrel-game.zip
cd pirate-squirrel-game
git init
git add .
git commit -m "Pirate squirrel game: v1 and v2 prototypes"
# with the GitHub CLI:
gh repo create pirate-squirrel-game --private --source=. --push
# or create an empty repo on GitHub, then:
# git remote add origin git@github.com:<you>/pirate-squirrel-game.git
# git push -u origin main
```

To host it as a playable link, turn on GitHub Pages for the repo (Settings → Pages → deploy from branch `main`, root). The game is then at `https://<you>.github.io/pirate-squirrel-game/v2/`.

## Controls (v2)

| Key | Action |
|---|---|
| W / S | Forward / back (always relative to the squirrel) |
| A / D | Turn. Same on the boat. When climbing, move left/right around the trunk |
| Space | Jump. Hold while falling to glide |
| Walk into a trunk | Climb. W up, S down (S near a branch steps onto it), Space leaps off |
| E | Search a hollow, open the gate, board the boat, go ashore, open the chest |
| F | Tail-swipe. Landing on a crab also hits it |
| C | Toggle follow cam / free cam. Drag or arrow keys look around, scroll zooms |
| M | Treasure map (once found) |
| Esc / P | Pause |

Touch: left thumb drags to move and turn, right thumb drags to look, with Jump, Act and Swipe buttons.

## Smoke test

`tools/smoke_test.py` drives the game headlessly through the whole loop (gate, voyage, crabs, puzzle leaps, chest) using the `window.__psq` test hook in the page.

```bash
pip install playwright
playwright install chromium
python3 tools/smoke_test.py            # tests v2/index.html
python3 tools/smoke_test.py v1/index.html --screens-only
```

## Blender pipeline

Blender can be driven from Python, headless:

```bash
# Option A: Blender as a Python module (needs Python 3.11 for bpy 5.x)
pip install bpy
python3 tools/blender/chestnut_demo.py

# Option B: with an installed Blender
blender -b -P tools/blender/chestnut_demo.py
```

The demo builds a chestnut, renders a preview PNG with Cycles and exports `art/exports/chestnut.glb`. Use it as the template for the real assets. The asset plan is in `DESIGN.md`.
