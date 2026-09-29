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
"""
import math
import random
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
EXPORTS = ROOT / "art" / "exports"
PREVIEWS = ROOT / "art" / "previews"


def reset(seed=1):
    bpy.ops.wm.read_factory_settings(use_empty=True)
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


def preview(name, target, cam_loc, size=640, ground=None):
    """Cycles render to art/previews/<name>.png. `ground` = (hex, z) adds a render-only floor."""
    scene = bpy.context.scene
    extras = []
    if ground:
        bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, ground[1]))
        g = bpy.context.object
        g.data.materials.append(mat("PreviewGround", ground[0], 0.4))
        extras.append(g)
    aim = bpy.data.objects.new("Aim", None)
    bpy.context.collection.objects.link(aim)
    aim.location = target
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.data.lens = 50
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
    scene.cycles.samples = 48
    scene.render.resolution_x = scene.render.resolution_y = size
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(PREVIEWS / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    for o in extras + [cam, sun, aim]:
        bpy.data.objects.remove(o)


def export(name, obj):
    EXPORTS.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
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
