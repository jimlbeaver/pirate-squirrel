"""Blender asset-pipeline starter: build a chestnut, render a preview, export a GLB.

Run either way:
  pip install bpy            # Blender as a Python module (bpy 5.x needs Python 3.11)
  python3 tools/blender/chestnut_demo.py
or
  blender -b -P tools/blender/chestnut_demo.py

Outputs:
  art/previews/chestnut.png   Cycles preview render
  art/exports/chestnut.glb    game-ready asset (glTF binary)

Conventions for game assets:
  - 1 Blender unit = 1 game unit. The squirrel is about 0.9 units tall; branches are about 0.6 wide.
  - Blender is Z-up; the glTF exporter converts to the game's Y-up.
  - Keep each asset low-poly, with simple materials (Principled BSDF base colour and roughness).
"""
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
PREVIEW = ROOT / "art" / "previews" / "chestnut.png"
EXPORT = ROOT / "art" / "exports" / "chestnut.glb"
PREVIEW.parent.mkdir(parents=True, exist_ok=True)
EXPORT.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def material(name, rgb, rough=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    return m


# --- the chestnut: glossy nut, pale cap, little stem
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, segments=24, ring_count=12)
nut = bpy.context.object
nut.name = "Chestnut"
nut.scale = (1, 1, 0.88)
nut.data.materials.append(material("NutShell", (0.34, 0.15, 0.05), 0.3))
bpy.ops.object.shade_smooth()

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.163, segments=24, ring_count=12, location=(0, 0, 0.02))
cap = bpy.context.object
cap.name = "Cap"
cap.scale = (1, 1, 0.5)
cap.data.materials.append(material("NutCap", (0.72, 0.56, 0.32), 0.8))
bpy.ops.object.shade_smooth()

bpy.ops.mesh.primitive_cone_add(radius1=0.02, radius2=0.012, depth=0.08, location=(0, 0, 0.14))
stem = bpy.context.object
stem.name = "Stem"
stem.data.materials.append(material("Stem", (0.23, 0.15, 0.09), 0.9))

for o in (cap, stem):
    o.parent = nut

# --- preview render
bpy.ops.object.camera_add(location=(0.55, -0.55, 0.4))
cam = bpy.context.object
track = cam.constraints.new("TRACK_TO")
track.target = nut
scene.camera = cam
bpy.ops.object.light_add(type="SUN", location=(2, -2, 5))
bpy.context.object.data.energy = 4
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.95, 0.82, 0.62, 1)
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 32
scene.render.resolution_x = scene.render.resolution_y = 512
scene.render.filepath = str(PREVIEW)
bpy.ops.render.render(write_still=True)

# --- export only the asset (not camera or light)
bpy.ops.object.select_all(action="DESELECT")
for o in (nut, cap, stem):
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(EXPORT), export_format="GLB", use_selection=True)
print("preview:", PREVIEW)
print("glb:", EXPORT)
