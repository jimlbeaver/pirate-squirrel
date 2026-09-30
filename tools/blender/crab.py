"""Crab guard and Captain Pinch -> art/exports/crab.glb, art/exports/captain_pinch.glb

  blender -b -P tools/blender/crab.py

Matches `buildCrab()` in v2 (Treasure Island section), authored at the crab's unit scale; the game
scales Captain Pinch's `inner` group by 1.45, so captain_pinch.glb is NOT pre-scaled.
Characters are smooth-shaded (Jim, round 2); the world stays faceted.

  Crab (root, origin on the ground under the body centre, facing game +z)
    Body    carapace centred at y 0.24 (half-extents 0.42 x 0.2 x 0.32), beady eyes on stalks, 3 legs a side
    ClawL   pivot at game (+0.3, 0.26, 0.2), the crab's own left; the game rotates it about local x
    ClawR   pivot at game (-0.3, 0.26, 0.2); 1.35x on Captain Pinch
    Hat     captain only, pivot at the hat's base so it can pop off when he's beaten
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import psq_common as C  # noqa: E402
from psq_common import G, Vector, ellipsoid, gtube, hit, rot, tint_tip  # noqa: E402

import bpy  # noqa: E402

PAL = {
    "shell": ("CrabShell", 0xd2502c, 0.6), "shell_dark": ("CrabShellDark", 0xa33a20, 0.6),
    "pale": ("CrabPale", 0xf1b27a, 0.8), "eye": ("EyeWhite", 0xf3f0e6, 0.45), "ink": ("Ink", 0x151012, 0.45),
    "felt": ("HatFelt", 0x151012, 0.85), "gold": ("Gold", 0xe8b23d, 0.35, 0.7),
}
SAND = 0xe8d3a1


def M(key):
    return C.mat(*PAL[key])


def build_body():
    parts = []

    def shell_warp(p):
        x, y, z = p
        x *= 1 + 0.14 * (z / 0.32)          # wider at the front
        if y < 0:
            y *= 0.55                        # flat belly
        y += 0.035 * math.cos(min(1.0, abs(x) / 0.3) * math.pi / 2) * (y > 0)   # low ridge down the back
        return Vector((x, y, z))

    shell = ellipsoid("Carapace", (0, 0.24, 0), (0.42, 0.2, 0.32), M("shell"), segs=(16, 8), fn=shell_warp)
    parts.append(shell)
    bvh = C.surface(shell)
    parts.append(ellipsoid("Belly", (0, 0.15, 0.02), (0.33, 0.05, 0.25), M("pale"), segs=(12, 4)))

    for x, z, r in ((-0.15, -0.06, 0.07), (0.14, -0.1, 0.06), (0.0, 0.1, 0.05), (0.2, 0.08, 0.04), (-0.19, 0.12, 0.045)):
        p, _ = hit(bvh, (x, 1, z), (0, -1, 0))
        parts.append(ellipsoid("Spot", p + Vector((0, -0.004, 0)), (r, 0.016, r * 0.85), M("shell_dark"), segs=(8, 3)))

    for s in (-1, 1):   # rim spikes for a spiky silhouette
        for a in (0.95, 1.3):
            d = Vector((s * math.sin(a), 0, math.cos(a)))
            p, _ = hit(bvh, (d.x * 2, 0.27, d.z * 2), (-d.x, 0, -d.z))
            parts.append(gtube("Spike", [p - d * 0.02, p + d * 0.075 + Vector((0, 0.025, 0.02))], 0.028, M("shell"), [1, 0.12]))

    mouth = []
    for i in range(7):
        t = -1 + 2 * i / 6
        p, _ = hit(bvh, (0.07 * t, 0.285 + 0.014 * t * t, 1), (0, 0, -1))
        mouth.append(p + Vector((0, 0, 0.006)))
    parts.append(gtube("Mouth", mouth, 0.009, M("ink")))

    er, pr = 0.042, 0.03    # small beady eyes, mostly pupil
    for s in (-1, 1):
        e = Vector((0.1 * s, 0.46 + er, 0.22))
        parts.append(gtube("Stalk", [(0.08 * s, 0.34, 0.18), (0.09 * s, 0.42, 0.2), tuple(e - Vector((0, er * 0.7, 0)))], 0.021, M("shell"), [1.15, 1, 0.9]))
        parts.append(ellipsoid("Eye", e, (er, er * 1.12, er), M("eye"), segs=(12, 8)))
        parts.append(ellipsoid("Pupil", e + Vector((-0.008 * s, 0.004, er * 0.9)), (pr, pr * 1.12, pr * 0.45), M("ink"), segs=(10, 5)))

    for s in (-1, 1):
        for z in (0.1, -0.03, -0.15):
            hip, knee, foot = (0.3 * s, 0.21, z), (0.5 * s, 0.31, z * 1.25 + 0.01), (0.57 * s, 0.0, z * 1.5)
            leg = gtube("Leg", [hip, knee, ((knee[0] + foot[0]) / 2, 0.17, (knee[2] + foot[2]) / 2), foot], 0.038, M("shell"), [1, 0.85, 0.6, 0.25])
            parts.append(tint_tip(leg, M("shell_dark"), knee, foot, 0.55))
    return C.join_at("Body", parts)


ARM = (0.3, 0.26, 0.2)


def build_claw(s, size=1.0):
    """One claw arm, built around its pivot. `s` = +1 for the crab's left (+x)."""
    P = Vector((ARM[0] * s, ARM[1], ARM[2]))

    def at(x, y, z):
        return tuple(P + Vector((x * s, y, z)) * size)

    parts = [
        ellipsoid("Shoulder", at(0, 0, 0), (0.048 * size,) * 3, M("shell"), segs=(8, 5)),
        gtube("Forearm", [at(0, 0, 0), at(0.04, 0.0, 0.06), at(0.07, 0.01, 0.1)], 0.042 * size, M("shell"), [1, 0.9, 0.95]),
        ellipsoid("Palm", at(0.085, 0.02, 0.14), (0.088 * size, 0.08 * size, 0.1 * size), M("shell"), segs=(12, 6)),
    ]
    upper = [at(0.085, 0.06, 0.19), at(0.105, 0.085, 0.3), at(0.09, 0.05, 0.41)]
    lower = [at(0.08, -0.02, 0.19), at(0.09, -0.05, 0.29), at(0.08, -0.04, 0.375)]
    parts.append(tint_tip(gtube("Pincer", upper, 0.056 * size, M("shell"), [1, 0.75, 0.15], sides=2), M("pale"), upper[0], upper[-1], 0.62))
    parts.append(tint_tip(gtube("Pincer", lower, 0.045 * size, M("shell"), [1, 0.75, 0.15], sides=2), M("pale"), lower[0], lower[-1], 0.62))
    return C.join_at("ClawL" if s > 0 else "ClawR", parts, origin=tuple(G(*P)))


HAT_AT = (0.0, 0.46, -0.05)


def build_hat():
    hat = C.join("Hat", C.tricorne(HAT_AT, M("felt"), M("gold"), M("eye")))
    C.bake_rot(hat, rot(z=-0.12), HAT_AT)       # a rakish tilt
    return C.set_origin(hat, G(*HAT_AT))


def build(root_name, captain=False, smooth=False, offset=(0, 0, 0)):
    root = bpy.data.objects.new(root_name, None)
    bpy.context.collection.objects.link(root)
    kids = [build_body(), build_claw(1), build_claw(-1, 1.35 if captain else 1.0)]
    if captain:
        kids.append(build_hat())
    for k in kids:
        k.parent = root
        for p in k.data.polygons:
            p.use_smooth = smooth
    root.location = offset
    return root, kids


if __name__ == "__main__":
    C.reset(seed=11)
    cam = dict(target=tuple(G(-0.03, 0.27, 0.05)), cam_loc=tuple(G(1.1, 1.0, 1.65)), ground=(SAND, 0.0))
    for name, captain in (("crab", False), ("captain_pinch", True)):
        C.clear_objects()
        root, kids = build("CaptainPinch" if captain else "Crab", captain=captain, smooth=True)
        C.preview(name, **cam)
        path = C.export(name, [root] + kids)
        print(f"{name}: {C.tri_count(kids)} triangles -> {path}")
