@echo off
REM Double-click to run the full bake. Add the word  test  (run_bake.bat test) for a 1-minute check first.
set "BLENDER=C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
if not exist "%BLENDER%" (
  echo Blender 5.2 not found at: %BLENDER%
  echo Install Blender 5.2 LTS from blender.org, or edit the BLENDER line in this file.
  pause & exit /b 1
)
if /I "%1"=="test" (
  "%BLENDER%" -b "%~dp0v3-integrated.blend" -P "%~dp0run_bake.py" -- test
) else (
  "%BLENDER%" -b "%~dp0v3-integrated.blend" -P "%~dp0run_bake.py"
)
echo.
echo Finished. If it said DONE above, send back the file out\sakina-v21-baked.blend
pause
