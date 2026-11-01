"""Build one component in an empty scene: model -> previews -> GLB.

    python3 components/build.py <name> [--samples 64] [--no-render] [--no-glb] [--views hero,front]
                                       [--rigs studio,night] [--tex 1024]

Reads components/<name>/build.py (must define build() -> root object; may define CLOSEUPS).
Writes components/<name>/export/<name>.glb, <name>.blend, stats.json and components/<name>/previews/*.jpg.
"""
import bpy, os, sys, json, time, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _lib import studio, export  # noqa: E402


def load(name):
    spec = importlib.util.spec_from_file_location(f"cmp_{name}", os.path.join(HERE, name, "build.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def main(argv):
    name = argv[0]
    opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mod = load(name)
    root = mod.build()
    d = os.path.join(HERE, name)
    os.makedirs(d + "/export", exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=f"{d}/export/{name}.blend", compress=True)
    out = {"component": name}
    if "--no-render" not in argv and getattr(mod, "STUDIO_PREVIEW", True):
        files = studio.render(root, d + "/previews", name,
                              rigs=tuple(opt("--rigs", "studio,night").split(",")),
                              views=tuple(opt("--views", "hero,front,side,back").split(",")),
                              samples=int(opt("--samples", 64)),
                              closeups=getattr(mod, "CLOSEUPS", ()))
        out["previews"] = [os.path.relpath(f, HERE) for f in files]
    if "--no-glb" not in argv:
        if hasattr(mod, "export"):      # component ships its own textures (e.g. a photo) — no re-bake
            out["glb"] = mod.export(root, f"{d}/export/{name}.glb")
        else:
            out["glb"] = export.export_glb(root, f"{d}/export/{name}.glb", tex_size=int(opt("--tex", 1024)))
    out["seconds"] = round(time.time() - t0)
    with open(f"{d}/export/stats.json", "w") as f:
        json.dump(out, f, indent=2)
    print("DONE", json.dumps(out, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
