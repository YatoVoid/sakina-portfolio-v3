"""Position/look preview ONLY (no bake, nothing written to the room): opens the v17 room, replaces the centre CRT
(Monitor collection: CRT_*, Scr_*) with the new CRT from export/crt_source.blend at (-0.02, 1.600, 0.813), renders views.
    python3 components/crt/place_preview.py <out_prefix> <samples> <views> [new|old]
Views: tv, wide, ctrl, side.  Never edits assets/sakina-v17.blend or any pipeline file."""
import math, os, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
prefix, spp, views = sys.argv[1], int(sys.argv[2]), sys.argv[3].split(",")
use_new = (sys.argv[4] if len(sys.argv) > 4 else "new") != "old"
bpy.ops.wm.open_mainfile(filepath=str(ROOT / "assets/sakina-v17.blend"))
D, sc = bpy.data, bpy.context.scene
for o in D.objects:
    if o.name.startswith(("Rain", "Steam", "Haze")):
        o.hide_render = True
    if o.name == "Room_Volume":
        o.visible_camera = False
if use_new and D.objects.get("L6_TV_Screen"):        # old point light 5 cm in front of the glass: shows as a hot spot in the new glass
    D.objects["L6_TV_Screen"].hide_render = True
if use_new:
    for o in list(D.objects):
        if o.name.startswith(("CRT_", "Scr_")):
            D.objects.remove(o)
    with D.libraries.load(str(ROOT / "components/crt/export/crt_source.blend")) as (src, dst):
        dst.objects = list(src.objects)
    holder = D.objects.new("NewCRT_Root", None); sc.collection.objects.link(holder)
    holder.location = Vector((-0.02, 1.600, 0.813))
    for o in dst.objects:
        if o is not None and o.type in {"MESH", "FONT", "CURVE"}:
            sc.collection.objects.link(o); o.parent = holder
    bpy.context.view_layer.update()
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = spp; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.image_settings.file_format = "JPEG"
cd = D.cameras.new("PV"); cam = D.objects.new("PV", cd); sc.collection.objects.link(cam); sc.camera = cam
cd.sensor_fit = "VERTICAL"; cd.clip_start = 0.05; cd.clip_end = 7000
VIEWS = {   # pos, target, vertical fov  (Blender coords; the TV looks toward -Y into the room)
    "tv":   ((0.02, 0.35, 1.05), (-0.02, 1.60, 1.00), 36),
    "wide": ((0.20, -0.60, 1.30), (-0.02, 1.60, 0.95), 50),
    "ctrl": ((0.00, 0.80, 0.92), (-0.02, 1.60, 0.90), 24),
    "side": ((-0.75, 0.95, 1.10), (-0.02, 1.65, 0.98), 34),
}
for v in views:
    pos, tgt, fov = VIEWS[v]
    cam.location = Vector(pos)
    cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    cd.angle_y = math.radians(fov)
    sc.render.filepath = f"{prefix}_{v}.jpg"
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath, flush=True)
