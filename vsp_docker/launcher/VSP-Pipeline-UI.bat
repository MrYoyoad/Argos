@echo off
REM ================================================
REM VSP Pipeline — UI mode double-click target (Windows)
REM Starts the browser-based UI at http://localhost:8080
REM Wraps vsp-start.ps1 with -ExecutionPolicy Bypass.
REM ================================================
setlocal
set SCRIPT_DIR=%~dp0
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%vsp-start.ps1" %*
exit /b %ERRORLEVEL%
