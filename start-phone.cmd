@echo off
cd /d "%~dp0"
node start-dev.mjs --phone
if errorlevel 1 (
  echo.
  echo Phone mode could not start. Check that this PC is connected to Wi-Fi.
  pause
)
