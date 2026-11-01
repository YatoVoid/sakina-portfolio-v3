"""Small shader-node graph helper (sockets or constants anywhere)."""
import bpy


class G:
    def __init__(self, nt):
        self.nt, self.N, self.L = nt, nt.nodes, nt.links

    def set(self, sock, v):
        if isinstance(v, bpy.types.NodeSocket):
            self.L.new(v, sock)
        else:
            sock.default_value = v

    def node(self, kind, **kw):
        n = self.N.new(kind)
        for k, v in kw.items():
            self.set(n.inputs[k], v)
        return n

    def math(self, op, a, b=0.0, c=None):
        n = self.N.new("ShaderNodeMath")
        n.operation = op
        self.set(n.inputs[0], a)
        self.set(n.inputs[1], b)
        if c is not None:
            self.set(n.inputs[2], c)
        return n.outputs[0]

    def ramp(self, v, a, b, lo=0.0, hi=1.0, smooth=False):
        """Map Range: a -> lo, b -> hi, clamped (a may be > b for reversed ramps)."""
        n = self.N.new("ShaderNodeMapRange")
        n.interpolation_type = "SMOOTHSTEP" if smooth else "LINEAR"
        n.clamp = True
        for k, x in (("Value", v), ("From Min", a), ("From Max", b), ("To Min", lo), ("To Max", hi)):
            self.set(n.inputs[k], x)
        return n.outputs["Result"]

    def mix(self, fac, A, B, blend="MIX"):
        n = self.N.new("ShaderNodeMix")
        n.data_type = "RGBA"
        n.blend_type = blend
        self.set(n.inputs["Factor"], fac)
        self.set(n.inputs["A"], A)
        self.set(n.inputs["B"], B)
        return n.outputs["Result"]

    def noise(self, vec, scale, detail=2.0, rough=0.5):
        n = self.node("ShaderNodeTexNoise", Vector=vec, Scale=scale, Detail=detail, Roughness=rough)
        return n.outputs["Fac"]

    def xyz(self, vec):
        n = self.N.new("ShaderNodeSeparateXYZ")
        self.L.new(vec, n.inputs[0])
        return n.outputs["X"], n.outputs["Y"], n.outputs["Z"]

    def mapping(self, vec, scale=(1, 1, 1), loc=(0, 0, 0)):
        n = self.node("ShaderNodeMapping", Vector=vec)
        n.inputs["Scale"].default_value = scale
        n.inputs["Location"].default_value = loc
        return n.outputs["Vector"]
