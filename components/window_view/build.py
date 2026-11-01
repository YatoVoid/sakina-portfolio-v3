"""Window view component: the Berlin rail-yard night photo seen through the study-room window.

Two meshes, both unlit-style (emissive only, like every material in the baked room):
  WindowView_Photo — the photo at native resolution (2576 x 1718), mapped onto the exact patch of a cylinder
                     (r = 79.75 m around the opening camera) that its pixels cover. No resampling.
  WindowView_Pano  — 170 deg x 105 deg cylinder (r = 80 m) with the low-res extension panorama, plus top and
                     bottom caps, so oblique views through the window never show empty space.

Built in Blender world coordinates (Z-up) at the position it will occupy in the room: export with +Y up gives
three.js coordinates directly, so the website can add the GLB to the scene without any transform.
"""
import bpy, bmesh, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import view as V  # noqa: E402
import panorama  # noqa: E402

STUDIO_PREVIEW = False          # judged in the real room instead (preview/room_preview.py)
EXPOSURE = 1.0                  # emission strength; 1.0 = photo pixels shown exactly as photographed
PHOTO_GRID = (96, 64)           # patch tessellation (keeps the curved mapping accurate)
PANO_GRID = (144, 72)


def _emissive(name, image_path):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Specular IOR Level"].default_value = 0.0
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.location = (-400, 0)
    tex.image = bpy.data.images.load(image_path); tex.extension = 'EXTEND'
    tex.image.colorspace_settings.name = 'sRGB'
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = EXPOSURE
    return m


def _object(name, bm, mat, root):
    centre = V.view_to_blender((0, 0, 0))
    bm.normal_update()
    away = [f for f in bm.faces if f.normal.dot(f.calc_center_median() - __import__("mathutils").Vector(centre)) > 0]
    bmesh.ops.reverse_faces(bm, faces=away)            # every face must face the viewer (three.js culls back faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.parent = root
    return o


def _photo_patch(root, mat):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
    nx, ny = PHOTO_GRID
    verts = {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            px, py = i / nx * V.PHOTO_W, j / ny * V.PHOTO_H
            p = V.on_cylinder(V.photo_dir(px, py), V.PATCH_RADIUS)
            verts[i, j] = (bm.verts.new(V.view_to_blender(p)), (i / nx, 1 - j / ny))
    for j in range(ny):
        for i in range(nx):
            q = [verts[i, j], verts[i, j + 1], verts[i + 1, j + 1], verts[i + 1, j]]   # faces the viewer
            f = bm.faces.new([v for v, _ in q])
            for loop, (_, uv) in zip(f.loops, q):
                loop[uvl].uv = uv
    return _object("WindowView_Photo", bm, mat, root)


def _pano(root, mat):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
    nx, ny = PANO_GRID
    y0, y1 = map(math.radians, V.PANO_YAW)
    t0, t1 = (math.tan(math.radians(a)) for a in V.PANO_PITCH)
    R = V.RADIUS
    grid = {}
    for j in range(ny + 1):
        t = t0 + j / ny * (t1 - t0)
        for i in range(nx + 1):
            a = y0 + i / nx * (y1 - y0)
            p = (math.sin(a) * R, t * R, math.cos(a) * R)
            grid[i, j] = (bm.verts.new(V.view_to_blender(p)), (i / nx, j / ny))
    for j in range(ny):
        for i in range(nx):
            q = [grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]]
            f = bm.faces.new([v for v, _ in q])
            for loop, (_, uv) in zip(f.loops, q):
                loop[uvl].uv = uv
    # caps: fans to the centre line, sampling the panorama's first/last row (half a texel inside)
    for j, tv, flip in ((0, t0, False), (ny, t1, True)):
        c = bm.verts.new(V.view_to_blender((0, tv * R, R * 0.35)))
        v_uv = (0.5 / V.PANO_SIZE[1]) if j == 0 else 1 - 0.5 / V.PANO_SIZE[1]
        for i in range(nx):
            a, b = grid[i, j][0], grid[i + 1, j][0]
            ring = [a, c, b] if not flip else [b, c, a]
            uvs = [(i / nx, v_uv), ((i + 0.5) / nx, v_uv), ((i + 1) / nx, v_uv)]
            if flip:
                uvs = uvs[::-1]
            f = bm.faces.new(ring)
            for loop, uv in zip(f.loops, uvs):
                loop[uvl].uv = uv
    return _object("WindowView_Pano", bm, mat, root)


def build():
    pano_path = panorama.build()
    root = bpy.data.objects.new("CMP_window_view", None); bpy.context.scene.collection.objects.link(root)
    _photo_patch(root, _emissive("WindowView_Photo", os.path.join(HERE, "refs", "berlin-railyard-night.jpg")))
    _pano(root, _emissive("WindowView_Pano", pano_path))
    return root


def export(root, path):
    """Direct export: the photo is shipped as-is (no texture re-bake), JPEG kept."""
    bpy.ops.object.select_all(action='DESELECT')
    for o in [root] + list(root.children):
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True,
                              export_image_format='AUTO', export_texcoords=True, export_normals=False,
                              export_materials='EXPORT')
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in root.children)
    return {"file": os.path.basename(path), "bytes": os.path.getsize(path), "triangles": tris}
