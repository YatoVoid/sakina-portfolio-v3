"""Cycles studio previews for one component — independent of the room lighting.

Usage: python3 components/_lib/preview.py <name> [samples=96] [views=hero,front,side,back,detail,mood]

Renders components/<name>/export/<name>.blend (the exact baked materials that go into the GLB) on a
neutral grey sweep with a 3-light studio rig, plus a "mood" shot with one warm lamp-like key to judge the
material in a dark warm setting (an approximation, NOT the room bake). Output: phone-sized JPGs + a contact
sheet in components/<name>/previews/.
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, hex_lin  # noqa: E402

VIEWS = {  # azimuth deg (0 = front; front faces -Y as in the room), elevation deg, distance factor, lens
    "hero":   (-35, 18, 1.0, 70),
    "front":  (0, 8, 1.0, 85),
    "side":   (90, 8, 1.0, 85),
    "back":   (160, 20, 1.0, 70),
    "detail": (-20, 25, 0.5, 100),
    "mood":   (-30, 14, 1.0, 70),
}


def bbox(objs):
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for ob in objs:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    return lo, hi


def area(name, loc, target, size, energy, color="#ffffff"):
    ld = bpy.data.lights.new(name, "AREA")
    ld.size = size; ld.energy = energy; ld.color = hex_lin(color)[:3]
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (target - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


def setup(objs, mood=False):
    scn = bpy.context.scene
    for ob in [o for o in scn.objects if o.get("_studio")]:
        bpy.data.objects.remove(ob)
    lo, hi = bbox(objs)
    ctr = (lo + hi) / 2
    r = max((hi - lo).length / 2, 0.05)
    # sweep: floor + curved back, scaled to the object
    bpy.ops.mesh.primitive_plane_add(size=r * 30, location=(ctr.x, ctr.y, lo.z))
    floor = bpy.context.object
    floor["_studio"] = 1
    m = bpy.data.materials.new("_sweep"); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = hex_lin("#2a2724" if mood else "#5e5b58")
    p.inputs["Roughness"].default_value = 0.85
    floor.data.materials.append(m)
    world = bpy.data.worlds.new("_studio_world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = \
        hex_lin("#0d0b0a" if mood else "#6f6c69")
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.15 if mood else 0.35
    scn.world = world
    s = r  # light scale
    if mood:
        L = [area("_key", ctr + Vector((-1.4 * s, -0.9 * s, 1.8 * s)), ctr, 0.35 * s, 260 * s * s, "#ffb36b"),
             area("_cool", ctr + Vector((1.6 * s, -1.2 * s, 0.6 * s)), ctr, 0.8 * s, 25 * s * s, "#7d9cc9")]
    else:
        L = [area("_key", ctr + Vector((-2.2 * s, -2.4 * s, 2.6 * s)), ctr, 1.6 * s, 420 * s * s),
             area("_fill", ctr + Vector((2.8 * s, -1.6 * s, 0.9 * s)), ctr, 2.4 * s, 140 * s * s),
             area("_rim", ctr + Vector((0.6 * s, 2.8 * s, 2.2 * s)), ctr, 1.2 * s, 380 * s * s)]
    for o in L:
        o["_studio"] = 1
    return ctr, r


def _frame_ok(cam, corners, margin):
    from bpy_extras.object_utils import world_to_camera_view
    scn = bpy.context.scene
    bpy.context.view_layer.update()
    for c in corners:
        p = world_to_camera_view(scn, cam, c)
        if p.z <= 0 or not (margin < p.x < 1 - margin and margin < p.y < 1 - margin):
            return False
    return True


def camera(ctr, r, az, el, fac, lens, corners=None, target=None, dist=None):
    """Front = -Y (room convention). Fits the bbox corners in frame (binary search on distance),
    or uses an explicit target/distance for close-ups."""
    scn = bpy.context.scene
    cam = scn.camera
    if not cam:
        cam = bpy.data.objects.new("_cam", bpy.data.cameras.new("_cam"))
        scn.collection.objects.link(cam); scn.camera = cam
    cam.data.lens = lens
    cam.data.sensor_fit = "AUTO"
    a, e = math.radians(az), math.radians(el)
    dirv = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    tgt = Vector(target) if target else ctr.copy()

    def place(d):
        cam.location = tgt + dirv * d
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()

    if dist:
        place(dist)
    else:
        lo, hi = r * 0.3, r * 40
        for _ in range(30):
            mid = (lo + hi) / 2
            place(mid)
            if _frame_ok(cam, corners, 0.06):
                hi = mid
            else:
                lo = mid
        place(hi * fac)
    cam.data.dof.use_dof = False
    cam.data.dof.focus_distance = (tgt - cam.location).length
    cam.data.dof.aperture_fstop = 5.6


def main():
    """argv: name [spp] [views] [blend_path] [tag]"""
    import json
    name = sys.argv[1]
    spp = int(sys.argv[2]) if len(sys.argv) > 2 else 96
    views = sys.argv[3].split(",") if len(sys.argv) > 3 and sys.argv[3] != "all" else None
    d = ROOT / name
    blend = sys.argv[4] if len(sys.argv) > 4 else str(d / "export" / f"{name}.blend")
    tag = sys.argv[5] if len(sys.argv) > 5 else ""
    bpy.ops.wm.open_mainfile(filepath=blend)
    scn = bpy.context.scene
    objs = [o for o in scn.objects if o.type == "MESH" and not o.get("_studio")]
    extra = json.loads(scn.get("preview_views", "{}"))   # name -> [tx,ty,tz, az, el, dist, lens]
    allv = dict(VIEWS); allv.update({k: tuple(v) for k, v in extra.items()})
    views = views or list(allv)
    lo, hi = bbox(objs)
    size = hi - lo
    landscape = size.x > 1.3 * size.z
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = spp
    scn.cycles.use_denoising = True
    scn.render.resolution_x, scn.render.resolution_y = (1440, 1080) if landscape else (1080, 1350)
    scn.render.resolution_percentage = 100
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    scn.render.image_settings.file_format = "JPEG"
    scn.render.image_settings.quality = 90
    corners = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    out = []
    for v in views:
        spec = allv[v]
        ctr, r = setup(objs, mood=(v == "mood"))
        if len(spec) == 7:
            tx, ty, tz, az, el, dist, lens = spec
            camera(ctr, r, az, el, 1, lens, target=(tx, ty, tz), dist=dist)
        else:
            az, el, fac, lens = spec
            if fac < 1:   # generic detail: closer on the upper front
                camera(ctr, r, az, el, 1, lens, target=(ctr.x, lo.y, hi.z - size.z * 0.2), dist=r * 0.9)
            else:
                camera(ctr, r, az, el, fac, lens, corners=corners)
        p = d / "previews" / f"{name}{('_' + tag) if tag else ''}_{v}.jpg"
        scn.render.filepath = str(p)
        bpy.ops.render.render(write_still=True)
        out.append(p)
        print("rendered", p, flush=True)
    if len(out) > 1:
        sheet(out, d / "previews" / f"{name}{('_' + tag) if tag else ''}_sheet.jpg", landscape)


def sheet(paths, dst, landscape=False):
    try:
        from PIL import Image
    except ImportError:
        return
    ims = [Image.open(p) for p in paths]
    w, h = (720, 540) if landscape else (540, 675)
    cols = 2
    rows = math.ceil(len(ims) / cols)
    S = Image.new("RGB", (w * cols, h * rows), (20, 18, 17))
    for i, im in enumerate(ims):
        S.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
    S.save(dst, quality=88)
    print("sheet", dst)


if __name__ == "__main__":
    main()
