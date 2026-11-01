"""Edit #13 (Sakina request 2026-11-01): the walls of the whole room get the wall colour of her reference photo.

Reference (vintage framed gallery wall, warm cream plaster): the wall samples to sRGB (207, 197, 183) = #CFC5B7 in four
regions away from shadows and sun patches (individual regions #CEC4B5 .. #D1C7B9).

All seven wall meshes (Wall_Left, Wall_Right, Wall_Front, Wall_Back_L/R/Below/Above) share the material `WallPlaster`, so one change
recolours the room. The ceiling (`CeilingDarkBrown`), floor, baseboards (`TrimPaint`) and window paint are not walls and are left alone.

The old graph made the walls near-black: `Mix.002` / `Mix.003` blend toward (0.024, 0.015, 0.009) by height, and with
Map Range 2.8 -> 2.2 that blend is already 1.0 below z = 2.2 m, i.e. over almost the whole wall. New graph:
  - base colour mottling (`Mix`) = the reference colour and a 7% darker variant (plaster is never perfectly even)
  - stains (`Mix.001`) = reference colour x 0.78 (soft, was near-black brown)
  - ceiling-edge shade (`Mix.002`) = reference colour x 0.72, only above z = 2.45 m, up to 55%
  - floor-edge shade (`Mix.003`) = reference colour x 0.62, only below z = 0.35 m (unchanged range)
Noise patterns, bump and roughness are unchanged, so the plaster texture stays the same.

Value tuning (2026-11-01, low-res test bakes at scale 1.0 / 0.60 / 0.40, previews/integration/wall_value_test.jpg): 1.0 made the
lamp-lit room flat and bright, 0.40 turned murky; 0.60 keeps the reference hue and lets the lamp pools read. Default = 0.60.

Note: the colour is the paint (albedo). A photo shows lit paint, so the exact on-screen shade still depends on the room lighting.
"""
import bpy, os

REF_SRGB = (207, 197, 183)
# Paint albedo = reference colour x WALL_SCALE. The reference is a lit photo; as pure albedo it makes the lamp-lit night room
# bright and flat (see previews/integration/lowres_bake_test.jpg), so the albedo is scaled down. Same hue, lower value.
WALL_SCALE = float(os.environ.get("V3_WALL_SCALE", "0.60"))


def _lin(c8):
    c = c8 / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _col(k):
    r, g, b = (_lin(v) for v in REF_SRGB)
    k *= WALL_SCALE
    return (r * k, g * k, b * k, 1.0)


def apply():
    m = bpy.data.materials["WallPlaster"]
    nt = m.node_tree
    N = nt.nodes
    for n in ("Mix", "Mix.001", "Mix.002", "Mix.003", "Map Range", "Map Range.001"):
        assert n in N, f"WallPlaster node '{n}' missing"
    old = tuple(round(x, 3) for x in N["Mix"].inputs[6].default_value[:3])
    assert old == (0.262, 0.171, 0.091), f"unexpected WallPlaster base colour {old}; graph changed, re-check e13"

    N["Mix"].inputs[6].default_value = _col(1.00)       # A
    N["Mix"].inputs[7].default_value = _col(0.93)       # B
    N["Mix.001"].inputs[7].default_value = _col(0.78)   # stains
    N["Mix.002"].inputs[7].default_value = _col(0.72)   # ceiling-edge shade colour
    N["Mix.003"].inputs[7].default_value = _col(0.62)   # floor-edge shade colour

    mr = N["Map Range"]                                  # ceiling-edge shade: 0 below 2.45 m, 0.55 at the ceiling (2.8 m)
    mr.inputs[1].default_value, mr.inputs[2].default_value = 2.45, 2.80
    mr.inputs[3].default_value, mr.inputs[4].default_value = 0.0, 0.55
    bpy.context.view_layer.update()
    print("e13: WallPlaster recoloured to sRGB", REF_SRGB, "x albedo scale", WALL_SCALE, "(7 wall meshes share it)", flush=True)
