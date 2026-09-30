"""Hero squirrel: low-poly, rigged, with Idle / Run / Jump clips -> art/exports/squirrel.glb

  blender -b -P tools/blender/squirrel.py

Matches `buildSquirrel()` in v2: origin between the feet, facing game +z, body ~0.8 tall with ears
and tail tip at ~0.95-1.05. One skinned mesh (`SquirrelBody`) on a 17-bone armature (`Squirrel`),
plus rigid gear nodes parented to bones so `equip()` can toggle them by name:
  Ears (Head)  Patch (Head, over the LEFT eye = +x)  Hat (Head)
  Coat (Hips) + CoatSleeveL / CoatSleeveR (arm bones)  Map (Hips)
Clips are in place (the game moves the squirrel): Idle (2 s loop), Run (0.5 s loop), Jump (0.67 s,
play once and clamp), Glide (1 s loop), Climb (0.5 s loop), Swipe (0.29 s, once), Celebrate (1 s loop).
Smooth-shaded, like all the characters. Renders: art/previews/squirrel.png, squirrel_gamecam.png (follow
camera), squirrel_run.png, squirrel_jump.png, squirrel_idle.png, squirrel_clips.png (contact sheets) and
squirrel_run.mp4 / squirrel_jump.mp4.
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import psq_common as C  # noqa: E402
from psq_common import G, Matrix, Vector, ellipsoid, gtube, hit, rot, smoothstep, to_game  # noqa: E402

import bpy  # noqa: E402

FPS = 24
PAL = {
    "fur": ("Fur", 0xd4622a, 1.0), "fur_light": ("FurLight", 0xe3813f, 1.0), "cream": ("Cream", 0xf5e6cf, 1.0),
    "tail_tip": ("TailTip", 0xf1b27a, 1.0), "nose": ("Nose", 0xd98c86, 0.6), "ink": ("Ink", 0x151012, 0.45),
    "white": ("White", 0xf3f0e6, 0.45), "coat": ("Coat", 0x7a3421, 0.9), "leather": ("Leather", 0x4a2c1a, 0.8),
    "gold": ("Gold", 0xe8b23d, 0.35, 0.7), "red": ("Red", 0xb3261e, 0.8), "felt": ("HatFelt", 0x151012, 0.85),
    "paper": ("Paper", 0xe9d6a6, 0.9),
}


def M(key):
    return C.mat(*PAL[key])


# swept low and back so the follow camera sees the head, hat and coat over it; the tip curls away from the head
TAIL = [(0, 0.15, -0.16), (0, 0.19, -0.38), (0, 0.3, -0.58), (0, 0.46, -0.7), (0, 0.6, -0.74), (0, 0.69, -0.68)]
BONES = [  # name, head, tail (game coords), parent
    ("Hips", (0, 0.17, 0), (0, 0.32, 0), None),
    ("Spine", (0, 0.32, 0), (0, 0.46, 0.01), "Hips"),
    ("Chest", (0, 0.46, 0.01), (0, 0.54, 0.02), "Spine"),
    ("Head", (0, 0.54, 0.02), (0, 0.8, 0.03), "Chest"),
]
for _s, _side in ((1, "L"), (-1, "R")):
    BONES += [
        ("Arm" + _side, (0.14 * _s, 0.47, 0.04), (0.17 * _s, 0.31, 0.12), "Chest"),
        ("Thigh" + _side, (0.1 * _s, 0.21, 0.0), (0.11 * _s, 0.1, 0.035), "Hips"),
        ("Shin" + _side, (0.11 * _s, 0.1, 0.035), (0.1 * _s, 0.035, 0.0), "Thigh" + _side),
        ("Foot" + _side, (0.1 * _s, 0.035, 0.0), (0.1 * _s, 0.02, 0.15), "Shin" + _side),
    ]
BONES += [(f"Tail{i + 1}", TAIL[i], TAIL[i + 1], "Hips" if i == 0 else f"Tail{i}") for i in range(5)]

HEAD_C, HEAD_R = Vector((0, 0.64, 0.03)), (0.165, 0.15, 0.155)


# ---------------------------------------------------------------- skinning helpers

def skin(obj, fn):
    """Weight every vertex by fn(game point) -> {bone: weight}."""
    for v in obj.data.vertices:
        for b, w in fn(to_game(v.co)).items():
            if w > 1e-3:
                vg = obj.vertex_groups.get(b) or obj.vertex_groups.new(name=b)
                vg.add([v.index], w, "REPLACE")
    return obj


def rigid(bone):
    return lambda p: {bone: 1.0}


def torso_w(p):
    a, b = smoothstep(0.26, 0.4, p.y), smoothstep(0.44, 0.52, p.y)
    return {"Hips": 1 - a, "Spine": a * (1 - b), "Chest": a * b}


def torso_r(y):
    """Half-width of the torso at height y (matches the Torso ellipsoid and its pear warp)."""
    t = (y - 0.3) / 0.25
    k = 1 + 0.15 * max(0.0, -t) - 0.1 * max(0.0, t)
    return 0.19 * k * math.sqrt(max(0.0, 1 - t * t))


def aim(d):
    """Rotation taking game +z to direction d."""
    return Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix()


# ---------------------------------------------------------------- model

def build_body():
    parts = []

    def pear(p):
        t = p.y / 0.25
        k = 1 + 0.15 * max(0.0, -t) - 0.1 * max(0.0, t)
        return Vector((p.x * k, p.y, p.z * k))

    parts.append(skin(ellipsoid("Torso", (0, 0.3, -0.01), (0.19, 0.25, 0.17), M("fur"), segs=(14, 8), fn=pear), torso_w))
    parts.append(skin(ellipsoid("Belly", (0, 0.28, 0.075), (0.13, 0.19, 0.1), M("cream"), segs=(12, 6)), torso_w))

    head = ellipsoid("Head", HEAD_C, HEAD_R, M("fur"), segs=(14, 9),
                     fn=lambda p: Vector((p.x * (1.08 if p.y < 0 else 1.0), p.y, p.z)))
    bvh = C.surface(head)
    parts += [
        head,
        ellipsoid("Muzzle", (0, 0.595, 0.125), (0.095, 0.065, 0.07), M("cream"), segs=(12, 6)),
        ellipsoid("Nose", (0, 0.618, 0.193), (0.026, 0.02, 0.018), M("nose"), segs=(8, 4)),
    ]
    for s in (-1, 1):
        d = Vector((0.5 * s, 0.24, 0.83)).normalized()
        p, _ = hit(bvh, HEAD_C + d * 0.5, -d)
        R = aim(d)
        parts += [
            ellipsoid("EyeRing", p - d * 0.012, (0.056, 0.066, 0.02), M("cream"), segs=(12, 6), fn=lambda q, R=R: R @ q),
            ellipsoid("Eye", p - d * 0.004, (0.044, 0.054, 0.026), M("ink"), segs=(12, 6), fn=lambda q, R=R: R @ q),
            ellipsoid("Glint", p + R @ Vector((0.014 * s, 0.022, 0.02)), (0.012, 0.012, 0.006), M("white"), segs=(6, 3)),
        ]
    for part in parts[2:]:
        skin(part, rigid("Head"))

    for s, side in ((1, "L"), (-1, "R")):
        arm = [(0.13 * s, 0.47, 0.05), (0.175 * s, 0.39, 0.09), (0.16 * s, 0.315, 0.13)]
        parts.append(skin(gtube("Arm", arm, 0.042, M("fur"), [1, 0.85, 0.8], sides=2), rigid("Arm" + side)))
        parts.append(skin(ellipsoid("Paw", (0.15 * s, 0.295, 0.14), (0.04, 0.035, 0.042), M("fur_light"), segs=(8, 5)), rigid("Arm" + side)))
        parts.append(skin(ellipsoid("Haunch", (0.11 * s, 0.17, 0.0), (0.085, 0.1, 0.11), M("fur"), segs=(10, 6)), rigid("Thigh" + side)))
        parts.append(skin(gtube("Shin", [(0.11 * s, 0.12, 0.03), (0.1 * s, 0.04, 0.0)], 0.036, M("fur"), sides=2), rigid("Shin" + side)))
        parts.append(skin(ellipsoid("Foot", (0.1 * s, 0.028, 0.07), (0.05, 0.028, 0.1), M("fur_light"), segs=(10, 5)), rigid("Foot" + side)))

    # the bushy tail: overlapping lumpy puffs, two per tail bone, lighter toward the tip
    random.seed(5)
    radii = [0.09, 0.12, 0.14, 0.145, 0.125]
    for i in range(5):
        a, b = Vector(TAIL[i]), Vector(TAIL[i + 1])
        for j, f in enumerate((0.3, 0.8)):
            c = a.lerp(b, f)
            r = radii[i] * (0.9 + 0.1 * j)
            key = "fur" if i == 0 else "tail_tip" if i == 4 and j == 1 else "fur_light"
            puff = ellipsoid("Puff", c, (r * 0.8, r, r), M(key), ico=2, jitter=0.07)
            parts.append(skin(puff, rigid(f"Tail{i + 1}")))
    tip = Vector(TAIL[-1]) + Vector((0, 0.03, -0.05))
    parts.append(skin(ellipsoid("Curl", tip, (0.07, 0.08, 0.09), M("tail_tip"), ico=2, jitter=0.07), rigid("Tail5")))
    return C.join("SquirrelBody", parts)


def build_ears():
    parts = []
    for s in (-1, 1):
        pts = [(0.085 * s, 0.74, 0.0), (0.105 * s, 0.84, -0.01), (0.12 * s, 0.93, -0.025)]
        parts.append(C.tint_tip(gtube("Ear", pts, 0.048, M("fur"), [1, 0.6, 0.12], sides=2), M("fur_light"), pts[0], pts[-1], 0.7))
        parts.append(ellipsoid("InnerEar", (0.098 * s, 0.8, 0.028), (0.024, 0.045, 0.01), M("cream"), segs=(8, 4),
                               fn=lambda q, s=s: rot(z=-0.2 * s) @ q))
    return C.join("Ears", parts)


def eye_point(s):
    head = ellipsoid("HeadProbe", HEAD_C, HEAD_R, M("fur"), segs=(14, 9),
                     fn=lambda p: Vector((p.x * (1.08 if p.y < 0 else 1.0), p.y, p.z)))
    d = Vector((0.5 * s, 0.24, 0.83)).normalized()
    p, _ = hit(C.surface(head), HEAD_C + d * 0.5, -d)
    bpy.data.objects.remove(head)
    return p, d


def build_patch():
    p, d = eye_point(1)          # the squirrel's LEFT eye (+x)
    parts = [ellipsoid("PatchDisc", p + d * 0.02, (0.058, 0.066, 0.012), M("ink"), segs=(12, 4), fn=lambda q: aim(d) @ q)]
    # the strap runs up from the patch, over the forehead above the right eye, and round the back
    thp = math.atan2(p.x, p.z - HEAD_C.z)
    b = (0.78 - p.y) / (1 + math.sin(thp))
    strap = []
    for i in range(24):
        th = 2 * math.pi * i / 24
        y = 0.78 - b - b * math.sin(th)
        t = (y - HEAD_C.y) / HEAD_R[1]
        r = 0.168 * math.sqrt(max(0.3, 1 - t * t)) + 0.012
        strap.append((r * math.sin(th), y, HEAD_C.z + r * math.cos(th)))
    parts.append(gtube("Strap", strap, 0.009, M("ink"), closed=True))
    return C.join("Patch", parts)


HAT_AT = (0, 0.755, -0.01)


def build_hat():
    hat = C.join("Hat", C.tricorne(HAT_AT, M("felt"), M("gold"), M("white"), size=1.15, band=M("red")))
    return C.bake_rot(hat, rot(x=-0.15, z=0.06), HAT_AT)


def coat_r(y):
    return max(torso_r(y) + 0.025, 0.16 + 0.07 * ((0.46 - y) / 0.32) ** 2)


def build_coat():
    ys = [0.46, 0.4, 0.33, 0.26, 0.2, 0.14]
    th0, N = 0.55, 16
    bm = C.bmesh.new()
    grid = []
    for y in ys:
        r = coat_r(y)
        row = []
        for i in range(N + 1):
            th = th0 + (2 * math.pi - 2 * th0) * i / N
            row.append(bm.verts.new(G(r * math.sin(th), y, -0.01 + 0.92 * r * math.cos(th))))
        grid.append(row)
    for a, b in zip(grid, grid[1:]):
        for i in range(N):
            bm.faces.new([a[i], a[i + 1], b[i + 1], b[i]])
    C.bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=-0.014)
    parts = [C._obj_from_bmesh("CoatSkirt", bm, M("coat"))]
    parts.append(gtube("Collar", [(0.17 * math.sin(t), 0.475, -0.01 + 0.15 * math.cos(t))
                                  for t in (0.5 + (2 * math.pi - 1.0) * i / 14 for i in range(15))], 0.03, M("coat")))
    yb = 0.25
    rb = coat_r(yb) + 0.012
    parts.append(gtube("Belt", [(rb * math.sin(t), yb, -0.01 + 0.92 * rb * math.cos(t))
                                for t in (2 * math.pi * i / 20 for i in range(20))], 0.022, M("leather"), closed=True))
    zf = -0.01 + 0.92 * rb + 0.02
    parts.append(gtube("Buckle", [(-0.035, yb - 0.03, zf), (0.035, yb - 0.03, zf), (0.035, yb + 0.03, zf), (-0.035, yb + 0.03, zf)],
                       0.009, M("gold"), closed=True))
    return C.join("Coat", parts)


def build_sleeve(s, side):
    pts = [(0.135 * s, 0.465, 0.05), (0.175 * s, 0.39, 0.09), (0.165 * s, 0.335, 0.125)]
    return C.join(f"CoatSleeve{side}", [gtube("Sleeve", pts, 0.053, M("coat"), [1, 0.95, 1.05], sides=2)])


def build_map():
    a, b = Vector((-0.235, 0.19, 0.03)), Vector((-0.245, 0.36, 0.08))
    return C.join("Map", [gtube("Scroll", [a, b], 0.034, M("paper"), sides=2),
                          C.ring("Ribbon", tuple(G(*a.lerp(b, 0.5))), 0.037, 0.008, M("red"), axis="Z")])


# ---------------------------------------------------------------- rig

def build_rig(name="Squirrel"):
    rig = bpy.data.objects.new(name, bpy.data.armatures.new(name + "Rig"))
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = rig.data.edit_bones
    for bname, h, t, parent in BONES:
        b = eb.new(bname)
        b.head, b.tail = G(*h), G(*t)
        if parent:
            b.parent = eb[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return rig


def attach(obj, rig, bone):
    """Parent a world-space object to a bone without moving it."""
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    pb = rig.pose.bones[bone]
    obj.parent, obj.parent_type, obj.parent_bone = rig, "BONE", bone
    parent_m = rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.bone.length, 0))
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_basis = parent_m.inverted() @ world


GEAR = ("Patch", "Hat", "Coat", "CoatSleeveL", "CoatSleeveR", "Map")


def build_squirrel(name="Squirrel", gear=True, smooth=False):
    """Returns (rig, body, extras) where extras are the rigid nodes (Ears, gear)."""
    rig = build_rig(name)
    body = build_body()
    body.parent = rig
    body.modifiers.new("Armature", "ARMATURE").object = rig
    extras = [(build_ears(), "Head")]
    if gear:
        extras += [(build_patch(), "Head"), (build_hat(), "Head"), (build_coat(), "Hips"),
                   (build_sleeve(1, "L"), "ArmL"), (build_sleeve(-1, "R"), "ArmR"), (build_map(), "Hips")]
    for obj, bone in extras:
        vs = [v.co for v in obj.data.vertices]
        C.set_origin(obj, [(min(v[i] for v in vs) + max(v[i] for v in vs)) / 2 for i in range(3)])   # the game pops gear in about here
        attach(obj, rig, bone)
    for o in [body] + [e for e, _ in extras]:
        for p in o.data.polygons:
            p.use_smooth = smooth
    return rig, body, [e for e, _ in extras]


# ---------------------------------------------------------------- clips

def set_pose(rig, spec):
    """spec: {bone: (rx, ry, rz)} rotations about the game axes at rest, plus "lift": hips y offset."""
    for pb in rig.pose.bones:
        B = pb.bone.matrix_local.to_3x3()
        Rg = rot(*spec.get(pb.name, (0.0, 0.0, 0.0)))
        Rb = C.G_TO_B @ Rg @ C.G_TO_B.inverted()
        pb.rotation_quaternion = (B.inverted() @ Rb @ B).to_quaternion()
        pb.location = B.inverted() @ G(0, spec.get("lift", 0.0), 0) if pb.name == "Hips" else Vector()


def make_clip(rig, name, frames, pose_at):
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = act
    for f in frames:
        set_pose(rig, pose_at(f))
        for pb in rig.pose.bones:
            pb.keyframe_insert("rotation_quaternion", frame=f)
            pb.keyframe_insert("location", frame=f)
    return act


def idle(f):
    ph = 2 * math.pi * f / 48
    spec = {"Spine": (0.03 * math.sin(ph), 0, 0), "Chest": (0.02 * math.sin(ph), 0, 0),
            "Head": (0.04 * math.sin(2 * ph), 0.15 * math.sin(ph), 0.05 * math.sin(ph + 1)),
            "ArmL": (-0.1 + 0.05 * math.sin(ph), 0, 0), "ArmR": (-0.1 + 0.05 * math.sin(ph + 0.4), 0, 0),
            "lift": -0.004 * (1 - math.cos(ph))}
    for i in range(5):
        spec[f"Tail{i + 1}"] = (0.07 * math.sin(ph - 0.6 * i), 0, 0.06 * math.sin(ph - 0.5 * i))
    return spec


def run(f):
    ph = 2 * math.pi * f / 12
    spec = {"Hips": (0.28, 0.1 * math.sin(ph), 0.05 * math.sin(ph)), "Spine": (0.06, -0.12 * math.sin(ph), 0),
            "Head": (-0.3 + 0.04 * math.sin(2 * ph), 0, 0), "lift": 0.035 * abs(math.sin(ph)) - 0.01}
    for side, off in (("L", 0.0), ("R", math.pi)):
        q = ph + off
        spec["Thigh" + side] = (-0.95 * math.sin(q), 0, 0)
        spec["Shin" + side] = (0.2 + 1.0 * max(0.0, math.cos(q)), 0, 0)
        spec["Foot" + side] = (-0.4 * max(0.0, math.cos(q)) + 0.25 * math.sin(q), 0, 0)
        spec["Arm" + side] = (0.9 * math.sin(q) - 0.2, 0, 0)
    for i in range(5):
        spec[f"Tail{i + 1}"] = ((-0.75 if i == 0 else -0.12) + 0.14 * math.sin(2 * ph - 0.9 * i), 0, 0.05 * math.sin(ph - 0.7 * i))
    return spec


JUMP_KEYS = {
    0: {},
    3: {"lift": -0.07, "Hips": (0.35, 0, 0), "Head": (-0.3, 0, 0), "ThighL": (-0.9, 0, 0), "ThighR": (-0.9, 0, 0),
        "ShinL": (1.4, 0, 0), "ShinR": (1.4, 0, 0), "FootL": (-0.5, 0, 0), "FootR": (-0.5, 0, 0),
        "ArmL": (0.7, 0, 0), "ArmR": (0.7, 0, 0), "Tail1": (-0.2, 0, 0)},
    6: {"lift": 0.03, "Hips": (0.15, 0, 0), "Head": (-0.1, 0, 0), "ThighL": (0.35, 0, 0), "ThighR": (0.35, 0, 0),
        "ShinL": (0.1, 0, 0), "ShinR": (0.1, 0, 0), "FootL": (0.5, 0, 0), "FootR": (0.5, 0, 0),
        "ArmL": (-1.7, 0, 0.2), "ArmR": (-1.7, 0, -0.2), "Tail1": (-0.7, 0, 0), "Tail2": (-0.2, 0, 0), "Tail3": (-0.2, 0, 0),
        "Tail4": (-0.2, 0, 0), "Tail5": (-0.2, 0, 0)},
    10: {"Hips": (0.05, 0, 0), "ThighL": (-1.15, 0, 0), "ThighR": (-1.15, 0, 0), "ShinL": (1.3, 0, 0), "ShinR": (1.3, 0, 0),
         "FootL": (-0.2, 0, 0), "FootR": (-0.2, 0, 0), "ArmL": (-1.0, 0, 0.6), "ArmR": (-1.0, 0, -0.6),
         "Tail1": (-0.25, 0, 0), "Tail2": (0.1, 0, 0), "Tail3": (0.12, 0, 0), "Tail4": (0.12, 0, 0), "Tail5": (0.15, 0, 0)},
    16: {"Hips": (0.05, 0, 0), "ThighL": (-0.5, 0, 0), "ThighR": (-0.5, 0, 0), "ShinL": (0.5, 0, 0), "ShinR": (0.5, 0, 0),
         "FootL": (-0.1, 0, 0), "FootR": (-0.1, 0, 0), "ArmL": (-0.9, 0, 0.9), "ArmR": (-0.9, 0, -0.9),
         "Tail1": (-0.4, 0, 0), "Tail2": (0.05, 0, 0), "Tail3": (0.05, 0, 0)},
}
def glide(f):
    """Spread-eagle, limbs out like a flying squirrel's; the game tilts the whole model forward on top."""
    ph = 2 * math.pi * f / 24
    w = 0.08 * math.sin(ph)
    spec = {"Head": (-0.35, 0, 0), "ArmL": (-0.4, 0, 1.25 + w), "ArmR": (-0.4, 0, -1.25 - w),
            "ThighL": (0.5, 0, 0.55 + w), "ThighR": (0.5, 0, -0.55 - w), "ShinL": (0.2, 0, 0), "ShinR": (0.2, 0, 0),
            "FootL": (0.3, 0, 0), "FootR": (0.3, 0, 0)}
    for i in range(5):
        spec[f"Tail{i + 1}"] = ((-0.95 if i == 0 else 0.0) + 0.1 * math.sin(ph - 0.8 * i), 0, 0.06 * math.sin(ph - 0.6 * i))
    return spec


def climb(f):
    """Facing the trunk: diagonal pairs reach and push (left arm with right leg)."""
    ph = 2 * math.pi * f / 12
    spec = {"Head": (-0.25, 0, 0)}
    for side, s, off in (("L", 1, 0.0), ("R", -1, math.pi)):
        q = math.sin(ph + off)
        spec["Arm" + side] = (-2.0 - 0.5 * q, 0, 0.35 * s)
        spec["Thigh" + side] = (-0.9 - 0.45 * q, 0, 0.35 * s)
        spec["Shin" + side] = (1.0 + 0.4 * q, 0, 0)
    for i in range(5):
        spec[f"Tail{i + 1}"] = ((-0.5 if i == 0 else 0.0) + 0.12 * math.sin(ph - 0.9 * i), 0, 0)
    return spec


WHIP = {"lift": -0.03, "Hips": (0.15, 0, 0), "ArmL": (-0.3, 0, 1.0), "ArmR": (-0.3, 0, -1.0),
        "Tail1": (-1.3, 0, 0), "Tail2": (-0.2, 0, 0), "Tail3": (-0.1, 0, 0)}
SWIPE_KEYS = {0: {}, 2: WHIP, 5: WHIP, 7: {}}   # 0.29 s, under the game's 0.3 s spin


def celebrate(f):
    ph = 2 * math.pi * f / 24
    spec = {"lift": 0.07 * abs(math.sin(ph)), "Head": (-0.15, 0, 0.15 * math.sin(ph)),
            "ArmL": (-2.6, 0, 0.5 + 0.3 * math.sin(2 * ph)), "ArmR": (-2.6, 0, -0.5 - 0.3 * math.sin(2 * ph + 1)),
            "ThighL": (-0.3 * abs(math.sin(ph)), 0, 0), "ThighR": (-0.3 * abs(math.sin(ph)), 0, 0),
            "ShinL": (0.4 * abs(math.sin(ph)), 0, 0), "ShinR": (0.4 * abs(math.sin(ph)), 0, 0)}
    for i in range(5):
        spec[f"Tail{i + 1}"] = (0.0, 0, 0.25 * math.sin(2 * ph - 0.5 * i))
    return spec


CLIPS = {  # name: (key frames, pose function, loops)
    "Idle": (range(0, 49, 4), idle, True),
    "Run": (range(0, 13), run, True),
    "Jump": (sorted(JUMP_KEYS), JUMP_KEYS.get, False),
    "Glide": (range(0, 25, 3), glide, True),
    "Climb": (range(0, 13), climb, True),
    "Swipe": (sorted(SWIPE_KEYS), SWIPE_KEYS.get, False),
    "Celebrate": (range(0, 25, 2), celebrate, True),
}


def add_clips(rig):
    acts = {name: make_clip(rig, name, frames, fn) for name, (frames, fn, _) in CLIPS.items()}
    rig.animation_data.action = None
    set_pose(rig, {})
    return acts


def play(rig, act):
    rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]


# ---------------------------------------------------------------- renders

def jump_arc(f):
    """Display-only height for the jump renders (the game supplies the real arc): off the ground
    from frame 5, apex around frame 11, down again at frame 18."""
    t = (f - 5) / 13
    return 0.62 * (1 - (2 * t - 1) ** 2) if 0 < t < 1 else 0.0


def gamecam(extras, name):
    """The follow camera's view (6.2 behind, pitch 0.32, 58 deg vertical FOV) in the pirate look, plus a crop taken
    from the same spot with a narrow lens, so the squirrel is big enough to judge. Returns [full, crop]."""
    pitch, dist, eye = 0.32, 6.2, 0.55
    loc = tuple(G(0, eye + dist * math.sin(pitch), -dist * math.cos(pitch)))
    dress(extras, "pirate")
    files = []
    for tag, fov, res in (("_full", 58, (1280, 720)), ("", 12, (720, 720))):
        st = C.stage(target=tuple(G(0, eye, 0)), cam_loc=loc, res=res, fov_y=fov, ground=(0xe8d3a1, 0.0), ground_size=60)
        files.append(C.PREVIEWS / f"{name}{tag}.png")
        C.render(files[-1], samples=32)
        C.unstage(st)
    return files


def dress(extras, look):
    """'plain' shows the bare squirrel; 'pirate' all the gear, with the ears hidden as equip('hat') does."""
    for e in extras:
        e.hide_render = (e.name != "Ears") if look == "plain" else (e.name == "Ears")


def shoot(rig, extras, act, name, shots, cam, size, samples, look="pirate"):
    """Render (clip frame, display height) pairs to art/previews/frames/<name>/; returns the files."""
    st = C.stage(**cam, size=size, ground=(0xe8d3a1, 0.0))
    play(rig, act)
    dress(extras, look)
    files = []
    for i, (f, lift) in enumerate(shots):
        bpy.context.scene.frame_set(f)
        rig.location.z = lift
        files.append(C.PREVIEWS / "frames" / f"{name}_{look}" / f"{i:03d}.png")
        C.render(files[-1], samples=samples)
    C.unstage(st)
    rig.location.z = 0.0
    return files


def strip(rig, extras, act, name, shots, cam, size=400):
    """Contact sheet: the plain squirrel on the top row, the pirate on the bottom."""
    files = [f for look in ("plain", "pirate") for f in shoot(rig, extras, act, name, shots, cam, size, 24, look)]
    return C.contact_sheet(C.PREVIEWS / f"{name}.png", files, len(shots))


def movie(rig, extras, act, name, shots, cam, size=480):
    """MP4 of the shots (pirate look), stitched with the sequencer and Blender's FFmpeg output."""
    files = shoot(rig, extras, act, name + "_mp4", shots, cam, size, 16)
    seq_scene = bpy.data.scenes.new(name)
    seq_scene.render.resolution_x = seq_scene.render.resolution_y = size
    seq_scene.render.fps = FPS
    seq_scene.frame_start, seq_scene.frame_end = 1, len(files)
    seq_scene.sequence_editor_create()
    strips = seq_scene.sequence_editor.strips if hasattr(seq_scene.sequence_editor, "strips") else seq_scene.sequence_editor.sequences
    s = strips.new_image("frames", str(files[0]), channel=1, frame_start=1)
    for f in files[1:]:
        s.elements.append(f.name)
    ims = seq_scene.render.image_settings
    if hasattr(ims, "media_type"):
        ims.media_type = "VIDEO"
    ims.file_format = "FFMPEG"
    seq_scene.render.ffmpeg.format = "MPEG4"
    seq_scene.render.ffmpeg.codec = "H264"
    seq_scene.render.ffmpeg.constant_rate_factor = "HIGH"
    seq_scene.view_settings.view_transform = "Standard"
    seq_scene.render.filepath = str(C.PREVIEWS / f"{name}.mp4")
    seq_scene.render.use_sequencer = True
    with bpy.context.temp_override(scene=seq_scene):
        bpy.ops.render.render(animation=True)
    bpy.data.scenes.remove(seq_scene)
    return C.PREVIEWS / f"{name}.mp4"


if __name__ == "__main__":
    C.reset(seed=3)
    bpy.context.scene.render.fps = FPS
    rig, body, extras = build_squirrel(smooth=True)
    acts = add_clips(rig)
    path = C.export("squirrel", [rig, body] + extras)
    tris = C.tri_count([body] + extras)
    print(f"squirrel: {tris} triangles ({C.tri_count([body])} body), {len(rig.data.bones)} bones -> {path}")
    for name, (frames, _, loops) in CLIPS.items():
        print(f"  clip {name}: {max(frames) / FPS:.2f} s{' loop' if loops else ''}")

    front = dict(target=tuple(G(0, 0.5, 0)), cam_loc=tuple(G(1.3, 0.95, 2.1)))
    st = C.stage(**front, res=(640, 640), ground=(0xe8d3a1, 0.0))
    for look in ("pirate", "plain"):
        dress(extras, look)
        C.render(C.PREVIEWS / "frames" / f"squirrel_{look}.png")
    C.unstage(st)
    C.contact_sheet(C.PREVIEWS / "squirrel.png", [C.PREVIEWS / "frames" / "squirrel_plain.png", C.PREVIEWS / "frames" / "squirrel_pirate.png"], 2)
    gamecam(extras, "squirrel_gamecam")
    if "--quick" in sys.argv:     # blender -b -P squirrel.py -- --quick: model, export and still only
        sys.exit(0)

    side = dict(target=tuple(G(0, 0.45, -0.12)), cam_loc=tuple(G(1.95, 0.7, 0.75)))
    high = dict(target=tuple(G(0, 0.72, -0.08)), cam_loc=tuple(G(2.5, 1.0, 1.0)))
    strip(rig, extras, acts["Run"], "squirrel_run", [(f, 0.0) for f in range(0, 12, 2)], side)
    strip(rig, extras, acts["Jump"], "squirrel_jump", [(f, jump_arc(f)) for f in range(0, 17, 2)], high)
    strip(rig, extras, acts["Idle"], "squirrel_idle", [(f, 0.0) for f in range(0, 48, 12)], side)
    sheet = []
    for name, frames in (("Glide", (0, 6, 12, 18)), ("Climb", (0, 3, 6, 9)), ("Swipe", (0, 2, 5, 7)), ("Celebrate", (0, 6, 12, 18))):
        lift = 0.4 if name == "Glide" else 0.0
        sheet += shoot(rig, extras, acts[name], f"squirrel_{name.lower()}", [(f, lift) for f in frames], high, 400, 24)
    C.contact_sheet(C.PREVIEWS / "squirrel_clips.png", sheet, 4)
    movie(rig, extras, acts["Run"], "squirrel_run", [(f, 0.0) for f in range(12)] * 4, side)
    landing = [(16, jump_arc(17)), (16, 0.0), (16, 0.0), (16, 0.0), (3, 0.0), (0, 0.0), (0, 0.0), (0, 0.0)]
    movie(rig, extras, acts["Jump"], "squirrel_jump", [(f, jump_arc(f)) for f in range(17)] + landing, high)
    print("previews:", C.PREVIEWS)
