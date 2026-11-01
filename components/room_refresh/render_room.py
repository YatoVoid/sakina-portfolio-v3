"""In-room Cycles previews (room lighting = what the lightmap bake will see), before / after room_refresh.

    python3 components/room_refresh/render_room.py <scene.blend> <out_prefix> <spp> <views> [--apply]

views: comma list of VIEWS keys. --apply runs room_refresh.apply() on the scene first (the "after").
Same render rules as pipeline/render_preview.py (no haze volume on camera, no rain/steam), so results are
comparable with the room session's previews. The scene file on disk is never written.
"""
import bpy, sys, math, os, time, importlib.util
from mathutils import Vector

scene_path, prefix, spp, views = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4].split(",")
bpy.ops.wm.open_mainfile(filepath=scene_path)
if "--apply" in sys.argv:
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("room_refresh", os.path.join(here, "apply.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    mod.apply()
D, sc = bpy.data, bpy.context.scene
for o in D.objects:
    if o.name.startswith(("Rain", "Steam", "Haze")):
        o.hide_render = True
    if o.name == "Room_Volume":
        o.visible_camera = False
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = spp; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92

b = lambda x, y, z: Vector((x, -z, y))          # three.js (Y-up) -> Blender
VIEWS = {   # name: (camera, target, vertical fov) in Blender coordinates
    "opening": (b(-0.02, 1.12, -0.25), b(-0.02, 0.92, -1.65), 46.3),
    "props":   (Vector((-0.24, 0.80, 1.17)), Vector((-0.26, 1.52, 0.80)), 40),
    "window":  (Vector((0.18, 0.35, 1.50)), Vector((0.20, 2.45, 1.42)), 52),
    "lamp":    (Vector((-0.30, 1.18, 0.98)), Vector((-0.50, 1.68, 0.90)), 42),
    "handle":  (Vector((0.05, 1.95, 1.50)), Vector((-0.10, 2.50, 1.45)), 34),
}
cam = D.objects.new("RefreshCam", D.cameras.new("RefreshCam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.sensor_fit = 'VERTICAL'; cam.data.clip_start = 0.02; cam.data.clip_end = 7000
for name in views:
    pos, tgt, vfov = VIEWS[name]
    cam.location = pos; cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
    cam.data.angle_y = math.radians(vfov)
    sc.render.filepath = f"{prefix}_{name}.jpg"
    t = time.time(); bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath, round(time.time() - t), "s", flush=True)
