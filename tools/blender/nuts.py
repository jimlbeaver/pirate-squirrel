"""Sea nuts and the Chestnut prize -> art/exports/{peanut,acorn,walnut,chestnut}.glb

  blender -b -P tools/blender/nuts.py

Sea nuts (`voyage: nuts and hazards`) are authored at their in-game size with the origin at the
centre (the game floats them 0.4 above the water and spins them about +y). Each GLB is one mesh
named after the nut; value goes up with size:
  Peanut   0.6 long along x: pale pinched double lobe with a pitted net
  Acorn    0.75 tall: glossy dark nut under a scaly cap, stubby stem
  Walnut   1.0 across: deep wrinkles, raised seam round it in the x = 0 plane
The prize (`prize` in the treasure section) is authored 0.5 wide; the game scales it up as it rises.
  ChestnutPrize   root, origin at the nut's centre
    Chestnut      glossy and smooth-shaded; the game animates `ChestnutShell`'s emissive
    HuskA..D      spiky husk petals round the lower half on +z, +x, -z, -x. Each origin is the
                  petal's hinge at its base, so it opens outward with rotation.x > 0 (A),
                  rotation.z < 0 (B), rotation.x < 0 (C), rotation.z > 0 (D)
Previews in art/previews/: nuts_lineup.png, nuts_gamecam.png (boat follow camera), chestnut.png.
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import psq_common as C  # noqa: E402
from psq_common import G, Vector, ellipsoid, gtube, smoothstep, to_game  # noqa: E402

import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import noise  # noqa: E402

PAL = {
    "walnut": ("WalnutShell", 0xb8875a, 0.85), "walnut_dark": ("WalnutDark", 0x7d5a36, 0.9),
    "acorn": ("AcornNut", 0x7a4220, 0.35), "cap": ("AcornCap", 0xa8773f, 0.9),
    "cap_dark": ("AcornCapDark", 0x8a5e30, 0.9), "stem": ("AcornStem", 0x6a4a31, 0.9),
    "peanut": ("PeanutShell", 0xd9b77e, 0.9), "peanut_dark": ("PeanutDark", 0xb8955e, 0.95),
    "shell": ("ChestnutShell", 0x6b2a14, 0.25), "streak": ("ChestnutStreak", 0x5a2311, 0.3),
    "hilum": ("ChestnutHilum", 0xd8c08e, 0.9), "tuft": ("ChestnutTuft", 0xe9d6a6, 0.9),
    "husk": ("Husk", 0x6f8a2e, 0.8), "spike": ("HuskSpike", 0x9aa23f, 0.8),
}
SAND, WATER = 0xe8d3a1, 0x2a8a93


def M(key):
    return C.mat(*PAL[key])


def paint(obj, key, pick):
    """Give the faces whose game-space centre passes `pick` the material PAL[key]."""
    me = obj.data
    me.materials.append(M(key))
    for p in me.polygons:
        if pick(to_game(p.center)):
            p.material_index = len(me.materials) - 1
    return obj


def cone(name, base, tip, radius, key, sides=3):
    """A thin pointed cone from game point `base` to `tip`, open at the base (it sits in a surface)."""
    base, tip = Vector(base), Vector(tip)
    axis = (tip - base).normalized()
    u = axis.orthogonal().normalized()
    w = axis.cross(u)
    ring = [base + radius * (math.cos(a) * u + math.sin(a) * w) for a in (2 * math.pi * i / sides for i in range(sides))]
    return C.mesh_from(name, [tuple(G(*p)) for p in ring + [tip]], [(i, (i + 1) % sides, sides) for i in range(sides)], M(key))


def warp(obj, fn):
    """Move every vertex through `fn` (game coords), e.g. from a painted unit sphere to the nut's shape."""
    for v in obj.data.vertices:
        v.co = G(*fn(to_game(v.co)))
    return obj


def centred(obj):
    """Shift the geometry so its bounding-box centre sits on the origin."""
    vs = [v.co.copy() for v in obj.data.vertices]
    mid = Vector([(min(v[i] for v in vs) + max(v[i] for v in vs)) / 2 for i in range(3)])
    for v in obj.data.vertices:
        v.co -= mid
    return obj


# ---------------------------------------------------------------- walnut

WALNUT_R = 0.46


def walnut_groove(d):
    """1 at the bottom of a wrinkle, 0 on the lobes; the wrinkles fade out beside the seam (x = 0)."""
    n = noise.noise(Vector((d.x * 1.9, d.y * 1.0, d.z * 1.9)) + Vector((4.1, 7.3, 2.9)))
    return (1 - smoothstep(0.0, 0.26, abs(n))) * smoothstep(0.1, 0.3, abs(d.x))


def walnut_warp(p):
    d = p.normalized()
    lump = 0.05 * noise.noise(d * 1.3 + Vector((9.0, 1.0, 5.0)))
    r = 1 + lump - 0.25 * walnut_groove(d) - 0.05 * (1 - smoothstep(0.0, 0.2, abs(d.x))) + 0.1 * max(0.0, d.y) ** 8
    return Vector((d.x, d.y * 1.07, d.z)) * r * WALNUT_R


def build_walnut():
    shell = ellipsoid("Shell", (0, 0, 0), (1, 1, 1), M("walnut"), ico=4)
    warp(paint(shell, "walnut_dark", lambda d: walnut_groove(d.normalized()) > 0.6), walnut_warp)
    seam = [walnut_warp(Vector((0.012 * math.sin(5 * a), math.cos(a), math.sin(a)))) * 1.02
            for a in (2 * math.pi * i / 28 for i in range(28))]
    parts = [shell, gtube("Seam", seam, 0.045, M("walnut"), sides=0, closed=True)]
    return centred(C.join("Walnut", parts))


# ---------------------------------------------------------------- acorn

NUT_Y, CAP_Y, CAP = -0.1, 0.07, (0.225, 0.13)   # nut centre, cap centre, cap radius and height


def acorn_egg(p):
    if p.y >= 0:
        return p
    k = 1 - 0.28 * (p.y / 0.2) ** 2
    return Vector((p.x * k, p.y * 1.3, p.z * k))


def cap_pt(phi, th, lift=0.0):
    """Point on the cap dome at latitude `phi` (0 = rim) and heading `th`, pushed out by `lift`."""
    c = math.cos(phi)
    return Vector(((CAP[0] + lift) * c * math.sin(th), CAP_Y + (CAP[1] + lift) * math.sin(phi), (CAP[0] + lift) * c * math.cos(th)))


def shingle(phi, th, dphi, dth):
    """One cap scale: tucked in at the top, its lower tip lifted clear of the dome."""
    pts = [cap_pt(phi + dphi, th, -0.004), cap_pt(phi, th - dth, 0.006), cap_pt(phi, th + dth, 0.006),
           cap_pt(phi - 0.2 * dphi, th, 0.03), cap_pt(phi - 0.85 * dphi, th, 0.036)]
    faces = [(1, 3, 0), (3, 2, 0), (1, 4, 3), (4, 2, 3)]      # top, left, right, mid, tip
    return C.mesh_from("Scale", [tuple(G(*p)) for p in pts], faces, M("cap"))


def build_acorn():
    bottom = NUT_Y - 0.26
    parts = [
        ellipsoid("Nut", (0, NUT_Y, 0), (0.2, 0.2, 0.2), M("acorn"), segs=(14, 9), fn=acorn_egg),
        cone("Point", (0, bottom + 0.03, 0), (0, bottom - 0.035, 0), 0.03, "acorn", sides=5),
        ellipsoid("Cap", (0, CAP_Y, 0), (CAP[0], CAP[1], CAP[0]), M("cap_dark"), segs=(14, 6)),
        C.ring("Lip", G(0, CAP_Y - 0.01, 0), CAP[0] - 0.005, 0.03, M("cap_dark"), segs=14, minor_segs=4),
        gtube("Stem", [(0, CAP_Y + 0.1, 0), (0.01, CAP_Y + 0.19, 0), (0.035, CAP_Y + 0.26, 0.01)], 0.028, M("stem"), [1.2, 1, 0.8], sides=1),
    ]
    for ring, (phi, n) in enumerate(((0.12, 13), (0.5, 11), (0.88, 8), (1.22, 5))):
        for i in range(n):
            th = 2 * math.pi * (i + 0.5 * (ring % 2)) / n + random.uniform(-0.08, 0.08)
            parts.append(shingle(phi, th, 0.26, math.pi / n * 1.15))
    return centred(C.join("Acorn", parts))


# ---------------------------------------------------------------- peanut

PEANUT_L = 0.3


def peanut_r(t):
    """Radius at t in [-1, 1] along the pod: two round lobes pinched in the middle, the +x one fuller."""
    return 0.165 * (1 - t * t) ** 0.45 * (1 - 0.3 * math.exp(-(t / 0.24) ** 2)) * (1 + 0.06 * t)


def peanut_pt(t, a):
    r = peanut_r(t)
    return G(t * PEANUT_L, 0.03 * t * t + r * math.cos(a), r * math.sin(a))


def build_peanut(rings=13, sides=9):
    bm = bmesh.new()
    ends = [bm.verts.new(peanut_pt(-1, 0)), bm.verts.new(peanut_pt(1, 0))]
    grid = [[bm.verts.new(peanut_pt(-math.cos(math.pi * i / rings), 2 * math.pi * j / sides)) for j in range(sides)]
            for i in range(1, rings)]
    pits = []
    for i in range(len(grid) - 1):
        for j in range(sides):
            f = bm.faces.new((grid[i][j], grid[i][(j + 1) % sides], grid[i + 1][(j + 1) % sides], grid[i + 1][j]))
            if 0 < i < len(grid) - 2:
                pits.append(f)
    for j in range(sides):
        bm.faces.new((ends[0], grid[0][(j + 1) % sides], grid[0][j]))
        bm.faces.new((ends[1], grid[-1][j], grid[-1][(j + 1) % sides]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in pits:      # a netted shell: every cell a shallow pit of its own depth
        bmesh.ops.inset_individual(bm, faces=[f], thickness=0.009, depth=-random.uniform(0.007, 0.014))
    for f in pits:
        f.material_index = 1
    obj = C._obj_from_bmesh("Peanut", bm, M("peanut"))
    obj.data.materials.append(M("peanut_dark"))
    return centred(obj)


# ---------------------------------------------------------------- chestnut prize

STREAKS = (0.3, 1.5, 2.6, 3.9, 5.1)             # headings of the faint dark streaks toward the tip


def chestnut_pt(d):
    """Unit-sphere direction -> the nut's surface: flat base, rounded front, flatter back, pointed tip."""
    x, y, z = d
    if y < -0.7:
        y = -0.7 + (y + 0.7) * 0.35
    s = (1 - 0.12 * smoothstep(0.2, 0.9, y)) * (1 - 0.3 * smoothstep(0.85, 1.0, y)) * (1 + 0.08 * (1 - smoothstep(-0.6, 0.0, y)))
    tip = 0.28 * max(0.0, (y - 0.9) / 0.1) ** 6      # only the top ring and pole: a short point
    z *= 0.62 if z < 0 else 1.0
    return Vector((0.25 * s * x + 0.02 * max(0.0, y) ** 3, 0.2 * (y + tip), 0.17 * s * z))


def heading_near(c, heads, tol):
    h = math.atan2(c.x, c.z)
    return any(abs((h - a + math.pi) % (2 * math.pi) - math.pi) < tol for a in heads)


def gloss(obj):
    """Smooth-shade the nut for its highlight, keeping the tuft faceted and a crisp edge round the hilum."""
    names = [m.name for m in obj.data.materials]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for f in bm.faces:
        f.smooth = names[f.material_index] != "ChestnutTuft"
    for e in bm.edges:
        if len({names[f.material_index] == "ChestnutHilum" for f in e.link_faces}) > 1:
            e.smooth = False
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def build_chestnut():
    nut = ellipsoid("Nut", (0, 0, 0), (1, 1, 1), M("shell"), segs=(32, 16))
    paint(nut, "streak", lambda d: d.y > 0.55 and heading_near(d, STREAKS, math.pi / 32))
    paint(nut, "hilum", lambda d: d.y < -0.78)
    centred(warp(nut, chestnut_pt))
    tip = max((to_game(v.co) for v in nut.data.vertices), key=lambda p: p.y)
    parts = [nut]
    for i in range(7):
        a = 2 * math.pi * i / 7 + random.uniform(-0.3, 0.3)
        d = Vector((0.5 * math.sin(a), 1, 0.5 * math.cos(a))).normalized()
        parts.append(cone("Tuft", tip - Vector((0, 0.012, 0)), tip + d * random.uniform(0.045, 0.07), 0.007, "tuft"))
    return gloss(C.join("Chestnut", parts))


HUSK_C, HUSK_R = Vector((0, 0.01, 0.02)), (0.3, 0.3, 0.26)
PETAL_POL = (0.3, 1.72)          # the petal runs from its hinge near the bottom to just past the equator


def husk_pt(pol, az, lift=0.0):
    """Point on the husk cup at polar angle `pol` from the bottom and heading `az`."""
    rx, ry, rz = (r + lift for r in HUSK_R)
    return HUSK_C + Vector((rx * math.sin(pol) * math.sin(az), -ry * math.cos(pol), rz * math.sin(pol) * math.cos(az)))


def petal_half(pol):
    """Half-width (radians of heading) of a petal, narrowing to a point at its top."""
    return 0.7 * (1 - 0.85 * smoothstep(0.9, PETAL_POL[1], pol))


def build_petal(name, az0, rows=6, cols=4):
    p0, p1 = PETAL_POL
    pols = [p0 + (p1 - p0) * i / rows for i in range(rows + 1)]
    bm = bmesh.new()
    vs = [[bm.verts.new(G(*husk_pt(p, az0 + petal_half(p) * (2 * j / cols - 1)))) for j in range(cols + 1)] for p in pols]
    for i in range(rows):
        for j in range(cols):
            bm.faces.new((vs[i][j], vs[i][j + 1], vs[i + 1][j + 1], vs[i + 1][j]))
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.024)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    parts = [C._obj_from_bmesh("Petal", bm, M("husk"))]
    for i in range(8):
        for j in range(5):
            pol = p0 + 0.08 + (p1 - p0 - 0.2) * (i + random.uniform(0.2, 0.8)) / 8
            az = az0 + petal_half(pol) * 0.85 * (2 * (j + random.uniform(0.2, 0.8)) / 5 - 1)
            jit = Vector([random.uniform(-0.015, 0.015) for _ in range(3)])
            parts.append(cone("Spike", husk_pt(pol, az, -0.01), husk_pt(pol, az, 0.06) + jit, 0.011, "spike"))
    return C.join_at(name, parts, origin=tuple(G(*husk_pt(p0, az0))))


def build_prize():
    root = bpy.data.objects.new("ChestnutPrize", None)
    bpy.context.collection.objects.link(root)
    kids = [build_chestnut()] + [build_petal("Husk" + k, az) for k, az in zip("ABCD", (0, math.pi / 2, math.pi, 1.5 * math.pi))]
    for k in kids:
        k.parent = root
    return root, kids


# ---------------------------------------------------------------- previews

def meshes(obj):
    return list(obj.children) if obj.type == "EMPTY" else [obj]


def place(obj, x, y=0.0, scale=1.0, yaw=0.0, z=None):
    """Put `obj` at Blender (x, y), `scale` times its size; standing on z = 0 unless `z` is given."""
    bpy.context.view_layer.update()
    local = obj.matrix_world.inverted()
    low = min((local @ o.matrix_world @ v.co).z for o in meshes(obj) for v in o.data.vertices)
    obj.location = (x, y, -low * scale if z is None else z)
    obj.scale = (scale,) * 3
    obj.rotation_euler = (0, 0, yaw)
    return obj


def copy(obj):
    dup = obj.copy()
    bpy.context.collection.objects.link(dup)
    return dup


def water(size):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    bpy.context.object.data.materials.append(C.mat("Water", WATER, 0.26))
    return bpy.context.object


def hide(objs, hidden=True):
    for o in objs:
        for m in meshes(o):
            m.hide_render = hidden


def render_lineup(nuts, prize):
    row = [(nuts["peanut"], -1.75, "peanut +6", 1.0), (nuts["acorn"], -0.95, "acorn +12", 1.0),
           (nuts["walnut"], 0.1, "walnut +20", 1.0), (prize, 1.65, "chestnut prize\n(reveal size 2.2x)", 2.2)]
    labels = []
    for obj, x, text, scale in row:
        place(obj, x, scale=scale, yaw=0.5)
        for i, line in enumerate(text.split("\n")):
            labels.append(C.label(line, (x, -1.1, 0.06 + 0.16 * (text.count("\n") - i)), size=0.13))
    C.preview("nuts_lineup", target=(0.0, 0, 0.5), cam_loc=(0.6, -6.4, 2.5), res=(1600, 800), lens=45, ground=(SAND, 0.0))
    for o in labels:
        bpy.data.objects.remove(o)


def render_gamecam(nuts, prize):
    """The boat's follow camera: 8.5 behind a point 1.0 above the deck at pitch 0.32, 58 deg vertical FOV."""
    hide([prize] + list(nuts.values()))
    spots = {"walnut": ((-2.6, 5.2), (2.2, 8.6), (-1.2, 10.0)), "acorn": ((1.4, 4.4), (-3.4, 7.6), (3.6, 6.0)),
             "peanut": ((-1.5, 6.6), (1.2, 7.4), (-4.2, 9.6))}
    extras = [water(400)]
    for kind, where in spots.items():
        for gx, gz in where:
            extras.append(place(copy(nuts[kind]), *G(gx, 0, gz)[:2], yaw=random.uniform(0, 6.28), z=0.4))
    hide(extras, False)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(C.EXPORTS / "twig_boat.glb"))
    extras += list(set(bpy.data.objects) - before)
    pitch, dist, eye = 0.32, 8.5, 1.0
    C.preview("nuts_gamecam", target=tuple(G(0, eye, 0)), cam_loc=tuple(G(0, eye + dist * math.sin(pitch), -dist * math.cos(pitch))),
              res=(1280, 720), fov_y=58)
    for o in extras:
        bpy.data.objects.remove(o)


def render_chestnut(prize, kids):
    """Close-up of the prize at its authored size: husk shut, husk open (petals turned on their
    hinges), and the bare nut tipped toward the camera to show the hilum."""
    hide([prize], False)
    place(prize, 0, yaw=0.35)
    prize.location.z += 0.08       # room for the open petals to swing down
    shots = []
    for name, ang in (("chestnut_shut", 0.0), ("chestnut_open", 0.6), ("chestnut_hilum", None)):
        if ang is None:
            hide(kids[1:])
            prize.rotation_euler.x = -0.9
        else:
            for k, (ax, sign) in zip(kids[1:], ((0, 1), (1, 1), (0, -1), (1, -1))):
                k.rotation_euler[ax] = sign * ang        # game rot.x = Blender x; game rot.z = Blender -y
        C.preview(name, target=(0, 0, 0.26), cam_loc=(0.55, -1.25, 0.72), size=720, ground=(SAND, 0.0))
        shots.append(C.PREVIEWS / f"{name}.png")
    C.contact_sheet(C.PREVIEWS / "chestnut.png", shots, cols=3)


if __name__ == "__main__":
    C.reset(seed=14)
    noise.seed_set(14)
    nuts = {"peanut": build_peanut(), "acorn": build_acorn(), "walnut": build_walnut()}
    prize, kids = build_prize()
    for name, obj in nuts.items():
        print(f"{name}: {C.tri_count([obj])} triangles -> {C.export(name, obj)}")
    print(f"chestnut: {C.tri_count(kids)} triangles ({C.tri_count(kids[:1])} nut) -> {C.export('chestnut', [prize] + kids)}")
    render_lineup(nuts, prize)
    render_gamecam(nuts, prize)
    render_chestnut(prize, kids)
    print("previews:", C.PREVIEWS)
