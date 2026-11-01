"""Position preview ONLY (no bake, no room file is written): opens the v17 room, swaps the left-wall PC for the
new retro PC from export/retro_pc_source.blend, optionally shifts the cabinet, renders quick views.
    python3 components/retro_pc/place_preview.py <out_prefix> <samples> <views> [shift_y]
Views: ibm, room, top.  shift_y default -0.04 (cabinet 4 cm toward the viewer's left when facing the wall).
Nothing here edits assets/sakina-v17.blend or any pipeline file."""
import math, sys
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
prefix, spp, views = sys.argv[1], int(sys.argv[2]), sys.argv[3].split(",")
shift = float(sys.argv[4]) if len(sys.argv) > 4 else -0.04
use_new = shift != 99                       # 99 = untouched "before"
bpy.ops.wm.open_mainfile(filepath=str(ROOT / "assets/sakina-v17.blend"))
D, sc = bpy.data, bpy.context.scene
for o in D.objects:
    if o.name.startswith(("Rain", "Steam", "Haze")):
        o.hide_render = True
    if o.name == "Room_Volume":
        o.visible_camera = False
root = D.objects["Station_Root"]
if use_new:
    for o in list(D.objects):
        if o.parent == root and o.name.startswith(("PC_", "CRT2_", "Term_Key_")):
            D.objects.remove(o)
    with D.libraries.load(str(ROOT / "components/retro_pc/export/retro_pc_source.blend")) as (src, dst):
        dst.objects = list(src.objects)
    holder = D.objects.new("NewPC_Root", None)
    sc.collection.objects.link(holder)
    holder.location = (-2.675, 1.25, 0.55)
    holder.rotation_euler = (0, 0, math.radians(90))
    for o in dst.objects:
        if o is not None:
            sc.collection.objects.link(o)
            o.parent = holder
    bpy.context.view_layer.update()
    holder.parent = root
    holder.matrix_parent_inverse = root.matrix_world.inverted()
    root.location.y += shift
    pol = D.objects.get("Polaroid")                   # re-stick the Polaroid on the new monitor's right bezel corner
    if pol:
        pol.location.x += 0.013
        pol.location.y -= 0.028
    for o in D.objects:                               # preview only: calmer screen glow in the dark room
        for sl in o.material_slots:
            if sl.material and sl.material.name.startswith("PC_Glass"):
                for n in sl.material.node_tree.nodes:
                    if n.type == "BSDF_PRINCIPLED":
                        n.inputs["Emission Strength"].default_value = 0.6
    bpy.context.view_layer.update()

sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = spp; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.image_settings.file_format = "JPEG"
cd = D.cameras.new("PV"); cam = D.objects.new("PV", cd); sc.collection.objects.link(cam); sc.camera = cam
cd.sensor_fit = "VERTICAL"; cd.clip_start = 0.05; cd.clip_end = 7000
VIEWS = {   # pos, target, vertical fov  (Blender coords)
    "ibm":  ((-1.55, 1.55, 0.98), (-2.80, 1.25, 0.80), 46),      # like the site's IBM view (from the room side)
    "room": ((-0.40, 0.10, 1.45), (-2.85, 1.30, 0.70), 58),      # wider, shows the cabinet against the wall
    "top":  ((-2.50, 1.25, 3.2), (-2.50, 1.25, 0.0), 40),
}
for v in views:
    pos, tgt, fov = VIEWS[v]
    cam.location = Vector(pos)
    cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    cd.angle_y = math.radians(fov)
    if v == "top":
        for o in D.objects:
            if o.name in ("Ceiling",):
                o.hide_render = True
    sc.render.filepath = f"{prefix}_{v}.jpg"
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath, flush=True)
