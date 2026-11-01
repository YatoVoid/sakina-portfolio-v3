# Components workshop (parallel session, branch `components/detail-assets`)

Standalone, detailed 3D components built from Sakina's reference photos with Blender Python. Each component is
modelled, textured and previewed **in isolation**; nothing here changes the live room until Sakina approves an
integration.

## Ownership boundaries (agreed 2026-10-31)

A second session works in parallel on branch `round3` (room lighting, baking, wall shadows, furniture). This
workshop **does not edit** any of its files:

| Owned by the room session — never edited here | Owned by this workshop |
|---|---|
| `pipeline/edits/e*.py`, `pipeline/build_scene.py` | `components/**` |
| `pipeline/bake/**`, `pipeline/render_preview.py`, `pipeline/tools/**` | |
| `web/**` (renderer, `main.js`, scene assembly, GLBs) | |
| `assets/sakina-v17.blend`, root docs (`PROGRESS.md`, `DECISIONS.md`, …) | |

No deploys, no merges into `main`. Integration happens only after approval (see "Integration" below).

## Components

| Component | Status | Notes |
|---|---|---|
| `window_view` | approved, merged on `integration/v3-master` (e09) | Berlin rail-yard night photo outside the window (`window_view/spec.md`) |
| `room_refresh` | awaiting approval | Realistic lamp, remote, calculator, notebook; window without transom + brass handle; white curved curtains + rod; poster onto the wall post (`room_refresh/spec.md`) |

## Layout

```
components/
  _lib/            shared helpers (materials, geometry, studio previews, GLB export + checks)
  build.py         runner: python3 components/build.py <name> [--samples N] [--no-render]
  <name>/
    build.py       build(): creates the component at the origin, returns its root object
    materials.py   the component's PBR materials (procedural, bake-safe)
    spec.md        reference analysis: dimensions, materials, certain vs. inferred
    refs/          Sakina's reference photos
    export/        <name>.glb (+ <name>.blend source) — rebuilt by the runner
    previews/      phone-friendly preview renders (JPEG)
```

## Conventions (match the room pipeline)

- Metres, Z-up, front faces **−Y** (the room's CRT faces −Y), base resting at z = 0, centred on x/y.
- One root empty `CMP_<name>` parents every part; part names are prefixed `<Name>_`.
- Materials: Principled BSDF with procedural detail (wear, grain, roughness breakup). Room bakes use them
  directly; the standalone GLB gets them baked to image textures (base colour, roughness, metallic, normal).
- Previews are lit by a neutral studio rig plus a warm "desk lamp at night" rig that imitates the room mood.
  They are component previews only — the final look comes from the room's own lighting bake.

## Integration (after approval, done together with the room session)

1. A new room edit `pipeline/edits/eNN_<name>.py` (number chosen with the room session) calls
   `components/<name>/build.py: build()` inside the room scene, positions the root, removes the old object and
   moves the parts into the right bake collection.
2. Re-bake only the affected bake group(s), splice into the room GLB under a **new filename**, publish to
   `/preview/`, verify, then promote after approval.
