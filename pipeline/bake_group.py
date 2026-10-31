"""Bake ONE bake group from an edited scene and export it, V2 pipeline steps unchanged.

    python3 pipeline/bake_group.py <Group> <scene.blend> <out_dir>
      -> <out_dir>/lm_<Group>.png/.exr, <out_dir>/<Group>/sakina-room.glb (contains Room_<Group> only)

Each group is baked in its own run, starting from the unbaked scene, so every group sees the same lighting
(other groups keep their original materials while one is baked). Full quality: SPP=192, V2 resolutions.
"""
import bpy, os, sys, runpy, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
group, scene, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
os.environ.update(COLS=group, BAKE_OUT=out, SAVE=f"{out}/{group}-baked.blend", EXPORT_DIR=f"{out}/{group}")
os.environ.setdefault("SPP", "192")
t = time.time()
bpy.ops.wm.open_mainfile(filepath=scene)
runpy.run_path(ROOT + "/pipeline/bake/bake_lightmaps.py", run_name="__main__")
print("GROUP baked", group, round(time.time() - t), "s", flush=True)
runpy.run_path(ROOT + "/pipeline/bake/fix_baked21.py", run_name="__main__")
runpy.run_path(ROOT + "/pipeline/bake/export_web.py", run_name="__main__")
print("GROUP exported", group, round(time.time() - t), "s", flush=True)
