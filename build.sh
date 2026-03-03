#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────
#  Build Kitto.app for macOS
#  Run this on a Mac with Python 3.10+ installed.
# ──────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Creating virtual environment…"
python3 -m venv .venv
source .venv/bin/activate

echo "==> Installing dependencies…"
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Generating app icon (if iconutil is available)…"
if [ ! -f resources/Kitto.icns ]; then
    mkdir -p resources
    python3 scripts/generate_icon.py
fi

echo "==> Building Kitto.app with py2app…"
python3 setup.py py2app --dist-dir dist

echo ""
echo "✅  Build complete!  Kitto.app is in dist/"
echo ""
echo "To install:"
echo "  cp -r dist/Kitto.app /Applications/"
echo ""
echo "To create a DMG:"
echo "  hdiutil create -volname Kitto -srcfolder dist/Kitto.app -ov -format UDZO dist/Kitto.dmg"
echo ""
