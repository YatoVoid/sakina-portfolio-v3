# Copied from the V2 pipeline (C:\Users\sakin\Downloads\v2\v2\pipeline, read-only source; V2 untouched).
# V3 changes: work dir from $V3_WORK instead of /home/wali/...; Cycles on CPU (cloud has no GPU).
import os
import bpy
D=bpy.data; sc=bpy.context.scene
for o in list(D.collections["Outside"].all_objects):
    if o is not None: o.hide_render=False
for o in D.objects:
    if o.name.startswith(("Rain","Steam","Haze")): o.hide_render=False
sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'; sc.view_settings.exposure=0.0
baked=[o for o in D.objects if o.get("bake_group")]
print("FIX baked objects",len(baked),"groups",sorted({o["bake_group"] for o in baked}))
print("FIX uvs",{len(o.data.uv_layers) for o in baked},{o.data.uv_layers[0].name for o in baked})
bpy.ops.wm.save_as_mainfile(filepath=os.environ.get("V3_WORK", "/tmp/v3work") + "/source/sakina-v21-baked.blend",compress=True)
