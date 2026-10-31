#!/usr/bin/env python3
"""
V3 Pipeline — build_model.py
Runs in cloud via: python pipeline/build_model.py <model_name> [--preview] [--samples N]

Generates a single room element as a .glb file using the bpy pip package.
No full Blender binary required.

Usage:
  python pipeline/build_model.py desk            # export desk.glb
  python pipeline/build_model.py monitor         # export monitor.glb
  python pipeline/build_model.py all             # build every model
  python pipeline/build_model.py desk --preview  # also render a 320x240 PNG

Output:
  assets/models/<name>.glb        (Three.js-ready)
  assets/previews/<name>.png      (if --preview)
"""

import sys, os, math, argparse, time

# ── bpy availability check ────────────────────────────────────────────────
try:
    import bpy
except ImportError:
    print("[ERROR] bpy not installed. Run:  pip install bpy==5.2.3 --break-system-packages")
    sys.exit(1)

# ── Paths ─────────────────────────────────────────────────────────────────
REPO_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR  = os.path.join(REPO_ROOT, 'assets', 'models')
PREVIEW_DIR = os.path.join(REPO_ROOT, 'assets', 'previews')
os.makedirs(MODELS_DIR,  exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────────────────
def reset():
    """Clear the scene completely."""
    bpy.ops.wm.read_factory_settings(use_empty=True)


def hex_to_linear(h):
    """Convert sRGB hex (#rrggbb or 0xrrggbb) → linear RGB tuple for bpy."""
    h = int(h) if isinstance(h, int) else int(h.lstrip('#'), 16)
    r, g, b = (h >> 16) & 0xFF, (h >> 8) & 0xFF, h & 0xFF
    def s2l(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (s2l(r), s2l(g), s2l(b), 1.0)


def add_material(obj, name, base_color, roughness=0.8, metallic=0.0,
                 emission_color=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if not bsdf:
        bsdf = mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value  = hex_to_linear(base_color)
    bsdf.inputs['Roughness'].default_value   = roughness
    bsdf.inputs['Metallic'].default_value    = metallic
    if emission_color and emission_strength > 0:
        bsdf.inputs['Emission Color'].default_value    = hex_to_linear(emission_color)
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    obj.data.materials.append(mat)
    return mat


def export_glb(filepath):
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLB',
        export_apply=True,
        export_materials='EXPORT',
    )
    size = os.path.getsize(filepath)
    print(f"  Exported → {filepath}  ({size:,} bytes)")


def setup_camera_for_preview(location, look_at=(0, 0, 0)):
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.active_object
    dx, dy, dz = (look_at[i] - location[i] for i in range(3))
    cam.rotation_euler = (
        math.atan2(math.sqrt(dx*dx + dy*dy), dz) - math.pi/2,
        0,
        math.atan2(dx, -dy)
    )
    bpy.context.scene.camera = cam
    return cam


def render_preview(name, samples=32):
    bpy.ops.object.light_add(type='POINT', location=(2, -2, 3))
    light = bpy.context.active_object
    light.data.energy = 800
    light.data.color  = (1.0, 0.92, 0.78)
    bpy.context.scene.render.engine             = 'CYCLES'
    bpy.context.scene.cycles.device             = 'CPU'
    bpy.context.scene.cycles.samples            = samples
    bpy.context.scene.render.resolution_x       = 320
    bpy.context.scene.render.resolution_y       = 240
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    out = os.path.join(PREVIEW_DIR, f"{name}.png")
    bpy.context.scene.render.filepath = out
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"  Preview rendered in {time.time()-t0:.1f}s → {out}")


# ── Model builders ─────────────────────────────────────────────────────────

def build_desk():
    """Vintage wooden writing desk."""
    reset()
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    top = bpy.context.active_object
    top.name = 'desk_top'
    top.scale = (1.2, 0.45, 0.03)
    top.location = (0, 0, 0.39)
    bpy.ops.object.transform_apply(scale=True)
    add_material(top, 'DarkOak', 0x2d1a09, roughness=0.75)

    # Legs
    for lx, ly in [(-0.55, -0.4), (0.55, -0.4), (-0.55, 0.4), (0.55, 0.4)]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(lx, ly, 0))
        leg = bpy.context.active_object
        leg.name = f'leg_{lx}_{ly}'
        leg.scale = (0.04, 0.04, 0.39)
        bpy.ops.object.transform_apply(scale=True)
        add_material(leg, 'DarkOak', 0x261507, roughness=0.8)

    # Lower shelf
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.05))
    shelf = bpy.context.active_object
    shelf.name = 'desk_shelf'
    shelf.scale = (1.2, 0.45, 0.025)
    bpy.ops.object.transform_apply(scale=True)
    add_material(shelf, 'DarkOak', 0x2d1a09, roughness=0.8)

    return 'desk'


def build_monitor():
    """CRT-era flat monitor with subtle glow."""
    reset()
    # Body
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    body = bpy.context.active_object
    body.name = 'monitor_body'
    body.scale = (0.425, 0.035, 0.26)
    bpy.ops.object.transform_apply(scale=True)
    add_material(body, 'MonitorFrame', 0x0d0d0d, roughness=0.6, metallic=0.1)
    # Screen
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.04, 0))
    scr = bpy.context.active_object
    scr.name = 'monitor_screen'
    scr.scale = (0.38, 0.005, 0.22)
    bpy.ops.object.transform_apply(scale=True)
    add_material(scr, 'ScreenGlow', 0x001520, roughness=0.15,
                 emission_color=0x1a4060, emission_strength=0.8)
    # Stand
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.28))
    stem = bpy.context.active_object
    stem.name = 'monitor_stem'
    stem.scale = (0.02, 0.02, 0.14)
    bpy.ops.object.transform_apply(scale=True)
    add_material(stem, 'MonitorFrame', 0x0d0d0d, roughness=0.6, metallic=0.1)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.43))
    base = bpy.context.active_object
    base.name = 'monitor_base'
    base.scale = (0.12, 0.1, 0.01)
    bpy.ops.object.transform_apply(scale=True)
    add_material(base, 'MonitorFrame', 0x0d0d0d, roughness=0.6, metallic=0.1)

    setup_camera_for_preview((1.5, -1.0, 0.5), look_at=(0, 0, 0))
    return 'monitor'


def build_tv():
    """CRT television with VCR under it."""
    reset()
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    body = bpy.context.active_object
    body.name = 'tv_body'
    body.scale = (0.36, 0.125, 0.25)
    bpy.ops.object.transform_apply(scale=True)
    add_material(body, 'TVPlastic', 0x111111, roughness=0.5, metallic=0.15)
    # Screen
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.13, 0))
    scr = bpy.context.active_object
    scr.name = 'tv_screen'
    scr.scale = (0.31, 0.005, 0.205)
    bpy.ops.object.transform_apply(scale=True)
    add_material(scr, 'TVGlow', 0x050810, roughness=0.1,
                 emission_color=0x004488, emission_strength=0.5)
    # VCR
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.34))
    vcr = bpy.context.active_object
    vcr.name = 'vcr'
    vcr.scale = (0.25, 0.16, 0.04)
    bpy.ops.object.transform_apply(scale=True)
    add_material(vcr, 'VCRPlastic', 0x0a0a0a, roughness=0.4, metallic=0.1)

    setup_camera_for_preview((1.2, -0.8, 0.4), look_at=(0, 0, 0))
    return 'tv'


def build_vhs_rack():
    """VHS tape rack with 7 labelled cassettes."""
    reset()
    # Rack frame
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    rack = bpy.context.active_object
    rack.name = 'vhs_rack'
    rack.scale = (0.125, 0.06, 0.325)
    bpy.ops.object.transform_apply(scale=True)
    add_material(rack, 'RackMetal', 0x1a1a1a, roughness=0.3, metallic=0.8)
    # Tapes
    tape_colors = [0x0a1020, 0x200808, 0x0a1a08, 0x0a1020, 0x200808, 0x0a1a08, 0x100a20]
    for i, col in enumerate(tape_colors):
        x = -0.092 + i * 0.028
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, 0))
        tape = bpy.context.active_object
        tape.name = f'tape_{i:02d}'
        tape.scale = (0.013, 0.05, 0.095)
        bpy.ops.object.transform_apply(scale=True)
        add_material(tape, f'Tape_{i}', col, roughness=0.8)

    setup_camera_for_preview((0.6, -0.4, 0.3), look_at=(0, 0, 0))
    return 'vhs-rack'


def build_chair():
    """Simple wooden study chair."""
    reset()
    # Seat
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    seat = bpy.context.active_object
    seat.name = 'chair_seat'
    seat.scale = (0.28, 0.26, 0.02)
    bpy.ops.object.transform_apply(scale=True)
    add_material(seat, 'DarkFabric', 0x0e0b07, roughness=0.95)
    # Back
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.24, 0.2))
    back = bpy.context.active_object
    back.name = 'chair_back'
    back.scale = (0.26, 0.025, 0.28)
    bpy.ops.object.transform_apply(scale=True)
    add_material(back, 'DarkFabric', 0x0e0b07, roughness=0.95)
    # Legs
    for lx, ly in [(-0.22, -0.22), (0.22, -0.22), (-0.22, 0.1), (0.22, 0.1)]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(lx, ly, -0.2))
        leg = bpy.context.active_object
        leg.name = f'chair_leg_{lx}_{ly}'
        leg.scale = (0.02, 0.02, 0.2)
        bpy.ops.object.transform_apply(scale=True)
        add_material(leg, 'DarkWood', 0x1a0e06, roughness=0.8)

    setup_camera_for_preview((1.0, -0.8, 0.5), look_at=(0, 0, 0))
    return 'chair'


def build_lamp():
    """Desk lamp with emissive bulb."""
    reset()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.01, location=(0, 0, -0.18))
    base = bpy.context.active_object
    base.name = 'lamp_base'
    add_material(base, 'BrassArm', 0x8a6a20, roughness=0.3, metallic=0.7)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.2, location=(0, 0, 0))
    arm = bpy.context.active_object
    arm.name = 'lamp_arm'
    add_material(arm, 'BrassArm', 0x8a6a20, roughness=0.3, metallic=0.7)
    bpy.ops.mesh.primitive_cone_add(radius1=0.07, radius2=0.0, depth=0.05, location=(0, 0, 0.14))
    shade = bpy.context.active_object
    shade.name = 'lamp_shade'
    add_material(shade, 'LampShade', 0x1a1208, roughness=0.6)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.02, location=(0, 0, 0.12))
    bulb = bpy.context.active_object
    bulb.name = 'lamp_bulb'
    add_material(bulb, 'Bulb', 0xffc840, roughness=0.1,
                 emission_color=0xffc840, emission_strength=4.0)

    setup_camera_for_preview((0.5, -0.4, 0.4), look_at=(0, 0, 0))
    return 'lamp'


def build_bookshelf():
    """Bookshelf with procedural books."""
    reset()
    # Panels
    for x in [-0.5, 0.5]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0, 0))
        panel = bpy.context.active_object
        panel.name = f'shelf_panel_{x}'
        panel.scale = (0.04, 0.16, 0.9)
        bpy.ops.object.transform_apply(scale=True)
        add_material(panel, 'ShelfWood', 0x2d1a09, roughness=0.75)
    # Shelves
    for y in [-0.88, -0.24, 0.4, 0.88]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, y))
        sh = bpy.context.active_object
        sh.name = f'shelf_{y}'
        sh.scale = (0.53, 0.16, 0.02)
        bpy.ops.object.transform_apply(scale=True)
        add_material(sh, 'ShelfWood', 0x2d1a09, roughness=0.75)
    # Books
    import random; random.seed(42)
    book_cols = [0x4a1a0a, 0x0a2a1a, 0x1a1a3a, 0x2a0a2a, 0x0a2a2a]
    for row_z, n_books in [(-0.54, 9), (0.12, 8)]:
        x = -0.45
        for _ in range(n_books):
            w = random.uniform(0.025, 0.05)
            h = random.uniform(0.08, 0.14)
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x + w/2, 0, row_z + h/2))
            bk = bpy.context.active_object
            bk.name = f'book_{_}_{row_z}'
            bk.scale = (w, 0.12, h)
            bpy.ops.object.transform_apply(scale=True)
            col = random.choice(book_cols)
            add_material(bk, f'BookCloth_{col}', col, roughness=0.9)
            x += w + 0.004

    setup_camera_for_preview((1.2, -0.8, 0), look_at=(0, 0, 0))
    return 'bookshelf'


def build_room_shell():
    """Floor, walls, ceiling, window."""
    reset()
    w, d, h = 7.0, 8.0, 3.4
    # Floor
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    fl = bpy.context.active_object; fl.name = 'floor'
    fl.scale = (w/2, d/2, 0.03); bpy.ops.object.transform_apply(scale=True)
    add_material(fl, 'Floor', 0x1c1108, roughness=0.9)
    # Back wall
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -d/2+0.06, h/2))
    bw = bpy.context.active_object; bw.name = 'back_wall'
    bw.scale = (w/2, 0.06, h/2); bpy.ops.object.transform_apply(scale=True)
    add_material(bw, 'Wall', 0x14100a, roughness=0.95)
    # Left wall
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-w/2+0.06, 0, h/2))
    lw = bpy.context.active_object; lw.name = 'left_wall'
    lw.scale = (0.06, d/2, h/2); bpy.ops.object.transform_apply(scale=True)
    add_material(lw, 'Wall', 0x14100a, roughness=0.95)
    # Right wall
    bpy.ops.mesh.primitive_cube_add(size=1, location=(w/2-0.06, 0, h/2))
    rw = bpy.context.active_object; rw.name = 'right_wall'
    rw.scale = (0.06, d/2, h/2); bpy.ops.object.transform_apply(scale=True)
    add_material(rw, 'Wall', 0x14100a, roughness=0.95)
    # Ceiling
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, h))
    cw = bpy.context.active_object; cw.name = 'ceiling'
    cw.scale = (w/2, d/2, 0.06); bpy.ops.object.transform_apply(scale=True)
    add_material(cw, 'Ceiling', 0x10080a, roughness=0.95)
    # Window glass (emissive moonlight)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-1.2, -d/2+0.09, h/2+0.3))
    win = bpy.context.active_object; win.name = 'window'
    win.scale = (0.8, 0.03, 0.55); bpy.ops.object.transform_apply(scale=True)
    add_material(win, 'WindowGlass', 0x304060, roughness=0.05,
                 emission_color=0x8ab8e8, emission_strength=0.6)

    return 'room-shell'


def build_props():
    """Small desk props: mug, papers, keyboard."""
    reset()
    # Mug
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.1, location=(0, 0, 0))
    mug = bpy.context.active_object; mug.name = 'mug'
    add_material(mug, 'MugCeramic', 0x1a0a0a, roughness=0.7)
    # Papers stack
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.4, 0, 0.005))
    paper = bpy.context.active_object; paper.name = 'papers'
    paper.scale = (0.2, 0.16, 0.004); bpy.ops.object.transform_apply(scale=True)
    add_material(paper, 'Paper', 0x1a1508, roughness=0.95)
    # Keyboard
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.1, -0.15, 0.012))
    kb = bpy.context.active_object; kb.name = 'keyboard'
    kb.scale = (0.275, 0.09, 0.013); bpy.ops.object.transform_apply(scale=True)
    add_material(kb, 'KeyboardPlastic', 0x0a0a08, roughness=0.7)

    return 'props'


# ── Model registry ─────────────────────────────────────────────────────────
MODELS = {
    'desk':       build_desk,
    'monitor':    build_monitor,
    'tv':         build_tv,
    'vhs-rack':   build_vhs_rack,
    'chair':      build_chair,
    'lamp':       build_lamp,
    'bookshelf':  build_bookshelf,
    'room-shell': build_room_shell,
    'props':      build_props,
}


# ── CLI ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='V3 bpy model builder')
    parser.add_argument('model', help=f'Model name or "all". Choices: {list(MODELS.keys())}')
    parser.add_argument('--preview', action='store_true', help='Render 320x240 preview PNG')
    parser.add_argument('--samples', type=int, default=32, help='Cycles samples for preview (default 32)')
    args = parser.parse_args()

    targets = list(MODELS.keys()) if args.model == 'all' else [args.model]
    for name in targets:
        if name not in MODELS:
            print(f"[ERROR] Unknown model: {name}. Choices: {list(MODELS.keys())}")
            sys.exit(1)
        print(f"\n── Building: {name} ──────────────────────────────────────")
        t0 = time.time()
        result_name = MODELS[name]()
        glb_path = os.path.join(MODELS_DIR, f"{result_name}.glb")
        export_glb(glb_path)
        if args.preview:
            render_preview(result_name, samples=args.samples)
        print(f"  Done in {time.time()-t0:.1f}s")

    print("\n✓ All done.")


if __name__ == '__main__':
    main()
