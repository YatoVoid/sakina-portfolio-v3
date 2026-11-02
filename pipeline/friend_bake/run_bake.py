"""Final lightmap bake for Sakina's V3 room. Run INSIDE Blender (see run_bake.bat / README.txt):

    blender -b v3-integrated.blend -P run_bake.py            # full bake, GPU
    blender -b v3-integrated.blend -P run_bake.py -- test    # 1-minute check (one small group, low quality)

Everything it writes goes to the folder  out/  next to this file. When it finishes, send back  out/sakina-v21-baked.blend  (one file, lightmaps embedded).
"""
import os, sys, time, runpy, bpy

HERE = os.path.dirname(os.path.abspath(__file__))
TEST = "test" in sys.argv

# ---- settings (change DEVICE if the laptop has no NVIDIA RTX card) ---------------------------------------------------------
os.environ.setdefault("DEVICE", "OPTIX")          # OPTIX = NVIDIA RTX (fastest). Use CUDA for older NVIDIA, HIP for AMD, CPU if nothing else works.
os.environ.setdefault("SPP", "8" if TEST else "256")
if TEST:
    os.environ.setdefault("RES_SCALE", "0.125")
    os.environ.setdefault("COLS", "Lamp")
os.environ["V3_WORK"] = os.path.join(HERE, "work")
os.environ["BAKE_OUT"] = os.path.join(HERE, "out", "test" if TEST else "lightmaps")
os.environ["SAVE"] = os.path.join(HERE, "out", "test-baked.blend" if TEST else "sakina-v21-baked.blend")
os.environ["PACK"] = "1"
for d in (os.environ["V3_WORK"], os.path.dirname(os.environ["SAVE"])):
    os.makedirs(d, exist_ok=True)

print("=" * 70)
print("V3 bake:", "TEST" if TEST else "FULL", "| Blender", bpy.app.version_string, "| DEVICE", os.environ["DEVICE"], "| SPP", os.environ["SPP"])
print("=" * 70, flush=True)
t0 = time.time()
runpy.run_path(os.path.join(HERE, "pipeline", "bake", "bake_lightmaps.py"), run_name="__main__")
print(f"DONE in {(time.time() - t0) / 60:.1f} min -> {os.environ['SAVE']}", flush=True)
