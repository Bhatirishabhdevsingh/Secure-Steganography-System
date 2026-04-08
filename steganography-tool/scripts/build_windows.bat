@echo off
setlocal

set "PROJECT_DIR=%~dp0.."
for %%I in ("%PROJECT_DIR%") do set "PROJECT_DIR=%%~fI"
set "VENV_DIR=%PROJECT_DIR%\.venv"

echo [+] Building Windows application package

where py >nul 2>nul
if errorlevel 1 (
  echo [-] Python launcher 'py' not found. Install Python 3 first.
  exit /b 1
)

if not exist "%VENV_DIR%" (
  py -3 -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r "%PROJECT_DIR%\requirements.txt" pyinstaller

cd /d "%PROJECT_DIR%"
pyinstaller --noconfirm --clean SecureSteganography.spec

echo [+] Build complete
echo [+] Output folder: %PROJECT_DIR%\dist
endlocal
