"""Pipeline self-test: a bevelled ceramic mug-like cylinder with a worn metal band. Not a real component."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _lib.pbr import Mat

def build():
    root = bpy.data.objects.new("CMP__selftest", None); bpy.context.scene.collection.objects.link(root)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.04, depth=0.095, location=(0, 0, 0.0475))
    body = bpy.context.object; body.name = "Selftest_Body"; body.parent = root
    m = Mat("Selftest_Glaze"); m.colour_variation("#8a3b2a", "#a5503a", scale=8); m.roughness_variation(0.2, 0.45); m.micro_bump()
    body.data.materials.append(m.material)
    bv = body.modifiers.new("b", 'BEVEL'); bv.width = 0.003; bv.segments = 3
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_torus_add(major_radius=0.0405, minor_radius=0.003, location=(0, 0, 0.07))
    band = bpy.context.object; band.name = "Selftest_Band"; band.parent = root
    b = Mat("Selftest_Brass").base("#b08d57").set(Metallic=1.0); b.roughness_variation(0.25, 0.5)
    band.data.materials.append(b.material)
    return root

CLOSEUPS = [("band", (0, -0.04, 0.07), 0.03, -20, 15)]
