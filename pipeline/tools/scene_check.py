"""Scene integrity checks for the integrated V3 scene. Read-only: opens .blend files, prints a JSON report.

    python3 pipeline/tools/scene_check.py <scene.blend> [--baseline <baseline.blend>] [--out report.json]

Checks
  lights/cameras   name, type, transform, energy, colour, lens identical to the baseline (must not change)
  duplicates       objects with a ".001"-style suffix; different objects with identical geometry at the same place
  bake groups      every mesh is in exactly one collection; bake collections listed; empty / unassigned meshes
  desk props       each prop on the desk: gap between its lowest point and the desk top (0.720 m), vs baseline
  intersections    BVH overlaps between desk props / desk parts, new ones vs baseline
  textures         images with external (non-packed) paths -> not portable
  materials / UV   material count per collection; meshes lacking any UV layer (the Lightmap layer is added at bake)
"""
import bpy, sys, json, math, collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree

BAKE = ["Desk", "Keepsakes", "Lamp", "Monitor", "Plant", "Right_Nook", "Room", "Station", "Tapes", "Wall_Decor", "Window"]
NON_BAKE = ["Outside", "Lights", "Camera", "WindowView"]
DESK_TOP_Z = 0.720


def _open(path):
    bpy.ops.wm.open_mainfile(filepath=path)


def _eval(o):
    dg = bpy.context.evaluated_depsgraph_get()
    return o.evaluated_get(dg)


def world_bounds(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (Vector(map(min, *pts)), Vector(map(max, *pts)))


def lights_cams():
    out = {}
    for o in bpy.data.objects:
        if o.type == 'LIGHT':
            d = o.data
            out[o.name] = dict(kind="light", type=d.type, energy=round(d.energy, 4), color=[round(x, 4) for x in d.color],
                               m=[round(x, 4) for r in o.matrix_world for x in r])
        elif o.type == 'CAMERA':
            out[o.name] = dict(kind="camera", lens=round(o.data.lens, 4), m=[round(x, 4) for r in o.matrix_world for x in r])
    sc = bpy.context.scene
    out["_scene"] = dict(camera=sc.camera.name if sc.camera else None, engine=sc.render.engine,
                         samples=sc.cycles.samples, device=sc.cycles.device,
                         res=[sc.render.resolution_x, sc.render.resolution_y],
                         view_transform=sc.view_settings.view_transform, exposure=round(sc.view_settings.exposure, 4),
                         world=sc.world.name if sc.world else None)
    return out


def mesh_collection_map():
    m = collections.defaultdict(list)
    for o in bpy.data.objects:
        if o.type == 'MESH':
            m[o.name] = [c.name for c in o.users_collection]
    return m


def duplicates():
    sfx = [o.name for o in bpy.data.objects if len(o.name) > 4 and o.name[-4] == "." and o.name[-3:].isdigit()]
    seen = collections.defaultdict(list)
    for o in bpy.data.objects:
        if o.type != 'MESH' or len(o.data.vertices) < 4:
            continue
        b0, b1 = world_bounds(o)
        key = (len(o.data.vertices), len(o.data.polygons)) + tuple(round(x, 3) for x in (*b0, *b1))
        seen[key].append(o.name)
    same = [v for v in seen.values() if len(v) > 1]
    return dict(suffixed_names=sfx, identical_geometry_same_place=same)


def desk_props():
    desk = bpy.data.collections["Desk"]
    parts = [o for o in desk.objects if o.name.startswith("Desk_")]
    props = [o for o in desk.objects if o.type == 'MESH' and not o.name.startswith(("Desk_", "Chair_"))
             and o.parent is None and world_bounds(o)[0].z > 0.5]
    res = {}
    for o in props:
        b0, b1 = world_bounds(o)
        res[o.name] = dict(gap_to_top_mm=round((b0.z - DESK_TOP_Z) * 1000, 1), over_desk=(-1.25 <= b0.x <= 1.65 and 1.30 <= b0.y <= 2.0))
    if parts:
        b0 = Vector((1e9,) * 3); b1 = Vector((-1e9,) * 3)
        for o in parts:
            a, b = world_bounds(o); b0 = Vector(map(min, b0, a)); b1 = Vector(map(max, b1, b))
        res["_desk_bounds_m"] = dict(min=[round(x, 3) for x in b0], max=[round(x, 3) for x in b1])
    return res


def _bvh(o):
    e = _eval(o); me = e.to_mesh()
    verts = [e.matrix_world @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    t = BVHTree.FromPolygons(verts, polys)
    e.to_mesh_clear()
    return t


def intersections():
    desk = bpy.data.collections["Desk"]
    objs = [o for o in desk.objects if o.type == 'MESH' and len(o.data.polygons) > 0]
    named = {o.name: o for o in objs}
    trees = {n: _bvh(o) for n, o in named.items()}
    pairs = []
    names = sorted(named)
    boxes = {n: world_bounds(named[n]) for n in names}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            (a0, a1), (b0, b1) = boxes[a], boxes[b]
            if any(a1[k] < b0[k] or b1[k] < a0[k] for k in range(3)):
                continue
            ov = trees[a].overlap(trees[b])
            if ov:
                pairs.append(f"{a} x {b} ({len(ov)})")
    return pairs


def textures():
    return dict(external=[(i.name, i.filepath) for i in bpy.data.images if i.source == 'FILE' and not i.packed_file and i.filepath],
                packed=[i.name for i in bpy.data.images if i.packed_file],
                missing_data=[i.name for i in bpy.data.images if i.source == 'FILE' and not i.packed_file and not i.has_data])


def groups():
    out = {}
    for c in bpy.data.collections:
        meshes = [o for o in c.objects if o.type == 'MESH']
        mats = {s.material.name for o in meshes for s in o.material_slots if s.material}
        out[c.name] = dict(objects=len(c.objects), meshes=len(meshes), materials=len(mats),
                           tris=sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes),
                           no_uv=[o.name for o in meshes if len(o.data.uv_layers) == 0][:12],
                           no_uv_count=sum(1 for o in meshes if len(o.data.uv_layers) == 0),
                           lightmap_uv=sum(1 for o in meshes if "Lightmap" in o.data.uv_layers),
                           no_material=[o.name for o in meshes if not any(s.material for s in o.material_slots)][:12])
    mc = mesh_collection_map()
    multi = {n: c for n, c in mc.items() if len(c) != 1}
    unknown = sorted({c for cs in mc.values() for c in cs} - set(BAKE) - set(NON_BAKE))
    return dict(per_collection=out, meshes_not_in_exactly_one_collection=multi, unknown_collections=unknown)


def report():
    r = dict(lights_cams=lights_cams(), duplicates=duplicates(), groups=groups(), textures=textures(),
             desk_props=desk_props(), intersections=intersections())
    return r


def main():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    scene = a[0]; base = a[a.index("--baseline") + 1] if "--baseline" in a else None
    out = a[a.index("--out") + 1] if "--out" in a else None
    _open(scene); R = report()
    if base:
        _open(base); B = report()
        lc = {k: v for k, v in R["lights_cams"].items()}
        R["lights_cams_changed_vs_baseline"] = sorted(k for k in set(lc) | set(B["lights_cams"]) if lc.get(k) != B["lights_cams"].get(k))
        R["new_intersections_vs_baseline"] = sorted(set(R["intersections"]) - set(B["intersections"]))
        R["gone_intersections_vs_baseline"] = sorted(set(B["intersections"]) - set(R["intersections"]))
        R["prop_gap_changes_vs_baseline"] = {k: (B["desk_props"].get(k, {}).get("gap_to_top_mm"), v.get("gap_to_top_mm"))
                                             for k, v in R["desk_props"].items()
                                             if k != "_desk_bounds_m" and B["desk_props"].get(k, {}).get("gap_to_top_mm") != v.get("gap_to_top_mm")}
        R["baseline_desk_bounds_m"] = B["desk_props"].get("_desk_bounds_m")
    s = json.dumps(R, indent=1, default=str)
    if out:
        open(out, "w").write(s)
    print("REPORT_BEGIN"); print(s); print("REPORT_END")


main()
