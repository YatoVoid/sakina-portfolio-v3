"""Edit #19 (Sakina, 2026-11-01 15:05): small stones in the plant pot, with mud.

The alocasia pot (`Pot`, soil disc `Pot_Soil`, collection Plant) had a flat brown disc. Now:
  - the soil disc gets a damp-mud material (`PotMud`): dark brown with lighter dry patches, wet glossy patches, grainy bump
  - ~26 river pebbles (4-11 mm radius, flattened, lumpy, random tilt, half sunk into the mud) in three tones (grey / tan / dark)
  - ~16 tiny grit stones (3-5 mm)
  - ~16 small mud clods (6-14 mm, dark, squashed)
Everything is placed by a seeded dart-throwing scatter (no overlaps), away from the plant stems in the middle and inside the rim.
Bake group: Plant (same collection as the soil).
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise

SEED = 19


def _lin(h):
    c = int(h, 16)
    out = []
    for sh in (16, 8, 0):
        v = ((c >> sh) & 255) / 255.0
        out.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def _n(nt, typ, **kw):
    n = nt.nodes.new(typ)
    for k, v in kw.items():
        if k.startswith("in_"):
            n.inputs[k[3:].replace("_", " ")].default_value = v
        else:
            setattr(n, k, v)
    return n


def _stone_mat(name, hex_a, hex_b, rough):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    tc = _n(nt, "ShaderNodeTexCoord")
    nz = _n(nt, "ShaderNodeTexNoise", in_Scale=260.0, in_Detail=6.0, in_Roughness=0.6)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mix = _n(nt, "ShaderNodeMix", data_type='RGBA')
    mix.inputs[6].default_value = _lin(hex_a)
    mix.inputs[7].default_value = _lin(hex_b)
    nt.links.new(nz.outputs["Fac"], mix.inputs[0])
    nt.links.new(mix.outputs[2], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = rough
    bp = _n(nt, "ShaderNodeBump", in_Strength=0.5, in_Distance=0.0005)
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
    return m


def _mud_mat():
    m = bpy.data.materials.get("PotMud")
    if m:
        return m
    m = bpy.data.materials.new("PotMud")
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    tc = _n(nt, "ShaderNodeTexCoord")
    big = _n(nt, "ShaderNodeTexNoise", in_Scale=38.0, in_Detail=8.0, in_Roughness=0.62)
    fine = _n(nt, "ShaderNodeTexNoise", in_Scale=420.0, in_Detail=5.0, in_Roughness=0.7)
    nt.links.new(tc.outputs["Object"], big.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], fine.inputs["Vector"])
    mix = _n(nt, "ShaderNodeMix", data_type='RGBA')
    mix.inputs[6].default_value = _lin("1d130c")          # wet dark mud
    mix.inputs[7].default_value = _lin("4a3626")          # dried patches
    nt.links.new(big.outputs["Fac"], mix.inputs[0])
    nt.links.new(mix.outputs[2], bs.inputs["Base Color"])
    rr = _n(nt, "ShaderNodeMapRange", in_From_Min=0.35, in_From_Max=0.65, in_To_Min=0.50, in_To_Max=0.95)   # wet = glossy, dry = matte
    nt.links.new(big.outputs["Fac"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], bs.inputs["Roughness"])
    bp = _n(nt, "ShaderNodeBump", in_Strength=0.9, in_Distance=0.002)
    nt.links.new(fine.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
    return m


def _blob(bm, c, r, squash, rot, lump, seed):
    """One lumpy pebble: icosphere, squashed, noise-displaced, rotated, moved to c."""
    geo = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)["verts"]
    rm = Matrix.Rotation(rot[0], 3, 'X') @ Matrix.Rotation(rot[1], 3, 'Y') @ Matrix.Rotation(rot[2], 3, 'Z')
    for v in geo:
        p = v.co.copy()
        d = 1.0 + lump * noise.noise(p * 1.7 + Vector((seed, seed * 0.7, seed * 1.3)))
        p = Vector((p.x * r[0] * d, p.y * r[1] * d, p.z * r[2] * squash * d))
        v.co = rm @ p + c
    return geo


def _object(name, bm, mat, coll):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    for pl in me.polygons:
        pl.use_smooth = True
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    return o


def apply():
    D = bpy.data
    soil = D.objects["Pot_Soil"]
    ws = [soil.matrix_world @ Vector(c) for c in soil.bound_box]
    lo = Vector((min(w[i] for w in ws) for i in range(3)))
    hi = Vector((max(w[i] for w in ws) for i in range(3)))
    cx, cy, top = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z
    R = min(hi.x - lo.x, hi.y - lo.y) / 2 * 0.90
    coll = soil.users_collection[0]
    mud = _mud_mat()
    soil.data.materials.clear()
    soil.data.materials.append(mud)

    rnd = random.Random(SEED)
    placed = []                                            # (x, y, radius)

    def spot(rad, tries=400):
        for _ in range(tries):
            a, d = rnd.uniform(0, 2 * math.pi), math.sqrt(rnd.uniform(0.0, 1.0)) * (R - rad)
            x, y = cx + d * math.cos(a), cy + d * math.sin(a)
            if math.hypot(x - cx, y - cy) < 0.035 + rad:                    # keep the plant stems clear
                continue
            if all(math.hypot(x - px, y - py) > (rad + pr) * 1.08 for px, py, pr in placed):
                placed.append((x, y, rad))
                return x, y
        return None

    groups = {"PotStones_Grey": (_stone_mat("PotStoneGrey", "7d7a74", "a19d94", 0.78), bmesh.new()),
              "PotStones_Tan": (_stone_mat("PotStoneTan", "9c8d73", "bcae92", 0.82), bmesh.new()),
              "PotStones_Dark": (_stone_mat("PotStoneDark", "3d3b38", "5b5853", 0.7), bmesh.new()),
              "PotClods": (mud, bmesh.new())}
    names = ["PotStones_Grey", "PotStones_Tan", "PotStones_Dark"]
    counts = {n: 0 for n in groups}

    def add(group, rad, squash, lump, embed):
        pos = spot(rad)
        if pos is None:
            return
        sx, sy = rad * rnd.uniform(0.85, 1.25), rad * rnd.uniform(0.85, 1.25)
        z = top + rad * squash * embed
        rot = (rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25), rnd.uniform(0, 6.283))
        _blob(groups[group][1], Vector((pos[0], pos[1], z)), (sx, sy, rad), squash, rot, lump, rnd.uniform(0, 100))
        counts[group] += 1

    for _ in range(26):                                    # pebbles
        add(rnd.choice(names), rnd.uniform(0.0045, 0.011), rnd.uniform(0.5, 0.72), 0.16, 0.30)
    for _ in range(16):                                    # grit
        add(rnd.choice(names), rnd.uniform(0.003, 0.005), rnd.uniform(0.55, 0.8), 0.2, 0.20)
    for _ in range(16):                                    # mud clods
        add("PotClods", rnd.uniform(0.006, 0.014), rnd.uniform(0.35, 0.5), 0.28, 0.15)

    for n, (m, bm) in groups.items():
        if counts[n]:
            _object(n, bm, m, coll)
        else:
            bm.free()
    bpy.context.view_layer.update()
    print(f"e19: pot at ({cx:.2f}, {cy:.2f}) soil radius {R * 100:.0f} cm: pebbles/grit/clods per group {counts}", flush=True)
