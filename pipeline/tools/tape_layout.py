"""Write the 13 project tapes' spine centres (three.js Y-up coords) to JSON.
Usage: python3 tape_layout.py <scene.blend|-> <out.json>   ('-' = use already-open scene via import)"""
import bpy, json, sys, mathutils

# Order must match web/content.js projects[] (stack 0 top->bottom, then stack 1 top->bottom).
ORDER = ["Tape_Dental-X", "Tape_Tmac", "Tape_University", "Tape_Blutech", "Tape_Softsyncdev", "Tape_The",
         "PTape_1", "PTape_2", "PTape_3", "PTape_4", "PTape_5", "PTape_6", "PTape_7"]


def layout():
    out = []
    for i, name in enumerate(ORDER):
        root = bpy.data.objects[name]
        pts = [root.matrix_world @ mathutils.Vector(c) for c in root.bound_box]
        mn = [min(p[k] for p in pts) for k in range(3)]
        mx = [max(p[k] for p in pts) for k in range(3)]
        c = root.matrix_world.translation
        spine = (c.x, mn[1] + 0.002, (mn[2] + mx[2]) / 2)          # front (-Y) face centre, Blender Z-up
        to3 = lambda v: [round(v[0], 4), round(v[2], 4), round(-v[1], 4)]  # glTF/three: (x, z, -y)
        out.append({"idx": i, "object": name, "spine": to3(spine),
                    "min": to3((mn[0], mx[1], mn[2])), "max": to3((mx[0], mn[1], mx[2]))})
    return out


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if argv[0] != "-":
        bpy.ops.wm.open_mainfile(filepath=argv[0])
    json.dump(layout(), open(argv[1], "w"), indent=1)
    print("wrote", argv[1])
