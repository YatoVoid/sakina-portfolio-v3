SAKINA PORTFOLIO V3 - FINAL LIGHT BAKE (about 1-3 hours on an RTX laptop; nothing to design, just run it)

WHAT THIS DOES
  Blender "bakes" the room's lighting into pictures (lightmaps). Sakina's website then shows those pictures, which is why it looks real.
  Her own computer has no GPU, so this PC does the heavy part.

YOU NEED
  - Windows PC with an NVIDIA graphics card, plugged in (not on battery), ~10 GB free disk, up-to-date graphics driver
  - Blender 5.2 LTS (free): https://www.blender.org/download/  -> install with the default options

STEPS
  1. Unzip this folder anywhere (for example the Desktop). Keep all files together.
  2. QUICK TEST FIRST: click the folder's address bar, type  cmd  and press Enter, then type   run_bake.bat test   and press Enter.
     -> takes about 1 minute. It must end with "DONE in ..." and say  BAKE GPU devices: [ 'NVIDIA ...' ]
     If it says "no such GPU found", open run_bake.py in Notepad and change  "OPTIX"  to  "CUDA", then try again.
  3. Double-click  run_bake.bat  (no test). A black window shows progress lines starting with BAKE. Leave the PC on, plugged in, do not let it sleep.
     (Windows: Settings > System > Power > Screen and sleep > set both to Never until it is done.)
  4. When it ends with  DONE in ... min , send back this ONE file:   out\sakina-v21-baked.blend   (about 0.3-1 GB; use Google Drive / WeTransfer)
     Nothing else is needed. Do not edit or open the .blend files in Blender.

IF SOMETHING GOES WRONG
  - Window closes instantly: run it from Command Prompt (type  cmd  in the folder's address bar) so the message stays visible.
  - Out of memory error: close other programs (browser, games) and run again.
  - Send Sakina a screenshot of the last 20 lines of the window.
