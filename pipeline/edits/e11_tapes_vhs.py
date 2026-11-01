"""Edit #11 (round 4, user reference photo 2026-11-01, 'Free Blockbuster: VHS tapes are back'):
the 13 project tapes become real-looking VHS cassettes in a loose, hand-piled stack.

Reference, read from the photo:
- Every cassette is a black plastic shell with a visible parting seam, rounded edges, a smoked window and printed
  labels on top; the spine (the long narrow face toward the viewer) carries a WHITE paper label, usually full length,
  with printed text and coloured stripes. Stacks are irregular: tapes stick out left and right, a few are pulled
  forward or pushed back, and each one is rotated a few degrees.

Built here (what is kept from the V2/V3 tapes: names, numbers, logos, icons, and each tape's own colour):
- shell: two bevelled halves with a 0.8 mm seam, near-black plastic with soft edge highlights and micro texture
- spine: one full-length cream paper label over the shell; the tape's colour now runs as a stripe along the label
  (and as the colour block behind the logo, as before); name / site / number / logo / icons stay where they were
- top: smoked window on the back half; a white paper label with a colour stripe and the project name on the front half
  (Dental-X keeps its own dark sticker and logo)
- stack: seeded offsets (sideways, forward/back) and yaw per tape, bounded so nothing touches the VCR or the props
Tape order, object names and heights are unchanged, so tapes.json / click targets only need regenerating.
"""
import bpy, bmesh, math, random
from mathutils import Matrix, Vector

STACKS = {
    "left":  ["Tape_The", "Tape_Softsyncdev", "Tape_Blutech", "Tape_University", "Tape_Tmac", "Tape_Dental-X"],
    "right": ["PTape_7", "PTape_6", "PTape_5", "PTape_4", "PTape_3", "PTape_2", "PTape_1"],
}
COLOUR = {   # each tape's own colour (from its V2/V3 body material)
    "Tape_Dental-X": "2f6f73", "Tape_Tmac": "c9a227", "Tape_University": "b3242b", "Tape_Blutech": "2a3a8a",
    "Tape_Softsyncdev": "d9822b", "Tape_The": "3a7a4a", "PTape_1": "14224a", "PTape_2": "1f4a2a", "PTape_3": "4a2468",
    "PTape_4": "b5521a", "PTape_5": "26262a", "PTape_6": "12404a", "PTape_7": "6a1a1e"}
# sideways / forward-back offset ranges (m) and yaw range (deg) per stack: the left stack must stay clear of the VCR (x 0.18)
JITTER = {"left": dict(dx=(0.000, 0.040), dy=(-0.020, 0.016), yaw=(3.0, 9.0)),
          "right": dict(dx=(-0.030, 0.012), dy=(-0.020, 0.016), yaw=(3.0, 9.0))}
SEED = 41

L, W, T = 0.200, 0.112, 0.028
HL, HW = L / 2, W / 2
FACE_Y = -HW                      # spine face (toward the viewer)
SEAM = 0.0004


def _lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c) + (1.0,)


def _N(nt, t, **kw):
    n = nt.nodes.new(t)
    for k, v in kw.items():
        if k.startswith("in_"):
            n.inputs[k[3:].replace("_", " ")].default_value = v
        else:
            setattr(n, k, v)
    return n


# ------------------------------------------------------------------------------------------------ materials
def shell_mat():
    m = bpy.data.materials.get("VHSShell")
    if m:
        return m
    m = bpy.data.materials.new("VHSShell"); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    geo = _N(nt, "ShaderNodeNewGeometry")
    tc = _N(nt, "ShaderNodeTexCoord")
    edge = _N(nt, "ShaderNodeValToRGB")                          # pointiness -> edge wear (lighter, shinier)
    edge.color_ramp.elements[0].position = 0.50; edge.color_ramp.elements[1].position = 0.60
    nt.links.new(geo.outputs["Pointiness"], edge.inputs["Fac"])
    n1 = _N(nt, "ShaderNodeTexNoise", in_Scale=260.0, in_Detail=4.0, in_Roughness=0.6)
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    n2 = _N(nt, "ShaderNodeTexNoise", in_Scale=7.0, in_Detail=3.0)
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    base = _N(nt, "ShaderNodeMix", data_type='RGBA')
    base.inputs[6].default_value = _lin("0d0d0f"); base.inputs[7].default_value = _lin("1a1a1d")
    nt.links.new(n2.outputs["Fac"], base.inputs[0])
    wear = _N(nt, "ShaderNodeMix", data_type='RGBA'); wear.inputs[7].default_value = _lin("2e2d32")
    nt.links.new(edge.outputs["Color"], wear.inputs[0]); nt.links.new(base.outputs[2], wear.inputs[6])
    nt.links.new(wear.outputs[2], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.5; bs.inputs["Specular IOR Level"].default_value = 0.35
    bp = _N(nt, "ShaderNodeBump", in_Strength=0.18, in_Distance=0.0006)
    nt.links.new(n1.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
    return m


def window_mat():
    m = bpy.data.materials.get("VHSWindow")
    if m:
        return m
    m = bpy.data.materials.new("VHSWindow"); m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = _lin("1d2125")
    bs.inputs["Roughness"].default_value = 0.10; bs.inputs["Specular IOR Level"].default_value = 0.8
    bs.inputs["Coat Weight"].default_value = 0.3
    return m


def label_mat():
    m = bpy.data.materials.get("VHSLabel")
    if m:
        return m
    m = bpy.data.materials.new("VHSLabel"); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    tc = _N(nt, "ShaderNodeTexCoord"); oi = _N(nt, "ShaderNodeObjectInfo")
    n = _N(nt, "ShaderNodeTexNoise", in_Scale=26.0, in_Detail=5.0)
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    age = _N(nt, "ShaderNodeMix", data_type='RGBA')
    age.inputs[6].default_value = _lin("f1ede0"); age.inputs[7].default_value = _lin("d9d0b8")
    mix = _N(nt, "ShaderNodeMath", operation='MULTIPLY'); mix.inputs[1].default_value = 0.5
    nt.links.new(n.outputs["Fac"], mix.inputs[0]); nt.links.new(mix.outputs[0], age.inputs[0])
    nt.links.new(age.outputs[2], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.52; bs.inputs["Specular IOR Level"].default_value = 0.3
    bp = _N(nt, "ShaderNodeBump", in_Strength=0.08, in_Distance=0.0003)
    nt.links.new(n.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
    return m


def band_mat(name, hexcol):
    key = "VHSBand_" + name
    m = bpy.data.materials.get(key)
    if m:
        return m
    m = bpy.data.materials.new(key); m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = _lin(hexcol)
    bs.inputs["Roughness"].default_value = 0.5; bs.inputs["Specular IOR Level"].default_value = 0.3
    return m


# ------------------------------------------------------------------------------------------------ geometry
def shell_mesh(name):
    bm = bmesh.new()
    for z0, z1 in ((SEAM, T / 2), (-T / 2, -SEAM)):
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]:
            v.co.x *= L; v.co.y *= W; v.co.z = z0 if v.co.z < 0 else z1
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.0030, segments=3, affect='EDGES')
    bm.normal_update()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(shell_mat())
    return me


def _box(name, parent, x0, x1, y0, y1, z0, z1, mat):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co.x = x0 if v.co.x < 0 else x1
        v.co.y = y0 if v.co.y < 0 else y1
        v.co.z = z0 if v.co.z < 0 else z1
    bm.normal_update(); bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    o.parent = parent
    for c in bpy.data.collections:
        if parent.name in c.objects:
            c.objects.link(o)
    return o


def _remove(o):
    me = o.data if o.type in ('MESH', 'FONT') else None
    bpy.data.objects.remove(o, do_unlink=True)
    if me is not None and me.users == 0:
        (bpy.data.meshes if isinstance(me, bpy.types.Mesh) else bpy.data.curves).remove(me)


def _dress(root, rng):
    D = bpy.data
    n = root.name
    col = COLOUR[n]
    # shell
    old = root.data
    root.data = shell_mesh(n + "_Shell")
    if old.users == 0:
        D.meshes.remove(old)
    # drop the old coloured strip + edge line: replaced by one full-length label
    for c in list(root.children):
        if c.name in (n + "_Strip", n + "_StripEdge"):
            _remove(c)
    lab, band = label_mat(), band_mat(n, col)
    fy = FACE_Y
    # spine label: full length, cream paper, just proud of the shell face
    _box(n + "_Label", root, -0.0965, 0.0975, fy - 0.0008, fy + 0.0001, -0.0107, 0.0107, lab)
    # colour stripes along the label, right of the logo panel (panel spans x -0.094 .. -0.035)
    _box(n + "_LabelBand", root, -0.0335, 0.0965, fy - 0.0012, fy - 0.0007, -0.0105, -0.0052, band)
    _box(n + "_LabelLine", root, -0.0335, 0.0965, fy - 0.0011, fy - 0.0007, 0.0093, 0.0105, band)
    # top face: smoked window on the back half, flap hinge line
    win = window_mat()
    _box(n + "_Window", root, -0.052, 0.052, 0.004, 0.044, T / 2 - 0.0004, T / 2 + 0.0005, win)
    _box(n + "_Hinge", root, -0.094, 0.094, 0.0495, 0.0508, T / 2 - 0.0003, T / 2 + 0.0004, shell_mat())
    if n != "Tape_Dental-X":                                  # Dental-X keeps its own sticker + logo
        z = T / 2
        _box(n + "_TopLabel", root, -0.082, 0.082, -0.047, -0.006, z - 0.0003, z + 0.0006, lab)
        _box(n + "_TopBand", root, -0.082, 0.082, -0.047, -0.039, z + 0.0004, z + 0.0008, band)
        name = next((c for c in root.children if c.name == n + "_Name"), None)
        no = next((c for c in root.children if c.name == n + "_No"), None)
        if name is not None:
            t = D.objects.new(n + "_Top_Name", name.data.copy()); t.parent = root
            t.location = (-0.076, -0.0295, z + 0.0012); t.rotation_euler = (0, 0, 0)
            t.scale = (0.95, 0.95, 0.95)
            for c in D.collections:
                if root.name in c.objects:
                    c.objects.link(t)
        if no is not None:
            t2 = D.objects.new(n + "_Top_No", no.data.copy()); t2.parent = root
            t2.location = (0.066, -0.0295, z + 0.0012); t2.rotation_euler = (0, 0, 0)
            for c in D.collections:
                if root.name in c.objects:
                    c.objects.link(t2)


def apply():
    D = bpy.data
    rng = random.Random(SEED)
    for stack, names in STACKS.items():
        J = JITTER[stack]
        for i, n in enumerate(names):
            r = D.objects[n]
            _dress(r, rng)
            r.location.x += rng.uniform(*J["dx"])
            r.location.y += rng.uniform(*J["dy"])
            sgn = 1 if i % 2 else -1                                   # alternate lean so the pile zig-zags
            r.rotation_euler.z = math.radians(sgn * rng.uniform(*J["yaw"]))
    bpy.context.view_layer.update()
    print("e11 VHS tapes dressed:", sum(len(v) for v in STACKS.values()))


if __name__ == "__main__":                         # standalone: python3 e11_tapes_vhs.py <in.blend> <out.blend>
    import sys
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    bpy.ops.wm.open_mainfile(filepath=a[0]); apply()
    bpy.ops.wm.save_as_mainfile(filepath=a[1], compress=True)
