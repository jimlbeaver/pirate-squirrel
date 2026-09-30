"""Twig boat with an oak-leaf sail -> art/exports/twig_boat.glb

  blender -b -P tools/blender/twig_boat.py

Matches the stand-in in v2's `boat` section: hull half-ellipsoid 0.74 wide, 1.45 long
(half-extents) with its rim at 0.34, deck at 0.2, mast 0.42 toward the bow reaching
2.28 with a woven crow's nest at the top, leaf sail 1.55 tall from 0.42, bowsprit and pinecone figurehead
at the bow. The squirrel rides 0.25 aft of centre, so keep that part of the deck clear.
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import psq_common as C  # noqa: E402

C.reset(seed=7)

TWIG = C.mat("Twig", 0x7d5a36)
TWIG2 = C.mat("TwigDark", 0x684828)
BARK = C.mat("BarkDark", 0x3b2618)
ROPE = C.mat("Rope", 0xd9bf86)
DECK = C.mat("Deck", 0xd8b17a)
DECK2 = C.mat("Deck2", 0xc49a62)
SAIL = C.mat("Sail", 0xe2a73c, rough=0.7)
VEIN = C.mat("Vein", 0xb2702a, rough=0.8)
MOSS = C.mat("Moss", 0x7c9a3b)

A, B, DEPTH, RIM = 0.74, 1.45, 0.5, 0.34   # hull half-width, half-length, depth, rim height
BOW = -1                                    # game +z is Blender -Y
parts = []


def upsweep(u):
    e = max(0.0, abs(u) - 0.62) / 0.38
    return 0.16 * e * e


def hull_pt(u, phi, pad=0.0):
    """Point on the hull. u in [-1, 1] runs stern->bow along the length, phi in [-pi/2, pi/2] runs
    port rim -> keel -> starboard rim."""
    s = math.sqrt(max(0.0, 1 - u * u))
    return (
        (A + pad) * s * math.sin(phi),
        BOW * (B + pad) * u,
        RIM - (DEPTH + pad) * s * math.cos(phi) + upsweep(u),
    )


# --- inner shell (shows as dark gaps between the twigs)
bm = C.bmesh.new()
C.bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=10, radius=1.0)
C.bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 0, 1), clear_outer=True)
for v in bm.verts:
    x, y, z = v.co
    u = y
    v.co = C.Vector((x * (A - 0.02), y * (B - 0.02), RIM + z * (DEPTH - 0.02) + upsweep(u)))
parts.append(C._obj_from_bmesh("Shell", bm, BARK))

# --- lengthwise twigs, converging at bow and stern
N_TWIG, N_PTS = 11, 22
for k in range(N_TWIG):
    phi = -math.pi / 2 + math.pi * k / (N_TWIG - 1)
    rim = k in (0, N_TWIG - 1)
    jig = 0.0 if rim else random.uniform(-0.05, 0.05)
    pts, radii = [], []
    for i in range(N_PTS + 1):
        u = -0.985 + 1.97 * i / N_PTS
        wob = 0.0 if rim else 0.04 * math.sin(i * 1.7 + k * 2.3)
        pts.append(hull_pt(u, phi + jig + wob, pad=0.03 if rim else 0.012))
        radii.append(0.55 + 0.45 * math.sqrt(max(0.0, 1 - u * u)))
    parts.append(C.tube(f"Twig{k}", pts, 0.06 if rim else 0.034, TWIG if (k % 2 or rim) else TWIG2, radii))

# --- rope lashings on the gunwales, plus bundles where the twigs meet at bow and stern
for side in (-1, 1):
    for u in (-0.62, -0.2, 0.2, 0.62):
        x, y, z = hull_pt(u, side * math.pi / 2, pad=0.03)
        r = C.ring("Lash", (x, y, z), 0.07, 0.016, ROPE, axis="Y")
        r.rotation_euler.z = math.atan2(side * A * u / math.sqrt(1 - u * u), BOW * B)
        parts.append(r)
for u in (-0.94, 0.94):
    s = math.sqrt(1 - u * u)
    half_d = (DEPTH * s + 0.04) / 2
    b = C.ring("Bundle", (0, BOW * B * u, RIM + upsweep(u) - half_d + 0.03), half_d, 0.022, ROPE, axis="Y")
    b.scale = ((A * s + 0.05) / half_d, 1, 1)
    parts.append(b)

# --- deck of bark slabs, clear of the squirrel's spot
for j, x in enumerate((-0.48, -0.24, 0.0, 0.24, 0.48)):
    half = 1.3 * math.sqrt(1 - (x / 0.68) ** 2)
    parts.append(C.box(f"Plank{j}", (x, random.uniform(-0.03, 0.03), 0.2 - 0.02 + random.uniform(-0.006, 0.006)),
                       (0.22, 2 * half, 0.04), DECK if j % 2 == 0 else DECK2, rot_z=random.uniform(-0.02, 0.02)))
for y in (-0.95, 0.9):   # cross battens holding the slabs
    half = 0.66 * math.sqrt(1 - (y / 1.36) ** 2)
    parts.append(C.box("Batten", (0, y, 0.215), (2 * half, 0.07, 0.03), TWIG2))

# --- mast: a slightly crooked twig with a stub near the top
MY, MAST_Z0, MAST_H = 0.42 * BOW, 0.15, 2.13


def mast_x(z):
    return 0.03 * math.sin(2.1 * (z - MAST_Z0) / MAST_H)


mast_pts = [(mast_x(z), MY, z) for z in (MAST_Z0 + MAST_H * i / 10 for i in range(11))]
parts.append(C.tube("Mast", mast_pts, 0.045, BARK, [1.0 - 0.35 * i / 10 for i in range(11)]))
parts.append(C.tube("MastStub", [(0.02, MY, 1.72), (0.16, MY - 0.02, 1.84), (0.24, MY - 0.03, 1.87)], 0.02, BARK, [1, 0.8, 0.5]))
for z in (0.46, 1.9):
    parts.append(C.ring("MastTie", (0, MY, z), 0.055, 0.014, ROPE))

# --- crow's nest: a woven twig basket round the masthead, clear of the sail's tip (z 1.97)
NZ0, NZ1, NR0, NR1 = 2.03, 2.2, 0.17, 0.21   # bottom/top height and radius
NX, N_STAVES = mast_x(NZ0), 14
nest_rng = random.Random(3)   # own stream so the moss tufts below keep their places


def nest_r(z):
    return NR0 + (NR1 - NR0) * (z - NZ0) / (NZ1 - NZ0)


parts.append(C.blob("NestFloor", (NX, MY, NZ0), (NR0, NR0, 0.025), BARK))
stave_ang = [2 * math.pi * i / N_STAVES + nest_rng.uniform(-0.05, 0.05) for i in range(N_STAVES)]
for i, a in enumerate(stave_ang):
    top = NZ1 + nest_rng.uniform(0.0, 0.035)
    pts = [(NX + math.cos(a) * nest_r(z), MY + math.sin(a) * nest_r(z), z) for z in (NZ0 - 0.01, top)]
    parts.append(C.tube("NestStave", pts, 0.017, TWIG if i % 2 else TWIG2))
zw = (NZ0 + NZ1) / 2
weave = [(NX + math.cos(a) * (nest_r(zw) + 0.02 * (-1) ** i), MY + math.sin(a) * (nest_r(zw) + 0.02 * (-1) ** i), zw)
         for i, a in enumerate(stave_ang)]
parts.append(C.tube("NestWeave", weave, 0.016, TWIG, closed=True))
for z, minor in ((NZ0 + 0.01, 0.018), (NZ1, 0.024)):
    parts.append(C.ring("NestRim", (NX, MY, z), nest_r(z) + 0.01, minor, ROPE, segs=16))

# --- oak-leaf sail: lobed outline, billowed toward the bow, with midrib and veins
H, Z0, ROWS, COLS = 1.55, 0.42, 44, 8
ANG = math.pi / 2 - 0.75         # same trim angle as the stand-in sail
FRONT = 0.06                     # sits just ahead of the mast


def half_width(t, side):
    if t <= 0.05:
        return 0.02
    env = 0.47 * math.sin(math.pi * min(1.0, (t - 0.05) / 0.97) ** 0.95) ** 0.7
    lobes = 0.6 + 0.4 * abs(math.sin(math.pi * 4.5 * (t - 0.05) / 0.95 + (0.0 if side < 0 else 0.35))) ** 0.55
    return max(0.02, env * lobes)


def leaf_pt(t, s):
    """t along the midrib 0..1, s across -1..1 (fraction of the local half-width)."""
    w = half_width(t, -1 if s < 0 else 1) * abs(s)
    x = w * (1 if s >= 0 else -1)
    billow = 0.14 * math.sin(math.pi * t) * (1 - s * s) + 0.05 * t ** 3
    lx, ly, lz = x, -FRONT - billow, Z0 + t * H
    ca, sa = math.cos(ANG), math.sin(ANG)
    return (lx * ca - ly * sa, MY + lx * sa + ly * ca, lz)


verts, faces = [], []
for r in range(ROWS + 1):
    t = r / ROWS
    for c in range(COLS + 1):
        verts.append(leaf_pt(t, -1 + 2 * c / COLS))
for r in range(ROWS):
    for c in range(COLS):
        a = r * (COLS + 1) + c
        faces.append((a, a + 1, a + COLS + 2, a + COLS + 1))
parts.append(C.mesh_from("SailLeaf", verts, faces, SAIL))

rib = [leaf_pt(t, 0) for t in (i / 20 * 0.97 for i in range(21))]
parts.append(C.tube("Midrib", [leaf_pt(0, 0)[:2] + (Z0 - 0.08,)] + rib, 0.017, VEIN, [1.0] + [1.0 - 0.7 * i / 20 for i in range(21)]))
for side in (-1, 1):
    for n in range(4):
        t0 = 0.05 + 0.95 * (n + 0.5 - (0.0 if side < 0 else 0.35) / math.pi) / 4.5
        if not 0.1 < t0 < 0.9:
            continue
        vpts = [leaf_pt(t0 - 0.07 + 0.07 * f, side * 0.82 * f) for f in (0, 0.33, 0.66, 1.0)]
        parts.append(C.tube("Vein", vpts, 0.008, VEIN, [1, 0.85, 0.65, 0.4]))

# --- bowsprit with a little fork
parts.append(C.tube("Bowsprit", [(0, 1.18 * BOW, 0.4), (0, 1.5 * BOW, 0.6), (0.01, 1.74 * BOW, 0.84)], 0.03, BARK, [1, 0.85, 0.6]))
parts.append(C.tube("Fork", [(0, 1.6 * BOW, 0.7), (0.1, 1.72 * BOW, 0.74), (0.15, 1.78 * BOW, 0.73)], 0.014, BARK, [1, 0.7, 0.4]))

# --- pinecone figurehead: scales on a golden-angle spiral around an egg-shaped core, built along +Z,
# then tipped forward and up onto the bow stem under the bowsprit, lashed on at its stalk
CONE, CONE_TIP = C.mat("Pinecone", 0x8a5a2e), C.mat("PineconeTip", 0x5e3a1c)
PH, PR, RAISE = 0.32, 0.12, math.radians(20)
cone = [C.blob("ConeCore", (0, 0, PH * 0.45), (PR * 0.7, PR * 0.7, PH * 0.5), CONE_TIP)]
N_SCALES = 44
for i in range(N_SCALES):
    f = (i + 0.5) / N_SCALES
    ang = i * 2.39996
    r = PR * math.sin(math.pi * (0.12 + 0.8 * f)) ** 0.7
    tilt = 0.25 + 0.7 * f
    sc = C.blob("Scale", (math.cos(ang) * r * 0.85, math.sin(ang) * r * 0.85, f * PH),
                (0.05 * (1.1 - 0.5 * f), 0.042 * (1.1 - 0.5 * f), 0.018), CONE if i % 3 else CONE_TIP, subdiv=0)
    sc.rotation_euler = (0, -tilt, ang)
    cone.append(sc)
cone.append(C.tube("ConeStalk", [(0, 0, 0.02), (0, 0, -0.1)], 0.028, BARK))
cone.append(C.ring("ConeTie", (0, 0, -0.035), 0.036, 0.016, ROPE))
fig = C.join("Figurehead", cone)
fig.location = (0, 1.4 * BOW, 0.37)
fig.rotation_euler = (-BOW * (math.pi / 2 - RAISE), 0, 0)
parts.append(fig)

# --- moss tufts on the gunwales
for _ in range(7):
    u = random.uniform(-0.75, 0.75)
    side = random.choice((-1, 1))
    x, y, z = hull_pt(u, side * math.pi / 2, pad=0.05)
    parts.append(C.blob("Moss", (x, y, z + 0.03), (0.09, 0.09, 0.06), MOSS))

C.finish("twig_boat", parts, target=(0, 0, 0.7), cam_loc=(3.6, -4.4, 2.6), ground=(0x2a8a93, 0.08))
C.preview("twig_boat_bow", target=(0, 1.45 * BOW, 0.55), cam_loc=(2.4, 2.3 * BOW, 0.8), ground=(0x2a8a93, 0.08))
print("preview:", C.PREVIEWS / "twig_boat_bow.png")
