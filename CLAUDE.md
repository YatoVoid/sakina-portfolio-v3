# CLAUDE.md — Sakina Portfolio V3

Read this first in every session, then `PROJECT_VISION.md`, `ARCHITECTURE.md`, `PROGRESS.md`, `DECISIONS.md`.
The older files in `docs/` (`room-blueprint.md`, `design-brief.md`, `session-restore.md`) describe an earlier
golden-hour concept and are **superseded** — do not build from them.

## Hard rules

- **Never modify V2** (`C:\Users\sakin\Downloads\v2\` on Sakina's laptop) or the original portfolio
  (https://askksakina.netlify.app). Reading V2 through the device bridge is fine.
- **Preserve the approved room** (live site, see PROGRESS.md for the last verified commit) and every working
  interaction. Change only the component being worked on.
- **Do not restart brainstorming or redesign the room.** The concept is chosen (PROJECT_VISION.md).
- **Test actual results before claiming success.** A Blender render finishing is not proof of realism; a push
  or "Published" on Netlify is not proof the site works.
- **Never deploy an unfinished experiment over the main page.** Candidates go to `/preview/` first; the main
  page changes only after approval. Rollback = `git revert`.
- Save all source files and decisions to this repo (PROGRESS.md / DECISIONS.md).

## Reference-driven workflow (per component)

A. Analyse the reference photo (geometry, dimensions, materials, what is certain vs. inferred).
B. Model it as a script in `pipeline/edits/eNN_<name>.py` (applied on top of the V2 lighting state; the source
   `assets/sakina-v17.blend` is never edited).
C. Cycles preview: `pipeline/render_preview.py` (before vs. after, site framing). Fix obvious differences, then
   show the preview and wait for approval.
D. Integrate: re-bake only the affected bake groups, splice them into the room GLB, keep everything else.
E. Publish to `/preview/`, verify on the real site, then promote to the main page after approval.
F. Report with screenshots of the actual published site (full room + close-up) and the live link.

## Environment facts (cloud session)

- Blender: `pip` package `bpy` 5.2.3 (`import bpy`). Cycles runs on CPU (2 cores). No GPU.
- The cloud shell **cannot reach** `*.netlify.app`, `cdn.jsdelivr.net`, Poly Haven, ambientCG, Sketchfab.
  It can reach GitHub (incl. raw files) and npm/PyPI.
- Local site tests mirror three@0.160.0 from npm (see `pipeline/tests/tape_click_test.py`).
- Verifying the **published** site needs a real browser that can reach Netlify: the Claude desktop app's
  built-in browser on Sakina's laptop (device bridge). If the laptop is off, report "published, not verified".
- Netlify deploys `web/` automatically from `main` (no build command). `*.glb` is cached immutably for a year:
  **every changed GLB needs a new filename**. JS/CSS revalidate; bump `main.js?v=N` in `index.html` anyway.

## Commands

```bash
export V3_WORK=/tmp/v3work
python3 pipeline/build_scene.py                    # v17 -> v19 -> v20 -> all edits  => $V3_WORK/source/v3-edited.blend
SCENE_NAME=before python3 pipeline/build_scene.py --upto e00   # V2 state = what the live bake came from
python3 pipeline/render_preview.py <scene.blend> <out_prefix> 48   # home + tapes views, ~5 min each
python3 pipeline/tools/tape_layout.py <scene.blend> web/tapes.json
python3 pipeline/tests/tape_click_test.py web web/tapes.json      # clicks all 13 tapes, checks the panels
```
