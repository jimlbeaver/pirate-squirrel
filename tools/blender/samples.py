"""Style-decision sample sheets for Jim (renders only; nothing here is exported for the game).

  blender -b -P tools/blender/samples.py

  art/previews/sample_shading.png   crab and squirrel, faceted (A) vs smooth (B), next to faceted world pieces
  art/previews/sample_foliage.png   one branch-and-leaf clump three ways:
                                    A flat colours + boat-level moss, B flat + more moss and weathering,
                                    C vertex-colour gradients (also written to art/previews/foliage_c_test.glb
                                    to check what the glTF exporter emits)
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import psq_common as C  # noqa: E402
from psq_common import G, Vector, ellipsoid, gtube  # noqa: E402

import bpy  # noqa: E402
import crab  # noqa: E402
import squirrel  # noqa: E402

SAND = 0xe8d3a1
LEAF = [0xd9872a, 0xe8b441, 0xc0602a, 0x9aa23f, 0xe39a37]


# ---------------------------------------------------------------- world pieces (always faceted)

def rock(x0):
    random.seed(21)
    return [ellipsoid("Rock", (x0, 0.3, 0), (0.5, 0.38, 0.45), C.mat("Rock", 0x8e8474), ico=1, jitter=0.15),
            ellipsoid("RockMoss", (x0 - 0.05, 0.62, 0.02), (0.3, 0.1, 0.28), C.mat("Moss", 0x7c9a3b), ico=1, jitter=0.2)]


def trunk_chunk(x0):
    random.seed(22)
    bark = C.mat("Bark", 0x6a4a31)
    parts = []
    for name, r1, r2, h, z0 in (("Trunk", 0.36, 0.32, 1.0, 0.0), ("Flare", 0.6, 0.37, 0.28, 0.0)):
        bm = C.bmesh.new()
        C.bmesh.ops.create_cone(bm, cap_ends=True, segments=9, radius1=r1, radius2=r2, depth=h)
        for v in bm.verts:
            k = 1 + random.uniform(-0.07, 0.07)
            v.co.x, v.co.y, v.co.z = x0 + v.co.x * k, v.co.y * k, v.co.z + h / 2 + z0
        parts.append(C._obj_from_bmesh(name, bm, bark))
    for i in range(6):
        a = i * 1.1 + 0.3
        y = 0.45 + 0.25 * math.sin(i * 2.1)
        parts.append(ellipsoid("Moss", (x0 + 0.34 * math.cos(a), y, 0.34 * math.sin(a)), (0.11, 0.08, 0.11),
                               C.mat("MossBright" if i % 2 else "MossDark", 0x86b233 if i % 2 else 0x5b8424, 0.8), ico=1, jitter=0.2))
    return parts


def shading_sheet():
    C.clear_objects()
    xs = {"crabA": -3.0, "crabB": -1.8, "sqA": -0.6, "sqB": 0.25, "rock": 1.55, "trunk": 2.75}
    for key, smooth in (("crabA", False), ("crabB", True)):
        crab.build("Crab" + key, smooth=smooth, offset=(xs[key], 0, 0))
    for key, smooth in (("sqA", False), ("sqB", True)):
        rig, _, extras = squirrel.build_squirrel("Squirrel" + key, smooth=smooth)
        squirrel.dress(extras, "pirate")
        rig.location.x = xs[key]
    for o in rock(xs["rock"]) + trunk_chunk(xs["trunk"]):
        for p in o.data.polygons:
            p.use_smooth = False
    for key, text in (("crabA", "A  faceted"), ("crabB", "B  smooth"), ("sqA", "A  faceted"), ("sqB", "B  smooth")):
        C.label(text, (xs[key], -0.9, 0.05), size=0.12)
    C.label("world pieces: faceted", ((xs["rock"] + xs["trunk"]) / 2, -0.9, 0.05), size=0.12)
    C.preview("sample_shading", target=(-0.1, 0, 0.42), cam_loc=(0.1, -8.6, 2.1), res=(1800, 640), lens=42,
              ground=(SAND, 0.0))


# ---------------------------------------------------------------- foliage clump

def hex_mix(a, b, t):
    ca = [((a >> s) & 255) / 255 for s in (16, 8, 0)]
    cb = [((b >> s) & 255) / 255 for s in (16, 8, 0)]
    return tuple(C._lin(x + (y - x) * t) for x, y in zip(ca, cb))


def paint(obj, fn):
    """Vertex colours for gradient variant C: fn(game point, game normal) -> linear rgb."""
    attr = obj.data.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    for v in obj.data.vertices:
        attr.data[v.index].color = (*fn(C.to_game(v.co), C.to_game(v.normal)), 1.0)
    return obj


def vcol_mat():
    if "VertexColour" in bpy.data.materials:
        return bpy.data.materials["VertexColour"]
    m = bpy.data.materials.new("VertexColour")
    if not m.node_tree:
        m.use_nodes = True
    nt = m.node_tree
    node = nt.nodes.new("ShaderNodeVertexColor")
    node.layer_name = "Col"
    bsdf = nt.nodes["Principled BSDF"]
    nt.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    return m


def leaf(name, base, d, L, material, grad=None):
    """A lobed oak leaf, folded along its midrib. `grad` = (stem hex, tip hex) paints variant C."""
    d = d.normalized()
    side = d.cross(Vector((0, 1, 0)))
    side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
    n = side.cross(d).normalized()
    rows, cols = 8, 4
    verts, ts = [], []
    for r in range(rows + 1):
        t = r / rows
        env = 0.36 * math.sin(math.pi * min(1.0, t * 1.02)) ** 0.8
        lobes = 0.65 + 0.35 * abs(math.sin(math.pi * 3.5 * t))
        w = max(0.02, env * lobes) * L
        for c in range(cols + 1):
            s = -1 + 2 * c / cols
            verts.append(base + d * (t * L) + side * (w * s) + n * (0.3 * w * abs(s)))
            ts.append(t)
    faces = [(r * (cols + 1) + c, r * (cols + 1) + c + 1, (r + 1) * (cols + 1) + c + 1, (r + 1) * (cols + 1) + c)
             for r in range(rows) for c in range(cols)]
    o = C.mesh_from(name, [tuple(G(*v)) for v in verts], faces, material)
    if grad:
        attr = o.data.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        for i, t in enumerate(ts):
            attr.data[i].color = (*hex_mix(grad[0], grad[1], t), 1.0)
    return o


def clump(variant, x0):
    random.seed(40)
    grad = variant == "C"
    bark = vcol_mat() if grad else C.mat("Bark", 0x6a4a31)
    moss_b = vcol_mat() if grad else C.mat("MossBright", 0x86b233, 0.8)
    moss_d = vcol_mat() if grad else C.mat("MossDark", 0x5b8424, 0.8)
    parts = []
    path = [Vector((x0 - 0.85, 0.42, 0)), Vector((x0 - 0.3, 0.6, 0.02)), Vector((x0 + 0.3, 0.8, 0.05))]
    parts.append(gtube("Branch", path, 0.11, bark, [1, 0.8, 0.5], sides=2))
    parts.append(gtube("Twig", [Vector((x0 - 0.1, 0.68, 0.03)), Vector((x0 + 0.02, 0.93, -0.06))], 0.03, bark, [1, 0.4]))
    if grad:
        dark, light = 0x3b2618, 0x8a6440
        for p in parts:
            paint(p, lambda q, nrm: hex_mix(dark, light, 0.5 + 0.5 * nrm.y))

    def on_branch(f, up=0.0):
        seg = min(1, int(f * 2))
        u = f * 2 - seg
        r = 0.11 * (1 - 0.35 * f)
        return path[seg].lerp(path[seg + 1], u) + Vector((0, r * 0.85 + up, 0))

    tufts = [0.2, 0.42, 0.66] if variant != "B" else [0.08, 0.18, 0.28, 0.38, 0.48, 0.58, 0.68, 0.78, 0.33]
    for i, f in enumerate(tufts):
        big = 1.35 if variant == "B" else 1.0
        c = on_branch(f)
        t = ellipsoid("Moss", c, (0.1 * big, 0.055 * big, 0.09 * big), moss_b if i % 2 else moss_d, ico=1, jitter=0.2)
        if grad:
            paint(t, lambda q, nrm, c=c: hex_mix(0x5b8424, 0x86b233, min(1.0, max(0.0, (q.y - c.y) / 0.05 * 0.5 + 0.5))))
        parts.append(t)

    if variant == "B":   # more moss and weathering: drips, lichen, dark bark patches, dry leaves
        for f in (0.15, 0.35, 0.55, 0.72):
            c = on_branch(f, -0.1) + Vector((0, -0.12, 0.07))
            parts.append(ellipsoid("MossBeard", c, (0.05, 0.1, 0.04), moss_d, ico=1, jitter=0.25))
        for f, dz in ((0.12, 0.1), (0.45, 0.1), (0.62, -0.09), (0.3, -0.1)):
            c = on_branch(f, -0.1) + Vector((0, 0, dz))
            parts.append(ellipsoid("Lichen", c, (0.04, 0.035, 0.012), C.mat("Lichen", 0xa7ae7c, 0.95), segs=(6, 3)))
        for f in (0.25, 0.52):
            parts.append(ellipsoid("BarkScar", on_branch(f, -0.1) + Vector((0, 0, 0.1)), (0.07, 0.04, 0.012),
                                   C.mat("BarkDark", 0x3b2618), segs=(6, 3)))

    K = Vector((x0 + 0.45, 0.95, 0.03))       # the clump fills a squashed ball past the branch tip
    n_leaves = 24
    for i in range(n_leaves):
        y = 1 - 1.7 * (i + 0.5) / n_leaves
        r = math.sqrt(max(0.0, 1 - y * y))
        a = i * 2.39996
        u = Vector((r * math.cos(a), y, r * math.sin(a)))
        base = K + Vector((u.x * 0.3, u.y * 0.18, u.z * 0.26)) * random.uniform(0.3, 1.0)
        d = u + Vector((random.uniform(-0.4, 0.4), 0.25, random.uniform(-0.4, 0.4)))
        L = random.uniform(0.26, 0.34)
        col = LEAF[i % len(LEAF)]
        if variant == "B" and i % 5 == 2:
            col = 0x8a5a2e                       # a few dry, curled leaves
        mat = vcol_mat() if grad else C.mat(f"Leaf{col:06x}", col, 0.85)
        parts.append(leaf("Leaf", base, d, L, mat,
                          grad=(_blend(col, 0x7c9a3b, 0.6), _blend(col, 0xf1d27a, 0.45)) if grad else None))
    return parts


def _blend(a, b, t):
    return int("".join(f"{round(((a >> s) & 255) + (((b >> s) & 255) - ((a >> s) & 255)) * t):02x}" for s in (16, 8, 0)), 16)


def foliage_sheet():
    C.clear_objects()
    xs = {"A": -2.2, "B": 0.0, "C": 2.2}
    groups = {k: clump(k, x) for k, x in xs.items()}
    c_obj = C.join("FoliageC", groups["C"])
    for key, text in (("A", "A  flat colours, boat-level moss"), ("B", "B  flat, more moss + wear"), ("C", "C  vertex-colour gradients")):
        C.label(text, (xs[key], -0.8, 0.05), size=0.11)
    C.preview("sample_foliage", target=(0.0, 0, 0.62), cam_loc=(0.0, -7.2, 1.9), res=(1800, 640), lens=40, ground=(SAND, 0.0))
    bpy.ops.object.select_all(action="DESELECT")
    c_obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(C.PREVIEWS / "foliage_c_test.glb"), export_format="GLB", use_selection=True)
    tris = {k: C.tri_count([c_obj]) if k == "C" else C.tri_count(v) for k, v in groups.items()}
    print("foliage tris:", tris)


if __name__ == "__main__":
    C.reset(seed=9)
    shading_sheet()
    foliage_sheet()
    print("previews:", C.PREVIEWS)
