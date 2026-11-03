# GPU bake local test (2026-11-02)

Bake: OptiX, 256 spp, 42.8 min, 12 groups, no OIDN. Source files stay in `~/Downloads/v3-bake-kit/out/` (backup of the .blend and PNGs in `~/Downloads/v3-bake-backup/`).

## Bake check
- All 12 groups (Room, Window, Desk, Station, Monitor, Tapes, Keepsakes, Lamp, Plant, Right_Nook, Wall_Decor, Floor) have a PNG, an EXR, a `Baked_*` material and a `Lightmap` UV set on every object.
- No PNG is empty or saturated. No missing or external files (all images packed; stale `/home/claude/...` paths are only metadata).
- `No mesh data to join` for Floor: the group has one object (`Floor_Planks`, 785 polys), nothing to join. `lm_Floor.png` is valid.
- PNGs are encoded through the scene's Filmic Low Contrast view transform (same as the live site's bake), so Three.js shows them with `NoToneMapping`.

## Pipeline used (unchanged repo scripts)
`fix_baked21.py` -> `export_web.py` -> `compress_glb.mjs`. `web/gpu-test.html` + `main-gpu1.js` load `sakina-room-gpu1.glb` (raw bake). `gpu-test2.html` + `main-gpu2.js` load `sakina-room-gpu2.glb` (denoised). `main.js` and `index.html` are untouched.

## Finding: grain
Lightmaps are noisy (256 spp, bake not denoised). Visible on walls, curtains, floor. Fix without rebaking: OIDN on the existing EXRs (`pipeline/tools/denoise_lightmaps.py`, ~8 s per group), re-encode with the same view transform (control re-encode of Room matched the original PNG exactly), swap into the .blend (`swap_lightmaps.py`), re-export. Albedo guide was not available, so fine wallpaper texture is smoother. Tape and notepad text stays legible.

## Browser (Chromium, RTX 3050 via PRIME offload)
60 fps, worst frame 16.8 ms, no console errors, no failed requests. Tape click, T/I/N/Z/Esc, drag limits and zoom limits work.

## Not caused by this bake (also on the live site)
- Black rectangles on tape label windows.
- Dark upper window panes (photo does not cover them).
- Armchair cushion reads as wood grain.

Run: `node pipeline/tests/gpu_bake_tour.mjs <url> <prefix>` (needs `playwright`).
