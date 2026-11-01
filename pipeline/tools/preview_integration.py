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
    "wall_full":  (b(-1.2, 1.25, -0.10), b(-3.0, 1.35, -1.25), 55),  # left wall: IBM computer + gallery wall + clock
    "wall_close": (b(-1.7, 1.45, 0.00),  b(-3.0, 1.45, -1.25), 40),  # gallery wall close-up
    "wall_head": (b(-1.10, 1.45, -1.00), b(-3.0, 1.45, -1.25), 42),  # head-on to the gallery wall
    "wall_wide": (b(-0.90, 1.30, -0.55), b(-3.0, 1.15, -1.25), 58),  # IBM computer + gallery wall + clock, wide
    "crt":      (b(0.12, 1.02, -0.80), b(-0.02, 0.99, -1.65), 34),   # CRT front, close
    "crt_side": (b(0.55, 1.14, -1.00), b(-0.02, 0.97, -1.70), 36),   # CRT 3/4 from the right: bezel depth, funnel, housing
    "win_top":   (b(0.55, 2.35, -0.60), b(-0.10, 1.10, -2.45), 58),   # high angle onto the desk + window (like the reference shot)
    "win_side":  (b(-1.25, 1.55, -1.80), b(-0.10, 1.60, -2.60), 50),   # from the left, shows reveal depth and the two sashes
    "win_front": (b(-0.10, 1.60, -1.40), b(-0.10, 1.60, -2.60), 48),   # straight on
    "clocks":    (b(-1.80, 1.70, -1.00), b(-1.80, 2.00, -2.50), 52),   # back wall left of the window: clocks + degree frames
    "back_wall": (b(-0.70, 1.60, -0.20), b(-1.80, 1.90, -2.50), 62),   # wider, same wall with the desk end and curtain
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
