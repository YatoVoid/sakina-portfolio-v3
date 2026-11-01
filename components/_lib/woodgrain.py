"""Physically-structured wood: every part carries its own grain coordinates (point attribute "grain")
so the grain follows each board's long axis even after all parts are joined into one mesh.

Shader model (walnut-like, flat-sawn):
- annual rings = cylinders around a pith line placed outside the board, slightly tilted to the board, so the
  face shows straight stripes that open into cathedral arches; noise-distorted for irregular rings
- earlywood/latewood profile, pores (elongated dark specks), heartwood tone variation, per-part tone ("tone")
- satin lacquer: roughness from the ring pattern, pores rougher; bump from rings + pores
- grime in crevices (AO) and lightly worn convex edges (Pointiness) baked into the albedo
"""
import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

from common import hex_lin

AXIS = {"X": Matrix(((0, 1, 0), (0, 0, 1), (1, 0, 0))),   # world X -> grain Z
        "Y": Matrix(((1, 0, 0), (0, 0, 1), (0, 1, 0))),   # world Y -> grain Z
        "Z": Matrix.Identity(3)}


def tag_grain(bm, axis, seed, center):
    """Write the per-vertex grain coordinate + per-part tone into the bmesh."""
    rnd = random.Random(seed)
    R = AXIS[axis]
    tilt = Matrix.Rotation(math.radians(rnd.uniform(0.3, 1.3)), 3, "X") @ \
        Matrix.Rotation(math.radians(rnd.uniform(-0.8, 0.8)), 3, "Y")
    # pith outside the board -> flat-sawn
    pith = Vector((rnd.choice((-1, 1)) * rnd.uniform(0.02, 0.22), -rnd.uniform(0.12, 0.40), rnd.uniform(-5, 5)))
    tone = rnd.uniform(0.0, 1.0)
    lay = bm.verts.layers.float_vector.get("grain") or bm.verts.layers.float_vector.new("grain")
    tl = bm.verts.layers.float.get("tone") or bm.verts.layers.float.new("tone")
    for v in bm.verts:
        g = tilt @ (R @ (v.co - center)) - pith
        v[lay] = g
        v[tl] = tone


def wood_material(name, dark="#170c06", mid="#43291a", light="#7a5538", ring_scale=380.0,
                  rough=0.48, coat=0.12, wear=0.30, grime=0.55):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    N.clear()
    out = N.new("ShaderNodeOutputMaterial")
    b = N.new("ShaderNodeBsdfPrincipled")
    L.new(b.outputs["BSDF"], out.inputs["Surface"])

    attr = N.new("ShaderNodeAttribute"); attr.attribute_name = "grain"; attr.attribute_type = "GEOMETRY"
    tone = N.new("ShaderNodeAttribute"); tone.attribute_name = "tone"; tone.attribute_type = "GEOMETRY"

    # irregular rings: wobble the coordinate with low-frequency noise stretched along the grain
    wob_map = N.new("ShaderNodeMapping"); wob_map.inputs["Scale"].default_value = (22, 22, 2.2)
    L.new(attr.outputs["Vector"], wob_map.inputs["Vector"])
    wob = N.new("ShaderNodeTexNoise"); wob.inputs["Scale"].default_value = 1.0
    wob.inputs["Detail"].default_value = 1.5; wob.inputs["Roughness"].default_value = 0.55
    L.new(wob_map.outputs["Vector"], wob.inputs["Vector"])
    wc = N.new("ShaderNodeVectorMath"); wc.operation = "SUBTRACT"
    L.new(wob.outputs["Color"], wc.inputs[0]); wc.inputs[1].default_value = (0.5, 0.5, 0.5)
    ws = N.new("ShaderNodeVectorMath"); ws.operation = "SCALE"; ws.inputs["Scale"].default_value = 0.009
    L.new(wc.outputs["Vector"], ws.inputs[0])
    wadd = N.new("ShaderNodeVectorMath"); wadd.operation = "ADD"
    L.new(attr.outputs["Vector"], wadd.inputs[0]); L.new(ws.outputs["Vector"], wadd.inputs[1])
    flat = N.new("ShaderNodeMapping"); flat.inputs["Scale"].default_value = (1, 1, 0)   # cylinders
    L.new(wadd.outputs["Vector"], flat.inputs["Vector"])

    # explicit annual rings: fract(distance_to_pith * rings_per_metre); ring_scale = rings per metre
    dist = N.new("ShaderNodeVectorMath"); dist.operation = "LENGTH"
    L.new(flat.outputs["Vector"], dist.inputs[0])
    rmul = N.new("ShaderNodeMath"); rmul.operation = "MULTIPLY"; rmul.inputs[1].default_value = ring_scale
    L.new(dist.outputs["Value"], rmul.inputs[0])
    jmap = N.new("ShaderNodeMapping"); jmap.inputs["Scale"].default_value = (9, 9, 0.6)
    L.new(attr.outputs["Vector"], jmap.inputs["Vector"])
    jit = N.new("ShaderNodeTexNoise"); jit.inputs["Scale"].default_value = 1.0; jit.inputs["Detail"].default_value = 2
    L.new(jmap.outputs["Vector"], jit.inputs["Vector"])
    jadd = N.new("ShaderNodeMath"); jadd.operation = "MULTIPLY_ADD"
    L.new(jit.outputs["Fac"], jadd.inputs[0]); jadd.inputs[1].default_value = 6.0
    L.new(rmul.outputs["Value"], jadd.inputs[2])
    rings = N.new("ShaderNodeMath"); rings.operation = "FRACT"
    L.new(jadd.outputs["Value"], rings.inputs[0])
    # latewood: sharpen the saw profile into thin dark bands
    late = N.new("ShaderNodeMapRange"); late.inputs["From Min"].default_value = 0.68
    late.inputs["From Max"].default_value = 0.985
    L.new(rings.outputs["Value"], late.inputs["Value"])

    # pores: tiny streaks along the grain
    pmap = N.new("ShaderNodeMapping"); pmap.inputs["Scale"].default_value = (1400, 1400, 60)
    L.new(attr.outputs["Vector"], pmap.inputs["Vector"])
    pn = N.new("ShaderNodeTexNoise"); pn.inputs["Scale"].default_value = 1.0
    pn.inputs["Detail"].default_value = 1.0
    L.new(pmap.outputs["Vector"], pn.inputs["Vector"])
    pores = N.new("ShaderNodeMapRange"); pores.inputs["From Min"].default_value = 0.66
    pores.inputs["From Max"].default_value = 0.78
    L.new(pn.outputs["Fac"], pores.inputs["Value"])

    # heartwood / figure: broad colour drift
    fmap = N.new("ShaderNodeMapping"); fmap.inputs["Scale"].default_value = (34, 34, 0.9)
    L.new(attr.outputs["Vector"], fmap.inputs["Vector"])
    fig = N.new("ShaderNodeTexNoise"); fig.inputs["Scale"].default_value = 1.0
    fig.inputs["Detail"].default_value = 3
    L.new(fmap.outputs["Vector"], fig.inputs["Vector"])

    # base colour = ramp(figure + tone) then darken by latewood and pores
    tsum = N.new("ShaderNodeMath"); tsum.operation = "MULTIPLY_ADD"
    L.new(tone.outputs["Fac"], tsum.inputs[0]); tsum.inputs[1].default_value = 0.18
    L.new(fig.outputs["Fac"], tsum.inputs[2])
    ramp = N.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.25, hex_lin(mid)
    el[1].position, el[1].color = 0.90, hex_lin(light)
    L.new(tsum.outputs["Value"], ramp.inputs["Fac"])
    smap = N.new("ShaderNodeMapping"); smap.inputs["Scale"].default_value = (420, 420, 9)
    L.new(wadd.outputs["Vector"], smap.inputs["Vector"])
    sn = N.new("ShaderNodeTexNoise"); sn.inputs["Scale"].default_value = 1.0
    sn.inputs["Detail"].default_value = 4; sn.inputs["Roughness"].default_value = 0.6
    L.new(smap.outputs["Vector"], sn.inputs["Vector"])
    sr = N.new("ShaderNodeMapRange"); sr.inputs["To Min"].default_value = 0.72
    sr.inputs["To Max"].default_value = 1.12
    L.new(sn.outputs["Fac"], sr.inputs["Value"])
    streak = N.new("ShaderNodeMix"); streak.data_type = "RGBA"; streak.blend_type = "MULTIPLY"
    streak.inputs["Factor"].default_value = 1.0
    L.new(ramp.outputs["Color"], streak.inputs["A"])
    L.new(sr.outputs["Result"], streak.inputs["B"])
    mlate = N.new("ShaderNodeMix"); mlate.data_type = "RGBA"; mlate.blend_type = "MIX"
    L.new(late.outputs["Result"], mlate.inputs["Factor"])
    L.new(streak.outputs["Result"], mlate.inputs["A"]); mlate.inputs["B"].default_value = hex_lin(dark)
    lf = N.new("ShaderNodeMath"); lf.operation = "MULTIPLY"; lf.inputs[1].default_value = 0.42
    L.new(late.outputs["Result"], lf.inputs[0]); L.new(lf.outputs["Value"], mlate.inputs["Factor"])
    mpore = N.new("ShaderNodeMix"); mpore.data_type = "RGBA"
    pf = N.new("ShaderNodeMath"); pf.operation = "MULTIPLY"; pf.inputs[1].default_value = 0.55
    L.new(pores.outputs["Result"], pf.inputs[0]); L.new(pf.outputs["Value"], mpore.inputs["Factor"])
    L.new(mlate.outputs["Result"], mpore.inputs["A"]); mpore.inputs["B"].default_value = hex_lin("#120a05")

    # grime in crevices (AO) and worn convex edges (pointiness)
    ao = N.new("ShaderNodeAmbientOcclusion"); ao.inputs["Distance"].default_value = 0.04; ao.samples = 8
    gm = N.new("ShaderNodeMapRange"); gm.inputs["From Min"].default_value = 0.35
    gm.inputs["From Max"].default_value = 1.0
    gm.inputs["To Min"].default_value = grime; gm.inputs["To Max"].default_value = 0.0
    L.new(ao.outputs["AO"], gm.inputs["Value"])
    mgr = N.new("ShaderNodeMix"); mgr.data_type = "RGBA"; mgr.blend_type = "MULTIPLY"
    L.new(gm.outputs["Result"], mgr.inputs["Factor"])
    L.new(mpore.outputs["Result"], mgr.inputs["A"]); mgr.inputs["B"].default_value = hex_lin("#3a2a1e")
    # edge mask: where a 3 mm bevel normal departs from the true normal (works on low-poly meshes)
    geo = N.new("ShaderNodeNewGeometry")
    bev = N.new("ShaderNodeBevel"); bev.inputs["Radius"].default_value = 0.003; bev.samples = 6
    dot = N.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
    L.new(bev.outputs["Normal"], dot.inputs[0]); L.new(geo.outputs["Normal"], dot.inputs[1])
    wm = N.new("ShaderNodeMapRange"); wm.inputs["From Min"].default_value = 0.995
    wm.inputs["From Max"].default_value = 0.90
    wm.inputs["To Max"].default_value = wear
    L.new(dot.outputs["Value"], wm.inputs["Value"])
    mw = N.new("ShaderNodeMix"); mw.data_type = "RGBA"; mw.blend_type = "SCREEN"
    L.new(wm.outputs["Result"], mw.inputs["Factor"])
    L.new(mgr.outputs["Result"], mw.inputs["A"]); mw.inputs["B"].default_value = hex_lin("#9a7652")
    L.new(mw.outputs["Result"], b.inputs["Base Color"])

    # roughness: satin finish, pores and latewood slightly rougher, worn edges rougher
    rr = N.new("ShaderNodeMath"); rr.operation = "MULTIPLY_ADD"
    L.new(pores.outputs["Result"], rr.inputs[0]); rr.inputs[1].default_value = 0.18
    rr.inputs[2].default_value = rough
    rr2 = N.new("ShaderNodeMath"); rr2.operation = "MULTIPLY_ADD"
    L.new(wm.outputs["Result"], rr2.inputs[0]); rr2.inputs[1].default_value = 0.4
    L.new(rr.outputs["Value"], rr2.inputs[2])
    L.new(rr2.outputs["Value"], b.inputs["Roughness"])
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.18

    # bump: latewood ridges + pores sunk in
    hsum = N.new("ShaderNodeMath"); hsum.operation = "MULTIPLY_ADD"
    L.new(pores.outputs["Result"], hsum.inputs[0]); hsum.inputs[1].default_value = -1.0
    L.new(late.outputs["Result"], hsum.inputs[2])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.22
    bp.inputs["Distance"].default_value = 0.0004
    L.new(hsum.outputs["Value"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
