"""Isolated preview renders for a component (Cycles, CPU). Never touches the room scene.

Two lighting rigs:
  studio — neutral grey sweep, soft key/fill/rim: judges shape and material truthfully.
  night  — dark walnut desk top, warm desk-lamp key (~2700 K), faint cool screen/window fill: imitates the
           room's mood so the component can be judged in context. The real look comes from the room bake.
"""
import bpy, math, os
from mathutils import Vector
from .pbr import Mat, hex_rgba


def bounds(root):
    pts = []
    for o in [root] + list(root.children_recursive):
        if o.type == 'MESH':
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def _clear_rig():
    for o in list(bpy.data.objects):
        if o.get("studio_rig"):
            bpy.data.objects.remove(o, do_unlink=True)


def _tag(o):
    o["studio_rig"] = True
    bpy.context.scene.collection.objects.link(o)
    return o


def _area(name, loc, target, power, size, colour=(1, 1, 1), shape='RECTANGLE', size_y=None):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = power; d.color = colour; d.shape = shape
    d.size = size; d.size_y = size_y or size
    o = _tag(bpy.data.objects.new(name, d)); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o


def _point(name, loc, power, colour, radius=0.02):
    d = bpy.data.lights.new(name, 'POINT'); d.energy = power; d.color = colour; d.shadow_soft_size = radius
    o = _tag(bpy.data.objects.new(name, d)); o.location = loc
    return o


def _floor(rig, size):
    me = bpy.data.meshes.new("StudioFloor")
    s = size
    if rig == "studio":   # sweep: floor curving up into a back wall
        verts, faces = [], []
        n = 16
        for i in range(n + 1):
            a = i / n * math.pi / 2
            y = s * 0.6 + math.sin(a) * s * 0.4
            z = (1 - math.cos(a)) * s * 0.4
            verts += [(-s * 2, y, z), (s * 2, y, z)]
        verts = [(x, y, z) for x, y, z in verts]
        # flat part toward camera
        verts = [(-s * 2, -s * 2, 0), (s * 2, -s * 2, 0)] + verts + [(-s * 2, s * 1.2, s * 2.5), (s * 2, s * 1.2, s * 2.5)]
        rows = len(verts) // 2
        faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(rows - 1)]
        me.from_pydata(verts, [], faces)
        for p in me.polygons:
            p.use_smooth = True
        m = Mat("Studio_Grey").base("#7a7a7a").set(Roughness=0.9).material
    else:                 # desk top: walnut-ish, slightly glossy, with grain direction along X
        me.from_pydata([(-s * 2, -s * 2, 0), (s * 2, -s * 2, 0), (s * 2, s * 2, 0), (-s * 2, s * 2, 0)], [], [(0, 1, 2, 3)])
        mm = Mat("Studio_Desk")
        grain = mm.noise(3.0, 10.0, 0.7, distortion=4.0)
        mm.nt.nodes.remove(grain)
        mapping = mm.node("ShaderNodeMapping", (-1250, 300)); mapping.inputs["Scale"].default_value = (1, 18, 1)
        mm.link(mm.coord(), mapping.inputs["Vector"])
        w = mm.node("ShaderNodeTexNoise", (-1100, 300)); w.inputs["Scale"].default_value = 6
        w.inputs["Detail"].default_value = 12; w.inputs["Distortion"].default_value = 1.5
        mm.link(mapping.outputs["Vector"], w.inputs["Vector"])
        r = mm.ramp(w.outputs["Fac"], [(0.35, "#2a1a10"), (0.6, "#4a2f1c")], loc=(-800, 300))
        mm.link(r.outputs["Color"], mm.bsdf.inputs["Base Color"])
        mm.set(Roughness=0.42, **{"Coat Weight": 0.25, "Coat Roughness": 0.25})
        m = mm.material
    o = _tag(bpy.data.objects.new("StudioFloor", me)); o.data.materials.append(m)
    return o


def setup_rig(rig, root):
    _clear_rig()
    sc = bpy.context.scene
    lo, hi = bounds(root)
    c = (lo + hi) / 2; size = max((hi - lo).length, 0.05)
    _floor(rig, size * 1.5)
    w = sc.world or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if rig == "studio":
        bg.inputs["Color"].default_value = hex_rgba("#8a8a8a"); bg.inputs["Strength"].default_value = 0.25
        k = size * 2.2
        _area("Key", c + Vector((-k, -k, k * 0.9)), c, 260 * size ** 2, size * 1.6, (1.0, 0.97, 0.93))
        _area("Fill", c + Vector((k * 1.2, -k * 0.6, k * 0.4)), c, 70 * size ** 2, size * 2.0, (0.93, 0.96, 1.0))
        _area("Rim", c + Vector((k * 0.4, k * 1.3, k * 1.1)), c, 180 * size ** 2, size * 1.2)
    else:
        bg.inputs["Color"].default_value = hex_rgba("#0b0d14"); bg.inputs["Strength"].default_value = 0.4
        # desk lamp: warm, above-left-front, like the room's red lamp pool
        _point("Lamp", c + Vector((-size * 0.9, -size * 0.7, size * 1.3)), 33 * size ** 2 * 10, (1.0, 0.72, 0.45), size * 0.08)
        # cool fill from the screen / window side
        _area("ScreenFill", c + Vector((size * 1.4, -size * 0.4, size * 0.6)), c, 18 * size ** 2, size, (0.55, 0.7, 1.0))
        _area("RimWarm", c + Vector((size * 0.5, size * 1.4, size * 1.0)), c, 40 * size ** 2, size * 0.8, (1.0, 0.8, 0.6))
    return c, size


def _camera(c, size, yaw_deg, pitch_deg, dist_k, lens, focus=None):
    cam = bpy.data.objects.get("StudioCam")
    if cam is None:
        cam = bpy.data.objects.new("StudioCam", bpy.data.cameras.new("StudioCam"))
        bpy.context.scene.collection.objects.link(cam)
    cam.data.lens = lens; cam.data.clip_start = 0.005; cam.data.clip_end = 200
    target = focus if focus is not None else c
    yaw, pitch = math.radians(yaw_deg), math.radians(pitch_deg)
    d = size * dist_k
    # yaw 0 = straight in front (camera on -Y looking +Y)
    off = Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch))) * d
    cam.location = target + off
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.dof.use_dof = True; cam.data.dof.focus_distance = d; cam.data.dof.aperture_fstop = 8.0
    bpy.context.scene.camera = cam
    return cam


VIEWS = {   # name: (yaw, pitch, distance factor, lens mm)
    "hero":  (-35, 22, 2.3, 60),
    "front": (0, 8, 2.4, 70),
    "side":  (90, 10, 2.4, 70),
    "back":  (150, 25, 2.4, 60),
    "top":   (-20, 60, 2.2, 60),
}


def render(root, out_dir, name, rigs=("studio", "night"), views=("hero", "front", "side", "back"),
           samples=64, res=(1200, 900), closeups=()):
    """closeups: [(label, world_point, size_override, yaw, pitch)] — detail shots."""
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 90
    sc.cycles.max_bounces = 8
    os.makedirs(out_dir, exist_ok=True)
    files = []
    for rig in rigs:
        c, size = setup_rig(rig, root)
        shots = [(v, VIEWS[v], None) for v in views]
        shots += [(f"detail-{lab}", (yaw, pitch, 1.0, 85), (Vector(p), s)) for lab, p, s, yaw, pitch in closeups]
        for label, (yaw, pitch, dk, lens), focus in shots:
            if focus:
                _camera(focus[0], focus[1], yaw, pitch, 3.6, lens, focus[0])
            else:
                _camera(c, size, yaw, pitch, dk, lens)
            path = os.path.join(out_dir, f"{name}_{rig}_{label}.jpg")
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True)
            files.append(path)
            print("RENDERED", path, flush=True)
    _clear_rig()
    return files
