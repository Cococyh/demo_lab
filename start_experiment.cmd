@echo off
setlocal
rem ===== demo_lab experiment launcher (run on the home PC) =====
rem 1) start ComfyUI if it is not running  2) build frontend if needed  3) start backend (also serves the web page)
rem Remote access from a Mac: install Tailscale on both machines, then run once:  tailscale serve --bg 5000

cd /d "%~dp0"
if "%COMFY_LAUNCHER%"=="" set "COMFY_LAUNCHER=E:\AI\Start-ComfyUI.cmd"

echo [1/3] Checking ComfyUI ...
curl -s -m 3 http://127.0.0.1:8188/system_stats >nul 2>&1
if errorlevel 1 (
  echo ComfyUI not running, starting it ...
  start "ComfyUI" /min cmd /c ""%COMFY_LAUNCHER%""
  for /l %%i in (1,1,60) do (
    curl -s -m 2 http://127.0.0.1:8188/system_stats >nul 2>&1 && goto comfy_ready
    timeout /t 2 /nobreak >nul
  )
  echo ERROR: ComfyUI did not start within 2 minutes.
  pause
  exit /b 1
)
:comfy_ready
echo ComfyUI is ready.

echo [2/3] Checking frontend build ...
if not exist "frontend\dist\index.html" (
  pushd frontend
  call npm install
  call npm run build
  popd
)

echo [3/3] Starting backend (model warm-up runs in background) ...
echo.
echo   On this PC open:  http://127.0.0.1:5000
echo   Logs are written to backend\logs\  (do not commit them)
echo.
cd backend
python app.py
pause
