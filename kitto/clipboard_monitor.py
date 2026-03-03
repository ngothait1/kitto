"""Monitor macOS pasteboard for changes and store every new clip.

Supports: plain text (any language/Unicode), RTF, HTML, images (TIFF/PNG),
and file URLs.  Polls NSPasteboard every 0.5 s (macOS has no push API).
"""

import threading
import AppKit

_IMAGE_TYPES = [
    AppKit.NSPasteboardTypeTIFF,
    AppKit.NSPasteboardTypePNG,
]
_FILE_TYPE = "public.file-url"


def _image_to_png(tiff_data: bytes) -> bytes:
    """Convert any NSImage-compatible data to PNG bytes."""
    ns_image = AppKit.NSImage.alloc().initWithData_(
        AppKit.NSData.dataWithBytes_length_(tiff_data, len(tiff_data))
    )
    if ns_image is None:
        return tiff_data
    tiff_rep = ns_image.TIFFRepresentation()
    bitmap = AppKit.NSBitmapImageRep.imageRepWithData_(tiff_rep)
    if bitmap is None:
        return tiff_data
    png_data = bitmap.representationUsingType_properties_(
        AppKit.NSBitmapImageFileTypePNG, {}
    )
    if png_data is None:
        return tiff_data
    return bytes(png_data)


class ClipboardMonitor:
    """Watches NSPasteboard.generalPasteboard and pushes new items to Storage."""

    def __init__(self, storage):
        self._storage = storage
        self._pb = AppKit.NSPasteboard.generalPasteboard()
        self._last_count = self._pb.changeCount()
        self._running = False
        self._timer = None

    # ── lifecycle ───────────────────────────────────────────────

    def start(self):
        self._running = True
        self._poll()

    def stop(self):
        self._running = False
        if self._timer:
            self._timer.cancel()

    # ── internal ────────────────────────────────────────────────

    def _poll(self):
        if not self._running:
            return
        try:
            self._check()
        except Exception:
            pass
        self._timer = threading.Timer(0.5, self._poll)
        self._timer.daemon = True
        self._timer.start()

    def _check(self):
        count = self._pb.changeCount()
        if count == self._last_count:
            return
        self._last_count = count

        types = self._pb.types()
        if types is None:
            return

        # ── images (check first – screenshots, copied images) ──
        for img_type in _IMAGE_TYPES:
            if img_type in types:
                raw = self._pb.dataForType_(img_type)
                if raw and len(raw) > 0:
                    png = _image_to_png(bytes(raw))
                    if not self._storage.is_duplicate(png, "image"):
                        self._storage.add(png, "image", "[Image]")
                    return

        # ── plain text (highest text priority – any language) ──
        if AppKit.NSPasteboardTypeString in types:
            text = self._pb.stringForType_(AppKit.NSPasteboardTypeString)
            if text:
                encoded = text.encode("utf-8")
                preview = text[:300]
                if not self._storage.is_duplicate(encoded, "text"):
                    self._storage.add(encoded, "text", preview)
                return

        # ── RTF (binary data) ──────────────────────────────────
        if AppKit.NSPasteboardTypeRTF in types:
            raw = self._pb.dataForType_(AppKit.NSPasteboardTypeRTF)
            if raw and len(raw) > 0:
                content = bytes(raw)
                # Extract plain text preview from RTF
                attr_str = AppKit.NSAttributedString.alloc().initWithRTF_documentAttributes_(
                    raw, None
                )
                preview = str(attr_str.string())[:300] if attr_str else "[RTF]"
                if not self._storage.is_duplicate(content, "rtf"):
                    self._storage.add(content, "rtf", preview)
                return

        # ── HTML ───────────────────────────────────────────────
        if AppKit.NSPasteboardTypeHTML in types:
            raw = self._pb.dataForType_(AppKit.NSPasteboardTypeHTML)
            if raw and len(raw) > 0:
                content = bytes(raw)
                try:
                    preview = content.decode("utf-8")[:300]
                except UnicodeDecodeError:
                    preview = "[HTML]"
                if not self._storage.is_duplicate(content, "html"):
                    self._storage.add(content, "html", preview)
                return

        # ── file URLs ──────────────────────────────────────────
        if _FILE_TYPE in types:
            url_str = self._pb.stringForType_(_FILE_TYPE)
            if url_str:
                encoded = url_str.encode("utf-8")
                preview = url_str[:300]
                if not self._storage.is_duplicate(encoded, "file"):
                    self._storage.add(encoded, "file", preview)
                return
