#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
PIP_BIN="$VENV_DIR/bin/pip"
PYTHON_BIN="$VENV_DIR/bin/python"

echo "[+] Building Linux app package"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[-] python3 is required but was not found."
  exit 1
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "[-] python3-venv is required."
  echo "[*] On Debian/Kali/Ubuntu run: sudo apt install python3.13-venv"
  exit 1
fi

if [ ! -d "$VENV_DIR" ] || [ ! -x "$PYTHON_BIN" ] || [ ! -x "$PIP_BIN" ]; then
  rm -rf "$VENV_DIR"
  if ! python3 -m venv "$VENV_DIR"; then
    echo "[-] Failed to create virtual environment."
    echo "[*] Install venv support first: sudo apt install python3.13-venv"
    exit 1
  fi
fi

"$PIP_BIN" install --upgrade pip
"$PIP_BIN" install -r "$PROJECT_DIR/requirements.txt" pyinstaller

cd "$PROJECT_DIR"
"$VENV_DIR/bin/pyinstaller" --noconfirm --clean SecureSteganography.spec

echo "[+] Build complete"
echo "[+] Output: $PROJECT_DIR/dist/SecureSteganography"
