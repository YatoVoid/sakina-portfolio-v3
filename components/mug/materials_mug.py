"""Mug component materials (procedural; baked to textures for the GLB by _lib/materials.bake_to_images).

- speckled_glaze : white stoneware glaze with three layers of black speckles (tiny / small / rare larger,
                   slightly elongated), uneven glaze tone, orange-peel bump, brown coffee tide-line inside.
- crema          : espresso surface, radial tone, foam ring, bubbles, glossy.
- wood_slice     : end-grain top/bottom of the coaster (pith offset, annual rings, one radial crack).
- bark           : furrowed bark band with a pale cambium line at the top edge.
All coordinates are the object's local metres, so the pattern keeps its real scale.
"""
import math

import bpy

from common import hex_lin
from nodeg import G


def _base(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    g = G(nt)
    out = g.node("ShaderNodeOutputMaterial")
    b = g.node("ShaderNodeBsdfPrincipled")
    g.L.new(b.outputs["BSDF"], out.inputs["Surface"])
    tc = g.node("ShaderNodeTexCoord")
    return m, g, b, tc.outputs["Object"]


def _speck(g, pos, scale, rmin, rmax, dens, stretch=(1, 1, 1), seed=0.0):
    """Dots from a 3D Voronoi: per-cell random radius (R channel) and presence (G channel)."""
    mp = g.mapping(pos, (scale * stretch[0], scale * stretch[1], scale * stretch[2]),
                   (seed, seed * 1.7, seed * 0.3))
    vor = g.node("ShaderNodeTexVoronoi", Vector=mp, Scale=1.0, Randomness=1.0)
    vor.voronoi_dimensions = "3D"
    vor.feature = "F1"
    sep = g.N.new("ShaderNodeSeparateColor")
    g.L.new(vor.outputs["Color"], sep.inputs[0])
    rad = g.math("MULTIPLY_ADD", g.math("POWER", sep.outputs["Red"], 2.5), rmax - rmin, rmin)
    jitter = g.math("MULTIPLY", g.math("SUBTRACT", g.noise(pos, 1800.0, 1.0), 0.5), 0.035)
    d = g.math("ADD", vor.outputs["Distance"], jitter)
    mask = g.ramp(d, g.math("ADD", rad, 0.025), g.math("SUBTRACT", rad, 0.025))
    return g.math("MULTIPLY", mask, g.math("LESS_THAN", sep.outputs["Green"], dens))


def speckled_glaze(name, coffee_z, axis=(0.0, 0.0), density=1.0):
    m, g, b, pos = _base(name)
    x, y, z = g.xyz(pos)
    # --- speckles
    a = _speck(g, pos, 330.0, 0.13, 0.23, 1.0 * density, stretch=(1, 1, 0.85), seed=3.1)   # fine, dense
    s = _speck(g, pos, 170.0, 0.09, 0.17, 0.8 * density, stretch=(1, 1, 0.7), seed=7.7)    # small, slightly streaked
    r = _speck(g, pos, 95.0, 0.08, 0.14, 0.6 * density, stretch=(1.1, 1, 0.55), seed=11.3)  # few larger, streaked
    sp = g.math("MAXIMUM", g.math("MAXIMUM", a, s), r)

    # --- glaze tone: warm white, soft low-frequency drift, slightly creamier where the glaze pools
    drift = g.ramp(g.noise(pos, 11.0, 3.0), 0.35, 0.65)
    glaze = g.mix(drift, hex_lin("#efebe2"), hex_lin("#e0dacd"))
    pool = g.ramp(g.noise(pos, 42.0, 4.0, 0.6), 0.45, 0.75, 0.0, 0.35)
    glaze = g.mix(pool, glaze, hex_lin("#d9cfba"))
    sp_col = g.mix(g.noise(pos, 60.0, 2.0), hex_lin("#070605"), hex_lin("#201812"))
    col = g.mix(sp, glaze, sp_col)

    # --- coffee tide-line on the inside wall only (normal points toward the axis)
    geo = g.node("ShaderNodeNewGeometry")
    vt = g.N.new("ShaderNodeVectorTransform")
    vt.vector_type = "NORMAL"; vt.convert_from = "WORLD"; vt.convert_to = "OBJECT"
    g.L.new(geo.outputs["Normal"], vt.inputs[0])
    nx, ny, nz = g.xyz(vt.outputs[0])
    rx, ry = g.math("SUBTRACT", x, axis[0]), g.math("SUBTRACT", y, axis[1])
    rl = g.math("ADD", g.math("SQRT", g.math("ADD", g.math("MULTIPLY", rx, rx),
                                             g.math("MULTIPLY", ry, ry))), 1e-6)
    dot = g.math("DIVIDE", g.math("ADD", g.math("MULTIPLY", nx, rx), g.math("MULTIPLY", ny, ry)), rl)
    inside = g.ramp(dot, -0.15, -0.55)
    zj = g.math("ADD", z, g.math("MULTIPLY", g.math("SUBTRACT", g.noise(pos, 140.0, 2.0), 0.5), 0.0035))
    band = g.math("MULTIPLY", g.ramp(zj, coffee_z - 0.0015, coffee_z + 0.0005),
                  g.ramp(zj, coffee_z + 0.0065, coffee_z + 0.0015))
    line = g.math("MULTIPLY", g.ramp(zj, coffee_z - 0.0004, coffee_z + 0.0006),
                  g.ramp(zj, coffee_z + 0.0022, coffee_z + 0.0010))
    col = g.mix(g.math("MULTIPLY", g.math("MULTIPLY", inside, band), 0.5), col, hex_lin("#b9966c"))
    col = g.mix(g.math("MULTIPLY", g.math("MULTIPLY", inside, line), 0.55), col, hex_lin("#7d5834"))
    g.L.new(col, b.inputs["Base Color"])

    # --- roughness (satin-gloss glaze, specks slightly rougher) and orange-peel bump
    rough = g.math("MULTIPLY_ADD", g.math("SUBTRACT", g.noise(pos, 650.0, 2.0), 0.5), 0.10, 0.29)
    rough = g.math("ADD", rough, g.math("MULTIPLY", sp, 0.22))
    g.L.new(rough, b.inputs["Roughness"])
    b.inputs["Specular IOR Level"].default_value = 0.55
    h = g.math("SUBTRACT", g.math("MULTIPLY", g.noise(pos, 520.0, 3.0), 0.35),
               g.math("MULTIPLY", sp, 0.30))
    bump = g.node("ShaderNodeBump", Height=h, Strength=0.35, Distance=0.00025)
    g.L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def crema(name):
    m, g, b, pos = _base(name)
    x, y, z = g.xyz(pos)
    rx, ry = g.math("SUBTRACT", x, 0.0), g.math("SUBTRACT", y, 0.0)
    d = g.math("SQRT", g.math("ADD", g.math("MULTIPLY", rx, rx), g.math("MULTIPLY", ry, ry)))
    t = g.ramp(d, 0.010, 0.046, 0.0, 0.8, smooth=True)                # centre -> rim
    swirl = g.noise(g.mapping(pos, (260, 260, 1)), 1.0, 5.0, 0.6)
    t = g.math("ADD", t, g.math("MULTIPLY", g.math("SUBTRACT", swirl, 0.5), 0.55))
    ramp = g.N.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.15, hex_lin("#4a280f")
    e[1].position, e[1].color = 0.95, hex_lin("#7f4d22")
    mid = ramp.color_ramp.elements.new(0.55); mid.color = hex_lin("#623516")
    g.L.new(g.math("MAXIMUM", g.math("MINIMUM", t, 1.0), 0.0), ramp.inputs["Fac"])
    # bubbles: bright foam dots along the rim
    vor = g.node("ShaderNodeTexVoronoi", Vector=g.mapping(pos, (900, 900, 900)), Scale=1.0)
    vor.voronoi_dimensions = "3D"
    bub = g.math("MULTIPLY", g.ramp(vor.outputs["Distance"], 0.34, 0.2),
                 g.ramp(d, 0.034, 0.045))
    col = g.mix(g.math("MULTIPLY", bub, 0.35), ramp.outputs["Color"], hex_lin("#9a6430"))
    g.L.new(col, b.inputs["Base Color"])
    g.L.new(g.math("MULTIPLY_ADD", swirl, 0.16, 0.26), b.inputs["Roughness"])
    return m


def wood_slice(name, pith=(-0.007, 0.005)):
    m, g, b, pos = _base(name)
    x, y, z = g.xyz(pos)
    px, py = g.math("SUBTRACT", x, pith[0]), g.math("SUBTRACT", y, pith[1])
    dist = g.math("SQRT", g.math("ADD", g.math("MULTIPLY", px, px), g.math("MULTIPLY", py, py)))
    wob = g.math("MULTIPLY", g.math("SUBTRACT", g.noise(pos, 38.0, 3.0), 0.5), 0.006)
    ph = g.math("FRACT", g.math("MULTIPLY", g.math("ADD", dist, wob), 430.0))      # ~24 rings over 55 mm
    late = g.ramp(ph, 0.70, 0.99)
    base = g.mix(g.ramp(g.noise(pos, 20.0, 3.0), 0.3, 0.7), hex_lin("#9a7142"), hex_lin("#85603a"))
    col = g.mix(g.math("MULTIPLY", late, 0.40), base, hex_lin("#63421f"))
    fibre = g.noise(g.mapping(pos, (1400, 1400, 1400)), 1.0, 3.0)
    col = g.mix(g.math("MULTIPLY", g.ramp(fibre, 0.55, 0.8), 0.35), col, hex_lin("#bda070"))
    # one radial drying crack from the pith
    ang = g.math("ARCTAN2", py, px)
    dang = g.math("ABSOLUTE", g.math("SUBTRACT", ang, 0.55))
    arc = g.math("MULTIPLY", dang, g.math("MAXIMUM", dist, 0.001))                      # metres across the crack
    crack = g.math("MULTIPLY", g.ramp(arc, 0.0009, 0.0002),
                   g.math("MULTIPLY", g.ramp(dist, 0.005, 0.009), g.ramp(dist, 0.042, 0.030)))
    col = g.mix(crack, col, hex_lin("#4c351d"))
    g.L.new(col, b.inputs["Base Color"])
    g.L.new(g.math("MULTIPLY_ADD", fibre, 0.2, 0.55), b.inputs["Roughness"])
    h = g.math("SUBTRACT", g.math("MULTIPLY", late, 0.5), g.math("MULTIPLY", crack, 3.0))
    bump = g.node("ShaderNodeBump", Height=h, Strength=0.5, Distance=0.0004)
    g.L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def bark(name, top_z):
    m, g, b, pos = _base(name)
    x, y, z = g.xyz(pos)
    furrow = g.noise(g.mapping(pos, (260, 260, 34)), 1.0, 8.0, 0.68)
    plates = g.noise(g.mapping(pos, (90, 90, 14)), 1.0, 4.0, 0.55)
    patch = g.noise(pos, 30.0, 3.0)
    ramp = g.N.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.30, hex_lin("#1c140e")
    e[1].position, e[1].color = 0.82, hex_lin("#5b4636")
    g.L.new(furrow, ramp.inputs["Fac"])
    col = g.mix(g.ramp(patch, 0.55, 0.75, 0.0, 0.5), ramp.outputs["Color"], hex_lin("#8b8070"))
    cam = g.ramp(z, top_z - 0.0016, top_z - 0.0006)                                   # pale cambium line
    col = g.mix(g.math("MULTIPLY", cam, 0.9), col, hex_lin("#e6dabd"))
    g.L.new(col, b.inputs["Base Color"])
    g.L.new(g.math("MULTIPLY_ADD", furrow, -0.15, 0.93), b.inputs["Roughness"])
    bump = g.node("ShaderNodeBump", Height=g.math("ADD", furrow, g.math("MULTIPLY", plates, 0.8)), Strength=1.0, Distance=0.0030)
    g.L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m
