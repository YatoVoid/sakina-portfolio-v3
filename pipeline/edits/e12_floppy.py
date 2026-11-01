"""Edit #12 (round 4, user 2026-11-01): the blue-purple floppy disk lay on the yellow notepad; the user wants the yellow
paper left clear (reference: rieseberg.com). The disk moves onto the white sheet to its right (x 0.62-0.90), clear of the
tape stacks behind (y >= 1.49) and the glasses/phone side. Children (label, shutter, text) are parented and follow."""
import bpy, math


def apply():
    f = bpy.data.objects["Floppy"]
    f.location = (0.745, 1.385, 0.7265)            # 3 mm above the white sheet (top z 0.723), was 0.7295 over the yellow pad
    f.rotation_euler.z = math.radians(-14)
    bpy.context.view_layer.update()
    print("e12 floppy moved to", tuple(round(v, 3) for v in f.location))


if __name__ == "__main__":
    import sys
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    bpy.ops.wm.open_mainfile(filepath=a[0]); apply()
    bpy.ops.wm.save_as_mainfile(filepath=a[1], compress=True)
