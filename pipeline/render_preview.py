"""Cycles preview renders that match the website's framing.
    python3 pipeline/render_preview.py <scene.blend> <out_prefix> [samples]
Views: 'home' = the site's HOME camera; 'tapes' = close-up of tapes + VCR;
'chair' = right-wall armchair, front 3/4 view; 'chair_wide' = right side of the room."""
import bpy, sys, math, mathutils, time

scene_path, prefix = sys.argv[1], sys.argv[2]
SPP = int(sys.argv[3]) if len(sys.argv) > 3 else 48
bpy.ops.wm.open_mainfile(filepath=scene_path)
D, sc = bpy.data, bpy.context.scene

# Match what the web shows: no in-room haze volume on camera, no rain/steam, outside city visible.
for o in D.objects:
    if o.name.startswith(("Rain", "Steam", "Haze")):
        o.hide_render = True
    if o.name == "Room_Volume":
        o.visible_camera = False
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.render.image_settings.file_format = 'PNG'

# three.js (x, y, z) Y-up  ->  Blender (x, -z, y)
b = lambda x, y, z: mathutils.Vector((x, -z, y))
VIEWS = {
    "home":  (b(0.12, 0.86, -0.3), b(0.1, 0.98, -1.8), 46),
    "tapes": (b(0.42, 1.10, -0.78), b(0.42, 0.80, -1.65), 40),
    "chair": (b(1.95, 1.10, -0.55), b(3.15, 0.52, -1.42), 42),
    "chair_wide": (b(1.30, 1.45, 0.10), b(3.05, 0.55, -1.55), 62),
}
cam_data = D.cameras.new("PreviewCam"); cam = D.objects.new("PreviewCam", cam_data)
sc.collection.objects.link(cam); sc.camera = cam
cam_data.sensor_fit = 'VERTICAL'; cam_data.clip_start = 0.05; cam_data.clip_end = 7000
ONLY = sys.argv[4].split(",") if len(sys.argv) > 4 else list(VIEWS)
for name, (pos, tgt, vfov) in [(k, v) for k, v in VIEWS.items() if k in ONLY]:
    cam.location = pos
    cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
    cam_data.angle_y = math.radians(vfov)
    sc.render.filepath = f"{prefix}_{name}.png"
    t = time.time(); bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath, round(time.time() - t), "s", flush=True)
