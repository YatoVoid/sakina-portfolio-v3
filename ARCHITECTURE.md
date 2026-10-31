# Architecture

## Website (`web/`, deployed by Netlify from `main`)

- `index.html` — import map: `three@0.160.0` from jsDelivr (`three`, `three/addons/`). Loads `main.js?v=N`.
- `main.js` — baked-scene viewer (V2 logic):
  - `WebGLRenderer`, `NoToneMapping`, sRGB output. **No lights**: all lighting is baked into each material's
    emissive lightmap, so colours on screen are the Cycles bake.
  - Loads `sakina-room-baked.glb` (Draco; decoder from three@0.160.0 `examples/jsm/libs/draco/gltf/`) and
    `sakina-outside.glb` (city, cars, trains; emissive).
  - Camera: `PerspectiveCamera(46°, near 0.05, far 7000)` — the city spans ~2–6 km.
  - `OrbitControls`: free orbit + pan + zoom (min 0.5, max 12), damping; mouse parallax via `setViewOffset`.
  - Views/flights (`VIEWS`, `flyTo`): home, tapes, ibm, notepad, desk. Keys T / I / N / Z / Esc + HUD buttons.
  - Picking (`pick`): raycast against `Room_Tapes`, `Room_Station`, `Room_Desk`; tapes open project panels.
  - Panels: project pager (prev/next), IBM "About and contact", notepad "Currently", credits.
- `content.js` — projects, IBM, notepad, credits text. `audio.js` — rain + lo-fi (Web Audio).
- `netlify.toml` — `*.glb` immutable 1 year (**rename on every change**); `*.js`/`*.css` revalidate.

## Room model

`sakina-room-baked.glb` = 11 merged meshes, one per bake group, each with a baked lightmap (JPEG) on an
emissive-only material: `Room_Desk, Room_Keepsakes, Room_Lamp, Room_Monitor, Room_Plant, Room_Right_Nook,
Room_Shell, Room_Station, Room_Tapes, Room_Wall_Decor, Room_Window`.

Bake groups = Blender collections. Notable contents:
- `Tapes`: 13 tapes (`Tape_*` left stack, `PTape_1..7` right stack), phone, cassette recorder (`Rec_*`),
  remote, floppy, papers, ID card.
- `Monitor`: CRT (`CRT_*`), VCR (`VCR_*`), screen content (`Scr_*`), cables.
- `Station`: IBM PC corner (`Station_Root`) and white chair.
- `Desk`: desk, notepad (`Pad`), note stack.

## Pipeline (`pipeline/`)

```
assets/sakina-v17.blend (source, never edited)
  -> bake/sakina_v19.py, bake/sakina_v20.py        V2 lighting + material passes
  -> edits/eNN_*.py  (build_scene.py applies them in order)
  -> bake/bake_lightmaps.py   (COLS=<groups>, SPP=192; CPU)
  -> bake/fix_baked21.py -> bake/export_web.py
  -> gltf-transform draco (--quantize-texcoord 16) -> web/<new-name>.glb
```
`bake/*` are copies of V2's scripts (provenance in each header), changed only for paths and CPU.
Parity check (2026-10-31): CPU re-bake of the Lamp group at 1024 px / 192 spp matches the shipped lightmap
(brightness ratio 1.001, mean difference 1.4/255). Low sample counts (32 spp) come out ~14% brighter — always
use 192. Timing: Lamp group (23 meshes) 348 s; 4096 px groups are estimated at ~1.5 h each on 2 CPUs.

## Testing

- `pipeline/tests/tape_click_test.py` — serves `web/`, clicks the centre of every tape spine, checks the panel.
- `pipeline/render_preview.py` — Cycles previews in the site's framing.
- Published-site checks: built-in browser on Sakina's laptop (content check of served files, screenshots,
  console, interactions).
