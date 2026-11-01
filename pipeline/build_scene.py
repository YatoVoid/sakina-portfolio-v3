"""Rebuild the V3 room scene: v17 source -> V2 lighting passes (v19, v20) -> V3 edits, in order.
The source .blend is never modified; the result is saved to $V3_WORK/source/v3-edited.blend.

    python3 pipeline/build_scene.py                 # all edits in EDITS
    python3 pipeline/build_scene.py --upto e00      # V2 state only (no V3 edits) = what the live site was baked from
"""
import bpy, os, sys, runpy, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.setdefault("V3_WORK", "/tmp/v3work")
os.makedirs(WORK + "/source", exist_ok=True)
EDITS = ["e01_tapes_vcr", "e02_plant", "e03_ibm_corner", "e04_left_zone", "e05_crt_vcr", "e06_right_nook", "e07_warm_light", "e08_window_curtains", "e09_floor", "e10_plant_alocasia", "e11_tapes_vhs", "e12_floppy"]          # applied in this order; each is pipeline/edits/<name>.py with apply()


def build(upto=None, save=True):
    bpy.ops.wm.open_mainfile(filepath=ROOT + "/assets/sakina-v17.blend")
    runpy.run_path(ROOT + "/pipeline/bake/sakina_v19.py", run_name="__main__")
    runpy.run_path(ROOT + "/pipeline/bake/sakina_v20.py", run_name="__main__")
    for name in EDITS:
        if upto and name > upto:
            break
        spec = importlib.util.spec_from_file_location(name, f"{ROOT}/pipeline/edits/{name}.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        mod.apply()
        print("EDIT applied", name, flush=True)
    if save:
        out = WORK + "/source/" + os.environ.get("SCENE_NAME", "v3-edited") + ".blend"
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
        print("SAVED", out)


if __name__ == "__main__":
    a = sys.argv[1:]
    build(upto=a[a.index("--upto") + 1] if "--upto" in a else None)
