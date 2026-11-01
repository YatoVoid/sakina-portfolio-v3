"""Quick UNBAKED integration previews (Cycles, low samples, denoised). Not the lighting bake.

    python3 pipeline/tools/preview_integration.py <scene.blend> <out_prefix> [samples=24] [views=home,window,desk]

Same display setup as pipeline/render_preview.py (no haze/rain/steam on camera, CPU). Output 960x540 PNG per view.
Colours are Cycles with the scene's live lights, so they differ from the final lightmap look by design.
"""
import bpy, sys, math, mathutils, time

scene_path, prefix = sys.argv[1], sys.argv[2]
SPP = int(sys.argv[3]) if len(sys.argv) > 3 else 24
ONLY = sys.argv[4].split(",") if len(sys.argv) > 4 else ["home", "window", "desk"]
bpy.ops.wm.open_mainfile(filepath=scene_path)
D, sc = bpy.data, bpy.context.scene
for o in D.objects:
    if o.name.startswith(("Rain", "Steam", "Haze")):
        o.hide_render = True
    if o.name == "Room_Volume":
        o.visible_camera = False
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = SPP; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 540, 100
sc.render.image_settings.file_format = 'PNG'

b = lambda x, y, z: mathutils.Vector((x, -z, y))        # three.js (x, y, z) Y-up -> Blender (x, -z, y)
VIEWS = {
    "home":   (b(0.12, 0.86, -0.3),  b(0.10, 0.98, -1.8),  46),   # site HOME camera
    "window": (b(-0.02, 1.12, -0.25), b(-0.10, 1.15, -2.4), 46),   # round-3 opening camera, toward the window
    "desk":   (b(0.95, 1.20, -0.55),  b(0.10, 0.76, -1.55), 42),   # desk close-up from the right
    "desk_top": (b(0.55, 0.98, -0.80), b(0.45, 0.72, -1.50), 45),  # tabletop grain + front edge
    "drawer":   (b(0.20, 0.80, -0.62), b(0.20, 0.62, -1.32), 40),  # drawer front, pull, aprons
    "mug":      (b(-0.02, 0.98, -1.02), b(-0.23, 0.77, -1.40), 36),  # mug + coaster, from the front-right, above the desk
    "chair":    (b(-0.40, 1.30, 0.15),  b(-0.95, 0.50, -0.90), 52),  # white chair beside the desk, from the front
    "chair_side": (b(0.45, 1.20, -0.25), b(-0.95, 0.50, -0.90), 50),  # chair seen with the desk edge
}
cam_data = D.cameras.new("PreviewCam"); cam = D.objects.new("PreviewCam", cam_data)
sc.collection.objects.link(cam); sc.camera = cam
cam_data.sensor_fit = 'VERTICAL'; cam_data.clip_start = 0.05; cam_data.clip_end = 7000
for name in ONLY:
    pos, tgt, vfov = VIEWS[name]
    cam.location = pos
    cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
    cam_data.angle_y = math.radians(vfov)
    sc.render.filepath = f"{prefix}_{name}.png"
    t = time.time(); bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath, round(time.time() - t), "s", flush=True)
