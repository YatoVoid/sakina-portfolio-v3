"""Export the Berlin rail-yard window view (collection WindowView: photo patch + panorama) as its own GLB.
Not a bake group: the two meshes are unlit emissive picture surfaces ~80 m away; the site shows them behind the window glass.
    EXPORT_DIR=<dir> python3 -c "import bpy,runpy;bpy.ops.wm.open_mainfile(filepath='<scene.blend>');runpy.run_path('pipeline/bake/export_view.py')"
"""
import bpy, os
D = bpy.data
OUT = os.environ.get("EXPORT_DIR", os.environ.get("V3_WORK", "/tmp/v3work") + "/web")
os.makedirs(OUT, exist_ok=True)
coll = D.collections["WindowView"]
objs = [o for o in coll.all_objects if o.type == 'MESH']
assert len(objs) == 2, [o.name for o in objs]
for o in objs:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw
    o.hide_viewport = False
    o.hide_set(False)
bpy.ops.object.select_all(action='DESELECT')
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
path = OUT + "/sakina-view.glb"
bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_image_format='JPEG', export_jpeg_quality=90,
                          export_lights=False, export_cameras=False, export_apply=False, export_yup=True)
print("VIEW wrote", path, round(os.path.getsize(path) / 1e6, 2), "MB", flush=True)
