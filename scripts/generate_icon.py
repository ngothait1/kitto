"""Generate a simple Kitto app icon as .icns for macOS.

Uses Pillow to draw a minimal clipboard icon, then converts to .icns
via iconutil (macOS built-in).  Falls back to a bare .icns if iconutil
is unavailable.
"""

import os
import subprocess
import sys

SIZES = [16, 32, 64, 128, 256, 512, 1024]
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "resources")
ICONSET = os.path.join(OUT_DIR, "Kitto.iconset")


def _draw(size: int):
    """Return a PIL Image of the icon at the given pixel size."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Background rounded rectangle (clipboard body)
    margin = size // 8
    r = size // 6
    d.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=r,
        fill=(58, 134, 255),   # blue
        outline=(40, 100, 200),
        width=max(1, size // 64),
    )

    # Clipboard clip at top center
    clip_w = size // 4
    clip_h = size // 8
    cx = size // 2
    d.rounded_rectangle(
        [cx - clip_w // 2, margin - clip_h // 3, cx + clip_w // 2, margin + clip_h],
        radius=max(1, clip_h // 4),
        fill=(240, 240, 240),
        outline=(180, 180, 180),
        width=max(1, size // 128),
    )

    # "K" letter in center
    font_size = size // 3
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype(
                "/System/Library/Fonts/SFNSMono.ttf", font_size
            )
        except (OSError, IOError):
            font = ImageFont.load_default()
    bbox = d.textbbox((0, 0), "K", font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text(
        (cx - tw // 2, size // 2 - th // 3),
        "K",
        fill=(255, 255, 255),
        font=font,
    )
    return img


def main():
    os.makedirs(ICONSET, exist_ok=True)

    for sz in SIZES:
        img = _draw(sz)
        # Standard resolution
        if sz <= 512:
            img.save(os.path.join(ICONSET, f"icon_{sz}x{sz}.png"))
        # @2x Retina
        half = sz // 2
        if half in [16, 32, 128, 256, 512]:
            img.save(os.path.join(ICONSET, f"icon_{half}x{half}@2x.png"))

    # Convert .iconset → .icns via macOS iconutil
    icns_path = os.path.join(OUT_DIR, "Kitto.icns")
    try:
        subprocess.run(
            ["iconutil", "-c", "icns", ICONSET, "-o", icns_path],
            check=True,
        )
        print(f"Icon generated: {icns_path}")
    except FileNotFoundError:
        print("iconutil not found (not on macOS?). Skipping .icns generation.")
        # Keep the .iconset for manual conversion later
    except subprocess.CalledProcessError as e:
        print(f"iconutil failed: {e}")


if __name__ == "__main__":
    main()
