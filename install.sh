#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
#  Kitto — one-command install script for macOS
#
#  Usage:
#    curl -sL <raw-url>/install.sh | bash
#    — or —
#    git clone <repo> && cd kitto && ./install.sh
# ──────────────────────────────────────────────────────────────
set -euo pipefail

# ── colours ──────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { printf "${GREEN}[kitto]${NC} %s\n" "$*"; }
warn()  { printf "${YELLOW}[kitto]${NC} %s\n" "$*"; }
error() { printf "${RED}[kitto]${NC} %s\n" "$*"; exit 1; }

# ── pre-checks ──────────────────────────────────────────────
[[ "$(uname)" == "Darwin" ]] || error "Kitto only runs on macOS."

if ! command -v python3 &>/dev/null; then
    error "Python 3 is required.  Install it with:  brew install python"
fi

PY_VER=$(python3 -c 'import sys; print(sys.version_info[:2])')
info "Python version: $(python3 --version)"

# ── locate project root ─────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/setup.py" ]]; then
    cd "$SCRIPT_DIR"
else
    # Running via curl pipe — clone into a temp dir
    TMPDIR="$(mktemp -d)"
    info "Cloning Kitto into $TMPDIR …"
    git clone --depth 1 https://github.com/YOUR_USER/kitto.git "$TMPDIR/kitto"
    cd "$TMPDIR/kitto"
fi

# ── create venv ──────────────────────────────────────────────
info "Creating virtual environment…"
python3 -m venv .venv
source .venv/bin/activate

# ── install deps ─────────────────────────────────────────────
info "Installing dependencies (PyObjC, Pillow, py2app)…"
pip install --upgrade pip -q
pip install -r requirements.txt -q

# ── generate icon ────────────────────────────────────────────
if [[ ! -f resources/Kitto.icns ]]; then
    info "Generating app icon…"
    python3 scripts/generate_icon.py || warn "Icon generation skipped (non-critical)."
fi

# ── build .app ───────────────────────────────────────────────
info "Building Kitto.app…"
python3 setup.py py2app --dist-dir dist 2>&1 | tail -3

if [[ ! -d dist/Kitto.app ]]; then
    error "Build failed — dist/Kitto.app not found."
fi

# ── codesign with entitlements (no network) ──────────────────
if [[ -f resources/Kitto.entitlements ]]; then
    info "Signing with entitlements (network access denied)…"
    codesign --force --deep --sign - \
        --entitlements resources/Kitto.entitlements \
        dist/Kitto.app 2>/dev/null || warn "Codesign skipped (ad-hoc)."
fi

# ── install to /Applications ────────────────────────────────
info "Installing to /Applications…"
if [[ -d /Applications/Kitto.app ]]; then
    warn "Removing previous Kitto.app…"
    rm -rf /Applications/Kitto.app
fi
cp -r dist/Kitto.app /Applications/

# ── done ─────────────────────────────────────────────────────
echo ""
info "================================================"
info "  Kitto installed successfully!"
info "================================================"
echo ""
info "Open it with:  open /Applications/Kitto.app"
echo ""
warn "First launch: macOS will ask for Accessibility permission."
warn "Go to: System Settings → Privacy & Security → Accessibility"
warn "and enable Kitto."
echo ""
info "Default hotkey: ⌘⇧V (Cmd+Shift+V)"
info "Configure via the ✂ icon in your menu bar."
echo ""
