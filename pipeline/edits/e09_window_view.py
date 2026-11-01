"""Edit #9 (integration, Sakina approved 2026-10-31): Berlin rail-yard night photo outside the study window.

Adds the approved component `components/window_view` (two emissive meshes in room coordinates, built around the
round-3 opening camera) in a new collection `WindowView`. The photo patch sits r = 79.75 m from the camera and the
extension panorama r = 80 m, in front of the old `Outside` city (which starts beyond y = 100 m), so the photo
replaces the city for every ray through the window. `Outside` is left in the file untouched (the live site still
loads `sakina-outside.glb`; switching the site over is a separate, later step).

`WindowView` is NOT a bake group: it is a light source and a backdrop only. Its images are packed into the .blend
so the file is portable. Lighting: the emissive photo adds some light to the room; the window frame/sill and room
lightmaps must be re-baked to account for it (done later on the GPU laptop).
"""
import bpy, os, sys, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WV = os.path.join(ROOT, "components", "window_view")


def _load_build():
    sys.path.insert(0, WV)                       # view.py / panorama.py live next to build.py
    spec = importlib.util.spec_from_file_location("cmp_window_view_build", os.path.join(WV, "build.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def apply():
    mod = _load_build()
    before = set(bpy.data.objects)
    root = mod.build()
    new = [o for o in bpy.data.objects if o not in before]

    coll = bpy.data.collections.new("WindowView")
    bpy.context.scene.collection.children.link(coll)
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)

    for img in {s.material.node_tree.nodes[n].image
                for o in new if o.type == 'MESH'
                for s in o.material_slots if s.material and s.material.use_nodes
                for n in range(len(s.material.node_tree.nodes))
                if s.material.node_tree.nodes[n].type == 'TEX_IMAGE' and s.material.node_tree.nodes[n].image}:
        if not img.packed_file:
            img.pack()
    bpy.context.view_layer.update()
    print(f"e09: WindowView collection with {[o.name for o in new]}", flush=True)
