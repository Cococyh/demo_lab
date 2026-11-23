@echo off
setlocal
rem ===== 远程参与用：把本机的网站（127.0.0.1:5000）临时公开到外网 =====
rem 先运行 start_experiment.cmd，看到网站能在本机打开后，再运行本文件。
rem 窗口里会出现一行 https://xxxx.trycloudflare.com ，把这个网址发给远程的参与者。
rem 注意：网址每次启动都会变；没有密码，不要公开发布；实验结束后关掉这个窗口即可停止公开。

cd /d "%~dp0"
if not exist "tools\cloudflared.exe" (
  echo ERROR: tools\cloudflared.exe not found.
  pause
  exit /b 1
)
echo Starting tunnel ... look for the line with  https://....trycloudflare.com
echo Close this window to stop sharing the site.
echo.
tools\cloudflared.exe tunnel --no-autoupdate --url http://127.0.0.1:5000
pause
