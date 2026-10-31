# Copied from the V2 pipeline (C:\Users\sakin\Downloads\v2\v2\pipeline, read-only source; V2 untouched).
# V3 changes: work dir from $V3_WORK instead of /home/wali/...; Cycles on CPU (cloud has no GPU).
import os
import bpy, bmesh, random
D = bpy.data
sc = bpy.context.scene
B = os.environ.get("V3_WORK", "/tmp/v3work")


def lin(h):
    h = h.lstrip("#"); out = []
    for i in (0, 2, 4):
        c = int(h[i:i+2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


def rgba(h, k=1.0):
    return (*(c * k for c in lin(h)), 1.0)


class Mat:
    def __init__(self, mat):
        self.t = mat.node_tree
        self.n, self.l = self.t.nodes, self.t.links

    def add(self, kind, x=0, y=0, **inputs):
        nd = self.n.new(kind); nd.location = (x, y)
        for k, v in inputs.items():
            if k in ("data_type", "blend_type"):
                setattr(nd, k, v)
            else:
                nd.inputs[k.replace("_", " ")].default_value = v
        return nd

    def link(self, a, out, b, inp):
        self.l.new(a.outputs[out], b.inputs[inp])

    def noise(self, pos, scale, detail=4, rough=0.5, x=0, y=0, stretch=None):
        src = pos
        if stretch:
            mp = self.add("ShaderNodeVectorMath", x - 200, y); mp.operation = 'MULTIPLY'
            mp.inputs[1].default_value = stretch
            self.link(pos, "Position", mp, 0); src = mp
        nz = self.add("ShaderNodeTexNoise", x, y, Scale=scale, Detail=detail, Roughness=rough)
        self.link(src, "Position" if src is pos else "Vector", nz, "Vector")
        return nz

    def ramp(self, fac, stops, x=0, y=0):
        r = self.add("ShaderNodeValToRGB", x, y)
        el = r.color_ramp.elements
        el[0].position, el[0].color = stops[0]
        el[1].position, el[1].color = stops[1]
        for p, c in stops[2:]:
            e = el.new(p); e.color = c
        self.link(fac, "Factor", r, "Fac")
        return r


def reset(mat):
    mat.node_tree.nodes.clear()
    m = Mat(mat)
    out = m.add("ShaderNodeOutputMaterial", 1400, 0)
    bs = m.add("ShaderNodeBsdfPrincipled", 1100, 0)
    m.link(bs, "BSDF", out, "Surface")
    return m, bs


def no_emission(bs):
    bs.inputs["Emission Strength"].default_value = 0.0
    bs.inputs["Emission Color"].default_value = (0, 0, 0, 1)


def gray(v):
    return (v, v, v, 1)


# ---------- walls ----------
def build_wall():
    mat = D.materials["WallPlaster"]
    m, bs = reset(mat)
    pos = m.add("ShaderNodeNewGeometry", -1200, 0)
    sep = m.add("ShaderNodeSeparateXYZ", -1000, -300); m.link(pos, "Position", sep, "Vector")

    mottle = m.noise(pos, 0.9, 6, 0.55, -800, 300)
    patch = m.noise(pos, 5.0, 5, 0.6, -800, 100)
    streak = m.noise(pos, 3.0, 5, 0.6, -800, -100, stretch=(1.0, 1.0, 0.12))

    base = m.add("ShaderNodeMix", -300, 300, data_type='RGBA')
    base.inputs[6].default_value = rgba("#B39A7C")
    base.inputs[7].default_value = rgba("#8E765C")
    mr = m.ramp(mottle, [(0.35, gray(0)), (0.7, gray(1))], -500, 300)
    m.link(mr, "Color", base, "Factor")

    stain = m.add("ShaderNodeMix", -100, 300, data_type='RGBA')
    stain.inputs[7].default_value = rgba("#4A3A29")
    sr = m.ramp(streak, [(0.58, gray(0)), (0.75, gray(0.55))], -500, 100)
    m.link(sr, "Color", stain, "Factor")
    m.link(base, "Result", stain, 6)

    grime = m.add("ShaderNodeMapRange", -700, -300)
    grime.inputs["From Min"].default_value = 2.8
    grime.inputs["From Max"].default_value = 2.2
    m.link(sep, "Z", grime, "Value")
    dirt = m.add("ShaderNodeMix", 100, 300, data_type='RGBA')
    dirt.inputs[7].default_value = rgba("#2B2118")
    dirt.inputs["Factor"].default_value = 0.0
    m.link(grime, "Result", dirt, "Factor")
    m.link(stain, "Result", dirt, 6)
    low = m.add("ShaderNodeMapRange", -700, -450)
    low.inputs["From Min"].default_value = 0.35; low.inputs["From Max"].default_value = 0.0
    m.link(sep, "Z", low, "Value")
    dirt2 = m.add("ShaderNodeMix", 300, 300, data_type='RGBA')
    dirt2.inputs[7].default_value = rgba("#2B2118")
    m.link(low, "Result", dirt2, "Factor")
    m.link(dirt, "Result", dirt2, 6)
    m.link(dirt2, "Result", bs, "Base Color")

    peel = m.noise(pos, 14.0, 6, 0.65, -800, -600)
    grit = m.noise(pos, 260.0, 3, 0.7, -800, -800)
    h = m.add("ShaderNodeMath", -400, -650); h.operation = 'ADD'
    h.inputs[0].default_value = 0.0
    mix_h = m.add("ShaderNodeMix", -500, -650, data_type='FLOAT')
    mix_h.inputs["Factor"].default_value = 0.35
    m.link(peel, "Factor", mix_h, "A"); m.link(grit, "Factor", mix_h, "B")
    bump = m.add("ShaderNodeBump", 800, -300, Strength=0.9, Distance=0.02)
    m.link(mix_h, "Result", bump, "Height")
    m.link(bump, "Normal", bs, "Normal")

    rr = m.ramp(patch, [(0.3, gray(0.78)), (0.7, gray(0.95))], 700, -100)
    m.link(rr, "Color", bs, "Roughness")
    no_emission(bs)


# ---------- ceiling ----------
def build_ceiling():
    mat = D.materials["CeilingDarkBrown"]
    m, bs = reset(mat)
    pos = m.add("ShaderNodeNewGeometry", -1200, 0)

    mottle = m.noise(pos, 0.7, 6, 0.55, -800, 300)
    blot = m.noise(pos, 0.5, 4, 0.7, -800, 100)
    base = m.add("ShaderNodeMix", -300, 300, data_type='RGBA')
    base.inputs[6].default_value = rgba("#6E5B46")
    base.inputs[7].default_value = rgba("#54432F")
    m.link(m.ramp(mottle, [(0.3, gray(0)), (0.7, gray(1))], -500, 300), "Color", base, "Factor")

    wst = m.add("ShaderNodeMix", -50, 300, data_type='RGBA')
    wst.inputs[7].default_value = rgba("#2E2014")
    m.link(m.ramp(blot, [(0.55, gray(0)), (0.6, gray(0.9)), (0.7, gray(0.45))], -500, 100), "Color", wst, "Factor")
    m.link(base, "Result", wst, 6)
    m.link(wst, "Result", bs, "Base Color")

    pop = m.add("ShaderNodeTexVoronoi", -800, -300); pop.feature = 'F1'
    pop.inputs["Scale"].default_value = 70.0
    m.link(pos, "Position", pop, "Vector")
    fine = m.noise(pos, 300.0, 3, 0.7, -800, -550)
    wave = m.noise(pos, 6.0, 4, 0.6, -800, -750)
    h = m.add("ShaderNodeMix", -500, -400, data_type='FLOAT'); h.inputs["Factor"].default_value = 0.5
    m.link(pop, "Distance", h, "A"); m.link(fine, "Factor", h, "B")
    h2 = m.add("ShaderNodeMix", -300, -450, data_type='FLOAT'); h2.inputs["Factor"].default_value = 0.3
    m.link(h, "Result", h2, "A"); m.link(wave, "Factor", h2, "B")
    bump = m.add("ShaderNodeBump", 800, -300, Strength=0.6, Distance=0.012)
    m.link(h2, "Result", bump, "Height")
    m.link(bump, "Normal", bs, "Normal")
    bs.inputs["Roughness"].default_value = 0.93
    no_emission(bs)


# ---------- floor ----------
def build_floor():
    mat = D.materials["FloorWarmOak"]
    m = Mat(mat)
    bs = next(n for n in m.n if n.type == 'BSDF_PRINCIPLED')
    grp = next(n for n in m.n if n.type == 'GROUP')
    old_bump = next(n for n in m.n if n.type == 'BUMP')
    grp.inputs["Light"].default_value = rgba("#6A4624", 1.0)
    grp.inputs["Dark"].default_value = rgba("#3F2813", 1.0)
    no_emission(bs)

    pos = m.add("ShaderNodeNewGeometry", -900, -900)
    scr = m.noise(pos, 180.0, 4, 0.6, -700, -900, stretch=(0.06, 1.0, 1.0))
    scr2 = m.noise(pos, 60.0, 3, 0.6, -700, -1100, stretch=(0.04, 1.0, 1.0))
    sh = m.add("ShaderNodeMix", -450, -950, data_type='FLOAT'); sh.inputs["Factor"].default_value = 0.35
    m.link(scr, "Factor", sh, "A"); m.link(scr2, "Factor", sh, "B")
    b2 = m.add("ShaderNodeBump", -250, -950, Strength=0.5, Distance=0.004)
    m.link(sh, "Result", b2, "Height")
    m.link(b2, "Normal", old_bump, "Normal")
    old_bump.inputs["Strength"].default_value = 0.25

    wear = m.noise(pos, 0.9, 5, 0.6, -700, -1350)
    wr = m.ramp(wear, [(0.35, gray(0.38)), (0.65, gray(0.78))], -450, -1350)
    gl = m.noise(pos, 8.0, 3, 0.5, -700, -1550)
    for l in list(m.l):
        if l.to_node == bs and l.to_socket.name == "Roughness":
            m.l.remove(l)
    rough = m.add("ShaderNodeMath", -200, -1350); rough.operation = 'MULTIPLY'
    m.link(wr, "Color", rough, 0)
    rough.inputs[1].default_value = 1.0
    m.link(rough, "Value", bs, "Roughness")

    dust = m.add("ShaderNodeMix", 600, 0, data_type='RGBA')
    dust.inputs[7].default_value = rgba("#6F5C48")
    m.link(m.ramp(wear, [(0.62, gray(0)), (0.85, gray(0.28))], 300, -1700), "Color", dust, "Factor")
    for l in list(m.l):
        if l.to_node == bs and l.to_socket.name == "Base Color":
            src = l.from_node, l.from_socket.name
            m.l.remove(l)
    m.link(src[0], src[1], dust, 6)
    m.link(dust, "Result", bs, "Base Color")


# ---------- sky and haze ----------
def build_sky():
    mat = D.materials["Sky"]
    m = Mat(mat)
    r = next(n for n in m.n if n.type == 'VALTORGB')
    el = r.color_ramp.elements
    while len(el) > 4:
        el.remove(el[-1])
    for e, (p, c) in zip(el, [(0.0, (0.06, 0.034, 0.05, 1)), (0.10, (0.03, 0.022, 0.04, 1)),
                              (0.32, (0.006, 0.009, 0.022, 1)), (1.0, (0.002, 0.003, 0.008, 1))]):
        e.position, e.color = p, c
    em = next(n for n in m.n if n.type == 'EMISSION')
    em.inputs["Strength"].default_value = 1.0

    tc = next(n for n in m.n if n.type == 'TEX_COORD')
    nz = m.add("ShaderNodeTexNoise", -900, -400, Scale=0.0016, Detail=6, Roughness=0.65)
    vmul = m.add("ShaderNodeVectorMath", -1100, -400); vmul.operation = 'MULTIPLY'
    vmul.inputs[1].default_value = (1.0, 1.0, 2.6)
    m.link(tc, "Generated", vmul, 0); m.link(vmul, "Vector", nz, "Vector")
    cl = m.add("ShaderNodeMix", -300, -300, data_type='RGBA')
    cl.inputs[7].default_value = (0.5, 0.32, 0.3, 1)
    cr = m.ramp(nz, [(0.45, gray(0.55)), (0.7, gray(1.25))], -600, -400)
    mul = m.add("ShaderNodeMix", -150, -200, data_type='RGBA'); mul.blend_type = 'MULTIPLY'
    mul.inputs["Factor"].default_value = 1.0
    for l in list(m.l):
        if l.from_node == r and l.to_node == em:
            m.l.remove(l)
    m.link(r, "Color", mul, 6); m.link(cr, "Color", mul, 7)
    m.link(mul, "Result", em, "Color")


def build_haze():
    w = sc.world
    nt = w.node_tree
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_WORLD')
    vol = nt.nodes.new("ShaderNodeVolumeScatter")
    vol.inputs["Color"].default_value = (0.62, 0.55, 0.62, 1)
    vol.inputs["Density"].default_value = 0.00009
    vol.inputs["Anisotropy"].default_value = 0.35
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    sc.cycles.volume_bounces = 1


def build_buildings():
    for n in ("CityBldMid", "CityBldFar"):
        mat = D.materials[n]
        far = n == "CityBldFar"
        m, bs = reset(mat)
        pos = m.add("ShaderNodeNewGeometry", -900, 0)
        sep = m.add("ShaderNodeSeparateXYZ", -700, 0); m.link(pos, "Position", sep, "Vector")
        nz = m.noise(pos, 0.08 if not far else 0.05, 6, 0.6, -700, 250)
        base = m.add("ShaderNodeMix", -300, 250, data_type='RGBA')
        base.inputs[6].default_value = (0.012, 0.014, 0.024, 1) if not far else (0.02, 0.022, 0.034, 1)
        base.inputs[7].default_value = (0.030, 0.030, 0.042, 1) if not far else (0.045, 0.040, 0.055, 1)
        m.link(m.ramp(nz, [(0.35, gray(0)), (0.65, gray(1))], -500, 250), "Color", base, "Factor")
        m.link(base, "Result", bs, "Base Color")
        bs.inputs["Roughness"].default_value = 0.5
        bs.inputs["Specular IOR Level"].default_value = 0.6
        glow = m.add("ShaderNodeMapRange", -500, -200)
        glow.inputs["From Min"].default_value = 120.0 if not far else 40.0
        glow.inputs["From Max"].default_value = 0.0 if not far else -40.0
        m.link(sep, "Z", glow, "Value")
        bs.inputs["Emission Color"].default_value = (0.9, 0.38, 0.16, 1)
        gm = m.add("ShaderNodeMath", -250, -200); gm.operation = 'MULTIPLY'
        gm.inputs[1].default_value = 0.018 if not far else 0.012
        m.link(glow, "Result", gm, 0)
        m.link(gm, "Value", bs, "Emission Strength")


def vary_windows():
    rnd = random.Random(19)
    palette = [
        ("Warm", (1.0, 0.52, 0.17), 9, 0.34),
        ("WarmDim", (1.0, 0.45, 0.12), 3.5, 0.24),
        ("Tungsten", (1.0, 0.74, 0.38), 12, 0.12),
        ("Cool", (0.62, 0.78, 1.0), 8, 0.14),
        ("TV", (0.25, 0.42, 1.0), 4, 0.07),
        ("Green", (0.7, 1.0, 0.75), 7, 0.09),
    ]
    mats = []
    for name, col, st, _ in palette:
        mt = D.materials.get("Win_" + name) or D.materials.new("Win_" + name)
        mt.use_nodes = True
        nt = mt.node_tree; nt.nodes.clear()
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*col, 1)
        em.inputs["Strength"].default_value = st
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(em.outputs[0], out.inputs[0])
        mats.append(mt)
    weights = [p[3] for p in palette]
    keep = {"City_Midrise_Win": 0.5, "City_Midrise_WinCool": 0.4,
            "Houston_Windows": 0.55, "Houston_WindowsCool": 0.45}
    for name, frac in keep.items():
        o = D.objects[name]
        bm = bmesh.new(); bm.from_mesh(o.data)
        dead = [f for f in bm.faces if rnd.random() > frac]
        bmesh.ops.delete(bm, geom=dead, context='FACES')
        bm.to_mesh(o.data); bm.free()
        o.data.materials.clear()
        for mt in mats:
            o.data.materials.append(mt)
        cool_only = name.endswith("Cool")
        for p in o.data.polygons:
            p.material_index = (3 if rnd.random() < 0.7 else 4) if cool_only else rnd.choices(range(len(mats)), weights)[0]
        o.data.update()
    print("windows varied")


def glass():
    m = Mat(D.materials["WindowGlass"])
    bs = next(n for n in m.n if n.type == 'BSDF_PRINCIPLED')
    for l in list(m.l):
        if l.to_node == bs and l.to_socket.name == "Base Color":
            m.l.remove(l)
    bs.inputs["Base Color"].default_value = (0.02, 0.022, 0.026, 1)
    print("glass alpha", bs.inputs["Alpha"].default_value, [l.to_socket.name for l in m.l if l.to_node == bs])


# ---------- lights and look ----------
def lights():
    L = D.objects
    L["L1_DeskLamp_Key"].data.energy = 100
    L["L1_DeskLamp_Key"].data.color = (1.0, 0.56, 0.2)
    L["L2_DeskLamp_Spill"].data.energy = 5
    L["L2_DeskLamp_Spill"].data.color = (1.0, 0.56, 0.2)
    L["L3_FloorLamp"].data.energy = 28
    L["L3_FloorLamp"].data.color = (1.0, 0.5, 0.17)
    L["L4_Window_Night"].data.energy = 600
    L["L4_Window_Night"].data.color = (0.05, 0.07, 0.16)
    L["L5_IBM_Screen"].data.energy = 1.0
    L["L5_IBM_Screen"].data.color = (0.35, 1.0, 0.45)
    L["L6_TV_Screen"].data.energy = 14


def look():
    vs = sc.view_settings
    vs.view_transform = 'Filmic'
    vs.look = 'Low Contrast'
    vs.exposure = 0.55
    vs.gamma = 1.0
    sc.cycles.samples = 1000


def main():
    build_wall(); build_ceiling(); build_floor()
    build_sky(); build_haze(); build_buildings(); vary_windows()
    glass(); lights(); look()
    bpy.ops.wm.save_as_mainfile(filepath=B + "/source/sakina-v19.blend", compress=True)
    print("SAVED sakina-v19")


main()
