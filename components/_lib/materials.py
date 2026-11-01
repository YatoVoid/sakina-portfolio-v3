"""PBR material builders + texture baking so procedural detail survives glTF export.

Cycles previews and the GLB use the SAME baked textures (bake_to_images) so what is reviewed is what ships.
"""
import bpy

from common import hex_lin


def _new(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    out.location = (600, 0)
    return m, nt, bsdf


def _coords(nt, scale):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def pbr(name, base, rough=0.5, metal=0.0, var=0.08, var_scale=40.0, rough_var=0.12,
        bump=0.15, bump_scale=300.0, coat=0.0, spec=0.5):
    """Generic material: base colour with low-frequency variation, roughness breakup, micro bump.
    base: hex or list of two hex (dark, light) for the colour ramp."""
    m, nt, b = _new(name)
    lo, hi = (base, base) if isinstance(base, str) else base
    v = _coords(nt, (1, 1, 1))
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = var_scale
    n1.inputs["Detail"].default_value = 6
    nt.links.new(v, n1.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.5 - var * 3
    ramp.color_ramp.elements[1].position = 0.5 + var * 3
    ramp.color_ramp.elements[0].color = hex_lin(lo)
    ramp.color_ramp.elements[1].color = hex_lin(hi)
    nt.links.new(n1.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    # roughness breakup
    rmap = nt.nodes.new("ShaderNodeMapRange")
    rmap.inputs["To Min"].default_value = max(0.02, rough - rough_var)
    rmap.inputs["To Max"].default_value = min(1.0, rough + rough_var)
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = var_scale * 2.7
    nt.links.new(v, n2.inputs["Vector"])
    nt.links.new(n2.outputs["Fac"], rmap.inputs["Value"])
    nt.links.new(rmap.outputs["Result"], b.inputs["Roughness"])
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    # micro bump
    if bump:
        n3 = nt.nodes.new("ShaderNodeTexNoise")
        n3.inputs["Scale"].default_value = bump_scale
        n3.inputs["Detail"].default_value = 3
        nt.links.new(v, n3.inputs["Vector"])
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump
        bp.inputs["Distance"].default_value = 0.0005
        nt.links.new(n3.outputs["Fac"], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def wood(name, dark="#3b2414", light="#6e4528", rough=0.55, ring_scale=6.0, stretch=(1, 1, 18),
         coat=0.15, bump=0.08):
    """Long-grain wood. stretch elongates the grain along the object's local axis with the big value."""
    m, nt, b = _new(name)
    v = _coords(nt, stretch)
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "RINGS"
    wave.inputs["Scale"].default_value = ring_scale
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 4
    wave.inputs["Detail Scale"].default_value = 2.0
    nt.links.new(v, wave.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 25
    noise.inputs["Detail"].default_value = 8
    nt.links.new(v, noise.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs["Factor"].default_value = 0.35
    nt.links.new(wave.outputs["Fac"], mix.inputs["A"])
    nt.links.new(noise.outputs["Fac"], mix.inputs["B"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = hex_lin(dark)
    ramp.color_ramp.elements[1].color = hex_lin(light)
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[1].position = 0.8
    nt.links.new(mix.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    rm = nt.nodes.new("ShaderNodeMapRange")
    rm.inputs["To Min"].default_value = rough - 0.1
    rm.inputs["To Max"].default_value = rough + 0.1
    nt.links.new(mix.outputs["Result"], rm.inputs["Value"])
    nt.links.new(rm.outputs["Result"], b.inputs["Roughness"])
    b.inputs["Coat Weight"].default_value = coat
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    bp.inputs["Distance"].default_value = 0.0008
    nt.links.new(mix.outputs["Result"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def emissive(name, color, strength=2.0):
    m, nt, b = _new(name)
    b.inputs["Base Color"].default_value = hex_lin(color)
    b.inputs["Emission Color"].default_value = hex_lin(color)
    b.inputs["Emission Strength"].default_value = strength
    return m


def image_mat(name, img_path, rough=0.6):
    """Material from a texture image (labels, printed paper). Exports cleanly to glTF."""
    m, nt, b = _new(name)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(img_path), check_existing=True)
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    return m


# ---------------------------------------------------------------- bake procedural -> textures
def bake_to_images(objs, out_dir, px=1024, prefix="tex"):
    """Bake each procedural material per object into Base Color / Roughness / Normal images
    on a fresh non-overlapping UV layer, then swap in a plain image-texture Principled material
    (glTF-exportable). Objects that only use image/flat materials are skipped."""
    import os
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = 16
    scn.render.bake.margin = 6
    for ob in objs:
        if ob.type != "MESH" or not ob.material_slots:
            continue
        mats = [s.material for s in ob.material_slots if s.material]
        if not any(_is_procedural(m) for m in mats):
            continue
        # dedicated bake UVs
        me = ob.data
        uv = me.uv_layers.new(name="BakeUV")
        me.uv_layers.active = uv
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004, area_weight=0.0)
        bpy.ops.uv.pack_islands(margin=0.004)
        bpy.ops.object.mode_set(mode="OBJECT")
        imgs = {}
        for kind, cs in (("base", "sRGB"), ("rough", "Non-Color"), ("normal", "Non-Color")):
            img = bpy.data.images.new(f"{prefix}_{ob.name}_{kind}", px, px, alpha=False,
                                      float_buffer=False)
            img.colorspace_settings.name = cs
            imgs[kind] = img
        for kind, btype in (("base", "DIFFUSE"), ("rough", "ROUGHNESS"), ("normal", "NORMAL")):
            for m in mats:
                nt = m.node_tree
                for n in nt.nodes:
                    n.select = False
                t = nt.nodes.new("ShaderNodeTexImage")
                t.name = "_bake_target"
                t.image = imgs[kind]
                t.select = True
                nt.nodes.active = t
            saved = {}
            if btype == "DIFFUSE":
                scn.render.bake.use_pass_direct = False
                scn.render.bake.use_pass_indirect = False
                scn.render.bake.use_pass_color = True
                # a metal's diffuse colour is black: bake its albedo with Metallic temporarily 0
                for m in mats:
                    pb = m.node_tree.nodes.get("Principled BSDF")
                    if pb and not pb.inputs["Metallic"].is_linked:
                        saved[m] = pb.inputs["Metallic"].default_value
                        pb.inputs["Metallic"].default_value = 0.0
            bpy.ops.object.bake(type=btype, uv_layer="BakeUV")
            for m, val in saved.items():
                m.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = val
            for m in mats:
                nt = m.node_tree
                nt.nodes.remove(nt.nodes["_bake_target"])
        os.makedirs(out_dir, exist_ok=True)
        for kind, img in imgs.items():
            img.filepath_raw = os.path.join(out_dir, f"{img.name}.png")
            img.file_format = "PNG"
            img.save()
        # replace with one baked material (keeps emissive/image slots untouched)
        baked = _baked_material(f"{ob.name}_baked", imgs, mats)
        for s in ob.material_slots:
            if s.material and _is_procedural(s.material):
                s.material = baked
        # keep only the bake UVs so the exporter writes them as TEXCOORD_0
        for l in list(me.uv_layers):
            if l.name != "BakeUV":
                me.uv_layers.remove(l)


def _is_procedural(m):
    if not m or not m.use_nodes:
        return False
    return any(n.bl_idname in ("ShaderNodeTexNoise", "ShaderNodeTexWave", "ShaderNodeTexVoronoi",
                               "ShaderNodeTexMusgrave", "ShaderNodeValToRGB")
               for n in m.node_tree.nodes)


def _baked_material(name, imgs, src_mats):
    m, nt, b = _new(name)
    src = src_mats[0].node_tree.nodes.get("Principled BSDF")
    metal = src.inputs["Metallic"].default_value if src else 0.0
    coat = src.inputs["Coat Weight"].default_value if src else 0.0
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "BakeUV"
    tb = nt.nodes.new("ShaderNodeTexImage"); tb.image = imgs["base"]
    tr = nt.nodes.new("ShaderNodeTexImage"); tr.image = imgs["rough"]
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = imgs["normal"]
    for t in (tb, tr, tn):
        nt.links.new(uvn.outputs["UV"], t.inputs["Vector"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.uv_map = "BakeUV"
    nt.links.new(tb.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tr.outputs["Color"], b.inputs["Roughness"])
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    return m
