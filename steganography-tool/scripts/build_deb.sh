#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE_NAME="secure-steganography"
DISPLAY_NAME="Secure Steganography"
VERSION="${1:-1.0.0}"
ARCH="amd64"
DIST_BIN="$PROJECT_DIR/dist/SecureSteganography"
BUILD_ROOT="$PROJECT_DIR/package-build"
PKG_ROOT="$BUILD_ROOT/${PACKAGE_NAME}_${VERSION}_${ARCH}"
INSTALL_ROOT="$PKG_ROOT/opt/$PACKAGE_NAME"
BIN_DIR="$PKG_ROOT/usr/local/bin"
DESKTOP_DIR="$PKG_ROOT/usr/share/applications"
CONTROL_DIR="$PKG_ROOT/DEBIAN"
OUTPUT_DEB="$PROJECT_DIR/dist/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

echo "[+] Building Debian package"

if ! command -v dpkg-deb >/dev/null 2>&1; then
  echo "[-] dpkg-deb is required but not installed."
  exit 1
fi

if [ ! -x "$DIST_BIN" ]; then
  echo "[*] Linux binary not found. Building it first..."
  "$PROJECT_DIR/scripts/build_linux.sh"
fi

rm -rf "$PKG_ROOT"
mkdir -p "$INSTALL_ROOT" "$BIN_DIR" "$DESKTOP_DIR" "$CONTROL_DIR"

cp "$DIST_BIN" "$INSTALL_ROOT/SecureSteganography"
cp -r "$PROJECT_DIR/assets" "$INSTALL_ROOT/" 2>/dev/null || true
cp -r "$PROJECT_DIR/logs" "$INSTALL_ROOT/" 2>/dev/null || true
cp -r "$PROJECT_DIR/output" "$INSTALL_ROOT/" 2>/dev/null || true

cat > "$BIN_DIR/secure-steganography" <<EOF
#!/usr/bin/env bash
exec /opt/$PACKAGE_NAME/SecureSteganography
EOF
chmod 755 "$BIN_DIR/secure-steganography"
chmod 755 "$INSTALL_ROOT/SecureSteganography"

cat > "$DESKTOP_DIR/secure-steganography.desktop" <<EOF
[Desktop Entry]
Name=$DISPLAY_NAME
Comment=Hide and extract encrypted payloads inside images
Exec=/usr/local/bin/secure-steganography
Terminal=false
Type=Application
Categories=Utility;Security;
StartupNotify=true
EOF

INSTALLED_SIZE="$(du -sk "$PKG_ROOT" | awk '{print $1}')"
cat > "$CONTROL_DIR/control" <<EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: Secure Steganography Team
Installed-Size: $INSTALLED_SIZE
Depends: python3
Description: Secure steganography desktop application
 AES-256 protected hidden data inside images with randomized LSB embedding.
EOF

dpkg-deb --build "$PKG_ROOT" "$OUTPUT_DEB"

echo "[+] Debian package created"
echo "[+] Output: $OUTPUT_DEB"
