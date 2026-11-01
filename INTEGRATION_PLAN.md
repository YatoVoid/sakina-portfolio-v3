# Integration plan — Sakina Portfolio V3 (master integration session)

Branch: `integration/v3-master` (cut from `main` @ `57bdb1d`). Status: **desk, window view, mug + coaster, chair, the gallery wall and the new wall colour integrated; `round3` and its CRT are held (CRT not approved).**
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


---

## Status log

### Approvals received (Sakina, 2026-10-31 23:46 CT)

| Item | Decision |
|---|---|
| `components/detailed-assets` → desk | Approved |
| `components/detail-assets` → window_view | Approved |
| CRT | ~~Use the `round3` version~~ **Superseded 2026-11-01:** CRT is **not approved**; Sakina will decide later. No CRT change is integrated (`components/crt` and `round3` e05 both stay out) |
| `round3` | **In progress — not merged** (it also carries e01–e07 and the OIDN denoise / bake changes) |

### Stage 1 (done): desk + window view on top of `main`

- Merged `components/detailed-assets` and `components/detail-assets` into this branch. The only conflicts were
  `components/README.md` and `components/.gitignore`; both were combined without dropping content (the
  `*/export/*.blend` ignore rule was left out so the desk's source .blend stays trackable).
- `pipeline/edits/e08_desk_detail.py`: replaces the 43 `Desk_*` meshes with the 5 component meshes at (0.20, 1.65, 0).
- `pipeline/edits/e09_window_view.py`: adds the photo backdrop in a new, non-baked collection `WindowView`; its two
  images are packed in the .blend. `Outside` stays in the file (the photo sits in front of it).
- `pipeline/build_scene.py` `EDITS` is currently `e01, e08, e09`. **When `round3` is merged it must become
  `e01 … e07, e08, e09`** (round 3 owns e01–e07; resolve that one line by hand).
- Tools: `pipeline/tools/scene_check.py` (integrity report vs. a baseline) and
  `pipeline/tools/preview_integration.py` (low-sample unbaked previews).

Measured results (`previews/integration/scene_check_interim.json`, interim scene vs. the `main`+e01 baseline):

- Lights, cameras and render settings: **0 changes** (7 lights, 10 cameras, scene camera, engine, view transform).
- Desk: top surface 0.720 m (unchanged), footprint 2.90 × 0.70 m; all 37 props over the desk keep their exact
  previous gap to the top (0.0 mm; nothing floats). Worst new contact: `Rolodex_Base` sinks 0.08 mm into the top.
- Duplicates created by the edits: none. Every mesh is in exactly one collection. No external texture paths.
- Overlaps inside the new desk (frame/top, brass/frame, drawer box/frame) are joinery of the approved component.

Previews (unbaked Cycles, 24 samples, live scene lights — not the lightmap look): `previews/integration/`.

### Still to do

1. Merge `round3` when it is finished and approved; set `EDITS` as above; re-run build, checks and previews.
2. Lightmap UV layer + per-group UV coverage report (no group has the `Lightmap` layer in the source scene yet;
   the bake script creates it at bake time with `smart_project`).
3. Bake kit for the NVIDIA laptop (device selection, cross-platform OIDN, `run_bake.py`, manifest, README).
   Waits for `round3` because it changes `bake_lightmaps.py`.


### Stage 2 (2026-11-01): mug + coaster and chair

Sakina asked to integrate the mug/coaster and the chair and to see before/after of just those components; CRT ignored.

- Merged `components/detailed-assets` again (clean, no conflicts). It also carried later desk commits (final 2048 px bake
  and previews); `e08` uses `desk_source.blend`, so no change is needed.
- `pipeline/edits/e10_mug_coaster.py`: replaces `Mug`, `Mug_Handle`, `Coffee`, `Mug_Stain_A` with `Mug_Body`, `Mug_Coffee`,
  `Mug_Coaster` at (-0.2305, 1.3995, 0.720), rotZ 180°. `Mug_Stain_B` and `Steam` kept.
- `pipeline/edits/e11_chair.py`: replaces the `WhiteChair` empty + 17 `Chair_*` meshes with `Chair_Wood`, `Chair_Seat`,
  `Chair_Nails` in `Desk` at (-0.95, 0.90, 0), rotZ 158°.
- `EDITS` is now `e01, e08, e09, e10, e11`.

Checks (vs. the desk + window scene): lights, cameras and render settings 0 changes; no duplicates; no external textures.
Mug: coaster rests on the desk (0.0 mm), mug body seats 0.8 mm into the coaster, coaster clears the notebook by 4 mm and
`Note_Stack` by 38 mm. Chair: no overlap with the desk or any prop. The only new overlaps are inside the components
(chair wood/seat/studs, mug/coffee/coaster) and between the mug and the `Steam` effect mesh, which is skipped by the bake and
the web export.

### Open items that matter for the `round3` merge

- `round3` commit `cec81c4` includes a **chair recline** (it edits the old chair). `e11` asserts the old chair is at
  (-0.95, 0.90, 0) with rotZ -22°; after `round3` is merged it will fail until the recline is dealt with on purpose.
- The chair notes warn that the whitewash paint bakes much darker and warmer in the room than in the studio renders.
- Still unmerged and not approved: `round3` (incl. CRT), `components/detail-assets` `room_refresh` (WIP), `components/crt`.


### Stage 3 (2026-11-01): gallery wall above the IBM computer

Sakina's request (reference photo of a staggered canvas gallery wall): the frames above the IBM computer should follow that
layout and look realistic. Built here as an integration edit (no component branch involved).

- `pipeline/edits/e12_gallery_wall.py`: removes the 20 postcards (`Postcard_00..19` + photos, 40 objects) and adds
  `Gallery_Canvas_1..8` to `Wall_Decor`: two staggered rows copied from the reference (large landscapes in the middle,
  portraits between them), 2.5–3.5 cm deep gallery-wrap canvases with a 1.5 mm bevel, photo edge pixels wrapped over the sides,
  fine procedural canvas-weave bump, tiny fixed tilt (<= 0.25 deg). Photos are the ones already packed in the scene.
  The clock is kept. `EDITS` is now `e01, e08, e09, e10, e11, e12`.
- Measured: group 1.32 m x 0.63 m centred on the computer (y 0.59–1.91, z 1.13–1.77); gaps 15–30 mm; no overlaps; every canvas
  0.5 mm off the wall; 10.8 cm below the clock, 7.3 cm above the computer top; lights/cameras unchanged.
- Risk for the bake: `Wall_Decor` shares one lightmap with other decor (2048 px unless the bake config says otherwise), so photo
  sharpness on the canvases depends on that resolution; consider a higher `Wall_Decor` size for the GPU bake.
- `round3` conflict: its `e04_left_zone.py` rebuilds the postcards and clock and moves the left wall in to x = -2.30. After that
  merge `e12` will fail its postcard assertion and must be re-targeted to the new wall position.


### Stage 4 (2026-11-01): wall colour of the whole room

Sakina's request: all walls should be the wall colour of her reference photo (warm cream plaster, vintage framed gallery wall).

- `pipeline/edits/e13_wall_colour.py`: sampled the reference wall in four regions away from shadow/sun patches: sRGB (207, 197, 183)
  = #CFC5B7 (regions #CEC4B5 .. #D1C7B9). All 7 wall meshes share the material `WallPlaster`, so one material change covers the room.
- The old material was near-black over most of the wall (a height blend toward (0.024, 0.015, 0.009) is already 1.0 below z = 2.2 m).
  New: mottling around the reference colour, soft stains (x0.78), shade only near the ceiling (above 2.45 m) and floor (below 0.35 m).
  Noise patterns, bump and roughness unchanged. Ceiling, floor, baseboards and window paint untouched.
- Checks: lights/cameras 0 changes, no new overlaps. `EDITS` is now `e01, e08 .. e13`. This edit only changes a material, so it
  also works after the `round3` merge.
- Effect on lighting: lighter walls bounce much more light, so the room gets noticeably brighter and less moody with the same lights.
  Lights were not changed (they are preserved for the bake). The lit wall in the preview is (83, 70, 58) in a dim area, i.e. darker
  and warmer than the daylight photo; judge the final look after the GPU bake.


### Approvals log (update 2026-11-01 10:39 CT)

| Item | Status |
|---|---|
| Desk (e08) | Approved 2026-10-31 |
| Window view (e09) | Approved 2026-10-31 |
| Wall colour (e13) | **Approved 2026-11-01** (Sakina: "Approved", right after the before/after) |
| Mug + coaster (e10), chair (e11), gallery wall / frame layout (e12) | **Approved 2026-11-01 10:41 CT** |
| CRT, `round3` | Not approved, not merged |

**Approved set (2026-11-01 10:41 CT):** desk, window view (city life behind the window), mug + coaster, chair, wall colour, gallery-wall frame layout.
Pushed to `integration/v3-master` only. `main` and the live site are unchanged until the final integration is approved.
