"""Night-study lighting for the final bake. Run inside Blender on v3-integrated.blend before bake_lightmaps.py.
Cool moon and city glow through the window, a small warm sodium glow, a dim cool world fill, warmer and less
saturated lamps, deeper bounces."""
import bpy

D = bpy.data
sc = bpy.context.scene
w = sc.world.node_tree
L = D.objects


def set_light(name, color, energy):
    L[name].data.color = color
    L[name].data.energy = energy


set_light("L1_DeskLamp_Key", (1.0, 0.68, 0.34), 60)
set_light("L2_DeskLamp_Spill", (1.0, 0.68, 0.34), 4)
set_light("L3_FloorLamp", (1.0, 0.64, 0.30), 45)
set_light("L7_DeskPool", (1.0, 0.70, 0.32), 18)
set_light("L6_TV_Screen", (0.62, 0.76, 1.0), 14)
set_light("L4_Window_Night", (0.38, 0.52, 1.0), 200)

if "L8_CityGlow" not in L:
    glow = L["L4_Window_Night"].copy()
    glow.data = L["L4_Window_Night"].data.copy()
    glow.name = "L8_CityGlow"
    glow.location = (0.05, 3.0, 1.2)
    glow.data.size = 1.4
    glow.data.color = (1.0, 0.55, 0.25)
    glow.data.energy = 70
    sc.collection.objects.link(glow)

bg = next(n for n in w.nodes if n.type == 'BACKGROUND')
bg.inputs["Color"].default_value = (0.06, 0.09, 0.17, 1)
bg.inputs["Strength"].default_value = 0.9
out = next(n for n in w.nodes if n.type == 'OUTPUT_WORLD')
if not any(l.to_socket.name == "Surface" for l in w.links):
    w.links.new(bg.outputs["Background"], out.inputs["Surface"])

sc.cycles.max_bounces = 14
sc.cycles.diffuse_bounces = 8
sc.cycles.glossy_bounces = 4
sc.cycles.sample_clamp_indirect = 8
