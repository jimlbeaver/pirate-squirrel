# Project notes for Claude

- The game is a single-file three.js r128 page: `v2/index.html` is current and `v1/` is a frozen reference, so don't edit v1.
- No build step. Serve with `python3 -m http.server` and open `/v2/`.
- Read `DESIGN.md` first: gameplay rules, tuning numbers and the code-section map.
- Coordinates: y is up, the squirrel faces +z at rotation 0, facing angle = `atan2(dx, dz)`.
- Platforms (branches, dock, nest) are `{kind:'box'|'disc', …}` objects in `platforms`; terrain is analytic via `terrainY(x, z)`.
- After changes, run `python3 tools/smoke_test.py` and check it reports no page errors.
- Assets go in `art/` (Blender scripts in `tools/blender/`, exports in `art/exports/*.glb`).
