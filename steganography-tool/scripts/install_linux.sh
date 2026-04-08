#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
PIP_BIN="$VENV_DIR/bin/pip"
PYTHON_BIN="$VENV_DIR/bin/python"
LAUNCHER_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
LAUNCHER_PATH="$LAUNCHER_DIR/secure-steganography"
DESKTOP_FILE="$DESKTOP_DIR/secure-steganography.desktop"

echo "[+] Installing Secure Steganography System by Rishabh dev Singh for Linux"
mkdir -p "$LAUNCHER_DIR" "$DESKTOP_DIR"

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
"$PIP_BIN" install -r "$PROJECT_DIR/requirements.txt"

cat > "$LAUNCHER_PATH" <<EOF
#!/usr/bin/env bash
cd "$PROJECT_DIR"
exec "$VENV_DIR/bin/python" "$PROJECT_DIR/main.py"
EOF
chmod +x "$LAUNCHER_PATH"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=Secure Steganography
Comment=Secure steganography desktop app by Rishabh dev Singh
Exec=$LAUNCHER_PATH
Terminal=false
Type=Application
Categories=Utility;Security;
StartupNotify=true
EOF

echo "[+] Installation complete"
echo "[+] Launcher created: $LAUNCHER_PATH"
echo "[+] Desktop entry created: $DESKTOP_FILE"
echo "[+] Run from terminal with: secure-steganography"
