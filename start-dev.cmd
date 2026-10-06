@echo off
setlocal
where node >nul 2>nul
if errorlevel 1 (
    echo Node.js was not found. Install Node.js and npm first.
    exit /b 1
)
node "%~dp0start-dev.mjs"
exit /b %ERRORLEVEL%
