"""Edit #7 (round 3, user 2026-10-31): warm practical lighting + soft wall shadows (benchmark: Felix refs A, B, E).

Not a global brighten: exposure, the view transform and the night window stay as they were. Changes:
- Desk lamp = the key light. Its bulb is warm white (~2700 K, was deep orange) and a second "leak" light at the
  bulb sends light left/back past the shade (as a thin plastic/fabric shade does), so the pothos and the
  furniture throw soft, recognisable shadows onto the walls. Shadow-linking keeps the lamp's own shade from
  blocking that leak light; everything else (plant, CRT, computer, tapes) casts shadows normally.
- Bulb radius 2.5 cm (was 12 cm): soft but shaped shadows instead of no shadows.
- Floor lamp in the right nook: warm white bulb inside the now-translucent linen shade -> glowing shade,
  light pools up the wall and down onto the side table.
- Walls: warmer, lighter plaster (was dark brown) so lamp light and shadows actually read on them; ceiling
  slightly lighter. Same plaster texture.
- Screens: TV light from saturated blue to a soft cool white; IBM screen light less green.
"""
import bpy, math
from mathutils import Vector

KEY = dict(color=(1.0, 0.68, 0.40), energy=55.0, radius=0.025)
LEAK = dict(color=(1.0, 0.62, 0.36), energy=150.0, radius=0.03, aim=(-1.0, 0.22, 0.12), cone=115.0)
FLOOR = dict(color=(1.0, 0.70, 0.42), energy=100.0, radius=0.04)
WALL_A, WALL_B, WALL_DARK = (0.36, 0.25, 0.150), (0.30, 0.205, 0.120), (0.22, 0.150, 0.090)
CEIL_A, CEIL_B = (0.20, 0.140, 0.085), (0.12, 0.080, 0.045)


def _walls():
    nt = bpy.data.materials["WallPlaster"].node_tree
    mix = nt.nodes["Mix"]; mix.inputs[6].default_value = (*WALL_A, 1); mix.inputs[7].default_value = (*WALL_B, 1)
    nt.nodes["Mix.001"].inputs[7].default_value = (*WALL_DARK, 1)
    for n in ("Mix.002", "Mix.003"):                       # floor/ceiling-edge darkening: keep, a bit lighter
        nt.nodes[n].inputs[7].default_value = (0.05, 0.032, 0.02, 1)
    ct = bpy.data.materials["CeilingDarkBrown"].node_tree.nodes["Mix"]
    ct.inputs[6].default_value = (*CEIL_A, 1); ct.inputs[7].default_value = (*CEIL_B, 1)


def _light(name, kind, loc, color, energy, radius, rot=None, cone=None):
    D = bpy.data
    o = D.objects.get(name)
    if not o:
        ld = D.lights.new(name, kind); o = D.objects.new(name, ld); bpy.context.scene.collection.objects.link(o)
    l = o.data; o.location = loc
    l.color = color; l.energy = energy; l.shadow_soft_size = radius
    if hasattr(l, "use_custom_distance"):
        l.use_custom_distance = False
    if rot is not None:
        o.rotation_euler = rot
    if cone is not None:
        l.spot_size = math.radians(cone); l.spot_blend = 1.0
    return o


def _desk_lamp():
    D = bpy.data
    key = D.objects["L1_DeskLamp_Key"]
    key.data.color = KEY["color"]; key.data.energy = KEY["energy"]; key.data.shadow_soft_size = KEY["radius"]
    key.data.use_custom_distance = False
    for n in ("L2_DeskLamp_Spill", "L7_DeskPool"):
        D.objects[n].data.color = (1.0, 0.68, 0.42)
    bulb = Vector(key.location)
    aim = Vector(LEAK["aim"]).normalized()
    rot = aim.to_track_quat('-Z', 'Y').to_euler()
    leak = _light("L8_DeskLamp_Leak", 'SPOT', bulb, LEAK["color"], LEAK["energy"], LEAK["radius"], rot=rot, cone=LEAK["cone"])
    # the lamp's own shade/inner/cap/bulb must not block the leak light (shadow linking, Cycles)
    blockers = D.collections.get("L8_Unblocked") or D.collections.new("L8_Unblocked")
    lamp_parts = [o for o in D.collections["Lamp"].all_objects if o.name.startswith(("Lamp_Shade", "Lamp_Inner", "Lamp_Rim", "Lamp_Cap", "Lamp_Bulb", "Lamp_Joint"))]
    for o in lamp_parts:
        if o.name not in blockers.objects:
            blockers.objects.link(o)
    leak.light_linking.blocker_collection = blockers
    for co in blockers.collection_objects:
        co.light_linking.link_state = 'EXCLUDE'
    # warmer bulb + inner glow (was deep orange)
    bm = D.materials["Bulb"].node_tree.nodes["Emission"]; bm.inputs["Color"].default_value = (1.0, 0.72, 0.45, 1)
    im = D.materials["LampInner"].node_tree.nodes["Emission"]; im.inputs["Color"].default_value = (1.0, 0.55, 0.28, 1)


def _floor_lamp():
    D = bpy.data
    L3 = D.objects["L3_FloorLamp"]
    L3.data.color = FLOOR["color"]; L3.data.energy = FLOOR["energy"]; L3.data.shadow_soft_size = FLOOR["radius"]
    L3.data.use_custom_distance = False


def _screens():
    D = bpy.data
    tv = D.objects["L6_TV_Screen"].data; tv.color = (0.55, 0.64, 0.82); tv.energy = 5.0
    ibm = D.objects["L5_IBM_Screen"].data; ibm.color = (0.55, 0.95, 0.62); ibm.energy = 2.0
    led = D.materials.get("IBMLed")
    if led:
        led.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.8


def apply():
    _walls()
    _desk_lamp()
    _floor_lamp()
    _screens()
    print("e07 lighting done")
