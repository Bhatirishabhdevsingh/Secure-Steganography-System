#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$PROJECT_DIR/dist"
WEB_DOWNLOADS_DIR="$PROJECT_DIR/web/downloads"

echo "[+] Syncing desktop builds into web/downloads"
mkdir -p "$WEB_DOWNLOADS_DIR"

cp "$DIST_DIR/secure-steganography_1.0.0_amd64.deb" "$WEB_DOWNLOADS_DIR/secure-steganography_1.0.0_amd64.deb"
cp "$DIST_DIR/SecureSteganography" "$WEB_DOWNLOADS_DIR/SecureSteganography"
cp "$DIST_DIR/SecureSteganography.exe" "$WEB_DOWNLOADS_DIR/SecureSteganography.exe"

echo "[+] Downloads updated"
echo "[+] Linux .deb: $WEB_DOWNLOADS_DIR/secure-steganography_1.0.0_amd64.deb"
echo "[+] Linux binary: $WEB_DOWNLOADS_DIR/SecureSteganography"
echo "[+] Windows .exe: $WEB_DOWNLOADS_DIR/SecureSteganography.exe"
