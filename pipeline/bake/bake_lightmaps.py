# Copied from the V2 pipeline (C:\Users\sakin\Downloads\v2\v2\pipeline, read-only source; V2 untouched).
# V3 changes: work dir from $V3_WORK instead of /home/wali/...; Cycles on CPU (cloud has no GPU).
import bpy, os, math, time, sys
D = bpy.data
sc = bpy.context.scene
vl = bpy.context.view_layer
B = os.environ.get("V3_WORK", "/tmp/v3work")
OUTDIR = os.environ.get("BAKE_OUT", B + "/bake")
SPP = int(os.environ.get("SPP", "192"))  # V2 run_all.sh used 192
RES = int(os.environ.get("RES", "2048"))
ONLY = [c for c in os.environ.get("COLS", "").split(",") if c]
SAVE = os.environ.get("SAVE", B + "/source/sakina-v21-baked.blend")
os.makedirs(OUTDIR, exist_ok=True)

GROUP_RES = {"Room": 4096, "Window": 2048, "Desk": 4096, "Station": 4096, "Monitor": 4096,
             "Tapes": 4096, "Keepsakes": 4096, "Lamp": 1024, "Plant": 2048,
             "Right_Nook": 4096, "Wall_Decor": 4096, "Floor": 4096}
COLLECTIONS = ["Room", "Window", "Desk", "Station", "Monitor", "Tapes", "Keepsakes",
               "Lamp", "Plant", "Right_Nook", "Wall_Decor", "Floor"]
if ONLY:
    COLLECTIONS = [c for c in COLLECTIONS if c in ONLY]
SKIP_NAMES = ("Glass", "Steam", "Rain", "Sky", "Haze", "Room_")
SKIP_MATS = ("WindowGlass",)


def log(*a):
    print("BAKE", *a, flush=True)
    sys.stdout.flush()


def setup_cycles():
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = SPP
    # V3: bakes are never denoised by Cycles; its denoise buffers + one untiled 4096^2 bake OOM'd the 8 GB cloud box.
    sc.cycles.use_denoising = False
    sc.cycles.use_auto_tile = True; sc.cycles.tile_size = 1024
    sc.cycles.volume_bounces = 0
    w = sc.world.node_tree
    for l in list(w.links):
        if l.to_socket.name == "Volume":
            w.links.remove(l)
    for o in list(D.collections["Outside"].all_objects):
        if o is not None:
            o.hide_render = True
    for o in D.objects:
        if o.name.startswith(("Rain", "Steam", "Haze")):
            o.hide_render = True
    b = sc.render.bake
    b.use_pass_direct = True; b.use_pass_indirect = True; b.use_pass_color = True
    b.use_pass_diffuse = True if hasattr(b, "use_pass_diffuse") else None
    for attr in ("use_pass_glossy", "use_pass_transmission", "use_pass_emit"):
        if hasattr(b, attr):
            setattr(b, attr, True)
    b.margin = 8
    b.margin_type = 'EXTEND'
    b.use_selected_to_active = False
    b.use_clear = True


def bake_objects(coll):
    out, seen = [], set()
    def walk(c):
        for o in list(c.objects):
            if o is None or o.name in seen:
                continue
            seen.add(o.name)
            if o.type not in ('MESH', 'FONT', 'CURVE'):
                continue
            if o.hide_render or o.name.startswith(SKIP_NAMES):
                continue
            if any(s.material and s.material.name in SKIP_MATS for s in o.material_slots):
                continue
            out.append(o)
        for ch in c.children:
            walk(ch)
    walk(coll)
    return out


def unhide(coll):
    def find(lc):
        if lc.collection == coll:
            return lc
        for ch in lc.children:
            r = find(ch)
            if r:
                return r
    lc = find(vl.layer_collection)
    if lc:
        lc.exclude = False; lc.hide_viewport = False
    for o in list(coll.all_objects):
        if o is None:
            continue
        o.hide_viewport = False
        try:
            o.hide_set(False)
        except RuntimeError:
            pass


def select_only(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    vl.objects.active = objs[0]


def to_meshes(objs):
    need = [o for o in objs if o.type != 'MESH' or o.modifiers]
    singles = [o for o in objs if o.type == 'MESH' and o.data.users > 1]
    if singles:
        select_only(singles)
        bpy.ops.object.make_single_user(object=False, obdata=True, material=False, animation=False)
    if need:
        select_only(need)
        bpy.ops.object.convert(target='MESH')
    return [o for o in objs if o.name in D.objects]


def fallback_mat():
    m = D.materials.get("BakeFallback")
    if not m:
        m = D.materials.new("BakeFallback"); m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.2, 0.2, 0.2, 1)
    return m


def unwrap(objs):
    for o in objs:
        me = o.data
        if not me.materials:
            me.materials.append(fallback_mat())
        for i, s in enumerate(o.material_slots):
            if s.material is None:
                s.material = fallback_mat()
        uv = me.uv_layers.get("Lightmap") or me.uv_layers.new(name="Lightmap")
        me.uv_layers.active = uv
    select_only(objs)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(80), island_margin=0.003, area_weight=0.5, scale_to_bounds=False)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(margin=0.003, rotate=True, shape_method='AABB')
    bpy.ops.object.mode_set(mode='OBJECT')


def uv_coverage(objs):
    used = 0.0
    for o in objs:
        uv = o.data.uv_layers["Lightmap"].data
        # polygon area in UV space
        for p in o.data.polygons:
            pts = [uv[i].uv for i in p.loop_indices]
            a = 0.0
            for i in range(len(pts)):
                x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
                a += x1 * y2 - x2 * y1
            used += abs(a) / 2
    return used


def bake_collection(name, objs):
    res = GROUP_RES.get(name, RES) if not os.environ.get("RES") else RES
    if os.environ.get("RES_SCALE"):                 # low-res preview bakes: RES_SCALE=0.25 -> 4096 becomes 1024 (min 256)
        res = max(256, int(res * float(os.environ["RES_SCALE"])))
    img = D.images.new("LM_" + name, res, res, alpha=False, float_buffer=True)
    img.colorspace_settings.name = 'Linear Rec.709'
    mats = {s.material for o in objs for s in o.material_slots if s.material}
    added = []
    for m in mats:
        if not m.use_nodes:
            m.use_nodes = True
        nt = m.node_tree
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = img; n.name = "BAKE_TARGET"
        for x in nt.nodes:
            x.select = False
        n.select = True; nt.nodes.active = n
        added.append((nt, n))
    tmp = D.collections.new("_bake_tmp"); sc.collection.children.link(tmp)
    copies = []
    for o in objs:
        c = o.copy(); c.data = o.data.copy(); c.animation_data_clear()
        c.parent = None; c.matrix_world = o.matrix_world
        tmp.objects.link(c); copies.append(c)
        o.hide_render = True
    select_only(copies)
    bpy.ops.object.join()
    joined = vl.objects.active
    t = time.time()
    alb = None
    if os.environ.get("DENOISE"):                  # V3: quick albedo bake = OIDN guide (keeps text/texture sharp)
        alb = D.images.new("LMA_" + name, res, res, alpha=False, float_buffer=True)
        for nt, n in added:
            n.image = alb
        s0 = sc.cycles.samples; sc.cycles.samples = 8
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, margin=8, margin_type='EXTEND', use_clear=True)
        sc.cycles.samples = s0
        for nt, n in added:
            n.image = img
        log(name, "albedo baked", round(time.time() - t), "s")
    bpy.ops.object.bake(type='COMBINED', margin=8, margin_type='EXTEND', use_clear=True)
    if os.environ.get("DENOISE"):                  # V3: OIDN on the baked lightmap (Cycles does not denoise bakes)
        import sys as _s; _s.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
        from oidn import denoise_image
        td = time.time(); denoise_image(img, alb); log(name, "OIDN denoised in", round(time.time() - td), "s")
    D.objects.remove(joined, do_unlink=True)
    D.collections.remove(tmp)
    for o in objs:
        o.hide_render = False
    for nt, n in added:
        nt.nodes.remove(n)
    exr = f"{OUTDIR}/lm_{name}.exr"
    png = f"{OUTDIR}/lm_{name}.png"
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'
    img.save_render(exr, scene=sc)
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '8'
    sc.render.image_settings.color_mode = 'RGB'
    img.save_render(png, scene=sc)
    log(name, "objects", len(objs), "seconds", round(time.time() - t), "->", png)
    return png


def baked_material(name, png):
    m = D.materials.new("Baked_" + name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = (0, 0, 0, 1)
    bs.inputs["Roughness"].default_value = 1.0
    bs.inputs["Specular IOR Level"].default_value = 0.0
    uvn = nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "Lightmap"
    tex = nt.nodes.new("ShaderNodeTexImage")
    im = D.images.load(png)
    im.colorspace_settings.name = 'sRGB'
    tex.image = im
    nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], bs.inputs["Emission Color"])
    bs.inputs["Emission Strength"].default_value = 1.0
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
    return m


def main():
    setup_cycles()
    results = {}
    for cname in COLLECTIONS:
        coll = D.collections[cname]
        unhide(coll)
        objs = bake_objects(coll)
        objs = to_meshes(objs)
        objs = [o for o in objs if o.type == 'MESH' and len(o.data.polygons)]
        log(cname, "meshes", len(objs), "polys", sum(len(o.data.polygons) for o in objs))
        unwrap(objs)
        log(cname, "uv coverage", round(uv_coverage(objs), 3))
        results[cname] = (objs, bake_collection(cname, objs))
    # lightmap-only baked materials
    for cname, (objs, png) in results.items():
        bm = baked_material(cname, png)
        for o in objs:
            me = o.data
            for uv in list(me.uv_layers):
                if uv.name != "Lightmap":
                    me.uv_layers.remove(uv)
            me.materials.clear()
            me.materials.append(bm)
            o["bake_group"] = cname
    bpy.ops.wm.save_as_mainfile(filepath=SAVE, compress=True)
    log("SAVED", SAVE)


main()
