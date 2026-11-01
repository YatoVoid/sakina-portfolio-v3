# Vintage TV ads for the CRT tapes

One ad per tape project, played on the CRT in the room. Built with Python (PIL + numpy) -> ffmpeg; audio is synthesised with numpy/scipy; voiceover is espeak-ng (robotic placeholder).
Only the `*_web.mp4` previews are committed (full-quality files are ~40 MB each; regenerate with the scripts).

## Style rules (from Sakina)
- Open with ONLY the project / company logo: a short, smooth animation (soft glow, slow rise, one light sheen). No title card.
- Told in the third person about Sakina ("Sakina built...", "She designed..."): the problem she met, the technologies she used, the hard part she solved, the impact.
- Facts only from the portfolio / README. Never invent numbers. "150+ professors" for Cost Center Verification was stated by Sakina (the portfolio text still says dev-only, update it).
- Background colours follow each project's theme (UH red, PowerGuard electric blue, housing teal/amber, flood blue, cost warm amber), never one plain grey.
- Sound is quiet (the Blender scene carries rain and city sound): soft e-piano/pad, tape hiss, faint signal dips, optional robotic narration. A no-voiceover version is always exported.
- 30-60 s depending on content. NO end card: picture and sound fade smoothly to black.

## Files
- `src/adlib.py` frame engine helpers; `src/adkit.py` logo intro + fade to black; `src/adaudio.py` soft audio builder (JSON config: durations, narration plan, cuts)
- `src/pg_ad4.py` PowerGuard 360, `src/cioh2_ad.py` Can I Own a Home?, `src/ccv3_ad.py` Cost Center Verification (+ `ccv3_audio.py`)
- `assets/` logos used. Fonts (Bebas Neue, DM Serif Display) come from github.com/google/fonts.
- Paths inside the scripts point at the cloud session's scratchpad (`SP=`) and `/home/claude/ask-sakina-portfolio/public/...`; change them before re-running.

## Render
`python3 <ad>.py part out.mp4 <startFrame> <endFrame>` (two halves in parallel), concat, mux with the wav (`-c:a aac`), then `scale=800:600 -crf 29` for the web file.
Narration lines are in the commit message history / the scripts' cfg json (`plan`) and were spoken by `espeak-ng -v en-us+m3 -s 182`.

## Open items
- Replace the robotic voice with a recorded or neural voice (same timings).
- Can I Own a Home?: README mentions a separate model team; confirm Sakina's exact role before publishing the "Sakina built..." lines.
- Not yet made: remaining tapes.
