"""Room refresh (Sakina, 2026-11-01): apply all refreshed parts to the room scene.

Drop-in shape of a pipeline edit (`apply()`), so after approval it can become `pipeline/edits/eNN_room_refresh.py`
(thin wrapper) on the integration branch. Each part keeps its bake collection:
  Window collection : window (frame, sashes, glass, handle, hinges)
  Room collection   : curtains + rod, poster (moved)
  Lamp collection   : desk lamp            Desk collection : calculator, notebook
  Tapes collection  : remote
PARTS env var (comma list) limits which parts run, for quick previews.
"""
import bpy, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "parts"), os.path.dirname(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

ORDER = [("window", "Window"), ("curtains", "Room"), ("poster", "Room"),
         ("lamp", "Lamp"), ("remote", "Tapes"), ("calculator", "Desk"), ("notebook", "Desk")]


def apply():
    import importlib
    only = [s for s in os.environ.get("PARTS", "").split(",") if s]
    for name, coll in ORDER:
        if only and name not in only:
            continue
        if not os.path.exists(os.path.join(HERE, "parts", name + ".py")):
            print("REFRESH skip (not built yet)", name); continue
        mod = importlib.import_module(name)
        made = mod.build(bpy.data.collections[coll])
        print("REFRESH applied", name, len(made or []), "objects", flush=True)
