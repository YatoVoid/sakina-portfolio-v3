"""Rebuild the V3 room scene: v17 source -> V2 lighting passes (v19, v20) -> V3 edits, in order.
The source .blend is never modified; the result is saved to $V3_WORK/source/v3-edited.blend.

    python3 pipeline/build_scene.py                 # all edits in EDITS
    python3 pipeline/build_scene.py --upto e00      # V2 state only (no V3 edits) = what the live site was baked from
    python3 pipeline/build_scene.py --only e02      # V2 state + that one edit (edits are independent of each other, except e03 needs e02)
    python3 pipeline/build_scene.py --only e02,e03  # V2 state + the chair and the bookcase
    python3 pipeline/build_scene.py --only e02,e03,e04  # ... + the radiator under the desk
"""
import bpy, os, sys, runpy, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.setdefault("V3_WORK", "/tmp/v3work")
os.makedirs(WORK + "/source", exist_ok=True)
# e07_desk_shorten (Edit #6b) is intentionally NOT listed: Sakina excluded the desk shortening (2026-11-01) and it was written for the V2 desk
# that e08_desk_detail replaces. The file stays in pipeline/edits/ only so it can be tested separately later.
EDITS = ["e01_tapes_vcr", "e02_club_chair", "e03_antique_bookcase", "e04_radiator", "e05_remove_under_desk_wires",
         "e05_crt_vcr", "e08_desk_detail", "e09_window_view", "e10_mug_coaster", "e11_chair", "e12_gallery_wall",
         "e13_wall_colour", "e14_window_reveal", "e06_wall_clocks", "e08_degree_center"]          # applied in this order; each is pipeline/edits/<name>.py with apply()


def build(upto=None, save=True, only=None):
    bpy.ops.wm.open_mainfile(filepath=ROOT + "/assets/sakina-v17.blend")
    runpy.run_path(ROOT + "/pipeline/bake/sakina_v19.py", run_name="__main__")
    runpy.run_path(ROOT + "/pipeline/bake/sakina_v20.py", run_name="__main__")
    for name in EDITS:
        if upto and name > upto:
            break
        if only and not any(name.startswith(x) for x in only.split(',')):
            continue
        spec = importlib.util.spec_from_file_location(name, f"{ROOT}/pipeline/edits/{name}.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        mod.apply()
        print("EDIT applied", name, flush=True)
    # Portability for the GPU bake kit: no image may stay linked to a path on this machine. Pack every file-based image.
    packed = []
    for im in bpy.data.images:
        if im.source == 'FILE' and not im.packed_file and im.filepath and os.path.exists(bpy.path.abspath(im.filepath)):
            im.pack(); packed.append(im.name)
    if packed:
        print("PACKED external images:", packed, flush=True)
    if save:
        out = WORK + "/source/" + os.environ.get("SCENE_NAME", "v3-edited") + ".blend"
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
        print("SAVED", out)


if __name__ == "__main__":
    a = sys.argv[1:]
    build(upto=a[a.index("--upto") + 1] if "--upto" in a else None,
          only=a[a.index("--only") + 1] if "--only" in a else None)
