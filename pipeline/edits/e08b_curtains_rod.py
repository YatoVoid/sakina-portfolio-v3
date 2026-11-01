"""Edit #8b (integration): round3 curtains + rod + brighter city, WITHOUT round3's window.

Sakina (2026-11-01): the window is the recessed double casement from e14; the curtains are the round3 ones
(narrower stacks, so the blue poster stays on bare wall). e08_window_curtains.py builds window + curtains together, so
this wrapper reuses its rod, curtain and city functions only. Must run AFTER e14_window_reveal.
"""
import bpy, importlib.util, os

HERE = os.path.dirname(os.path.abspath(__file__))


def apply():
    spec = importlib.util.spec_from_file_location("e08_window_curtains_mod", os.path.join(HERE, "e08_window_curtains.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    D = bpy.data
    drop = [o for o in D.objects if o.name.startswith(("Curtain_", "Rod"))]
    for o in drop:
        me = o.data
        D.objects.remove(o, do_unlink=True)
        if me and me.users == 0:
            D.meshes.remove(me)
    m._rod()
    m._curtains()
    m._city()
    bpy.context.view_layer.update()
    print(f"e08b: replaced {len(drop)} old curtain/rod objects with round3 curtains + rod", flush=True)
