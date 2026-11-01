"""PBR material helpers for components. Procedural, bake-safe Principled BSDF node trees.

Colours are given as sRGB hex (as picked from a reference photo) and converted to linear for Blender.
Every material keeps the Principled BSDF as the single shader so Cycles lightmap bakes and the glTF
texture bake (export.py) both work.
"""
import bpy


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(h, a=1.0):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (a,)


class Mat:
    """Small builder around a node tree: m = Mat("Wood"); m.base("#6b4a2e"); ...; m.material"""

    def __init__(self, name):
        self.material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        self.material.use_nodes = True
        self.nt = self.material.node_tree
        for n in list(self.nt.nodes):
            self.nt.nodes.remove(n)
        self.out = self.node("ShaderNodeOutputMaterial", (600, 0))
        self.bsdf = self.node("ShaderNodeBsdfPrincipled", (300, 0))
        self.link(self.bsdf.outputs["BSDF"], self.out.inputs["Surface"])
        self._coord = None

    # ── plumbing ──────────────────────────────────────────────────────────
    def node(self, kind, loc=(0, 0), **props):
        n = self.nt.nodes.new(kind); n.location = loc
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def link(self, a, b):
        self.nt.links.new(a, b)

    def coord(self, kind="Object"):
        """Texture coordinates. Object space keeps patterns at real-world scale on any mesh."""
        if self._coord is None:
            self._coord = self.node("ShaderNodeTexCoord", (-1400, 0))
        return self._coord.outputs[kind]

    # ── simple inputs ─────────────────────────────────────────────────────
    def set(self, **inputs):
        """m.set(Roughness=0.6, Metallic=0.0, **{"Coat Weight": 0.3})"""
        for k, v in inputs.items():
            self.bsdf.inputs[k].default_value = v
        return self

    def base(self, hex_colour):
        self.bsdf.inputs["Base Color"].default_value = hex_rgba(hex_colour)
        return self

    # ── procedural layers ─────────────────────────────────────────────────
    def noise(self, scale, detail=6.0, rough=0.6, distortion=0.0, coord="Object", loc=(-1100, 0), dims="3D"):
        n = self.node("ShaderNodeTexNoise", loc)
        n.noise_dimensions = dims
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        n.inputs["Distortion"].default_value = distortion
        self.link(self.coord(coord), n.inputs["Vector"])
        return n

    def ramp(self, src, stops, loc=(-800, 0)):
        """stops: [(pos, hex_or_gray)] — gray floats give data ramps (roughness), hex strings give colour."""
        r = self.node("ShaderNodeValToRGB", loc)
        els = r.color_ramp.elements
        while len(els) > 1:
            els.remove(els[-1])
        for i, (pos, val) in enumerate(stops):
            e = els[0] if i == 0 else els.new(pos)
            e.position = pos
            e.color = hex_rgba(val) if isinstance(val, str) else (val, val, val, 1.0)
        self.link(src, r.inputs["Fac"])
        return r

    def colour_variation(self, hex_a, hex_b, scale=6.0, detail=8.0, contrast=(0.35, 0.65), loc_y=200):
        """Base colour drifting between two tones (dirt, fading, uneven paint)."""
        n = self.noise(scale, detail, 0.6, loc=(-1100, loc_y))
        r = self.ramp(n.outputs["Fac"], [(contrast[0], hex_a), (contrast[1], hex_b)], loc=(-800, loc_y))
        self.link(r.outputs["Color"], self.bsdf.inputs["Base Color"])
        return r

    def roughness_variation(self, lo, hi, scale=12.0, detail=6.0, loc_y=-200):
        n = self.noise(scale, detail, 0.55, loc=(-1100, loc_y))
        r = self.ramp(n.outputs["Fac"], [(0.35, lo), (0.65, hi)], loc=(-800, loc_y))
        self.link(r.outputs["Color"], self.bsdf.inputs["Roughness"])
        return r

    def bump(self, height_socket, strength=0.15, distance=0.002, loc=(0, -450)):
        b = self.node("ShaderNodeBump", loc)
        b.inputs["Strength"].default_value = strength
        b.inputs["Distance"].default_value = distance
        self.link(height_socket, b.inputs["Height"])
        self.link(b.outputs["Normal"], self.bsdf.inputs["Normal"])
        return b

    def micro_bump(self, scale=400.0, strength=0.05):
        """Fine surface texture (plastic grain, paper tooth)."""
        n = self.noise(scale, 4.0, 0.5, loc=(-400, -450))
        return self.bump(n.outputs["Fac"], strength, 0.0005)


def emission_mat(name, hex_colour, strength):
    m = Mat(name).base(hex_colour)
    m.set(**{"Emission Color": hex_rgba(hex_colour), "Emission Strength": strength, "Roughness": 0.4})
    return m.material
