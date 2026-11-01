# Integration plan — Sakina Portfolio V3 (master integration session)

Branch: `integration/v3-master` (cut from `main` @ `57bdb1d`). Status: **plan only — nothing merged yet.**
Owner: master integration session. Production (`main`, Netlify) is not touched until Sakina approves.

## Hard limits for this session

- No final Cycles lighting bake here (Sakina bakes later on an NVIDIA laptop).
- No push to `main`, no change to the live site, no claim that browser lighting is verified.
- Merge a branch only after Sakina confirms it is complete and approved.
- `assets/sakina-v17.blend` is never edited; the unified scene is built by scripts on top of it.

## Branch inventory (checked 2026-10-31, ~23:45 CT)

| Branch | Tip | vs `main` | Owner / content | Approval status |
|---|---|---|---|---|
| `round3` | `cec81c4` | +7 / −2 | Room session: edits e01–e07 (tapes/VCR, pothos, IBM corner, left zone + dresser, CRT bezel/VCR, right nook, warm light), OIDN lightmap denoise, `look-controls.js`, `tapes.json`, camera tests | Previews sent; **not recorded as approved** |
| `components/detailed-assets` | `6072b86` | +3 / 0 | Component session A: `desk` (built, exported, "awaiting approval"), `crt` (WIP: script + before shots, no export) | Desk awaiting; CRT unfinished |
| `components/detail-assets` | `cbb9a41` | +2 / 0 | Component session B: `window_view` (Berlin rail-yard photo backdrop, GLB exported) | **Awaiting approval** |
| `round2` | `97ad1a9` | — | Fully contained in `round3` | Merge via `round3` only |
| `release-camera` | `59c2bd1` | — | Already in `main` | Nothing to merge |

## Dry-run merge results (local scratch worktree, not pushed)

Order: `main` ← `round3` ← `components/detailed-assets` ← `components/detail-assets`.

| File | Conflict | Resolution plan |
|---|---|---|
| `pipeline/tests/camera_controls_test.py` | add/add, 9 hunks (main 174 lines = preview copy; round3 186 lines) | Take round3's version (newer, tests the orbit camera); confirm both preview and room checks still run |
| `components/README.md` | add/add, 2 hunks | Combine: shared layout + one table listing all components and both sessions' conventions |
| `components/.gitignore` | add/add, 1 hunk | Union of rules, **minus** `*/export/*.blend` (it would hide the desk's committed `desk_source.blend`) |

All other files merge cleanly.

## Overlaps git does not detect (decisions needed)

1. **CRT built twice.** `round3` `e05_crt_vcr.py` rebuilds the CRT bezel/housing in the room; `components/crt`
   rebuilds the same CRT from the v17 geometry. Applying both gives two CRTs. Need one owner:
   keep e05 (already in the room, previewed) **or** replace it with the component when it is finished.
2. **Window: three versions of "outside".** `main`/live uses `sakina-outside.glb` (3D city); `round3` adds a
   sky sphere and lowers the city 10 m; `window_view` replaces both with the photo backdrop and is placed for the
   round-3 opening camera. Integrate `window_view` only after `round3`, and only if Sakina prefers the photo.
3. **Two `components/_lib` conventions** (A: `common/materials/preview/woodgrain`, Z-up, `build_<name>.py`;
   B: package with `pbr/studio/export`, runner `components/build.py`). File names do not clash; both build
   scripts must be re-run after the merge to prove imports still work.
4. **Window-group lighting.** The window frame/sill lightmap was baked against a black sky; the photo backdrop
   is brighter. Include the backdrop as an emissive object in the unified scene so the GPU bake picks it up.

## Integration sequence (after approvals)

1. Merge approved branches into `integration/v3-master` in the order above; resolve conflicts as listed.
2. Add room edits for approved components, numbered after round 3:
   - `e08_desk_detail.py` — delete the 43 `Desk_*` meshes, append from `components/desk/export/desk_source.blend`,
     link into `Desk`, translate (0.20, 1.65, 0). Props stay at z = 0.720.
   - `e09_window_view.py` — emissive backdrop in the `Window` area for bake/preview (web asset handled separately).
   - CRT: per decision 1.
3. `python3 pipeline/build_scene.py` → unified `v3-integrated.blend`.
4. Scene checks (scripted, reported with numbers): duplicate names/meshes, objects without a bake collection,
   floating objects (gap > 2 mm above the support below), intersections (BVH overlap of desk props and furniture),
   scale (bounding boxes vs. spec), missing/absolute texture paths, material count per bake group,
   camera and light objects unchanged vs. `round3`.
5. Lightmap readiness: generate and save the `Lightmap` UV layer per group (same settings as
   `bake_lightmaps.unwrap`), report UV coverage and overlaps; keep all lights and bake settings.
6. Quick previews: `render_preview.py` at low samples (home, tapes, orbit ±55°) — clearly labelled
   "unbaked preview".
7. Portable bake package (below), tested here on CPU at tiny size for one group to prove the script runs.
8. Report: integrated list, issues list, branch + SHA, previews. Then Sakina approves before any bake.

## Portable GPU bake package (planned contents)

```
v3-bake-kit/
  scene/v3-integrated.blend      all images packed (no absolute or cloud paths)
  pipeline/                      bake_lightmaps.py, bake_group.py, fix_baked21.py, export_web.py, tools/oidn.py
  run_bake.py                    Blender-run entry point; DEVICE=OPTIX|CUDA|CPU, SPP, groups, output folder
  bake_config.json               groups, resolutions, samples, denoise, version pins
  README-BAKE.md                 step-by-step for Windows/Linux, expected outputs, how to send results back
  MANIFEST.txt                   file list + SHA-256
```

Changes needed in the bake code (integration branch only):
- `bake_lightmaps.py` hard-codes `device = 'CPU'` → read `DEVICE`, enable OptiX/CUDA in Cycles preferences,
  fall back to CPU with a printed warning.
- `tools/oidn.py` only finds the Linux `libOpenImageDenoise.so` next to the pip `bpy` wheel → add Windows/macOS
  library names and the desktop Blender install path, or use Blender's compositor Denoise node instead.
- Run inside desktop **Blender 5.2.x** (`blender -b scene.blend --python run_bake.py`), not pip `bpy`.
- Output: one lightmap PNG per bake group + a baked `.blend`; the GLB export/splice stays in this pipeline
  after the bake is returned.
