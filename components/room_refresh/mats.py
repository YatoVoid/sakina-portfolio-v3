"""Procedural PBR materials for the room refresh (single Principled BSDF each: bake-safe).
Colours are sRGB hex. Existing room materials are reused where the approved look must not change
(WindowPaint, WindowGlass, Bulb)."""
import bpy, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from _lib.pbr import Mat, hex_rgba  # noqa: E402

D = bpy.data
_cache = {}


def _once(fn):
    def wrap(*a):
        k = fn.__name__ + repr(a)
        if k not in _cache or _cache[k].name not in D.materials:
            _cache[k] = fn(*a)
        return _cache[k]
    wrap.__name__ = fn.__name__
    return wrap


def _sock(sockets, name, kind='RGBA'):
    return next(x for x in sockets if x.name == name and x.type == kind)


def mix_rgb(m, fac, a, b, loc):
    """Colour mix with sockets chosen by type (the Mix node has A/B sockets for every data type)."""
    n = m.node("ShaderNodeMix", loc); n.data_type = 'RGBA'
    m.link(fac, n.inputs["Factor"]) if not isinstance(fac, float) else None
    for name, v in (("A", a), ("B", b)):
        s = _sock(n.inputs, name)
        if isinstance(v, tuple):
            s.default_value = v
        else:
            m.link(v, s)
    return _sock(n.outputs, "Result")


def existing(name, fallback):
    return D.materials.get(name) or fallback()


# ── fabric / paper / leather ──────────────────────────────────────────────
@_once
def curtain_white():
    m = Mat("R_CurtainWhite")
    m.colour_variation("#e4ded2", "#efeae1", scale=3.0, detail=4, contrast=(0.3, 0.7))
    m.set(Roughness=0.88, **{"Sheen Weight": 0.45, "Sheen Roughness": 0.55, "Sheen Tint": hex_rgba("#fffaf2"),
                             "Subsurface Weight": 0.12, "Subsurface Radius": (0.02, 0.02, 0.02), "Subsurface Scale": 0.01})
    # woven texture: two stretched noises (warp + weft)
    a = m.node("ShaderNodeMapping", (-1250, -500)); a.inputs["Scale"].default_value = (1.0, 1.0, 60.0)
    m.link(m.coord(), a.inputs["Vector"])
    n1 = m.node("ShaderNodeTexNoise", (-1050, -500)); n1.inputs["Scale"].default_value = 900; n1.inputs["Detail"].default_value = 1
    m.link(a.outputs["Vector"], n1.inputs["Vector"])
    m.bump(n1.outputs["Fac"], 0.08, 0.0004)
    return m.material


@_once
def paper(hex_a="#efe9dc", hex_b="#e6dfcf"):
    m = Mat("R_Paper")
    m.colour_variation(hex_a, hex_b, scale=40, detail=6)
    m.set(Roughness=0.92, **{"Subsurface Weight": 0.05})
    m.micro_bump(900, 0.06)
    return m.material


def ruled_paper(name, handwriting_png, flip=False):
    """Paper + blue ruled lines + red margin + pencil handwriting image (UV mapped 0..1 over the page)."""
    m = Mat(name)
    uv = m.coord("UV")
    # ruled lines: horizontal stripes every 7 mm on a 260 mm page -> 37 lines in UV v
    sep = m.node("ShaderNodeSeparateXYZ", (-1250, 300)); m.link(uv, sep.inputs["Vector"])
    wave = m.node("ShaderNodeMath", (-1050, 300), operation='MULTIPLY'); wave.inputs[1].default_value = 37.0
    m.link(sep.outputs["Y"], wave.inputs[0])
    fr = m.node("ShaderNodeMath", (-900, 300), operation='FRACT'); m.link(wave.outputs[0], fr.inputs[0])
    line = m.node("ShaderNodeMath", (-750, 300), operation='LESS_THAN'); line.inputs[1].default_value = 0.06
    m.link(fr.outputs[0], line.inputs[0])
    top = m.node("ShaderNodeMath", (-750, 150), operation='LESS_THAN'); top.inputs[1].default_value = 0.90
    m.link(sep.outputs["Y"], top.inputs[0])
    lines = m.node("ShaderNodeMath", (-600, 300), operation='MULTIPLY'); m.link(line.outputs[0], lines.inputs[0]); m.link(top.outputs[0], lines.inputs[1])
    # margin: thin vertical red line near the outer edge of the page
    mx = m.node("ShaderNodeMath", (-900, 0), operation='SUBTRACT'); m.link(sep.outputs["X"], mx.inputs[0])
    mx.inputs[1].default_value = 0.86 if flip else 0.14
    ab = m.node("ShaderNodeMath", (-750, 0), operation='ABSOLUTE'); m.link(mx.outputs[0], ab.inputs[0])
    margin = m.node("ShaderNodeMath", (-600, 0), operation='LESS_THAN'); margin.inputs[1].default_value = 0.0035
    m.link(ab.outputs[0], margin.inputs[0])
    img = m.node("ShaderNodeTexImage", (-600, -300)); img.image = D.images.load(handwriting_png, check_existing=True)
    img.image.colorspace_settings.name = 'Non-Color'
    m.link(uv, img.inputs["Vector"])
    c1 = mix_rgb(m, lines.outputs[0], hex_rgba("#efe9dc"), hex_rgba("#93a3bd"), (-400, 400))
    c2 = mix_rgb(m, margin.outputs[0], c1, hex_rgba("#c98a86"), (-250, 300))
    c3 = mix_rgb(m, img.outputs["Color"], c2, hex_rgba("#34343c"), (-100, 200))   # graphite
    m.link(c3, m.bsdf.inputs["Base Color"])
    # graphite is slightly shiny where written
    rr = m.node("ShaderNodeMapRange", (-100, -100)); m.link(img.outputs["Color"], rr.inputs["Value"])
    rr.inputs["To Min"].default_value = 0.9; rr.inputs["To Max"].default_value = 0.55
    m.link(rr.outputs["Result"], m.bsdf.inputs["Roughness"])
    m.micro_bump(900, 0.05)
    return m.material


@_once
def page_edges():
    """Stacked sheet edges: fine light/dark stripes along the page thickness (object Z)."""
    m = Mat("R_PageEdges")
    w = m.node("ShaderNodeTexWave", (-1100, 0)); w.wave_type = 'BANDS'; w.bands_direction = 'Z'
    w.inputs["Scale"].default_value = 260; w.inputs["Distortion"].default_value = 3; w.inputs["Detail"].default_value = 2
    m.link(m.coord(), w.inputs["Vector"])
    r = m.ramp(w.outputs["Fac"], [(0.3, "#d8d0bd"), (0.7, "#f1ebdf")])
    m.link(r.outputs["Color"], m.bsdf.inputs["Base Color"])
    m.set(Roughness=0.95)
    return m.material


@_once
def leather():
    m = Mat("R_Leather")
    m.colour_variation("#2f1b10", "#4a2c1a", scale=9, detail=8)
    v = m.node("ShaderNodeTexVoronoi", (-1100, -450)); v.inputs["Scale"].default_value = 700
    m.link(m.coord(), v.inputs["Vector"])
    m.bump(v.outputs["Distance"], 0.18, 0.0006)
    m.roughness_variation(0.45, 0.72, scale=18)
    m.set(**{"Coat Weight": 0.15, "Coat Roughness": 0.4})
    return m.material


@_once
def satin(hex_c):
    m = Mat("R_Satin_" + hex_c.strip("#")).base(hex_c)
    m.set(Roughness=0.35, **{"Sheen Weight": 0.6, "Sheen Roughness": 0.3})
    return m.material


# ── metals ────────────────────────────────────────────────────────────────
@_once
def brass_aged():
    m = Mat("R_BrassAged")
    m.colour_variation("#9c7840", "#c49a55", scale=14, detail=8)
    m.set(Metallic=1.0)
    m.roughness_variation(0.2, 0.42, scale=40)
    sc = m.node("ShaderNodeMapping", (-1250, -600)); sc.inputs["Scale"].default_value = (1, 1, 30)
    m.link(m.coord(), sc.inputs["Vector"])
    n = m.node("ShaderNodeTexNoise", (-1050, -600)); n.inputs["Scale"].default_value = 300
    m.link(sc.outputs["Vector"], n.inputs["Vector"])
    m.bump(n.outputs["Fac"], 0.06, 0.0002)     # fine brushing / handling scratches
    return m.material


@_once
def chrome():
    m = Mat("R_Chrome").base("#d2d2d4").set(Metallic=1.0)
    m.roughness_variation(0.12, 0.28, scale=60)
    return m.material


@_once
def dark_bronze():
    m = Mat("R_DarkBronze")
    m.colour_variation("#2c231b", "#433426", scale=10)
    m.set(Metallic=0.85); m.roughness_variation(0.3, 0.5, scale=30)
    return m.material


# ── paints and plastics ───────────────────────────────────────────────────
@_once
def enamel(hex_a, hex_b, name):
    m = Mat(name)
    m.colour_variation(hex_a, hex_b, scale=7, detail=6)
    m.roughness_variation(0.22, 0.36, scale=25)
    m.set(**{"Coat Weight": 0.35, "Coat Roughness": 0.12})
    n = m.noise(180, 3, 0.5, loc=(-400, -450))          # orange-peel of sprayed enamel
    m.bump(n.outputs["Fac"], 0.04, 0.0004)
    return m.material


@_once
def plastic(hex_a, hex_b, name, rough=(0.35, 0.55), grain=0.08):
    m = Mat(name)
    m.colour_variation(hex_a, hex_b, scale=10, detail=5)
    m.roughness_variation(*rough, scale=30)
    m.micro_bump(1600, grain)                            # moulded texture
    return m.material


@_once
def flat(hex_c, name, rough=0.5, metal=0.0, emit=0.0):
    m = Mat(name).base(hex_c).set(Roughness=rough, Metallic=metal)
    if emit:
        m.set(**{"Emission Color": hex_rgba(hex_c), "Emission Strength": emit})
    return m.material


@_once
def lcd():
    m = Mat("R_CalcLCD")
    m.colour_variation("#8b9580", "#9aa48e", scale=30)
    m.set(Roughness=0.18, **{"Coat Weight": 0.6, "Coat Roughness": 0.05})
    return m.material


@_once
def solar():
    m = Mat("R_SolarCell")
    w = m.node("ShaderNodeTexWave", (-1100, 0)); w.wave_type = 'BANDS'; w.bands_direction = 'X'
    w.inputs["Scale"].default_value = 90; m.link(m.coord(), w.inputs["Vector"])
    r = m.ramp(w.outputs["Fac"], [(0.05, "#181012"), (0.12, "#3a2a2e")])
    m.link(r.outputs["Color"], m.bsdf.inputs["Base Color"])
    m.set(Roughness=0.12, Metallic=0.3, **{"Coat Weight": 0.8, "Coat Roughness": 0.03})
    return m.material
