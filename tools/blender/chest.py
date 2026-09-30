"""Treasure chest -> art/exports/chest.glb

  blender -b -P tools/blender/chest.py

Matches the `chest` group in v2's treasure section: origin at the bottom centre, lock on +z.
  Chest (root)
    ChestBody   planked box 0.62 x 0.36 x 0.42 on y = 0, open at the top with a dark lining and a
                few coins inside; gold bands at y 0.06 and 0.31, gold corner caps, lock plate at
                (0, 0.3, 0.225) in `ChestLock` (the game pulses its emissive)
    Lid         half-cylinder of radius 0.21 along x, origin on the back hinge at (0, 0.36, -0.21);
                the game opens it with rotation.x 0 -> -1.9 (up and back). The hasp is ChestLock too
Preview: art/previews/chest.png (closed and open).
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import psq_common as C  # noqa: E402
from psq_common import G, Matrix, Vector, ellipsoid, gtube, rot, to_game  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402

PAL = {
    "wood": ("ChestWood", 0x7a4a26, 0.85), "wood_dark": ("ChestWoodDark", 0x5a3419, 0.9),
    "gold": ("ChestGold", 0xe8b23d, 0.35, 0.7), "lock": ("ChestLock", 0xe8b23d, 0.35, 0.7),
    "inside": ("ChestInside", 0x2a170c, 1.0), "keyhole": ("Keyhole", 0x151012, 0.6),
}
SAND = 0xe8d3a1
W, H, D = 0.62, 0.36, 0.42        # body width (x), height (y), depth (z)
WALL, FLOOR, GAP = 0.035, 0.04, 0.008
R, STAVES, END = 0.21, 6, 0.03    # lid radius, planks round the lid, end-panel thickness
HINGE = (0, H, -D / 2)


def M(key):
    return C.mat(*PAL[key])


def solid(name, bm, key, R_=None, at=(0, 0, 0)):
    """Object from a bmesh built in local game coords, turned by game matrix R_ and moved to `at`."""
    R_ = R_ or Matrix.Identity(3)
    for v in bm.verts:
        v.co = G(*(Vector(at) + R_ @ to_game(v.co)))
    bm.normal_update()
    return C._obj_from_bmesh(name, bm, M(key))


def gbox(name, centre, size, key, R_=None):
    """Box with full extents `size` (game x, y, z) centred on `centre`."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[2], v.co.z * size[1]))
    return solid(name, bm, key, R_, centre)


def disc(name, centre, radius, depth, key, R_=None, segs=8):
    """Short cylinder along game y (coins, the hasp's hinge pin)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=radius, radius2=radius, depth=depth)
    return solid(name, bm, key, R_, centre)


def wonk(a):
    return random.uniform(-a, a)


# ---------------------------------------------------------------- body

def planks():
    """Three rows of slightly wonky planks per wall; the gaps show the dark lining behind."""
    parts, h = [], H / 3
    for i in range(3):
        y = h * (i + 0.5)
        for s in (-1, 1):
            parts.append(gbox("Plank", (wonk(0.004), y + wonk(0.003), s * (D - WALL) / 2 + wonk(0.003)),
                              (W, h - GAP, WALL), "wood", rot(x=wonk(0.03), y=wonk(0.006), z=wonk(0.02))))
            parts.append(gbox("Plank", (s * (W - WALL) / 2 + wonk(0.003), y + wonk(0.003), wonk(0.004)),
                              (WALL, h - GAP, D - 2 * WALL), "wood", rot(x=wonk(0.025), y=wonk(0.006), z=wonk(0.03))))
    return parts


def lining():
    """Open-topped box facing inward, just inside the walls."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    iw, ih, idp = W - 2 * WALL, H - FLOOR - 0.004, D - 2 * WALL
    for v in bm.verts:
        v.co = Vector((v.co.x * iw, v.co.y * idp, v.co.z * ih))
    bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.5], context="FACES")
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    return solid("Lining", bm, "inside", at=(0, FLOOR + ih / 2, 0))


def band(y, h=0.05, t=0.02):
    """A gold band round the body, 0.64 x 0.44 outside, hollow so it doesn't fill the chest."""
    ow, od = W + 0.02, D + 0.02
    return [gbox("Band", (0, y, s * (od - t) / 2), (ow, h, t), "gold") for s in (-1, 1)] + \
           [gbox("Band", (s * (ow - t) / 2, y, 0), (t, h, od - 2 * t), "gold") for s in (-1, 1)]


def coins():
    parts = [ellipsoid("Hoard", (0, FLOOR, 0), (0.22, 0.12, 0.13), M("gold"), segs=(10, 4), keep_above=0.0)]
    for x, z in ((-0.12, 0.05), (0.05, -0.06), (0.16, 0.04), (-0.02, 0.08), (0.1, -0.02), (-0.15, -0.06)):
        y = FLOOR + 0.12 * math.sqrt(max(0.0, 1 - (x / 0.22) ** 2 - (z / 0.13) ** 2)) + 0.004
        parts.append(disc("Coin", (x, y, z), 0.034, 0.008, "gold", rot(x=wonk(0.5), z=wonk(0.5))))
    return parts


def build_body():
    parts = planks() + band(0.06) + band(0.31) + coins() + [
        gbox("Floor", (0, FLOOR / 2, 0), (W - 0.01, FLOOR, D - 0.01), "wood_dark"),
        lining(),
        gbox("LockPlate", (0, 0.3, 0.225), (0.1, 0.12, 0.03), "lock"),
        ellipsoid("Keyhole", (0, 0.276, 0.24), (0.016, 0.016, 0.004), M("keyhole"), segs=(8, 4)),
        gbox("Keyhole", (0, 0.262, 0.2405), (0.014, 0.03, 0.004), "keyhole"),
    ]
    for sx in (-1, 1):
        for sz in (-1, 1):
            for y in (0.035, H - 0.035):
                parts.append(gbox("Corner", (sx * W / 2, y, sz * D / 2), (0.07, 0.07, 0.07), "gold",
                                  rot(x=wonk(0.04), y=wonk(0.04), z=wonk(0.04))))
    return C.join("ChestBody", parts)


# ---------------------------------------------------------------- lid

def arc(a, r):
    """Point on the lid's cross-section: a = 0 at the front edge, pi at the hinge."""
    return Vector((0, H + r * math.sin(a), r * math.cos(a)))


def staves():
    parts, half = [], math.pi / (2 * STAVES)
    for i in range(STAVES):
        am = (2 * i + 1) * half + wonk(0.015)
        centre = arc(am, R * math.cos(half) - 0.015 + wonk(0.003))
        parts.append(gbox("Stave", centre, (W - 2 * END, 0.03, 2 * R * math.sin(half) * 0.97), "wood",
                          rot(x=math.pi / 2 - am) @ rot(y=wonk(0.01))))
    return parts


def end_panel(x0, x1):
    bm = bmesh.new()
    rings = [[bm.verts.new(G(x, *arc(math.pi * k / STAVES, R - 0.002).yz)) for k in range(STAVES + 1)] for x in (x0, x1)]
    for ring in rings:
        bm.faces.new(ring)
    for k in range(STAVES + 1):
        a, b = rings[0][k], rings[0][(k + 1) % (STAVES + 1)]
        bm.faces.new((a, b, rings[1][(k + 1) % (STAVES + 1)], rings[1][k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return C._obj_from_bmesh("LidEnd", bm, M("wood_dark"))


def strap(x, w=0.05):
    """Gold strap over the lid, following the stave corners."""
    bm = bmesh.new()
    st = [[bm.verts.new(G(x + dx, *arc(math.pi * k / STAVES, r).yz)) for dx, r in
           ((-w / 2, R - 0.004), (w / 2, R - 0.004), (w / 2, R + 0.016), (-w / 2, R + 0.016))] for k in range(STAVES + 1)]
    for k in range(STAVES):
        for j in range(4):
            bm.faces.new((st[k][j], st[k][(j + 1) % 4], st[k + 1][(j + 1) % 4], st[k + 1][j]))
    bm.faces.new(st[0])
    bm.faces.new(st[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return C._obj_from_bmesh("Strap", bm, M("gold"))


def build_lid():
    parts = staves() + [end_panel(s * (W / 2 - END), s * W / 2) for s in (-1, 1)] + [strap(-0.19), strap(0.19)] + [
        gbox("LidInside", (0, H + 0.008, 0), (W - 2 * END, 0.012, 2 * R - 0.03), "inside"),
        gbox("Hasp", (0, 0.35, 0.247), (0.055, 0.09, 0.014), "lock"),
        gtube("HaspPin", [(-0.035, 0.392, 0.226), (0.035, 0.392, 0.226)], 0.016, M("lock"), sides=1),
    ]
    return C.join_at("Lid", parts, origin=tuple(G(*HINGE)))


def build():
    root = bpy.data.objects.new("Chest", None)
    bpy.context.collection.objects.link(root)
    kids = [build_body(), build_lid()]
    for k in kids:
        k.parent = root
    return root, kids


if __name__ == "__main__":
    C.reset(seed=23)
    root, kids = build()
    path = C.export("chest", [root] + kids)
    print(f"chest: {C.tri_count(kids)} triangles (lid {C.tri_count(kids[1:])}) -> {path}")
    shots = []
    for name, lid, cam in (("chest_closed", 0.0, (0.95, 0.75, 1.25)), ("chest_open", -1.9, (0.6, 1.25, 1.05))):
        kids[1].rotation_euler.x = lid           # game rotation.x is rotation about Blender x
        C.preview(name, target=tuple(G(0, 0.26, 0)), cam_loc=tuple(G(*cam)), size=720, ground=(SAND, 0.0))
        shots.append(C.PREVIEWS / f"{name}.png")
    C.contact_sheet(C.PREVIEWS / "chest.png", shots, cols=2)
    print("preview:", C.PREVIEWS / "chest.png")
