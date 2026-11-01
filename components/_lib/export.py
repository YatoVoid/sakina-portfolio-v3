"""Standalone GLB export for a component.

Procedural node trees do not survive glTF export, so each material is baked (Cycles, CPU) to image
textures on a per-component UV atlas: base colour, roughness, metallic and a tangent-space normal map.
The baked copy is built on duplicates, so the component's own procedural materials stay untouched for the
room's lightmap bake.
"""
import bpy, os, json, subprocess
from .studio import bounds


def _meshes(root):
    return [o for o in [root] + list(root.children_recursive) if o.type == 'MESH']


def _apply_modifiers_copy(root, coll):
    """Duplicate every mesh with modifiers applied, world transforms baked in, parented to a new root."""
    dg = bpy.context.evaluated_depsgraph_get()
    new_root = bpy.data.objects.new(root.name, None); coll.objects.link(new_root)
    out = []
    for o in _meshes(root):
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
        me.transform(o.matrix_world)
        c = bpy.data.objects.new(o.name, me); coll.objects.link(c); c.parent = new_root
        out.append(c)
    return new_root, out


def _join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = name; o.data.name = name
    return o


def _atlas_uv(o, margin=0.004):
    me = o.data
    uv = me.uv_layers.get("BakeUV") or me.uv_layers.new(name="BakeUV")
    me.uv_layers.active = uv
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=margin, area_weight=0.0, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    return uv


def _bake_pass(o, kind, img, socket=None):
    """kind: DIFFUSE colour, NORMAL, or EMIT-routed data pass for a BSDF input (roughness/metallic)."""
    sc = bpy.context.scene
    saved = {}
    for slot in o.material_slots:
        nt = slot.material.node_tree
        tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.name = "__bake"
        nt.nodes.active = tex
        if socket:   # route the input value to an emission shader temporarily
            bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
            out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
            em = nt.nodes.new("ShaderNodeEmission"); em.name = "__emit"
            src = bsdf.inputs[socket]
            if src.is_linked:
                nt.links.new(src.links[0].from_socket, em.inputs["Color"])
            else:
                v = src.default_value; em.inputs["Color"].default_value = (v, v, v, 1)
            prev = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].is_linked else None
            nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
            saved[slot.material.name] = prev
    if kind == 'DIFFUSE':
        sc.render.bake.use_pass_direct = False; sc.render.bake.use_pass_indirect = False
        sc.render.bake.use_pass_color = True
    bpy.ops.object.bake(type='EMIT' if socket else kind, margin=8, use_clear=True, uv_layer="BakeUV")
    for slot in o.material_slots:
        nt = slot.material.node_tree
        for nm in ("__bake", "__emit"):
            n = nt.nodes.get(nm)
            if n:
                nt.nodes.remove(n)
        if socket and saved.get(slot.material.name):
            out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
            nt.links.new(saved[slot.material.name], out.inputs["Surface"])


def export_glb(root, path, tex_size=1024, samples=16):
    """Bake textures and write `path` (.glb). Returns a dict of stats."""
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples
    coll = bpy.data.collections.new("__export"); sc.collection.children.link(coll)
    new_root, objs = _apply_modifiers_copy(root, coll)
    # materials on the copy are duplicated so the bake routing never edits the originals
    for o in objs:
        for slot in o.material_slots:
            if slot.material:
                slot.material = slot.material.copy()
    merged = _join(objs, root.name + "_Mesh")
    _atlas_uv(merged)
    base = os.path.splitext(path)[0]
    imgs = {}
    for key, kind, socket, colour in [("basecolor", 'DIFFUSE', None, 'sRGB'), ("roughness", 'EMIT', "Roughness", 'Non-Color'),
                                       ("metallic", 'EMIT', "Metallic", 'Non-Color'), ("normal", 'NORMAL', None, 'Non-Color')]:
        img = bpy.data.images.new(f"{root.name}_{key}", tex_size, tex_size, alpha=False, float_buffer=False)
        img.colorspace_settings.name = colour
        _bake_pass(merged, kind, img, socket if kind == 'EMIT' else None)
        img.filepath_raw = f"{base}_{key}.png"; img.file_format = 'PNG'; img.save()
        imgs[key] = img
    # one clean glTF material wired to the baked maps
    m = bpy.data.materials.new(root.name + "_Baked"); m.use_nodes = True; nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    def tex(img, loc):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; t.location = loc; return t
    nt.links.new(tex(imgs["basecolor"], (-600, 300)).outputs["Color"], bsdf.inputs["Base Color"])
    rm = nt.nodes.new("ShaderNodeSeparateColor"); rm.location = (-300, 0)
    # glTF packs roughness (G) and metallic (B); feeding them separately lets the exporter pack them
    nt.links.new(tex(imgs["roughness"], (-600, 0)).outputs["Color"], rm.inputs["Color"])
    nt.links.new(rm.outputs["Green"], bsdf.inputs["Roughness"])
    mt = nt.nodes.new("ShaderNodeSeparateColor"); mt.location = (-300, -250)
    nt.links.new(tex(imgs["metallic"], (-600, -250)).outputs["Color"], mt.inputs["Color"])
    nt.links.new(mt.outputs["Blue"], bsdf.inputs["Metallic"])
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.location = (-300, -500)
    nt.links.new(tex(imgs["normal"], (-600, -500)).outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    merged.data.materials.clear(); merged.data.materials.append(m)
    for uvl in [u for u in merged.data.uv_layers if u.name != "BakeUV"]:   # ship only the baked atlas UVs
        merged.data.uv_layers.remove(uvl)
    # export just the copy
    bpy.ops.object.select_all(action='DESELECT')
    new_root.select_set(True); merged.select_set(True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                              export_yup=True, export_image_format='JPEG', export_jpeg_quality=88,
                              export_texcoords=True, export_normals=True, export_tangents=False)
    lo, hi = bounds(new_root)
    stats = {"file": os.path.basename(path), "bytes": os.path.getsize(path),
             "triangles": sum(len(p.vertices) - 2 for p in merged.data.polygons),
             "size_m": [round(v, 4) for v in (hi - lo)], "texture_px": tex_size}
    # tidy: remove the export copy from the scene
    for o in list(coll.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(coll)
    return stats
