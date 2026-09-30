"""Style-check lineup: the exported GLBs side by side at true game scale.

  blender -b -P tools/blender/lineup.py [-- --boat path/to/twig_boat.glb]

Loads art/exports/*.glb (run the asset scripts first) and renders two views to art/previews/:
  lineup.png          3/4 view with labels, left to right in size order
  lineup_gamecam.png  the follow camera's view (6.2 behind, pitch 0.32 rad, 58 deg vertical FOV)
Scales are the game's: the chestnut prize at 1x, sea nuts at 2.4x, Captain Pinch at 1.45x.
`--boat` swaps in a boat from another branch without committing it here, e.g.
  git show origin/<branch>:art/exports/twig_boat.glb > art/previews/ref/twig_boat.glb   (cmd, binary-safe)
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import psq_common as C  # noqa: E402

import bpy  # noqa: E402

SAND, WATER = 0xe8d3a1, 0x2a8a93
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
BOAT = Path(ARGS[ARGS.index("--boat") + 1]) if "--boat" in ARGS else C.EXPORTS / "twig_boat.glb"


def load(name, loc, scale=1.0, yaw=0.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(BOAT if name == "twig_boat" else C.EXPORTS / f"{name}.glb"))
    imported = set(bpy.data.objects) - before
    holder = bpy.data.objects.new(f"{name}_at", None)
    bpy.context.collection.objects.link(holder)
    for o in imported:
        if o.parent is None:
            o.parent = holder
        if o.name.startswith("Ears"):       # the hat is on, so the ears are hidden, as equip('hat') does
            o.hide_render = True
    holder.location, holder.scale, holder.rotation_euler = loc, (scale,) * 3, (0, 0, yaw)
    return holder


def water(center, size):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(center[0], center[1], 0.02))
    bpy.context.object.data.materials.append(C.mat("Water", WATER, 0.26, 0.18))


def label(text, x, y=-1.0, size=0.12):
    for i, line in enumerate(text.split("\n")):
        C.label(line, (x, y - 0.1 * i, 0.08 + 0.15 * (text.count("\n") - i)), size=size)


# assets face game +z = Blender -Y, i.e. toward a camera on the -Y side
C.reset()
ROW = [  # glb, x, label, scale, lift, yaw
    ("chestnut", -2.45, "chestnut\nprize 1x", 1.0, 0.14, 0.0),
    ("chestnut", -1.85, "sea nut\n2.4x", 2.4, 0.34, 0.0),
    ("crab", -1.0, "crab", 1.0, 0.0, 0.25),
    ("squirrel", 0.05, "squirrel\n(rest pose)", 1.0, 0.0, -0.3),
    ("captain_pinch", 1.2, "Captain Pinch\n1.45x", 1.45, 0.0, -0.25),
    ("twig_boat", 3.45, "twig boat\n(PR #17)", 1.0, 0.0, math.radians(115)),
]
for glb, x, text, scale, lift, yaw in ROW:
    load(glb, (x, 0, lift), scale, yaw)
    label(text, x, y=-2.0 if glb == "twig_boat" else -1.0)
water((4.4, 0.9), 4.0)
C.preview("lineup", target=(0.6, 0, 0.75), cam_loc=(1.2, -9.4, 2.9), res=(1800, 820), lens=38, ground=(SAND, 0.0))

# the same assets as the follow camera sees them: squirrel at the origin facing -Y, crabs facing him
C.clear_objects()
load("squirrel", (0, 0, 0))
load("crab", (-1.1, -2.6, 0), 1.0, math.pi + 0.3)
load("crab", (1.4, -4.2, 0), 1.0, math.pi - 0.4)
load("captain_pinch", (0.25, -3.6, 0), 1.45, math.pi)
load("chestnut", (0.55, -1.3, 0.14), 1.0)
load("twig_boat", (4.2, -6.5, 0), 1.0, math.radians(200))
load("chestnut", (2.6, -5.0, 0.36), 2.4)
water((5.0, -6.0), 6.0)
pitch, dist, eye = 0.32, 6.2, 0.55
C.preview("lineup_gamecam", target=(0, 0, eye), cam_loc=(0, dist * math.cos(pitch), eye + dist * math.sin(pitch)),
          res=(1280, 720), fov_y=58, ground=(SAND, 0.0), ground_size=80)
print("boat:", BOAT)
print("previews:", C.PREVIEWS)
