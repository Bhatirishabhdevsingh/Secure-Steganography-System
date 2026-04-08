@echo off
setlocal

set "PROJECT_DIR=%~dp0.."
for %%I in ("%PROJECT_DIR%") do set "PROJECT_DIR=%%~fI"
set "VENV_DIR=%PROJECT_DIR%\.venv"
set "LAUNCHER_PATH=%PROJECT_DIR%\Launch Secure Steganography.bat"

echo [+] Installing Secure Steganography System by Rishabh dev Singh for Windows

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
pip install -r "%PROJECT_DIR%\requirements.txt"

(
  echo @echo off
  echo cd /d "%PROJECT_DIR%"
  echo call "%VENV_DIR%\Scripts\activate.bat"
  echo python "%PROJECT_DIR%\main.py"
) > "%LAUNCHER_PATH%"

echo [+] Installation complete
echo [+] Launcher created: %LAUNCHER_PATH%
echo [+] Double-click the launcher to run the app.
endlocal
