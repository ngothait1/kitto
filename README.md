# Kitto

A lightweight clipboard manager for macOS. Keeps your last 500 copied items — text, images, RTF, HTML, files — and lets you search and paste them instantly with a hotkey.

**Fully offline.** No internet access, no telemetry, no analytics. Your clipboard data never leaves your machine.

---

## Install

### Download (recommended)

1. Go to [**Releases**](../../releases/latest)
2. Download **Kitto.dmg**
3. Open the DMG and drag **Kitto.app** to your Applications folder
4. Open Kitto from Applications
5. macOS will ask for **Accessibility** permission — grant it in:
   **System Settings → Privacy & Security → Accessibility**

### Build from source

```bash
git clone https://github.com/YOUR_USER/kitto.git
cd kitto
./install.sh
```

Requires Python 3.10+ and macOS 12+.

---

## How to use

### Basic workflow

1. **Copy things as usual** — Kitto runs silently in your menu bar (✂ icon) and saves every copy automatically
2. **Press `⌘⇧V`** (Cmd+Shift+V) to open the clipboard history at your mouse cursor
3. **Scroll** through items or **type to search** — no need to click a search box, just start typing
4. **Press Enter** or **double-click** an item to paste it into the active app
5. **Press Escape** to close without pasting

### Keyboard shortcuts (in the popup)

| Key | Action |
|---|---|
| `↑` `↓` | Navigate items |
| `Tab` | Next item |
| `Shift+Tab` | Previous item |
| `Enter` | Paste selected item |
| `Escape` | Close popup |
| Any letter/number | Start searching |

### Menu bar

Click the **✂** icon in your menu bar to:

- **Show Clipboard History** — same as the hotkey
- **Configure Hotkey** — change the key combination to whatever you prefer
- **Clear History** — delete all non-pinned items
- **Quit Kitto**

### What it captures

- Plain text (any language — English, Hebrew, Chinese, emoji, etc.)
- Images (screenshots, copied pictures)
- Rich text (RTF)
- HTML
- File paths

### Storage

- Keeps up to **500 items** (configurable)
- Oldest items are automatically removed when the limit is reached (pinned items are kept)
- Data is stored locally in `~/Library/Application Support/Kitto/`
- Window size and hotkey preferences are remembered between sessions

---

## Privacy

Kitto has **zero network access** — enforced at three levels:

1. No networking code in the source
2. macOS App Transport Security set to deny all loads
3. Sandbox entitlements explicitly block inbound and outbound connections

Your clipboard data stays on your computer. Period.

---

## Uninstall

1. Quit Kitto from the menu bar
2. Delete `/Applications/Kitto.app`
3. Optionally remove data: `rm -rf ~/Library/Application\ Support/Kitto`

---

## License

MIT
