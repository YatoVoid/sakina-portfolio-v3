# Copied from the V2 pipeline (C:\Users\sakin\Downloads\v2\v2\pipeline, read-only source; V2 untouched).
# V3 changes: work dir from $V3_WORK instead of /home/wali/...; Cycles on CPU (cloud has no GPU).
import bpy, os
D = bpy.data
sc = bpy.context.scene
vl = bpy.context.view_layer
B = os.environ.get("V3_WORK", "/tmp/v3work")
OUT = os.environ.get("EXPORT_DIR", B + "/web")
os.makedirs(OUT, exist_ok=True)
SKIP_OUT = ("Sky", "Rain", "Steam", "Haze", "Glass")


def log(*a):
    print("EXP", *a, flush=True)


def select_only(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    vl.objects.active = objs[0]


def unparent(o):
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw


def animated(o):
    p = o
    while p is not None:
        if p.animation_data and p.animation_data.action:
            return True
        p = p.parent
    return False


def merge(objs, name):
    for o in objs:
        unparent(o)
    select_only(objs)
    if len(objs) > 1:
        bpy.ops.object.join()
    j = vl.objects.active
    j.name = name; j.data.name = name
    return j


def emissive_principled(mat):
    nt = mat.node_tree
    em = next((n for n in nt.nodes if n.type == 'EMISSION'), None)
    if not em:
        return False
    col = tuple(em.inputs["Color"].default_value)
    st = em.inputs["Strength"].default_value
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = (0, 0, 0, 1)
    bs.inputs["Roughness"].default_value = 1.0
    bs.inputs["Emission Color"].default_value = col
    bs.inputs["Emission Strength"].default_value = st
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
    return True


def flat_principled(mat, base, rough, emit=None, emit_strength=0.0):
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = base
    bs.inputs["Roughness"].default_value = rough
    if emit:
        bs.inputs["Emission Color"].default_value = emit
        bs.inputs["Emission Strength"].default_value = emit_strength
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])


def export(path, objs, animations):
    select_only(objs)
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB', use_selection=True,
        export_image_format='JPEG', export_jpeg_quality=88,
        export_lights=False, export_cameras=False, export_apply=False,
        export_animations=animations, export_yup=True)
    log("wrote", path, round(os.path.getsize(path) / 1e6, 1), "MB")


def main():
    groups = {}
    for o in D.objects:
        g = o.get("bake_group")
        if g and o.type == 'MESH':
            groups.setdefault(g, []).append(o)
    room = []
    for g, objs in sorted(groups.items()):
        j = merge(objs, "Room_" + g if g != "Room" else "Room_Shell")
        log(g, "objects", len(objs), "-> 1 mesh,", len(j.data.polygons), "polys")
        room.append(j)

    outside = [o for o in D.collections["Outside"].all_objects
               if o is not None and o.type == 'MESH' and not o.name.startswith(SKIP_OUT)]
    static = [o for o in outside if not animated(o)]
    moving = [o for o in outside if animated(o)]
    for m in {s.material for o in outside for s in o.material_slots if s.material}:
        if m.name in ("CityBldMid", "CityBldFar", "CityBldNear"):
            flat_principled(m, (0.02, 0.022, 0.034, 1), 0.6)
        elif not emissive_principled(m) and not any(n.type == 'TEX_IMAGE' for n in m.node_tree.nodes):
            pr = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if pr:
                for l in list(m.node_tree.links):
                    if l.to_node == pr and l.to_socket.name in ("Base Color", "Roughness", "Normal", "Emission Color", "Emission Strength"):
                        m.node_tree.links.remove(l)
    by_mat = {}
    for o in static:
        key = tuple(s.material.name if s.material else "" for s in o.material_slots)
        by_mat.setdefault(key, []).append(o)
    merged_out = []
    for i, (key, objs) in enumerate(sorted(by_mat.items())):
        merged_out.append(merge(objs, "Outside_%02d_%s" % (i, (key[0] if key else "none"))))
    log("outside static groups", len(merged_out), "moving objects", len(moving))

    export(OUT + "/sakina-room.glb", room, False)
    export(OUT + "/sakina-outside.glb", merged_out + moving, True)
    glass = D.objects.get("Glass")
    if glass:
        log("glass pane left out; recreate transparency in Three.js")


main()
