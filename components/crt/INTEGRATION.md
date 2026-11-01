# Center CRT TV: integration notes (NOT approved, NOT baked)

Branch `components/detailed-assets`. Source: `build_crt.py` + `materials_crt.py` -> `export/crt_source.blend`.
Preview in the room (no bake): `python3 components/crt/place_preview.py <prefix> <spp> tv,ctrl,side [new|old]`.
Build without baking: `SKIP_BAKE=1 python3 components/crt/build_crt.py`. Full bake (later): `python3 components/crt/build_crt.py`.

## Replaces (v17, collection `Monitor`)
All `CRT_*` and `Scr_*` objects (back, front, glass, brand, buttons, knobs, labels, screen texts). Kept: VCR, cables, desk, books, everything else.

## Placement
Local frame: origin = bottom centre of the bezel front plane, front faces -Y. Room transform: translate (-0.02, 1.600, 0.813), no rotation. Same footprint as the old TV (bezel 0.36 x 0.36 m, back y 1.90).

## Lights
`L6_TV_Screen` (point light 5 cm in front of the glass) shows as a hot spot in the new glossy glass, so it is hidden in the preview. At integration decide whether to keep it as a glow (move it further out / make it invisible to glossy rays) or drop it, because the new screen is emissive.

## Open decisions
- Round3's `e05` also rebuilds the CRT. Choose one (or merge) before anything is integrated.
- Cables and the mug in the preview are the old ones.
- Bake groups: bezel + housing textures (`crt_bezel`, `crt_housing`), then splice into the room GLB with a new filename.
