# Window view — Berlin rail yard at night

Sakina's photo (2026-10-31): `refs/berlin-railyard-night.jpg`, 2576 × 1718. Request: "This view should be
outside my window."

## Reference analysis

| Item | Value | Status |
|---|---|---|
| Horizon (photographer's eye level) | row 960 — rails converge at ≈ (1080, 960) | measured |
| Camera height above the tracks | ≈ 4.7 m (rail gauge 1.435 m = 232 px, 758 px below the horizon) | measured |
| Photo pitch | ≈ 1.8° up (horizon 101 px below centre) | derived |
| Field of view used | 43.8° across (focal 3200 px) | chosen for framing |
| Lighting | overcast night, sodium-orange lamps, neutral grey sky glow, fine grain | observed |
| Content | Mercedes-Benz Arena building and cranes (left), tracks to a central vanishing point, Ostbahnhof hall + METRO signs (right), TV tower (right), apartment blocks | observed |

## Build

- `view.py` — placement. Centre = round-3 opening camera eye, three.js (−0.02, 1.12, −0.25). Photo centre
  2.5° left of straight ahead; horizon **4° above eye level** (skyline sits in the lower window panes, just
  above the CRT, clear of the window's crossbar; cranes and TV tower rise into the upper panes).
- `build.py` — two meshes, emissive only (same model as the baked room, so colours on screen equal the photo):
  - `WindowView_Photo`: the photo at native resolution on the cylinder patch its pixels cover (r = 79.75 m).
  - `WindowView_Pano`: 170° × 105° cylinder (r = 80 m) + caps with a 2048 × 1024 extension panorama.
- `panorama.py` — extension beyond the photo's frame: mirrored in angle space (ground stays ground, sky stays
  sky), progressively blurred and darkened, sky gradient continued upward, even dark ground below, matching grain.
- Output `export/window_view.glb`: 2.54 MB, 33 k triangles, 2 JPEG textures. `gltf-transform validate`:
  0 errors, 0 warnings (1 info: non-power-of-two photo, fine in WebGL 2).

## Preview (real room, not a mock-up)

`preview/room_preview.py` renders the **live** baked room (`web/sakina-room-baked.glb`) the same way
`web/main.js` does (unlit, NoToneMapping, sRGB) in headless Chromium, before (current 3D city) vs. after.
Views: opening camera, live home camera, orbit ±50–55°, raised orbit, phone portrait. Console errors: none.
Screenshots: `previews/*_compare.jpg` (top/left = before, bottom/right = after).

Known limits:
- From high orbit angles the camera looks below the photo's lower edge and sees only the dark extension.
- The room's lightmaps were baked with the old black sky; the new grey sky glow is slightly brighter, so the
  window frame/sill lighting is not re-matched (optional re-bake of the Window group).
- Placement is tuned for the round-3 opening camera; if that camera moves, change `CENTRE_THREE` and rebuild.

## Integration (after approval — touches files owned by the room session)

1. Copy `export/window_view.glb` to `web/window-view-berlin-v1.glb` (new filename: GLBs are cached immutably).
2. In `web/main.js`, load `window-view-berlin-v1.glb` instead of `sakina-outside.glb`, with **no** position
   offset (round 3 lowers the city by 10 m — that must not apply here). The round-3 sky sphere is fully hidden
   behind the backdrop and can be removed.
3. Bump `main.js?v=N`, publish to `/preview/`, verify on the real site, then promote after approval.
