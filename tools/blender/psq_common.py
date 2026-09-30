"""Shared helpers for the game's Blender asset scripts.

Each asset script builds its geometry in world space around the origin, then calls
`finish(name, parts, camera=...)` to join the parts into one object, render a preview
to art/previews/<name>.png and export art/exports/<name>.glb.

Colours are given as the same hex values the game uses for its stand-in materials.
The scene uses the Standard view transform so previews show them as-is, and the
game's loader converts the exported (linear) colours back, so a GLB part matches the
primitive it replaces.

Axes: Blender is Z-up and the glTF exporter converts to the game's Y-up, so
game (x, y, z) = Blender (x, z, -y). "Forward" in the game (+z) is -Y here.
The helpers at the bottom (`G`, `ellipsoid`, `gtube`, `rot`, ...) take game coordinates,
so numbers can be copied straight from the stand-in code.
"""
import math
import random
from pathlib import Path

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
EXPORTS = ROOT / "art" / "exports"
PREVIEWS = ROOT / "art" / "previews"


def reset(seed=1):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()
    random.seed(seed)


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgb(h):
    return tuple(_lin(((h >> s) & 255) / 255) for s in (16, 8, 0))


_mats = {}


def mat(name, hexcol, rough=0.9, metal=0.0):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    if not m.node_tree:
        m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*hex_rgb(hexcol), 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    _mats[name] = m
    return m


def _obj_from_bmesh(name, bm, material):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    return o


def mesh_from(name, verts, faces, material):
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in verts]
    for f in faces:
        bm.faces.new([vs[i] for i in f])
    bm.normal_update()
    return _obj_from_bmesh(name, bm, material)


def tube(name, points, radius, material, radii=None, sides=1, closed=False):
    """A bevelled poly curve through `points`, converted to a mesh. `radii` scales per point."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = sides
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for i, p in enumerate(points):
        sp.points[i].co = (*p, 1)
        sp.points[i].radius = radii[i] if radii else 1.0
    sp.use_cyclic_u = closed
    o = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(o)
    deps = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(deps))
    bpy.data.objects.remove(o)
    me.materials.clear()
    me.materials.append(material)
    out = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(out)
    return out


def box(name, center, size, material, rot_z=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    o = _obj_from_bmesh(name, bm, material)
    o.location = center
    o.rotation_euler = (0, 0, rot_z)
    return o


def blob(name, center, scale, material, subdiv=1):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    o = _obj_from_bmesh(name, bm, material)
    o.location = center
    o.scale = scale
    return o


def ring(name, center, major, minor, material, axis="Z", segs=12, minor_segs=5):
    """A torus, e.g. a rope lashing. `axis` is the ring's normal."""
    bm = bmesh.new()
    verts = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        row = []
        for j in range(minor_segs):
            b = 2 * math.pi * j / minor_segs
            r = major + minor * math.cos(b)
            row.append(bm.verts.new((r * math.cos(a), r * math.sin(a), minor * math.sin(b))))
        verts.append(row)
    for i in range(segs):
        for j in range(minor_segs):
            a, b = verts[i][j], verts[(i + 1) % segs][j]
            c, d = verts[(i + 1) % segs][(j + 1) % minor_segs], verts[i][(j + 1) % minor_segs]
            bm.faces.new((a, b, c, d))
    o = _obj_from_bmesh(name, bm, material)
    o.location = center
    o.rotation_euler = {"Z": (0, 0, 0), "Y": (math.pi / 2, 0, 0), "X": (0, math.pi / 2, 0)}[axis]
    return o


def join(name, parts):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = o.data.name = name
    for poly in o.data.polygons:
        poly.use_smooth = False
    return o


def join_at(name, parts, origin=(0, 0, 0)):
    """Join `parts` like `join`, then move the object's origin to `origin` (a pivot the game
    rotates about) without moving the geometry. The node keeps an identity rotation."""
    return set_origin(join(name, parts), origin)


def set_origin(obj, origin):
    """Move an untransformed object's origin to `origin` (Blender coords), keeping the geometry put."""
    off = Vector(origin)
    for v in obj.data.vertices:
        v.co -= off
    obj.location = off
    return obj


def tri_count(objs):
    return sum(len(p.vertices) - 2 for o in objs if o.type == "MESH" for p in o.data.polygons)


def clear_objects():
    """Delete every object and orphan mesh, keeping the cached materials."""
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for m in list(bpy.data.meshes):
        if not m.users:
            bpy.data.meshes.remove(m)


def preview(name, target, cam_loc, size=640, ground=None, res=None, fov_y=None, lens=50, ground_size=40):
    """Cycles render to art/previews/<name>.png. `ground` = (hex, z) adds a render-only floor.
    `res` = (w, h) overrides the square `size`; `fov_y` (degrees) matches the game camera."""
    st = stage(target, cam_loc, size, ground, res, fov_y, lens, ground_size)
    render(PREVIEWS / f"{name}.png")
    unstage(st)


def render(path, samples=48):
    bpy.context.scene.cycles.samples = samples
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def unstage(st):
    for o in st["objects"]:
        bpy.data.objects.remove(o)


def stage(target, cam_loc, size=640, ground=None, res=None, fov_y=None, lens=50, ground_size=40):
    """Camera, sun, sky and optional floor for `render`. Returns {"camera", "objects"}."""
    scene = bpy.context.scene
    extras = []
    if ground:
        bpy.ops.mesh.primitive_plane_add(size=ground_size, location=(0, 0, ground[1]))
        g = bpy.context.object
        g.data.materials.append(mat("PreviewGround", ground[0], 0.4))
        extras.append(g)
    aim = bpy.data.objects.new("Aim", None)
    bpy.context.collection.objects.link(aim)
    aim.location = target
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.data.lens = lens
    if fov_y:
        cam.data.sensor_fit = "VERTICAL"
        cam.data.angle_y = math.radians(fov_y)
    cam.constraints.new("TRACK_TO").target = aim
    scene.camera = cam
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 10), rotation=(math.radians(50), 0, math.radians(-35)))
    sun = bpy.context.object
    sun.data.energy = 3.5
    sun.data.color = (1.0, 0.86, 0.68)
    world = bpy.data.worlds.new("World")
    scene.world = world
    if not world.node_tree:
        world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (*hex_rgb(0xf0caa0), 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    scene.view_settings.view_transform = "Standard"
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.render.resolution_x, scene.render.resolution_y = res or (size, size)
    return {"camera": cam, "objects": extras + [cam, sun, aim]}


def contact_sheet(path, files, cols):
    """Tile same-sized PNGs into one image, left to right, top to bottom."""
    import numpy as np
    imgs = [bpy.data.images.load(str(f)) for f in files]
    w, h = imgs[0].size
    rows = -(-len(imgs) // cols)
    sheet = np.ones((rows * h, cols * w, 4), dtype=np.float32)
    for i, img in enumerate(imgs):
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        r, c = divmod(i, cols)
        y0 = (rows - 1 - r) * h
        sheet[y0:y0 + h, c * w:(c + 1) * w] = px.reshape(h, w, 4)
    out = bpy.data.images.new(Path(path).stem, cols * w, rows * h, alpha=True)
    out.pixels.foreach_set(sheet.ravel())
    out.filepath_raw, out.file_format = str(path), "PNG"
    out.save()
    for img in imgs + [out]:
        bpy.data.images.remove(img)
    return path


def export(name, obj):
    """Export `obj` (or a list of objects, e.g. a root empty and its children) as one GLB."""
    EXPORTS.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in obj if isinstance(obj, (list, tuple)) else [obj]:
        o.select_set(True)
    path = EXPORTS / f"{name}.glb"
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True)
    return path


def finish(name, parts, target, cam_loc, ground=None):
    obj = join(name, parts)
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    preview(name, target, cam_loc, ground=ground)
    path = export(name, obj)
    print(f"{name}: {tris} triangles")
    print("preview:", PREVIEWS / f"{name}.png")
    print("glb:", path)


# ---------------------------------------------------------------- game-coordinate helpers

def G(x, y, z):
    """Game (x, y, z) -> Blender. Also right for directions (it's a proper rotation)."""
    return Vector((x, -z, y))


def to_game(v):
    return Vector((v.x, v.z, -v.y))


G_TO_B = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))


def rot(x=0.0, y=0.0, z=0.0):
    """Rotation matrix about the game axes (applied X, then Y, then Z), in game coordinates."""
    return Matrix.Rotation(z, 3, "Z") @ Matrix.Rotation(y, 3, "Y") @ Matrix.Rotation(x, 3, "X")


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def ellipsoid(name, center, radii, material, segs=(12, 6), fn=None, keep_above=None, ico=None, jitter=0.0):
    """Ellipsoid in game coords: a UV sphere, or an icosphere with `ico` subdivisions.
    `fn` warps each scaled local point; `keep_above` cuts the unit sphere at that game-y and keeps
    the top (an open dome); `jitter` randomly pushes vertices in/out for a lumpy, hand-made look."""
    bm = bmesh.new()
    if ico is not None:
        bmesh.ops.create_icosphere(bm, subdivisions=ico, radius=1.0)
    else:
        bmesh.ops.create_uvsphere(bm, u_segments=segs[0], v_segments=segs[1], radius=1.0)
    if keep_above is not None:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, keep_above), plane_no=(0, 0, 1), clear_inner=True)
    for v in bm.verts:
        p = to_game(v.co) * (1 + random.uniform(-jitter, jitter))
        p = Vector((p.x * radii[0], p.y * radii[1], p.z * radii[2]))
        if fn:
            p = fn(p)
        v.co = G(*(Vector(center) + p))
    return _obj_from_bmesh(name, bm, material)


def gtube(name, pts, radius, material, radii=None, sides=1, closed=False):
    return tube(name, [tuple(G(*p)) for p in pts], radius, material, radii, sides=sides, closed=closed)


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


def bake_rot(obj, R, pivot):
    """Rotate an object's vertices by the game-space matrix R about the game point `pivot`."""
    P = Vector(pivot)
    for v in obj.data.vertices:
        v.co = G(*(P + R @ (to_game(v.co) - P)))
    return obj


def surface(obj):
    verts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return BVHTree.FromPolygons(verts, [p.vertices for p in obj.data.polygons])


def hit(bvh, origin, direction):
    """Ray-cast in game coords; returns (point, normal) in game coords."""
    loc, nrm, _, _ = bvh.ray_cast(G(*origin), G(*direction))
    return to_game(loc), to_game(nrm)


def label(text, loc, size=0.14, hexcol=0x151012):
    """Upright text facing Blender -Y (the preview cameras' side). `loc` is in Blender coords."""
    cu = bpy.data.curves.new(text, "FONT")
    cu.body, cu.size, cu.align_x = text, size, "CENTER"
    o = bpy.data.objects.new(text, cu)
    o.data.materials.append(mat("LabelInk", hexcol, 0.5))
    o.location, o.rotation_euler = loc, (math.pi / 2, 0, 0)
    bpy.context.collection.objects.link(o)
    return o


def tricorne(H, felt, trim, skull, size=1.0, band=None):
    """Parts of a three-cornered hat whose brim sits at game point H, one corner forward.
    `size` 1 = Captain Pinch's hat (corners 0.25 from the centre). Optional `band` material."""
    H, k = Vector(H), size
    parts = [ellipsoid("Crown", H + Vector((0, 0.035 * k, 0)), (0.095 * k, 0.11 * k, 0.09 * k), felt, segs=(12, 6), keep_above=-0.3)]
    N, rings, outer = 36, [], []
    for i in range(N):
        th = 2 * math.pi * i / N
        c = abs(math.cos(1.5 * th)) ** 2          # 1 at the three corners (front, back-left, back-right)
        ro, up = (0.15 + 0.1 * c) * k, (0.015 + 0.11 * (1 - c)) * k
        row = [(0.08 * k, 0.0), ((0.08 * k + ro) / 2, up * 0.35), (ro, up)]
        rings.append([H + Vector((r * math.sin(th), y, r * math.cos(th))) for r, y in row])
        outer.append(H + Vector(((ro + 0.004) * math.sin(th), up + 0.004, (ro + 0.004) * math.cos(th))))
    bm = bmesh.new()
    vs = [bm.verts.new(G(*p)) for ring in rings for p in ring]
    for i in range(N):
        for j in range(2):
            a, b = i * 3 + j, ((i + 1) % N) * 3 + j
            bm.faces.new([vs[a], vs[b], vs[b + 1], vs[a + 1]])
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.014 * k)
    parts.append(_obj_from_bmesh("Brim", bm, felt))
    parts.append(gtube("Trim", outer, 0.011 * k, trim, closed=True))
    if band:
        parts.append(gtube("Band", [H + Vector((0.1 * k * math.sin(a), 0.03 * k, 0.095 * k * math.cos(a)))
                                    for a in (2 * math.pi * i / 16 for i in range(16))], 0.018 * k, band, closed=True))
    parts.append(ellipsoid("Skull", H + Vector((0, 0.085 * k, 0.09 * k)), (0.034 * k, 0.031 * k, 0.014 * k), skull, segs=(8, 4)))
    for d in (-1, 1):
        parts.append(gtube("Bone", [H + Vector((-0.04 * d * k, 0.03 * k, 0.09 * k)), H + Vector((0.04 * d * k, 0.065 * k, 0.09 * k))], 0.008 * k, skull))
    return parts
