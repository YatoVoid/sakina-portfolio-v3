# Copied from the V2 pipeline (C:\Users\sakin\Downloads\v2\v2\pipeline, read-only source; V2 untouched).
# V3 changes: work dir from $V3_WORK instead of /home/wali/...; Cycles on CPU (cloud has no GPU).
import os
import bpy
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


def no_emission(bs):
    bs.inputs["Emission Strength"].default_value = 0.0
    bs.inputs["Emission Color"].default_value = (0, 0, 0, 1)


def cut(light, dist):
    light.data.use_custom_distance = True
    light.data.cutoff_distance = dist


L = D.objects

# 1 IBM PC
ibm = L["L5_IBM_Screen"]
ibm.data.energy = 3
cut(ibm, 0.4)

# 2 walls
wall = D.materials["WallPlaster"]
mixes = [n for n in wall.node_tree.nodes if n.type == 'MIX' and n.data_type == 'RGBA' and n.inputs[6].default_value[0] > 0.2]
for n in wall.node_tree.nodes:
    if n.type == 'MIX' and n.data_type == 'RGBA' and tuple(round(c, 3) for c in n.inputs[6].default_value[:3]) == tuple(round(c, 3) for c in rgba("#B39A7C")[:3]):
        n.inputs[6].default_value = rgba("#8C7355")
        n.inputs[7].default_value = rgba("#8C7355", 0.8)
for n in wall.node_tree.nodes:
    if n.type == 'BSDF_PRINCIPLED':
        no_emission(n)
for o in D.objects:
    if o.type == 'MESH' and o.name.startswith("Wall_"):
        assert o.material_slots[0].material == wall, o.name

# 3 floor
floor = D.materials["FloorWarmOak"]
ft = floor.node_tree
bs = next(n for n in ft.nodes if n.type == 'BSDF_PRINCIPLED')
for n in ft.nodes:
    if n.type == 'GROUP' and n.node_tree.name == "WoodPBR":
        n.inputs["Light"].default_value = rgba("#2E1A0E")
        n.inputs["Dark"].default_value = rgba("#2E1A0E", 0.6)
    if n.type == 'MIX' and n.data_type == 'RGBA' and n.inputs["Factor"].default_value != 0.0 and not n.inputs[7].is_linked is False:
        pass
for n in ft.nodes:
    if n.type == 'MIX' and n.data_type == 'RGBA':
        if n.inputs[6].is_linked and n.inputs[7].is_linked and not n.inputs["Factor"].is_linked:
            n.inputs["Factor"].default_value = 0.0
        elif n.inputs[7].is_linked is False and n.inputs["Factor"].is_linked:
            n.inputs[7].default_value = rgba("#2E1A0E", 1.3)
for l in list(ft.links):
    if l.to_node == bs and l.to_socket.name == "Roughness":
        ft.links.remove(l)
bs.inputs["Roughness"].default_value = 0.6
no_emission(bs)

# 4 floor lamp
fl = L["L3_FloorLamp"]
fl.data.color = rgba("#C68B3A")[:3]
fl.data.energy = 30
cut(fl, 1.2)

# 5 curtains
cm = D.materials["Curtain"]
ct = cm.node_tree
cb = next(n for n in ct.nodes if n.type == 'BSDF_PRINCIPLED')
for l in list(ct.links):
    if l.to_node == cb and l.to_socket.name == "Base Color":
        ct.links.remove(l)
cb.inputs["Base Color"].default_value = rgba("#D4B896")
cb.inputs["Roughness"].default_value = 0.95
no_emission(cb)

# 6 desk area light
ad = D.lights.new("L7_DeskPool", 'AREA')
ad.shape = 'RECTANGLE'; ad.size = 0.6; ad.size_y = 0.3
ad.color = rgba("#FFCC77")[:3]; ad.energy = 15
ao = D.objects.new("L7_DeskPool", ad)
sc.collection.objects.link(ao)
ao.location = (0.2, 1.65, 0.72 + 0.5)
ao.rotation_euler = (0, 0, 0)

# overall dark room
L["L1_DeskLamp_Key"].data.energy = 45
cut(L["L1_DeskLamp_Key"], 2.5)
L["L2_DeskLamp_Spill"].data.energy = 3
L["L4_Window_Night"].data.energy = 200
sc.view_settings.exposure = 0.3

bpy.ops.wm.save_as_mainfile(filepath=B + "/source/sakina-v20.blend", compress=True)
print("SAVED sakina-v20")
