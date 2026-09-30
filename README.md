# Pirate Squirrel: Quest for the Chest Nuts

Browser game prototype spun off from the Sloppy Beaver Productions pirate squirrel short. Plain three.js, no build step. Each version is a single self-contained HTML file.

| Folder | What it is |
|---|---|
| `v2/` | **Current version (2.3).** Home Isle (gear, map, Pirates Only gate), the voyage (energy, nuts, hazards), Treasure Island (crab guards, branch-sign puzzle with decoys, a Komodo dragon below and a hawk above, treasure chest). Blender-built art for the squirrel and his gear, the boat, crabs, sea nuts, chest and Chestnut. |
| `v1/` | First playable greybox, kept as a reference. |
| `refs/` | Concept art: plain squirrel and full pirate gear. |
| `vendor/` | Local copies of three.js r128 and its `GLTFLoader`, used automatically if the CDNs are unreachable. |
| `tools/` | Headless smoke test and review screenshots (Playwright), and the Blender scripts that build every asset. |
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
| W / S or ↑ / ↓ | Forward / back (always relative to the squirrel) |
| A / D or ← / → | Turn. Same on the boat. When climbing, move left/right around the trunk |
| Space | Jump. Hold while falling to glide |
| Walk into a trunk | Climb. W up, S down (S near a branch steps onto it), Space leaps off |
| E | Search a hollow, open the gate, board the boat, go ashore, open the chest |
| F or left click | Tail-swipe. Landing on a crab or the Komodo dragon also hits it; a swipe can bonk a diving hawk |
| C | Toggle follow cam / free cam. Right-drag (or Ctrl + drag) or Shift + arrow keys look around, scroll zooms |
| M | Treasure map (once found) |
| H or ? | Help card with the controls |
| Esc / P | Pause |

Touch: left thumb drags to move and turn, right thumb drags to look, with Jump, Act and Swipe buttons.

## Smoke test

`tools/smoke_test.py` drives the game headlessly through the whole loop (gate, voyage, crabs, puzzle leaps, chest) using the `window.__psq` test hook in the page. It serves the repo over a local HTTP server so GLB assets load, and warns if a GLB in `art/exports/` fell back to its stand-in.

```bash
pip install playwright
playwright install chromium
python3 tools/smoke_test.py            # tests v2/index.html
python3 tools/smoke_test.py v1/index.html --screens-only
python3 tools/screenshots.py            # in-game review shots to art/previews/ingame/
```

## Blender pipeline

Every asset is built by a Blender script, run headless. The scripts use the shared helpers in `tools/blender/psq_common.py`; each writes `art/exports/<name>.glb` and a preview to `art/previews/<name>.png` (gitignored):

```bash
blender -b -P tools/blender/twig_boat.py     # also crab.py, squirrel.py, nuts.py, chest.py; lineup.py renders them all
# Windows: & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b -P tools\blender\twig_boat.py
```

The asset plan and how to swap a GLB in for a stand-in are in `DESIGN.md`. The asset inventory, budgets and style guide are in `ASSETS.md`.
