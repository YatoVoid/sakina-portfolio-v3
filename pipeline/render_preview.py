"""Cycles preview renders that match the website's framing.
    python3 pipeline/render_preview.py <scene.blend> <out_prefix> [samples]
Views: 'home' = the site's HOME camera; 'tapes' = close-up of tapes + VCR."""
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
VIEWS = {   # name: (camera, target, vertical fov, (width, height))
    "home":  (b(0.12, 0.86, -0.3), b(0.1, 0.98, -1.8), 46, (1280, 720)),       # site HOME before round 2
    "hero":  (b(-0.02, 1.12, -0.25), b(-0.02, 0.92, -1.65), 38, (1600, 724)),  # new HOME (round 2), 2.21:1 screen
    "tapes": (b(0.42, 1.10, -0.78), b(0.42, 0.80, -1.65), 40, (1280, 720)),
    "plant": (b(-0.55, 1.22, -1.05), b(-0.92, 1.02, -1.74), 42, (1280, 720)),
    "ibm":   (b(-1.75, 1.18, -1.55), b(-2.78, 0.80, -1.97), 40, (1280, 720)),   # IBM corner after the slide
    "left":  (b(-0.95, 1.24, -1.30), b(-2.05, 0.98, -2.00), 46, (1280, 720)),      # round 3: left dresser + computer
    "left_wide": (b(0.85, 1.45, 0.75), b(-1.35, 0.95, -1.85), 56, (1600, 900)),     # round 3: spacing left <-> desk
    "nook":  (b(1.55, 1.35, 0.05), b(3.15, 0.85, -1.75), 52, (1280, 720)),         # round 3: right nook
    "tv":    (b(-0.02, 1.00, -1.02), b(-0.02, 0.96, -1.62), 40, (1280, 720)),      # round 3: CRT + VCR close-up
    "orbit_left":  (b(1.296, 1.12, -1.171), b(-0.02, 0.92, -1.65), 38, (1600, 724)),   # HOME, max drag left (az +70)
    "orbit_right": (b(-1.256, 1.12, -0.993), b(-0.02, 0.92, -1.65), 38, (1600, 724)),  # HOME, max drag right (az -62)
}
cam_data = D.cameras.new("PreviewCam"); cam = D.objects.new("PreviewCam", cam_data)
sc.collection.objects.link(cam); sc.camera = cam
cam_data.sensor_fit = 'VERTICAL'; cam_data.clip_start = 0.05; cam_data.clip_end = 7000
ONLY = sys.argv[4].split(",") if len(sys.argv) > 4 else list(VIEWS)
for name, (pos, tgt, vfov, (rx, ry)) in [(k, v) for k, v in VIEWS.items() if k in ONLY]:
    sc.render.resolution_x, sc.render.resolution_y = rx, ry
    sc.render.resolution_percentage = int(__import__('os').environ.get('PCT', '100'))
    cam.location = pos
    cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
    cam_data.angle_y = math.radians(vfov)
    sc.render.filepath = f"{prefix}_{name}.png"
    t = time.time(); bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath, round(time.time() - t), "s", flush=True)
