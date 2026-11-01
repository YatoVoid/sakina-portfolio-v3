# Room refresh — desk props, window, curtains, poster

Request (Sakina, 2026-11-01): make the remote, calculator, notebook and lamp look really real (texture and
geometry); window with only the vertical line (remove the horizontal bar) and a realistic handle; plain
white curtains, more curved at the bottom; the blue poster off the curtain, on the wall right of the curtain.

Built on the approved scene (`integration/v3-master`: main + e01 tapes + e08 desk + e09 window view).
`apply.py` has the shape of a pipeline edit (`apply()`); each part is its own module in `parts/`.

| Part | Replaces | Bake group | What changed |
|---|---|---|---|
| `window.py` | Frame_L/R/Top, Mullion_H/V, Glass, Handle_* | Window | Outer frame + trim, two casement sashes meeting at **one vertical stile** with a cover strip (no horizontal bar), glazing beads, two panes (`Glass_L/R`, still skipped by bake/export), 4 brass hinges, brass window handle (rosette, slotted screws, neck, curved lever). Sill kept. |
| `curtains.py` | Curtain_L/R | Room | Plain warm-white cotton (sheen, light translucency, weave bump), 2.2× fullness, folds that deepen toward the floor, bottom 38 cm curves into the room and breaks on the floor, inner edge flares. New rod with rings, finials, brackets (there was no rod). Same footprint. |
| `poster.py` | (moves Poster*) | Room | Off the curtain onto the wall surface right of it. That surface is the wooden post `Wood_Post` (30 cm); the plaster beyond it is 13 cm, too narrow. Poster taped flat on the post face, scaled 0.92. |
| `lamp.py` | Lamp_* except Lamp_Bulb | Lamp | Cast domed enamel base, rubber foot, rocker switch, ribbed chrome gooseneck, spun shade with rolled rim, white interior, vent slots, socket, power cord. **Bulb object and position kept** (room lights / round-3 e07 depend on it); names e07 looks up are reused. |
| `remote.py` | Remote (+buttons) | Tapes | Tapered soft body, mould seam, IR window, raised rubber keys (power, eject, 12-key pad, transport cluster, channel rocker), printed legends. |
| `calculator.py` | Calculator (+keys, LCD) | Desk | Wedge body, faceplate, recessed LCD with seven-segment digits, solar strip, 25 bevelled keys with legends on the slope. |
| `notebook.py` | Notebook (+lines, pages) | Desk | Open leather notebook: two page blocks curving into the gutter, layered page edges, ruled paper with pencil handwriting (`handwriting.py`, illegible generated strokes), red ribbon, elastic band. Detailed pencil kept. Still the site's "Currently" notepad spot. |

Previews: `render_room.py` — Cycles with the room's own lights (what the lightmap bake sees), before vs after.

## Integration (after approval)

1. On the integration branch: `pipeline/edits/eNN_room_refresh.py` = thin wrapper calling
   `components/room_refresh/apply.py: apply()`; append to `EDITS` after `e09_window_view`.
2. Re-bake groups **Window, Room, Lamp, Desk, Tapes**; splice; new GLB filename; publish to `/preview/`.
3. Round 3 compatibility: `Lamp_Bulb` unchanged; e07's `Lamp_*` name lookups still match; plant keep-out boxes
   (lamp base, calculator) unchanged footprints; curtain footprint unchanged for e04's keepsakes layout.
