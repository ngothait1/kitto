"""Register and manage a global hotkey on macOS via Quartz Event Taps."""

import Quartz
import AppKit

# Mapping from human-readable modifier names to CGEvent flag masks.
_MOD_MAP = {
    "command": Quartz.kCGEventFlagMaskCommand,
    "shift": Quartz.kCGEventFlagMaskShift,
    "control": Quartz.kCGEventFlagMaskControl,
    "option": Quartz.kCGEventFlagMaskAlternate,
}

# Mapping from human-readable key names to virtual key codes.
_KEY_MAP = {
    "a": 0x00, "s": 0x01, "d": 0x02, "f": 0x03, "h": 0x04, "g": 0x05,
    "z": 0x06, "x": 0x07, "c": 0x08, "v": 0x09, "b": 0x0B, "q": 0x0C,
    "w": 0x0D, "e": 0x0E, "r": 0x0F, "y": 0x10, "t": 0x11, "1": 0x12,
    "2": 0x13, "3": 0x14, "4": 0x15, "6": 0x16, "5": 0x17, "9": 0x19,
    "7": 0x1A, "8": 0x1C, "0": 0x1D, "o": 0x1F, "u": 0x20, "i": 0x22,
    "p": 0x23, "l": 0x25, "j": 0x26, "k": 0x28, "n": 0x2D, "m": 0x2E,
    "`": 0x32, "space": 0x31, "tab": 0x30, "return": 0x24, "escape": 0x35,
    "delete": 0x33, "f1": 0x7A, "f2": 0x78, "f3": 0x63, "f4": 0x76,
    "f5": 0x60, "f6": 0x61, "f7": 0x62, "f8": 0x64, "f9": 0x65,
    "f10": 0x6D, "f11": 0x67, "f12": 0x6F,
}


class HotkeyManager:
    """Listens for a global key combo and fires a callback."""

    def __init__(self, modifiers: list[str], key: str, callback):
        self._callback = callback
        self._target_keycode = _KEY_MAP.get(key.lower(), 0x09)  # default 'v'
        self._target_flags = 0
        for m in modifiers:
            self._target_flags |= _MOD_MAP.get(m.lower(), 0)
        self._tap = None
        self._source = None

    # ── lifecycle ───────────────────────────────────────────────

    def start(self):
        mask = Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown)
        self._tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionDefault,
            mask,
            self._event_callback,
            None,
        )
        if self._tap is None:
            raise RuntimeError(
                "Failed to create event tap. "
                "Grant Accessibility permission in System Settings → "
                "Privacy & Security → Accessibility."
            )
        self._source = Quartz.CFMachPortCreateRunLoopSource(None, self._tap, 0)
        Quartz.CFRunLoopAddSource(
            Quartz.CFRunLoopGetMain(), self._source, Quartz.kCFRunLoopCommonModes
        )
        Quartz.CGEventTapEnable(self._tap, True)

    def stop(self):
        if self._tap:
            Quartz.CGEventTapEnable(self._tap, False)

    def update_hotkey(self, modifiers: list[str], key: str):
        self._target_keycode = _KEY_MAP.get(key.lower(), 0x09)
        self._target_flags = 0
        for m in modifiers:
            self._target_flags |= _MOD_MAP.get(m.lower(), 0)

    # ── internal ────────────────────────────────────────────────

    def _event_callback(self, proxy, event_type, event, refcon):
        if event_type == Quartz.kCGEventKeyDown:
            keycode = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGKeyboardEventKeycode
            )
            flags = Quartz.CGEventGetFlags(event)
            # Mask off device-dependent bits
            flags &= (
                Quartz.kCGEventFlagMaskCommand
                | Quartz.kCGEventFlagMaskShift
                | Quartz.kCGEventFlagMaskControl
                | Quartz.kCGEventFlagMaskAlternate
            )
            if keycode == self._target_keycode and flags == self._target_flags:
                self._callback()
                return None  # swallow the event
        return event

    @staticmethod
    def modifier_names() -> list[str]:
        return list(_MOD_MAP.keys())

    @staticmethod
    def key_names() -> list[str]:
        return sorted(_KEY_MAP.keys())
