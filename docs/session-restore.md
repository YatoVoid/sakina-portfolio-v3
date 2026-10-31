> **Superseded (2026-10-31):** this describes an earlier concept/setup. The approved room is the live baked night scene — start from `CLAUDE.md`, `PROJECT_VISION.md` and `ARCHITECTURE.md`. Kept for history.

# V3 Session Restore Guide

Every cloud session starts from a blank container. This guide gets V3 back to a working state in about 3 minutes.

---

## Step 1 — Clone the repository

```bash
git clone https://github.com/sakina-saifuddin/sakina-portfolio-v3.git /home/claude/v3
cd /home/claude/v3
```

This restores:
- All web source files (`web/`)
- Pipeline scripts (`pipeline/`)
- Documentation (`docs/`)
- `.gitignore` and `README.md`

**Not restored** (excluded by `.gitignore`, must be rebuilt or re-copied):
- `assets/models/*.glb` — rebuild with pipeline
- `assets/previews/*.png` — rebuild with pipeline
- `assets/images/` and `assets/resume/` — copy from V2 via device bridge

---

## Step 2 — Install bpy (Blender Python package)

```bash
pip install bpy==5.2.3 --break-system-packages
```

Verify:
```bash
python -c "import bpy; print(bpy.app.version_string)"
# Expected: 5.2.3 (or similar)
```

---

## Step 3 — Rebuild GLB assets

```bash
cd /home/claude/v3
python pipeline/build_model.py all
# Outputs: assets/models/{desk,monitor,tv,vhs-rack,chair,lamp,bookshelf,room-shell,props}.glb
```

To also render 320×240 preview PNGs (adds ~8 s):
```bash
python pipeline/build_model.py all --preview --samples 32
```

---

## Step 4 (optional) — Compress GLBs

Requires Node.js (pre-installed in most cloud containers):
```bash
npm install -g @gltf-transform/cli
bash pipeline/compress_assets.sh
# Outputs: assets/models/*.compressed.glb
```

---

## Step 5 — Copy V2 assets (requires desktop app)

V2 assets live on the user's Windows machine at:
```
C:\Users\sakin\Downloads\v2\v2\sakina-portfolio\public\
```

They cannot be downloaded from the internet — they must come through the Claude desktop app's device bridge.

**To copy them:**
1. Open this session in the Claude desktop app on the Windows machine.
2. In the chat, ask: "Copy V2 assets to /home/claude/v3/assets/"
3. The session will use `mcp__remote-devices__device_stage_files` to transfer them.

Assets needed:
- `public/images/` → `assets/images/`
- `public/resume/` → `assets/resume/`
- `public/logos/` → `assets/images/logos/`
- `public/certs/` → `assets/images/certs/`

---

## Step 6 — Verify the preview

The Three.js preview artifact is always available at:
```
https://claude.ai/artifact/VjgVeoT8PVN1fUDzrL1UNy
```

This uses placeholder geometry and CDN-hosted Three.js — it works without any local files.

To test with real GLB assets, publish a new artifact or serve locally:
```bash
cd /home/claude/v3/web
python -m http.server 8080
# Open http://localhost:8080 (or use the built-in browser)
```

---

## Quick-reference: session state checklist

| Item | Where | Status after clone |
|------|-------|--------------------|
| `web/` source files | git | ✅ Restored |
| `pipeline/build_model.py` | git | ✅ Restored |
| `assets/models/*.glb` | gitignored | 🔄 Run Step 3 |
| `assets/previews/*.png` | gitignored | 🔄 Run Step 3 with `--preview` |
| `assets/images/` | gitignored | 🔄 Step 5 (device bridge) |
| `assets/resume/` | gitignored | 🔄 Step 5 (device bridge) |
| bpy installed | pip | 🔄 Run Step 2 |
| Three.js artifact | claude.ai | ✅ Always live |

---

## What NOT to do in any session

- ❌ Do NOT modify `C:\Users\sakin\Downloads\v2\` (V2 source)
- ❌ Do NOT push to or modify https://askksakina.netlify.app (live V2)
- ❌ Do NOT commit credentials, API keys, or secrets
- ❌ Do NOT commit `.glb`, `.png`, or large binary files (gitignored)

---

## Picking up where you left off

The session's conversation history is compacted between sessions. To resume design work:

1. Complete Steps 1–3 above.
2. Tell the new session: _"We're building V3 of my 3D portfolio. The repo is cloned at /home/claude/v3. Here is where we left off: [paste last status from previous session]."_
3. Reference this guide for any restore questions.

The architecture document and all source code are in the repo — a new Claude session can read them and continue the work without needing the previous conversation.
