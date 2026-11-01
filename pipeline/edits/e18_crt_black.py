"""Edit #18 (Sakina, 2026-11-01 14:42): the CRT must read BLACK, not blue, and look like real moulded TV plastic.

Why it looked blue (measured, not guessed):
  - L6_TV_Screen (the light that carries the screen glow into the room) was deep blue (0.04, 0.11, 0.69) at 14 W: it painted the bezel, the
    desk and the VCR blue.
  - the phosphor ramp was blue-grey, the knob marks (PosterInk) slightly blue.
  The plastic itself was already near-black. Changes: neutral phosphor + neutral, weaker screen light; plastic base colour a true black;
  real-plastic surface: fine stipple (existing) made stronger + orange-peel moulding texture + roughness variation (satin in places,
  slightly shinier where it would be handled). Bake group: Monitor (+ Desk/Station get a different, neutral light cast) -> rebake needed.
"""
import bpy


def _n(nt, typ, **kw):
    n = nt.nodes.new(typ)
    for k, v in kw.items():
        if k.startswith("in_"):
            n.inputs[k[3:].replace("_", " ")].default_value = v
        else:
            setattr(n, k, v)
    return n


def apply():
    D = bpy.data
    L6 = D.objects["L6_TV_Screen"].data
    L6.color = (0.90, 0.92, 0.90)          # neutral phosphor white, a hair cool like a real tube
    L6.energy = 7.0                        # was 14 W blue
    m = D.materials["CRT_Screen"]
    ramp = next(n for n in m.node_tree.nodes if n.type == 'VALTORGB')
    ramp.color_ramp.elements[0].color = (0.011, 0.012, 0.012, 1)
    ramp.color_ramp.elements[1].color = (0.040, 0.042, 0.042, 1)
    ink = D.materials.get("PosterInk")
    if ink and ink.use_nodes:
        for nd in ink.node_tree.nodes:
            if nd.type == 'BSDF_PRINCIPLED' and not nd.inputs["Base Color"].is_linked:
                nd.inputs["Base Color"].default_value = (0.80, 0.80, 0.78, 1)

    pl = D.materials["CRTPlastic"]
    nt = pl.node_tree
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.0045, 0.0045, 0.0045, 1)       # true black plastic (not blue, not grey)
    bs.inputs["Specular IOR Level"].default_value = 0.18      # low sheen: warm lamp/window light must not wash the black to grey
    for k in ("Sheen Weight", "Coat Weight"):
        if k in bs.inputs:
            bs.inputs[k].default_value = 0.0
    tc = next(n for n in nt.nodes if n.type == 'TEX_COORD')
    bump_fine = next(n for n in nt.nodes if n.type == 'BUMP')
    bump_fine.inputs["Strength"].default_value = 0.10                         # stipple was 0.04: invisible
    # orange-peel moulding texture (broad, soft) chained under the fine stipple
    peel = _n(nt, "ShaderNodeTexNoise", in_Scale=140.0, in_Detail=6.0, in_Roughness=0.6)
    nt.links.new(tc.outputs["Object"], peel.inputs["Vector"])
    bump_peel = _n(nt, "ShaderNodeBump", in_Strength=0.05, in_Distance=0.0006)
    nt.links.new(peel.outputs["Fac"], bump_peel.inputs["Height"])
    nt.links.new(bump_peel.outputs["Normal"], bump_fine.inputs["Normal"])
    # roughness varies across the housing: matte-satin 0.58 .. 0.78
    low = _n(nt, "ShaderNodeTexNoise", in_Scale=9.0, in_Detail=3.0, in_Roughness=0.5)
    nt.links.new(tc.outputs["Object"], low.inputs["Vector"])
    rr = _n(nt, "ShaderNodeMapRange", in_From_Min=0.35, in_From_Max=0.65, in_To_Min=0.58, in_To_Max=0.78)
    nt.links.new(low.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], bs.inputs["Roughness"])
    f = D.materials.get("CRTFunnel")
    if f:
        nd = f.node_tree.nodes.get("Principled BSDF")
        nd.inputs["Base Color"].default_value = (0.003, 0.003, 0.003, 1)
        nd.inputs["Specular IOR Level"].default_value = 0.12
        nd.inputs["Roughness"].default_value = 0.8
    print("e18: CRT neutralised (screen light 14 W blue -> 7 W neutral), plastic true black with moulded texture", flush=True)
