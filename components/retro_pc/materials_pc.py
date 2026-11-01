"""Materials for the retro beige desktop PC: yellowed ABS (procedural, baked later), flat dark parts,
glossy phosphor screen."""
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


def beige_abs(name, base="#cdc7a8", aged="#aa9e76", rough=0.52, dust=0.30, scuff=0.35):
    """1980s computer plastic: warm cream that has yellowed unevenly, fine moulded texture, grime in crevices,
    dust on up-facing surfaces, a few scuffs. Uses object coordinates (component-local)."""
    m, nt, b = _base(name)
    g = G(nt)
    tc = g.N.new("ShaderNodeTexCoord")
    obj = tc.outputs["Object"]
    geo = g.N.new("ShaderNodeNewGeometry")
    nrm = g.N.new("ShaderNodeVectorTransform"); nrm.vector_type = "NORMAL"
    nrm.convert_from = "WORLD"; nrm.convert_to = "OBJECT"
    g.L.new(geo.outputs["Normal"], nrm.inputs[0])
    _, _, nz = g.xyz(nrm.outputs[0])

    blot = g.noise(g.mapping(obj, scale=(7, 7, 7)), 1.0, detail=4.0, rough=0.6)         # yellowing, broad
    blot2 = g.noise(g.mapping(obj, scale=(26, 26, 26), loc=(3, 1, 2)), 1.0, detail=3.0)
    age = g.ramp(g.math("ADD", g.math("MULTIPLY", blot, 0.75), g.math("MULTIPLY", blot2, 0.35)), 0.30, 0.80)
    col = g.mix(age, hex_lin(base), hex_lin(aged))

    # fine moulded grain
    micro = g.noise(g.mapping(obj, scale=(1, 1, 1)), 2200.0, detail=2.0)
    col = g.mix(g.math("MULTIPLY", g.ramp(micro, 0.4, 0.7), 0.06), col, hex_lin("#8f866a"))

    # grime in crevices, darker toward the floor of the case
    ao = g.N.new("ShaderNodeAmbientOcclusion"); ao.inputs["Distance"].default_value = 0.025; ao.samples = 8
    crev = g.ramp(ao.outputs["AO"], 0.30, 1.0, 0.55, 0.0)
    col = g.mix(crev, col, hex_lin("#5e5438"), blend="MIX")

    # dust on up-facing surfaces
    dn = g.noise(g.mapping(obj, scale=(40, 40, 40)), 1.0, detail=6.0)
    dmask = g.math("MULTIPLY", g.math("MULTIPLY", g.ramp(nz, 0.55, 0.95), g.math("POWER", dn, 2.0)), dust)
    col = g.mix(dmask, col, hex_lin("#c9c2a6"))

    # scuffs: pale streaks along edges (bevel mask)
    bev = g.N.new("ShaderNodeBevel"); bev.inputs["Radius"].default_value = 0.002; bev.samples = 6
    dot = g.N.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
    g.L.new(bev.outputs["Normal"], dot.inputs[0]); g.L.new(geo.outputs["Normal"], dot.inputs[1])
    edge = g.ramp(dot.outputs["Value"], 0.997, 0.94)
    sc = g.ramp(g.noise(g.mapping(obj, scale=(140, 140, 14)), 1.0, detail=3.0), 0.5, 0.65)
    scm = g.math("MULTIPLY", edge, g.math("MULTIPLY_ADD", sc, scuff, 0.2))
    col = g.mix(scm, col, hex_lin("#e6e0c8"))
    g.L.new(col, b.inputs["Base Color"])

    rr = g.math("MULTIPLY_ADD", micro, 0.10, rough - 0.05)
    rr = g.math("ADD", rr, g.math("MULTIPLY", dmask, 0.4))
    g.L.new(g.math("MINIMUM", rr, 0.95), b.inputs["Roughness"])
    b.inputs["Specular IOR Level"].default_value = 0.45
    bump = g.N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.0008
    g.L.new(g.math("MULTIPLY", micro, 0.4), bump.inputs["Height"])
    g.L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def flat(name, color, rough=0.5, metal=0.0, coat=0.0):
    m, nt, b = _base(name)
    b.inputs["Base Color"].default_value = hex_lin(color)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    return m


def screen(name, img_path, strength=1.6):
    m, nt, b = _base(name)
    g = G(nt)
    t = g.N.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(str(img_path), check_existing=True)
    b.inputs["Base Color"].default_value = hex_lin("#0b0f0c")
    b.inputs["Roughness"].default_value = 0.10
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.04
    g.L.new(t.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = strength
    return m
