# V3 Room Blueprint — Master Specification

**Single authoritative reference for all agents and sessions.**  
All component builders must read this before touching geometry.

---

## Concept

**"Cinematic vintage graduate study, 1997 — golden hour"**

A lived-in graduate student's room at dusk. Warm amber sunset floods through a large back-wall window onto a cluttered wooden desk. Two vintage CRT computers sit on the desk. A TV+VCR with interactive project tapes occupies the left wall. Academic books, posters, and certificates cover every surface. The mood is warm, dark, and specific — not a museum, not a dorm cliché.

Reference images: `docs/ref-warm-mac-desk.jpg` (lighting, desk, window) + `docs/ref-90s-pc-room.jpg` (poster density, tech clutter)

---

## Room Dimensions

| Property | Value |
|----------|-------|
| Width (X) | 6.0 m |
| Depth (Y) | 7.0 m |
| Height (Z) | 3.2 m |
| Coordinate origin | Floor centre |
| +X direction | Right |
| +Y direction | Front (toward camera) |
| +Z direction | Up |
| Back wall Y | −3.5 |
| Front (open) Y | +3.5 |
| Left wall X | −3.0 |
| Right wall X | +3.0 |

---

## Object Registry

Every object must match this placement exactly. Tolerances: ±0.02 m.

### Room Shell
| Object | Centre (X, Y, Z) | Scale (half-extents) | Material |
|--------|------------------|----------------------|----------|
| Floor | (0, 0, 0) | (3.0, 3.5, 0.03) | Dark oak `#1c1108` |
| Back wall | (0, −3.5, 1.6) | (3.0, 0.05, 1.6) | Dark brown `#120e09` |
| Left wall | (−3.0, 0, 1.6) | (0.05, 3.5, 1.6) | Dark brown `#120e09` |
| Right wall | (3.0, 0, 1.6) | (0.05, 3.5, 1.6) | Dark brown `#120e09` |
| Ceiling | (0, 0, 3.2) | (3.0, 3.5, 0.03) | Near-black `#0a0806` |

### Window (Back Wall — centred)
| Property | Value |
|----------|-------|
| Centre | (0, −3.45, 1.5) |
| Width | 1.6 m (half: 0.8) |
| Height | 1.1 m (half: 0.55) |
| Frame material | Warm wood `#261507` |
| Glass material | Emissive amber `#ffd090`, strength 4.0 |
| Mullion | Vertical centre cross |

### Main Desk (filing-cabinet style, front-centre)
| Property | Value |
|----------|-------|
| Desk top centre | (0, −2.2, 0.76) |
| Desk top size | 1.5 m wide × 0.65 m deep × 0.04 m thick |
| Left cabinet | (−0.55, −2.2, 0.38) — 0.22w × 0.60d × 0.38h |
| Right cabinet | (0.55, −2.2, 0.38) — 0.22w × 0.60d × 0.38h |
| Drawer pulls | Brass `#8a6a20` cylinders, 3 per cabinet |
| Wood colour | `#2d1a09` desk top, `#1a0e06` cabinets |
| One drawer | Right cabinet, top drawer offset +0.04 Y (slightly open) |

### Main Computer — Left of desk centre
| Property | Value |
|----------|-------|
| Monitor body centre | (−0.28, −2.15, 0.97) |
| Monitor size | 0.32w × 0.28d × 0.30h (cream beige `#d8c8a0`) |
| Screen face | Slightly recessed, dark green-black `#001a10`, emissive teal `#1a4060` str 1.5 |
| Neck/stem | (−0.28, −2.15, 0.78) cylinder r=0.04 h=0.06 |
| Base | (−0.28, −2.15, 0.77) box 0.18w × 0.14d × 0.02h |
| Keyboard | (−0.28, −1.98, 0.78) box 0.28w × 0.12d × 0.02h, cream `#c8b880` |

### Second Computer — Right of desk centre
| Property | Value |
|----------|-------|
| Monitor body centre | (0.42, −2.15, 0.92) |
| Monitor size | 0.28w × 0.24d × 0.26h (grey beige `#c0b090`) |
| Screen face | Dark, emissive blue `#003366` str 0.8 |
| Keyboard | (0.42, −1.98, 0.78) box 0.24w × 0.10d × 0.015h, grey `#a8a090` |
| Tower / CPU box | (0.75, −2.15, 0.88) box 0.12w × 0.28d × 0.38h, beige `#b8a880` |

### Desk Lamp
| Property | Value |
|----------|-------|
| Base | (−0.62, −2.10, 0.77) cylinder r=0.06 h=0.01 brass `#8a6a20` |
| Arm | (−0.62, −2.10, 0.94) box 0.01w × 0.01d × 0.18h brass |
| Head | (−0.62, −2.07, 1.06) box 0.08w × 0.06d × 0.06h dark `#1a0e06` |
| Bulb (emissive) | cylinder r=0.02 h=0.02 inside head, `#ffc840` str 6.0 |

### Rug
| Property | Value |
|----------|-------|
| Centre | (0, −1.2, 0.01) |
| Size | 2.4w × 1.8d |
| Base colour | Dark red `#3a1a0a` |
| Pattern overlay | Slightly lighter `#6a2808`, 0.002 above base |

### TV + VCR (Left wall)
| Property | Value |
|----------|-------|
| Shelf centre | (−2.6, −1.8, 0.85) — 0.7w × 0.30d × 0.03h, wood `#261507` |
| TV body | (−2.6, −1.8, 1.05) — 0.42w × 0.22d × 0.28h, black `#0d0d0d` |
| TV screen | Slightly forward, emissive blue `#0044aa` str 0.8 |
| VCR | (−2.6, −1.8, 0.90) — 0.32w × 0.20d × 0.08h, dark grey `#1a1a18` |
| VHS tapes | 7 tapes in rack below shelf, each ~0.03w × 0.11d × 0.09h |
| Tape rack | (−2.6, −1.8, 0.70) — shelf-mounted |

### Tape labels (VHS = portfolio projects)
| Slot | Label | Colour accent |
|------|-------|---------------|
| 0 | DENTAL-X | `#200808` dark red |
| 1 | HOUSING AI | `#082008` dark green |
| 2 | FLOOD CAST | `#080820` dark blue |
| 3 | POWERGUARD | `#201008` dark orange |
| 4 | WARMTHREAD | `#0a0818` purple |
| 5 | SUMUS | `#181808` olive |
| 6 | RESUME | `#1a1a1a` near-black |

### Bookshelf (Right wall)
| Property | Value |
|----------|-------|
| Back panel | (2.65, −1.0, 1.0) — 0.04w × 0.45d × 1.0h, wood `#261507` |
| 3 shelves | At Z = 0.35, 0.75, 1.15 — 0.30w × 0.45d × 0.02h |
| Books | 5–7 per shelf, varied widths 0.025–0.05m, heights 0.12–0.18m |
| Book colours | Rotate: `#4a1a0a`, `#0a2a1a`, `#1a1a3a`, `#2a0a2a`, `#3a2a0a` |

### Posters / Certificates (Back wall, sides of window)
| Object | Position | Approx size |
|--------|----------|-------------|
| Certificate (cream) | (−1.7, −3.45, 2.5) | 0.45w × 0.35h |
| Hackathon poster (dark red) | (−1.3, −3.45, 1.8) | 0.38w × 0.55h |
| Dark game poster (navy) | (−2.0, −3.45, 1.6) | 0.32w × 0.48h |
| Certificate right | (1.7, −3.45, 2.4) | 0.42w × 0.32h |
| Tech poster (dark green) | (1.4, −3.45, 1.7) | 0.35w × 0.52h |
| Retro poster (dark blue) | (1.9, −3.45, 1.4) | 0.30w × 0.44h |

### Surface Clutter (Desk)
- Papers: stack at (0.20, −2.05, 0.785), slightly fanned
- Mug: (0.55, −2.10, 0.82) cylinder r=0.035 h=0.09
- Floppy disk: (0.05, −1.95, 0.781) flat box
- Sticky notes: small coloured boxes on monitor bezel

### Floor Clutter
- 3× CDs: cylinders r=0.065 h=0.002, scattered near desk chair
- 2× floppy disks near TV area

### Chair
| Property | Value |
|----------|-------|
| Seat | (0, −1.60, 0.45) — 0.48w × 0.45d × 0.04h, wood `#2d1a09` |
| Seat pad | Same XY, 0.005 above seat, dark fabric `#4a1a1a` |
| Back | (0, −1.82, 0.70) — 0.46w × 0.03d × 0.45h, wood |
| 4 legs | Corners at ±0.20, ±0.18 from seat centre, height 0.45m |

---

## Lighting

| Light | Type | Position | Energy | Colour |
|-------|------|----------|--------|--------|
| Window sun | Point | (0, −3.2, 1.5) | 2800 | `#ffd090` |
| Window bounce | Point | (−1.0, −2.5, 1.8) | 350 | `#e8a840` |
| Desk lamp | Point | (−0.62, −2.07, 1.08) | 90 | `#ffc840` |
| Monitor glow | Point | (−0.28, −1.95, 0.97) | 18 | `#1a6080` |
| TV glow | Point | (−2.6, −1.6, 1.05) | 22 | `#0044aa` |

**Ratio: 70% warm amber window : 20% desk lamp : 10% cool monitor/TV**

World background: `#06040a`, strength 0.0 (pure black — window punches hard)

---

## Camera

### HOME view (Three.js default)
| Property | Value |
|----------|-------|
| Position | (0.3, 2.8, 1.55) |
| Target | (0, −1.5, 0.9) |
| FOV | 52° |
| Blender lens | 28 mm |
| Rotation | pitch ~78°, yaw ~178° |

### Blender preview camera
Same as HOME view. Orient so desk is centred, window visible behind monitors, TV visible left, bookshelf right.

---

## Visual Standards (all agents must follow)

1. **No pure white** — everything has a warm tint. Lightest colour is cream `#e8d8b0`.
2. **No pure black shadows** — deepest shadow is `#06040a`.
3. **sRGB conversion** — all hex values go through `hex_to_linear()` before assigning to Blender materials.
4. **Roughness** — wood 0.75–0.85, metal 0.25–0.40, plastic 0.55–0.70, fabric 0.95–0.99.
5. **Scale** — desk height 0.76 m, monitor centre ~0.97 m, chair seat 0.45 m. These are locked.
6. **Emissive screens** — never pure white. Monitor: teal/blue. TV: deep blue. Both very dim.
7. **No IKEA-clean** — slightly offset books, one open drawer, papers not perfectly stacked.

---

## File Conventions

| Component | Agent | GLB output |
|-----------|-------|------------|
| Room shell + window | shell-agent | `assets/models/room-shell.glb` |
| Desk + chair | desk-agent | `assets/models/desk.glb` |
| Main computer (left) | computer-agent | `assets/models/computer-main.glb` |
| Second computer (right) | computer-agent | `assets/models/computer-secondary.glb` |
| Desk lamp + clutter | props-agent | `assets/models/desk-props.glb` |
| TV + VCR + VHS rack | tv-agent | `assets/models/tv-setup.glb` |
| Bookshelf | shelf-agent | `assets/models/bookshelf.glb` |
| Rug | props-agent | `assets/models/rug.glb` |
| Posters / wall dressing | props-agent | `assets/models/wall-dressing.glb` |

All agents write **only their assigned file**. Never write to another agent's file.  
Blueprint version: **1.0** — do not deviate without coordinator approval.

---

## Three.js Performance Targets

| Metric | Target |
|--------|--------|
| Total GLB budget | < 4 MB compressed |
| Draw calls | < 120 |
| Polygons | < 80 k |
| Target FPS | 60 fps on mid-range laptop |
| Texture maps | None for MVP — procedural materials only |

---

## Integration Order

1. Shell + window (sets lighting anchor)
2. Desk + chair (primary interactive zone)
3. Computers (DESK hotspot)
4. TV + VHS (TV hotspot)
5. Props, rug, clutter, wall dressing
6. Final lighting pass + camera polish
