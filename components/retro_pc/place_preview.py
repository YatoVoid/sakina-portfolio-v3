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
if D.objects.get("L5_IBM_Screen"):            # room light that fakes the old screen glow (a textured area light, visible to camera)
    D.objects["L5_IBM_Screen"].hide_render = True   # old fake screen glow: shows as a hot spot in the new glass
import os
WIDEN = float(os.environ.get("WIDEN", "0.30"))         # extra cabinet width toward the viewer's left (-Y), keyboard lives there
CY = 1.25
def _vshift(o, fn):
    o.data = o.data.copy()
    mw = o.matrix_world; inv = mw.inverted()
    for v in o.data.vertices:
        w = mw @ v.co
        w.y += fn(w.y)
        v.co = inv @ w
    o.data.update()
def widen(W):
    for o in list(D.objects):
        if o.type != "MESH" or o.parent != root or not o.name.startswith(("Cabinet_", "Drawer_")):
            continue
        n = o.name
        cy = sum((o.matrix_world @ Vector(c)).y for c in o.bound_box) / 8
        if n in ("Cabinet_Body", "Cabinet_Top", "Cabinet_Plinth", "Cabinet_Crown") or n.startswith(("Drawer_Front", "Drawer_Gap")) \
                or (n.startswith("Drawer_Mould") and n[-1] in "TB"):
            _vshift(o, lambda y: -W if y < CY else 0.0)
        elif n.startswith(("Cabinet_Foot", "Drawer_Mould")):
            _vshift(o, lambda y, d=(-W if cy < CY else 0.0): d)
        elif n.startswith(("Drawer_Bar", "Drawer_Escutcheon", "Drawer_Keyhole")):
            _vshift(o, lambda y: -W / 2)
if use_new:
    widen(WIDEN)
if use_new:
    for o in list(D.objects):
        if (o.parent == root and o.name.startswith(("PC_", "CRT2_", "Term_"))) or \
           (o.name.startswith("KB_") and any(c.name == "Station" for c in o.users_collection)):   # old keyboard is not parented to the root
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
        bpy.context.view_layer.update()
        m = pol.matrix_world.copy()                    # keep its orientation (faces +X), only move it
        m.translation = Vector((float(os.environ.get("PHOTO_X", "-2.650")), 1.394 + float(os.environ.get("PHOTO_DY", "-0.04")), 0.870))  # world: on top of the monitor, right end
        pol.matrix_world = m
        bd = D.objects.get("Polaroid_Border")           # no white frame: just the photo, cropped tight (no wall/white at the bottom)
        if bd:                                           # thin white border: 3 mm all round the cropped photo
            bd.data = bd.data.copy()
            for v in bd.data.vertices:
                v.co.x = 0.040 if v.co.x > 0 else -0.040
                v.co.z = 0.051 if v.co.z > 0 else -0.035   # photo is centred at z +0.008 on the frame
        ph = D.objects["Polaroid_Photo"]
        me = ph.data.copy(); ph.data = me
        W, H = 0.037, 0.040                              # half sizes (m): 7.4 x 8.0 cm print
        for v in me.vertices:
            v.co.x = W if v.co.x > 0 else -W
            v.co.z = H if v.co.z > 0 else -H
        U0, U1, V0, V1 = 0.14, 0.88, 0.0, 0.80            # crop of profile.jpg around her
        for l in me.uv_layers.active.data:
            l.uv = (U1 if l.uv[0] > 0.5 else U0, V1 if l.uv[1] > 0.5 else V0)
        pol.rotation_euler = (0, 0, 0)                 # upright, no lean: faces straight into the room
        bpy.context.view_layer.update()
        print("POL", pol.parent.name if pol.parent else None, tuple(pol.matrix_world.translation), tuple(pol.rotation_euler), pol.matrix_world.to_euler())
    for o in D.objects:                               # preview only: calmer screen glow in the dark room
        for sl in o.material_slots:
            if sl.material and sl.material.name.startswith("PC_Glass"):
                for n in sl.material.node_tree.nodes:
                    if n.type == "BSDF_PRINCIPLED":
                        n.inputs["Emission Strength"].default_value = 0.35
    bpy.context.view_layer.update()

def _bb(n):
    o = D.objects.get(n)
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [round(min(w[i] for w in ws), 3) for i in range(3)], [round(max(w[i] for w in ws), 3) for i in range(3)]
if os.environ.get("DEBUG"):
    for n in ("PC_Monitor", "PC_Case", "Polaroid_Border", "PC_Keyboard", "Cabinet_Top"):
        print("BB", n, *_bb(n))
    sys.exit(0)
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = spp; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.image_settings.file_format = "JPEG"
cd = D.cameras.new("PV"); cam = D.objects.new("PV", cd); sc.collection.objects.link(cam); sc.camera = cam
cd.sensor_fit = "VERTICAL"; cd.clip_start = 0.05; cd.clip_end = 7000
VIEWS = {   # pos, target, vertical fov  (Blender coords)
    "ibm":  ((-1.55, 1.55, 0.98), (-2.80, 1.25, 0.80), 46),      # like the site's IBM view (from the room side)
    "room": ((-0.40, 0.10, 1.45), (-2.85, 1.30, 0.70), 58),      # wider, shows the cabinet against the wall
    "top":  ((-2.50, 1.25, 3.2), (-2.50, 1.25, 0.0), 40),
    "pwr": ((-2.15, 1.45, 0.80), (-2.70, 1.37, 0.71), 30),
    "close": ((-1.95, 1.22, 0.93), (-2.72, 1.24, 0.88), 40),     # like the reference screenshot: monitor + photo on its right side
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
