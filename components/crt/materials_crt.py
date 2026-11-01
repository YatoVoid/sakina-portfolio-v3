"""CRT-specific PBR materials: textured black ABS with moulded vent slots / speaker perforations
(procedural masks in the CRT's local frame, baked to textures for the GLB), and the phosphor screen."""
import bpy

from common import hex_lin


class G:
    """Tiny node-graph helper."""
    def __init__(self, nt):
        self.nt, self.N, self.L = nt, nt.nodes, nt.links

    def node(self, kind, **inputs):
        n = self.N.new(kind)
        for k, v in inputs.items():
            if isinstance(v, bpy.types.NodeSocket):
                self.L.new(v, n.inputs[k])
            else:
                n.inputs[k].default_value = v
        return n

    def math(self, op, a, b=0.0, c=None):
        n = self.N.new("ShaderNodeMath"); n.operation = op
        for i, x in enumerate((a, b) if c is None else (a, b, c)):
            if isinstance(x, bpy.types.NodeSocket):
                self.L.new(x, n.inputs[i])
            else:
                n.inputs[i].default_value = x
        return n.outputs[0]

    def between(self, x, lo, hi, soft=0.0005):
        a = self.math("GREATER_THAN", x, lo)
        return self.math("MULTIPLY", a, self.math("LESS_THAN", x, hi))


def abs_plastic(name, base="#161514", rough=0.55, gloss_front=False, dust=0.35):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    g = G(nt)
    out = g.node("ShaderNodeOutputMaterial")
    b = g.node("ShaderNodeBsdfPrincipled")
    g.L.new(b.outputs["BSDF"], out.inputs["Surface"])

    tc = g.node("ShaderNodeTexCoord")
    xyz = g.node("ShaderNodeSeparateXYZ"); g.L.new(tc.outputs["Object"], xyz.inputs[0])
    X, Y, Z = xyz.outputs["X"], xyz.outputs["Y"], xyz.outputs["Z"]
    geo = g.node("ShaderNodeNewGeometry")
    nrm = g.node("ShaderNodeVectorTransform"); nrm.vector_type = "NORMAL"
    nrm.convert_from = "WORLD"; nrm.convert_to = "OBJECT"
    g.L.new(geo.outputs["Normal"], nrm.inputs[0])
    n = g.node("ShaderNodeSeparateXYZ"); g.L.new(nrm.outputs[0], n.inputs[0])
    NX, NZ = g.math("ABSOLUTE", n.outputs["X"]), n.outputs["Z"]

    # top vent slots (along Y), pitch 12 mm, on the sloped top of the housing
    top = g.math("GREATER_THAN", NZ, 0.5)
    stripes = g.math("LESS_THAN", g.math("FRACT", g.math("DIVIDE", g.math("ADD", X, 0.3), 0.012)), 0.42)
    top_vent = g.math("MULTIPLY", g.math("MULTIPLY", top, stripes),
                      g.math("MULTIPLY", g.between(Y, 0.135, 0.265), g.between(X, -0.084, 0.084)))
    # side vent slots (horizontal), on both flanks of the housing
    side = g.math("GREATER_THAN", NX, 0.5)
    hz = g.math("LESS_THAN", g.math("FRACT", g.math("DIVIDE", Z, 0.011)), 0.40)
    side_vent = g.math("MULTIPLY", g.math("MULTIPLY", side, hz),
                       g.math("MULTIPLY", g.between(Y, 0.150, 0.255), g.between(Z, 0.10, 0.25)))
    # speaker perforations on the bezel flanks: dot grid, pitch 5.5 mm, r 1.5 mm
    fy = g.math("SUBTRACT", g.math("FRACT", g.math("DIVIDE", Y, 0.0055)), 0.5)
    fz = g.math("SUBTRACT", g.math("FRACT", g.math("DIVIDE", Z, 0.0055)), 0.5)
    rr = g.math("SQRT", g.math("ADD", g.math("MULTIPLY", fy, fy), g.math("MULTIPLY", fz, fz)))
    dots = g.math("LESS_THAN", rr, 0.28)
    spk = g.math("MULTIPLY", g.math("MULTIPLY", side, dots),
                 g.math("MULTIPLY", g.between(Y, 0.012, 0.070), g.between(Z, 0.05, 0.31)))
    holes = g.math("MAXIMUM", g.math("MAXIMUM", top_vent, side_vent), spk)

    # moulded micro texture (EDM finish)
    tex_map = g.node("ShaderNodeMapping", Vector=tc.outputs["Object"], Scale=(1, 1, 1))
    micro = g.node("ShaderNodeTexNoise", Vector=tex_map.outputs["Vector"], Scale=2600.0, Detail=2.0)
    blot = g.node("ShaderNodeTexNoise", Vector=tex_map.outputs["Vector"], Scale=18.0, Detail=4.0)

    # colour: black ABS, slight blotchy fade, grime in crevices, dust on up-facing surfaces, holes darker
    c1 = g.node("ShaderNodeMix"); c1.data_type = "RGBA"
    g.L.new(blot.outputs["Fac"], c1.inputs["Factor"])
    c1.inputs["A"].default_value = hex_lin(base)
    c1.inputs["B"].default_value = hex_lin("#232120")
    ao = g.node("ShaderNodeAmbientOcclusion", Distance=0.02); ao.samples = 8
    grime = g.node("ShaderNodeMapRange", Value=ao.outputs["AO"], **{"From Min": 0.3, "From Max": 1.0,
                                                                   "To Min": 0.6, "To Max": 0.0})
    c2 = g.node("ShaderNodeMix"); c2.data_type = "RGBA"; c2.blend_type = "MIX"
    g.L.new(grime.outputs["Result"], c2.inputs["Factor"])
    g.L.new(c1.outputs["Result"], c2.inputs["A"]); c2.inputs["B"].default_value = hex_lin("#2b2620")
    dustn = g.node("ShaderNodeTexNoise", Vector=tex_map.outputs["Vector"], Scale=60.0, Detail=6.0)
    dmask = g.math("MULTIPLY", g.math("MULTIPLY", g.math("GREATER_THAN", NZ, 0.6),
                                      g.math("POWER", dustn.outputs["Fac"], 2.0)), dust)
    c3 = g.node("ShaderNodeMix"); c3.data_type = "RGBA"
    g.L.new(dmask, c3.inputs["Factor"]); g.L.new(c2.outputs["Result"], c3.inputs["A"])
    c3.inputs["B"].default_value = hex_lin("#5b5652")
    c4 = g.node("ShaderNodeMix"); c4.data_type = "RGBA"
    g.L.new(holes, c4.inputs["Factor"]); g.L.new(c3.outputs["Result"], c4.inputs["A"])
    c4.inputs["B"].default_value = hex_lin("#030303")
    g.L.new(c4.outputs["Result"], b.inputs["Base Color"])

    # roughness: textured, dust rougher, holes fully rough
    r = g.math("MULTIPLY_ADD", micro.outputs["Fac"], 0.12, rough - 0.06)
    r = g.math("MAXIMUM", g.math("ADD", r, g.math("MULTIPLY", dmask, 0.5)), g.math("MULTIPLY", holes, 0.95))
    g.L.new(r, b.inputs["Roughness"])
    b.inputs["Specular IOR Level"].default_value = 0.5

    # normal: micro texture + recessed holes
    h = g.math("SUBTRACT", g.math("MULTIPLY", micro.outputs["Fac"], 0.15), holes)
    bump = g.node("ShaderNodeBump", Height=h, Strength=0.6, Distance=0.0015)
    g.L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def screen(name, img_path, strength=1.4):
    """CRT faceplate: glossy dark glass + phosphor image as emission (strength 0 = TV off)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    g = G(nt)
    out = g.node("ShaderNodeOutputMaterial")
    b = g.node("ShaderNodeBsdfPrincipled")
    g.L.new(b.outputs["BSDF"], out.inputs["Surface"])
    t = g.node("ShaderNodeTexImage")
    t.image = bpy.data.images.load(str(img_path), check_existing=True)
    b.inputs["Base Color"].default_value = hex_lin("#121615")
    b.inputs["Roughness"].default_value = 0.08
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.03
    g.L.new(t.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = strength
    return m
