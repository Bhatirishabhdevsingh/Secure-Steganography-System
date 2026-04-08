@echo off
setlocal

set "PROJECT_DIR=%~dp0.."
for %%I in ("%PROJECT_DIR%") do set "PROJECT_DIR=%%~fI"
set "INNO_SCRIPT=%PROJECT_DIR%\installers\windows\SecureSteganography.iss"

echo [+] Building Windows setup installer

if not exist "%PROJECT_DIR%\dist\SecureSteganography.exe" (
  echo [*] Windows executable not found. Running PyInstaller build first...
  call "%PROJECT_DIR%\scripts\build_windows.bat"
)

where iscc >nul 2>nul
if errorlevel 1 (
  echo [-] Inno Setup Compiler ^(iscc^) not found.
  echo [*] Install Inno Setup on Windows, then run this script again.
  echo [*] Installer script is ready at: %INNO_SCRIPT%
  exit /b 1
)

cd /d "%PROJECT_DIR%"
iscc "%INNO_SCRIPT%"

echo [+] Windows setup created in: %PROJECT_DIR%\dist
endlocal
