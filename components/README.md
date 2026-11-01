# Components — detailed standalone assets

Merged on `integration/v3-master` from two parallel sessions:
`components/detailed-assets` (desk, crt) and `components/detail-assets` (window_view).
Nothing here is loaded by the website; components enter the room only through `pipeline/edits/eNN_*.py`.

## Components

| Component | Source branch | Status on integration branch |
|---|---|---|
| `desk` | `components/detailed-assets` | **Approved** (Sakina, 2026-10-31) — integrated by `e08_desk_detail.py` |
| `window_view` | `components/detail-assets` | **Approved** (Sakina, 2026-10-31) — integrated by `e09_window_view.py` |
| `crt` | `components/detailed-assets` | **Not used.** Sakina chose the `round3` CRT (`e05_crt_vcr.py`); this WIP stays unintegrated |
| `room_refresh` | `components/detail-assets` | **Partly approved** (Sakina, 2026-11-01): lamp, calculator, remote only. Window, curtains, poster and notebook are NOT used (e14 window and round3 curtains win) |

## Ownership boundary (original parallel work)

The room session (`round3`) owns room lighting/baking/denoise (`pipeline/bake/*`, `e07_warm_light.py`,
`pipeline/tools/oidn.py`), scene assembly (`pipeline/build_scene.py`, `pipeline/edits/e0*.py`,
`assets/sakina-v17.blend`), the site (`web/*`) and room previews. The component sessions only added files under
`components/`.

## Layout (two conventions coexist; file names do not clash)

```
components/
  _lib/                shared helpers. desk/crt use common.py, materials.py, preview.py, woodgrain.py;
                       window_view uses the package modules export.py, pbr.py, studio.py
  build.py             runner used by window_view: python3 components/build.py <name> [--samples N] [--no-render]
  <name>/
    build_<name>.py    (desk, crt)  geometry + materials -> <name>.blend + <name>.glb
    build.py           (window_view) build() creates the component at the origin
    materials*.py      component PBR materials (procedural, bake-safe)
    spec.md / INTEGRATION.md   reference analysis, placement, bake group
    refs/              reference photos
    export/            GLB / source .blend
    previews/          phone-friendly JPG renders (neutral studio light, NOT the room lighting)
```

## Conventions

- Metres, Z-up, front faces **−Y**, base at z = 0. Part names prefixed `<Name>_`.
- Materials are procedural Principled BSDF so room bakes use them directly; standalone GLBs get baked textures.

## Commands

```bash
python3 components/desk/build_desk.py                 # desk
python3 components/build.py window_view --no-render   # window view
```

## Integration

A room edit appends the component into the right bake collection, then only that bake group is re-baked
(on the GPU laptop for this release). See `INTEGRATION_PLAN.md` at the repository root.
