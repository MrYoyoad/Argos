@echo off
REM ================================================
REM VSP Pipeline — double-click target (Windows)
REM Wraps vsp-pipeline.ps1 with -ExecutionPolicy Bypass
REM so unsigned PowerShell scripts run without admin tweaks.
REM ================================================
setlocal
set SCRIPT_DIR=%~dp0
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%vsp-pipeline.ps1" %*
exit /b %ERRORLEVEL%
