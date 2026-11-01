"""Materials for the Havalance-style chair: distressed whitewash over wood grain, woven taupe seat fabric,
aged-brass nailheads. Everything is procedural here and baked to image textures by build_chair.py."""
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
from common import hex_lin  # noqa: E402
from nodeg import G  # noqa: E402


def _base(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    return m, nt, b


def _col_ramp(g, fac, stops):
    n = g.N.new("ShaderNodeValToRGB")
    el = n.color_ramp.elements
    while len(el) < len(stops):
        el.new(0.5)
    for e, (pos, hx) in zip(el, stops):
        e.position, e.color = pos, hex_lin(hx)
    g.L.new(fac, n.inputs["Fac"])
    return n.outputs["Color"]


# ------------------------------------------------------------------ whitewash
def paint_material(name="Chair_Whitewash"):
    """Limewash / chalk paint over oak: grey-white, brushed, grain showing through, rubbed back to dark
    wood on edges and in patches, dirt in crevices and near the floor. Needs per-vertex 'grain' (woodgrain.tag_grain)."""
    m, nt, b = _base(name)
    g = G(nt)
    attr = g.node("ShaderNodeAttribute"); attr.attribute_name = "grain"; attr.attribute_type = "GEOMETRY"
    gv = attr.outputs["Vector"]
    tc = g.N.new("ShaderNodeTexCoord")

    # --- wood underneath: rings + pores
    flat = g.mapping(gv, scale=(1, 1, 0))
    dist = g.N.new("ShaderNodeVectorMath"); dist.operation = "LENGTH"
    g.L.new(flat, dist.inputs[0])
    jit = g.noise(g.mapping(gv, scale=(9, 9, 0.6)), 1.0, detail=2.0)
    ringv = g.math("FRACT", g.math("MULTIPLY_ADD", dist.outputs["Value"], 300.0, g.math("MULTIPLY", jit, 6.0)))
    band = g.ramp(ringv, 0.62, 0.97)                                    # latewood bands 0..1
    pores = g.ramp(g.noise(g.mapping(gv, scale=(1500, 1500, 55)), 1.0, detail=1.0), 0.60, 0.76)
    streak = g.noise(g.mapping(gv, scale=(380, 380, 8)), 1.0, detail=4.0, rough=0.6)
    wood_c = g.mix(g.math("MAXIMUM", band, pores), hex_lin("#7d7164"), hex_lin("#40372e"))
    wood_c = g.mix(g.ramp(streak, 0.35, 0.7, 0.0, 0.5), wood_c, hex_lin("#8e8374"))

    # --- the paint: two limewash tones, brush streaks along the grain, grain telegraphing through
    wash = g.ramp(g.noise(g.mapping(gv, scale=(16, 16, 2.4)), 1.0, detail=3.0), 0.35, 0.68)
    paint = g.mix(wash, hex_lin("#d3d1c6"), hex_lin("#a9aeac"))
    brush = g.noise(g.mapping(gv, scale=(70, 70, 2.2)), 1.0, detail=3.0, rough=0.6)
    paint = g.mix(1.0, paint, g.mix(g.ramp(brush, 0.3, 0.75), hex_lin("#e9e9e9"), hex_lin("#ffffff")),
                  blend="MULTIPLY")
    show = g.math("MULTIPLY", g.math("MAXIMUM", g.math("MULTIPLY", band, 0.30), g.math("MULTIPLY", pores, 0.9)), 0.42)
    paint = g.mix(show, paint, hex_lin("#6b6558"))                       # grain lines through the paint
    fine = g.ramp(g.noise(g.mapping(gv, scale=(900, 900, 26)), 1.0, detail=2.0), 0.45, 0.8)
    paint = g.mix(g.math("MULTIPLY", fine, 0.22), paint, hex_lin("#8b877c"))

    # --- wear: edges (bevel normal vs geometric normal) broken up by noise + patches rubbed through
    geo = g.N.new("ShaderNodeNewGeometry")
    bev = g.N.new("ShaderNodeBevel"); bev.inputs["Radius"].default_value = 0.0035; bev.samples = 6
    dot = g.N.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
    g.L.new(bev.outputs["Normal"], dot.inputs[0]); g.L.new(geo.outputs["Normal"], dot.inputs[1])
    edge = g.ramp(dot.outputs["Value"], 0.996, 0.93)
    chips = g.ramp(g.noise(g.mapping(gv, scale=(260, 260, 40)), 1.0, detail=3.0, rough=0.7), 0.42, 0.62)
    patch = g.ramp(g.noise(g.mapping(gv, scale=(7, 7, 1.0)), 1.0, detail=2.0), 0.55, 0.66)
    scuff = g.ramp(g.noise(g.mapping(gv, scale=(110, 110, 9)), 1.0, detail=3.0, rough=0.65), 0.44, 0.56)
    nick = g.ramp(g.noise(g.mapping(gv, scale=(34, 34, 34)), 1.0, detail=1.0), 0.68, 0.74)   # sparse dents
    wear = g.math("MAXIMUM", g.math("MULTIPLY", edge, g.math("MULTIPLY_ADD", chips, 0.9, 0.18)),
                  g.math("MAXIMUM", g.math("MULTIPLY", patch, g.math("MULTIPLY", scuff, 0.95)),
                         g.math("MULTIPLY", nick, 0.6)))
    wear = g.ramp(wear, 0.26, 0.66)
    col = g.mix(wear, paint, wood_c)

    # --- dirt: crevices (AO) and the last 12 cm above the floor
    ao = g.N.new("ShaderNodeAmbientOcclusion"); ao.inputs["Distance"].default_value = 0.05; ao.samples = 8
    crev = g.ramp(ao.outputs["AO"], 0.30, 1.0, 0.65, 0.0)
    _, _, oz = g.xyz(tc.outputs["Object"])
    floor = g.ramp(oz, 0.12, 0.0, 0.0, 0.40)
    col = g.mix(g.math("MAXIMUM", crev, floor), col, hex_lin("#5f574c"), blend="MULTIPLY")
    g.L.new(col, b.inputs["Base Color"])

    # --- roughness: chalky matt, a little glossier rubbed wood, rough chips
    r = g.math("MULTIPLY_ADD", wear, -0.12, g.math("MULTIPLY_ADD", fine, 0.10, 0.70))
    g.L.new(r, b.inputs["Roughness"])
    b.inputs["Specular IOR Level"].default_value = 0.35

    # --- bump: grain ridges, brush ridges, rubbed-through areas sunk, nicks
    h = g.math("MULTIPLY_ADD", wear, -0.55,
               g.math("MULTIPLY_ADD", band, -0.22, g.math("MULTIPLY_ADD", brush, 0.25,
                      g.math("MULTIPLY_ADD", nick, -0.8, g.math("MULTIPLY", pores, -0.15)))))
    bp = g.N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.55
    bp.inputs["Distance"].default_value = 0.0007
    g.L.new(h, bp.inputs["Height"])
    g.L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


# ------------------------------------------------------------------ fabric
def fabric_material(name="Chair_SeatFabric", period=0.0030):
    """Basket-weave upholstery in taupe/brown/sand threads (reference: woven textured seat)."""
    m, nt, b = _base(name)
    g = G(nt)
    uvn = g.N.new("ShaderNodeUVMap"); uvn.uv_map = "FabricUV"
    ux, uy, _ = g.xyz(uvn.outputs["UV"])
    # shift into positive coordinates: Blender's MODULO is truncated, so negative cells would break the weave parity
    uu = g.math("DIVIDE", g.math("ADD", ux, 5.0), period)
    vv = g.math("DIVIDE", g.math("ADD", uy, 5.0), period)
    # a 2x2 basket: pairs of threads travel together -> cell index = floor(coord / 2)
    cu = g.math("FLOOR", uu); cv = g.math("FLOOR", vv)
    par = g.math("MODULO", g.math("ADD", g.math("FLOOR", g.math("DIVIDE", cu, 2.0)),
                                  g.math("FLOOR", g.math("DIVIDE", cv, 2.0))), 2.0)
    pi = math.pi
    hu = g.math("POWER", g.math("SINE", g.math("MULTIPLY", g.math("FRACT", uu), pi)), 0.55)
    hv = g.math("POWER", g.math("SINE", g.math("MULTIPLY", g.math("FRACT", vv), pi)), 0.55)
    height = g.math("MULTIPLY_ADD", par, g.math("SUBTRACT", hu, hv), hv)   # parity picks the over-thread

    def wn(a, bb, c):
        n = g.N.new("ShaderNodeTexWhiteNoise"); n.noise_dimensions = "3D"
        v = g.N.new("ShaderNodeCombineXYZ")      # decorrelate the integer lattice (plain integers hash into diagonal terraces)
        g.set(v.inputs[0], g.math("MULTIPLY_ADD", a, 0.6180339, g.math("MULTIPLY", bb, 0.7548776) if not isinstance(bb, float) else 0.37))
        g.set(v.inputs[1], g.math("MULTIPLY_ADD", bb if not isinstance(bb, float) else a, 0.3819660, 0.113))
        g.set(v.inputs[2], c)
        g.L.new(v.outputs[0], n.inputs["Vector"])
        return n.outputs["Value"]
    ru = wn(cu, 0.0, 7.3)
    rv = wn(0.0, cv, 3.1)
    r = g.math("MULTIPLY_ADD", par, g.math("SUBTRACT", ru, rv), rv)        # random value per visible thread
    mott = g.noise(g.mapping(g.N.new("ShaderNodeTexCoord").outputs["Object"], scale=(9, 9, 9)), 1.0, detail=3.0)
    r = g.math("ADD", g.math("MULTIPLY", r, 0.75), g.math("MULTIPLY", g.math("SUBTRACT", mott, 0.5), 0.5))
    col = _col_ramp(g, r, [(0.00, "#43352a"), (0.30, "#66574a"), (0.62, "#85765f"), (1.00, "#b0a28a")])
    shade = g.ramp(height, 0.0, 1.0, 0.55, 1.05)                              # valleys between threads darker
    col = g.mix(1.0, col, _gray(g, shade), blend="MULTIPLY")
    # dark tuck under the lower edge of the upholstery
    tc = g.N.new("ShaderNodeTexCoord")
    _, _, oz = g.xyz(tc.outputs["Object"])
    tuck = g.ramp(oz, 0.405, 0.428, 0.45, 1.0)
    col = g.mix(1.0, col, _gray(g, tuck), blend="MULTIPLY")
    g.L.new(col, b.inputs["Base Color"])
    g.L.new(g.ramp(height, 0.0, 1.0, 0.95, 0.80), b.inputs["Roughness"])
    b.inputs["Sheen Weight"].default_value = 0.35
    b.inputs["Sheen Roughness"].default_value = 0.5
    b.inputs["Sheen Tint"].default_value = hex_lin("#c9bba3")
    bp = g.N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 1.0
    bp.inputs["Distance"].default_value = 0.0007
    g.L.new(height, bp.inputs["Height"])
    g.L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def _gray(g, val):
    n = g.N.new("ShaderNodeCombineColor")
    for i in range(3):
        g.set(n.inputs[i], val)
    return n.outputs["Color"]


def nail_material(name="Chair_Nailheads"):
    m, nt, b = _base(name)
    b.inputs["Base Color"].default_value = hex_lin("#8a7b5c")
    b.inputs["Metallic"].default_value = 0.85
    b.inputs["Roughness"].default_value = 0.5
    return m
