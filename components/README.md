# Components — detailed standalone assets (parallel session)

Branch: `components/detailed-assets` (never merged into `main` without Sakina's approval).

This folder holds individual, reference-driven 3D components built in isolation from the room.
Nothing here is loaded by the website, the room bake, or `pipeline/build_scene.py`.

## Ownership boundary (parallel work)

The active room session (branch `round3`) owns — **not touched here**:

- Room lighting, baking and denoise: `pipeline/bake/*`, `pipeline/edits/e07_warm_light.py`, `pipeline/tools/oidn.py`
- Main scene assembly: `pipeline/build_scene.py`, `pipeline/edits/e0*.py`, `assets/sakina-v17.blend`
- Renderer / site: `web/*` (main.js, index.html, look-controls.js, tapes.json, GLBs)
- Room previews: `pipeline/render_preview.py`, `pipeline/tests/*`

This folder only adds new files under `components/`.

## Layout

```
components/
  _lib/                 shared helpers (PBR materials, studio preview rig, GLB export, checks)
  <name>/
    refs/               reference photos + analysis.md (certain vs. inferred)
    build_<name>.py     Blender Python: geometry + materials -> <name>.blend + <name>.glb
    materials_<name>.py component-specific PBR materials
    export/<name>.glb   web asset (real-time PBR, metres, Y-up glTF, origin at base centre)
    previews/*.jpg      Cycles studio renders (neutral lighting, NOT the room lighting)
    INTEGRATION.md      size, origin, placement suggestion, bake group, triangle/texture budget
```

## Commands

```bash
python3 components/<name>/build_<name>.py            # build + export GLB + checks
python3 components/_lib/preview.py <name> [samples]  # Cycles studio previews (phone-sized JPGs)
```

## Integration (later, only after approval)

The room is rendered unlit from Cycles lightmaps. A component enters the room as an edit script
(`pipeline/edits/eNN_<name>.py`) that appends its collection from `<name>.blend` into the right bake group,
followed by a re-bake of that group only. The standalone GLB is for review and for any real-time use.
