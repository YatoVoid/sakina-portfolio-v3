"""Edit #12 (Sakina request 2026-11-01): gallery wall above the IBM computer, laid out like her reference photo.

Reference: eight gallery-wrapped canvas prints in two staggered rows (landscape / portrait / large landscape pieces,
about 2 cm gaps, tops and bottoms deliberately uneven). Replaces the 20 small postcards (`Postcard_00..19` and their
`_Photo` meshes) on the left wall above the IBM station. The clock above is kept.

Each canvas is a real box (2.5-3.5 cm deep, 1.5 mm bevel) with the photo on the front and the photo's edge pixels
stretched over the sides (the look of a gallery wrap). Photos are the ones already packed in the scene (the same
images the postcards used), cropped to each canvas's aspect ratio. Material: photo + fine procedural canvas-weave bump.
Slight, fixed tilt per canvas (|tilt| <= 0.25 deg) so the wall does not look machine-aligned.

Layout in the reference's pixel space, scaled so the whole group is ~1.32 m wide x 0.63 m tall, centred on the IBM
station (y = 1.25) with its middle at z = 1.45 (computer top 1.06 m, clock frame bottom 1.875 m).
Wall: left wall inner face x = -3.0; viewer looks toward -X, so +Y is the viewer's right.
"""
import bpy, bmesh, math, random
from mathutils import Vector

WALL_X = -3.0
CENTRE_Y, CENTRE_Z = 1.25, 1.45
S = 0.00156                                  # metres per reference pixel
REF_C = (484.0, 590.0)                       # centre of the reference group (px)

# (x0, y0, x1, y1) in reference px; image; focus (fu, fv) for the crop; depth (m)
PIECES = [
    ((60, 453, 258, 584),  "Photo_18_coast",     (0.5, 0.5),   0.030),
    ((272, 410, 403, 583), "Photo_12_buildings", (0.85, 0.5),  0.030),
    ((418, 387, 675, 580), "Photo_02_mountains", (0.5, 0.4),   0.035),
    ((687, 460, 838, 577), "Photo_10_city",      (0.5, 0.5),   0.025),
    ((137, 601, 290, 720), "Photo_19_coast",     (0.5, 0.5),   0.025),
    ((305, 598, 562, 793), "Photo_16_coast",     (0.5, 0.5),   0.035),
    ((574, 597, 705, 768), "Photo_06_lake",      (0.615, 0.5), 0.030),
    ((715, 594, 908, 720), "Photo_20_forest",    (0.5, 0.5),   0.025),
]
TILT_DEG = [0.15, -0.20, 0.10, -0.15, -0.10, 0.20, -0.25, 0.10]
BEVEL = 0.0015
EXPECT_OLD = 40


def _material(name, img):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.72
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.extension = 'EXTEND'
    tex.image.colorspace_settings.name = 'sRGB'
    coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 1400.0
    noise.inputs["Detail"].default_value = 2.0; noise.inputs["Roughness"].default_value = 0.6
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.10
    bump.inputs["Distance"].default_value = 0.002
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def _crop(img, w, h, focus):
    """UV window (u0, v0, u1, v1) that covers a w x h canvas with the photo (centre-crop with a focus point)."""
    A = img.size[0] / img.size[1]; P = w / h
    if P < A:
        uw = P / A; u0 = focus[0] * (1 - uw); return (u0, 0.0, u0 + uw, 1.0)
    vh = A / P; v0 = focus[1] * (1 - vh); return (0.0, v0, 1.0, v0 + vh)


def _canvas(name, w, h, depth, img, focus, mat):
    """Box centred on the origin: width along +Y (viewer's right), height along +Z, front face towards +X."""
    bm = bmesh.new()
    hy, hz = w / 2, h / 2
    x_front, x_back = depth, 0.0
    corners = {}
    for sx, x in ((1, x_front), (0, x_back)):
        for sy, y in ((0, -hy), (1, hy)):
            for sz, z in ((0, -hz), (1, hz)):
                corners[sx, sy, sz] = bm.verts.new((x, y, z))
    f = lambda *k: bm.faces.new([corners[i] for i in k])
    f((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1))      # front
    f((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0))      # back
    f((1, 0, 0), (1, 0, 1), (0, 0, 1), (0, 0, 0))      # -Y side
    f((1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1))      # +Y side
    f((1, 0, 1), (1, 1, 1), (0, 1, 1), (0, 0, 1))      # top
    f((1, 0, 0), (0, 0, 0), (0, 1, 0), (1, 1, 0))      # bottom
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    front = [e for e in bm.edges if all(abs(v.co.x - x_front) < 1e-9 for v in e.verts)]
    bmesh.ops.bevel(bm, geom=front, offset=BEVEL, segments=2, affect='EDGES')
    uv = bm.loops.layers.uv.new("UVMap")
    u0, v0, u1, v1 = _crop(img, w, h, focus)
    for face in bm.faces:
        for loop in face.loops:                         # one projection for every face: sides become edge-pixel streaks
            p = loop.vert.co
            u = min(max((p.y + hy) / w, 0.0), 1.0); v = min(max((p.z + hz) / h, 0.0), 1.0)
            loop[uv].uv = (u0 + u * (u1 - u0), v0 + v * (v1 - v0))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    return o


def apply():
    wd = bpy.data.collections["Wall_Decor"]
    old = [o for o in wd.objects if o.name.startswith("Postcard_")]
    assert len(old) == EXPECT_OLD, f"expected {EXPECT_OLD} postcard objects, found {len(old)}"
    assert not [o.name for o in bpy.data.objects if o.parent in set(old) and o not in set(old)]
    meshes = {o.data for o in old}
    for o in old:
        bpy.data.objects.remove(o, do_unlink=True)
    for m in meshes:
        if m.users == 0:
            bpy.data.meshes.remove(m)

    made = []
    for i, ((x0, y0, x1, y1), image, focus, depth) in enumerate(PIECES, start=1):
        w, h = (x1 - x0) * S, (y1 - y0) * S
        cy = CENTRE_Y + ((x0 + x1) / 2 - REF_C[0]) * S
        cz = CENTRE_Z - ((y0 + y1) / 2 - REF_C[1]) * S
        img = bpy.data.images[image]
        mat = _material(f"Gallery_Canvas_{i}", img)
        o = _canvas(f"Gallery_Canvas_{i}", w, h, depth, img, focus, mat)
        wd.objects.link(o)
        o.location = (WALL_X + 0.0005, cy, cz)
        o.rotation_euler = (math.radians(TILT_DEG[i - 1]), 0.0, 0.0)   # tilt about the wall normal (X)
        made.append((o.name, round(w, 3), round(h, 3), round(cy, 3), round(cz, 3)))
    bpy.context.view_layer.update()
    print(f"e12: removed {len(old)} postcard objects, added {len(made)} canvases: {made}", flush=True)
