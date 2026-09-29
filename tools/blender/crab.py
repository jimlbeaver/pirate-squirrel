"""Crab guard and Captain Pinch -> art/exports/crab.glb, art/exports/captain_pinch.glb

  blender -b -P tools/blender/crab.py

Matches `buildCrab()` in v2 (Treasure Island section), authored at the crab's unit scale; the game
scales Captain Pinch's `inner` group by 1.45, so captain_pinch.glb is NOT pre-scaled.

  Crab (root, origin on the ground under the body centre, facing game +z)
    Body    carapace centred at y 0.24 (half-extents 0.42 x 0.2 x 0.32), eyes on stalks, 3 legs a side
    ClawL   pivot at game (+0.3, 0.26, 0.2), the crab's own left; the game rotates it about local x
    ClawR   pivot at game (-0.3, 0.26, 0.2)
    Hat     captain only, pivot at the hat's base so it can pop off when he's beaten

Also renders art/previews/crab_options.png (eye style and shading) and
captain_options.png (hat only vs hat plus one big claw) for the style check.
Geometry is written in game coordinates and converted with G(): game (x, y, z) = Blender (x, -z, y).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import psq_common as C  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import bpy  # noqa: E402

C.reset(seed=11)

SHELL = C.mat("CrabShell", 0xd2502c, rough=0.6)
SHELL_DARK = C.mat("CrabShellDark", 0xa33a20, rough=0.6)
PALE = C.mat("CrabPale", 0xf1b27a, rough=0.8)
EYE = C.mat("EyeWhite", 0xf3f0e6, rough=0.45)
INK = C.mat("Ink", 0x151012, rough=0.45)
FELT = C.mat("HatFelt", 0x151012, rough=0.85)
GOLD = C.mat("Gold", 0xe8b23d, rough=0.35, metal=0.7)

SAND = 0xe8d3a1


def G(x, y, z):
    return Vector((x, -z, y))


def to_game(v):
    return Vector((v.x, v.z, -v.y))


def ellipsoid(name, center, radii, material, segs=(12, 6), fn=None, keep_above=None):
    """UV ellipsoid in game coords. `fn` warps each scaled local point; `keep_above` cuts the unit
    sphere at that game-y and keeps the top (an open dome)."""
    bm = C.bmesh.new()
    C.bmesh.ops.create_uvsphere(bm, u_segments=segs[0], v_segments=segs[1], radius=1.0)
    if keep_above is not None:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        C.bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, keep_above), plane_no=(0, 0, 1), clear_inner=True)
    for v in bm.verts:
        p = to_game(v.co)
        p = Vector((p.x * radii[0], p.y * radii[1], p.z * radii[2]))
        if fn:
            p = fn(p)
        v.co = G(*(Vector(center) + p))
    return C._obj_from_bmesh(name, bm, material)


def tube(name, pts, radius, material, radii=None, sides=1):
    return C.tube(name, [tuple(G(*p)) for p in pts], radius, material, radii, sides=sides)


def tint_tip(obj, material, a, b, frac):
    """Give the faces past `frac` of the way from a to b (game coords) a second material."""
    obj.data.materials.append(material)
    idx = len(obj.data.materials) - 1
    A, B = G(*a), G(*b)
    ab = B - A
    for poly in obj.data.polygons:
        if (poly.center - A).dot(ab) / ab.length_squared > frac:
            poly.material_index = idx
    return obj


def rot(x=0.0, y=0.0, z=0.0):
    return Matrix.Rotation(z, 3, "Z") @ Matrix.Rotation(y, 3, "Y") @ Matrix.Rotation(x, 3, "X")


def surface(obj):
    verts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return BVHTree.FromPolygons(verts, [p.vertices for p in obj.data.polygons])


def hit(bvh, origin, direction):
    loc, nrm, _, _ = bvh.ray_cast(G(*origin), G(*direction))
    return to_game(loc), to_game(nrm)


EYES = {  # eye radius, pupil radius, angry lids, highlight
    "beady": (0.042, 0.03, False, False),
    "cartoon": (0.062, 0.034, True, True),
    "googly": (0.082, 0.032, False, True),
}


def build_body(eyes="cartoon"):
    parts = []

    def shell_warp(p):
        x, y, z = p
        x *= 1 + 0.14 * (z / 0.32)          # wider at the front
        if y < 0:
            y *= 0.55                        # flat belly
        y += 0.035 * math.cos(min(1.0, abs(x) / 0.3) * math.pi / 2) * (y > 0)   # low ridge down the back
        return Vector((x, y, z))

    shell = ellipsoid("Carapace", (0, 0.24, 0), (0.42, 0.2, 0.32), SHELL, segs=(16, 8), fn=shell_warp)
    parts.append(shell)
    bvh = surface(shell)
    parts.append(ellipsoid("Belly", (0, 0.15, 0.02), (0.33, 0.05, 0.25), PALE, segs=(12, 4)))

    for x, z, r in ((-0.15, -0.06, 0.07), (0.14, -0.1, 0.06), (0.0, 0.1, 0.05), (0.2, 0.08, 0.04), (-0.19, 0.12, 0.045)):
        p, _ = hit(bvh, (x, 1, z), (0, -1, 0))
        parts.append(ellipsoid("Spot", p + Vector((0, -0.004, 0)), (r, 0.016, r * 0.85), SHELL_DARK, segs=(8, 3)))

    for s in (-1, 1):   # rim spikes for a spiky silhouette
        for a in (0.95, 1.3):
            d = Vector((s * math.sin(a), 0, math.cos(a)))
            p, _ = hit(bvh, (d.x * 2, 0.27, d.z * 2), (-d.x, 0, -d.z))
            tip = p + d * 0.075 + Vector((0, 0.025, 0.02))
            parts.append(tube("Spike", [p - d * 0.02, tip], 0.028, SHELL, [1, 0.12]))

    mouth = []
    for i in range(7):
        t = -1 + 2 * i / 6
        p, _ = hit(bvh, (0.07 * t, 0.285 + 0.014 * t * t, 1), (0, 0, -1))
        mouth.append(p + Vector((0, 0, 0.006)))
    parts.append(tube("Mouth", mouth, 0.009, INK))

    er, pr, lids, glint = EYES[eyes]
    for s in (-1, 1):
        e = Vector((0.1 * s, 0.46 + er, 0.22))
        parts.append(tube("Stalk", [(0.08 * s, 0.34, 0.18), (0.09 * s, 0.42, 0.2), tuple(e - Vector((0, er * 0.7, 0)))], 0.021, SHELL, [1.15, 1, 0.9]))
        parts.append(ellipsoid("Eye", e, (er, er * 1.12, er), EYE, segs=(12, 8)))
        pc = e + Vector((-0.008 * s, 0.004, er * 0.9))
        parts.append(ellipsoid("Pupil", pc, (pr, pr * 1.12, pr * 0.45), INK, segs=(10, 5)))
        if glint:
            parts.append(ellipsoid("Glint", pc + Vector((0.35 * pr * s, 0.4 * pr, pr * 0.4)), (0.011, 0.011, 0.006), EYE, segs=(6, 3)))
        if lids:
            parts.append(ellipsoid("Lid", e, (er * 1.14, er * 1.2, er * 1.14), SHELL, segs=(12, 6), keep_above=0.1,
                                   fn=lambda p, s=s: rot(z=0.5 * s) @ (rot(x=0.35) @ p)))

    for s in (-1, 1):
        for i, z in enumerate((0.1, -0.03, -0.15)):
            hip = (0.3 * s, 0.21, z)
            knee = (0.5 * s, 0.31, z * 1.25 + 0.01)
            foot = (0.57 * s, 0.0, z * 1.5)
            leg = tube("Leg", [hip, knee, ((knee[0] + foot[0]) / 2, 0.17, (knee[2] + foot[2]) / 2), foot], 0.038, SHELL, [1, 0.85, 0.6, 0.25])
            parts.append(tint_tip(leg, SHELL_DARK, knee, foot, 0.55))
    return C.join_at("Body", parts)


ARM = (0.3, 0.26, 0.2)


def build_claw(s, size=1.0):
    """One claw arm, built around its pivot. `s` = +1 for the crab's left (+x)."""
    P = Vector((ARM[0] * s, ARM[1], ARM[2]))

    def at(x, y, z):
        return tuple(P + Vector((x * s, y, z)) * size)

    parts = [
        ellipsoid("Shoulder", at(0, 0, 0), (0.048 * size,) * 3, SHELL, segs=(8, 5)),
        tube("Forearm", [at(0, 0, 0), at(0.04, 0.0, 0.06), at(0.07, 0.01, 0.1)], 0.042 * size, SHELL, [1, 0.9, 0.95]),
        ellipsoid("Palm", at(0.085, 0.02, 0.14), (0.088 * size, 0.08 * size, 0.1 * size), SHELL, segs=(12, 6)),
    ]
    upper = [at(0.085, 0.06, 0.19), at(0.105, 0.085, 0.3), at(0.09, 0.05, 0.41)]
    lower = [at(0.08, -0.02, 0.19), at(0.09, -0.05, 0.29), at(0.08, -0.04, 0.375)]
    parts.append(tint_tip(tube("Pincer", upper, 0.056 * size, SHELL, [1, 0.75, 0.15], sides=2), PALE, upper[0], upper[-1], 0.62))
    parts.append(tint_tip(tube("Pincer", lower, 0.045 * size, SHELL, [1, 0.75, 0.15], sides=2), PALE, lower[0], lower[-1], 0.62))
    return C.join_at("ClawL" if s > 0 else "ClawR", parts, origin=tuple(G(*P)))


HAT_AT = (0.0, 0.46, -0.05)


def build_hat():
    H = Vector(HAT_AT)
    parts = [ellipsoid("Crown", H + Vector((0, 0.035, 0)), (0.095, 0.11, 0.09), FELT, segs=(12, 6), keep_above=-0.3)]

    N, rings, outer = 36, [], []
    for i in range(N):
        th = 2 * math.pi * i / N
        c = abs(math.cos(1.5 * th)) ** 2          # 1 at the three corners (front, back-left, back-right)
        ro, up = 0.15 + 0.1 * c, 0.015 + 0.11 * (1 - c)
        row = [(0.08, 0.0), ((0.08 + ro) / 2, up * 0.35), (ro, up)]
        rings.append([H + Vector((r * math.sin(th), y, r * math.cos(th))) for r, y in row])
        outer.append(tuple(H + Vector(((ro + 0.004) * math.sin(th), up + 0.004, (ro + 0.004) * math.cos(th)))))
    verts = [G(*p) for ring in rings for p in ring]
    faces = [(i * 3 + j, ((i + 1) % N) * 3 + j, ((i + 1) % N) * 3 + j + 1, i * 3 + j + 1) for i in range(N) for j in range(2)]
    bm = C.bmesh.new()
    vs = [bm.verts.new(v) for v in verts]
    for f in faces:
        bm.faces.new([vs[k] for k in f])
    C.bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.014)
    parts.append(C._obj_from_bmesh("Brim", bm, FELT))
    parts.append(C.tube("Trim", [tuple(G(*p)) for p in outer], 0.011, GOLD, closed=True))

    parts.append(ellipsoid("Skull", H + Vector((0, 0.085, 0.09)), (0.034, 0.031, 0.014), EYE, segs=(8, 4)))
    for d in (-1, 1):
        parts.append(tube("Bone", [H + Vector((-0.04 * d, 0.03, 0.09)), H + Vector((0.04 * d, 0.065, 0.09))], 0.008, EYE))

    hat = C.join_at("Hat", parts, origin=tuple(G(*H)))
    hat.rotation_euler = (0, 0.12, 0)            # a rakish tilt: rolls about game z (Blender y)
    bpy.ops.object.select_all(action="DESELECT")
    hat.select_set(True)
    bpy.context.view_layer.objects.active = hat
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    return hat


def build(root_name, eyes="cartoon", captain=False, big_claw=True, smooth=False, offset=(0, 0, 0)):
    root = bpy.data.objects.new(root_name, None)
    bpy.context.collection.objects.link(root)
    kids = [build_body(eyes), build_claw(1), build_claw(-1, 1.35 if captain and big_claw else 1.0)]
    if captain:
        kids.append(build_hat())
    for k in kids:
        k.parent = root
        if smooth:
            for p in k.data.polygons:
                p.use_smooth = True
    root.location = offset
    return root, kids


def label(text, loc, size=0.16):
    cu = bpy.data.curves.new(text, "FONT")
    cu.body = text
    cu.size = size
    cu.align_x = "CENTER"
    o = bpy.data.objects.new(text, cu)
    o.data.materials.append(INK)
    o.location = loc
    o.rotation_euler = (math.pi / 2, 0, 0)
    bpy.context.collection.objects.link(o)
    return o


CAM = dict(target=tuple(G(-0.03, 0.27, 0.05)), cam_loc=tuple(G(1.1, 1.0, 1.65)), ground=(SAND, 0.0))

for name, captain in (("crab", False), ("captain_pinch", True)):
    C.clear_objects()
    root, kids = build("CaptainPinch" if captain else "Crab", captain=captain)
    C.preview(name, **CAM)
    path = C.export(name, [root] + kids)
    print(f"{name}: {C.tri_count(kids)} triangles -> {path}")

# eye style and shading options, left to right
C.clear_objects()
OPTS = [("A", "beady", False), ("B", "cartoon", False), ("C", "googly", False), ("D", "cartoon", True)]
for i, (tag, eyes, smooth) in enumerate(OPTS):
    x = (i - 1.5) * 1.35
    build(f"Opt{tag}", eyes=eyes, smooth=smooth, offset=(x, 0, 0))
    label(tag, (x, -0.75, 0.02))
C.preview("crab_options", target=(0, 0, 0.2), cam_loc=(0.8, -8.2, 2.4), res=(1600, 560), ground=(SAND, 0.0))

C.clear_objects()
for i, (tag, big) in enumerate((("A", False), ("B", True))):
    x = (i - 0.5) * 1.5
    r, _ = build(f"Cap{tag}", captain=True, big_claw=big, offset=(x, 0, 0))
    r.scale = (1.45,) * 3
    label(tag, (x, -1.0, 0.02))
C.preview("captain_options", target=(0, 0, 0.4), cam_loc=(0.9, -4.6, 1.9), res=(1200, 640), ground=(SAND, 0.0))
print("previews:", C.PREVIEWS)
