"""Kitto – macOS clipboard manager.

Entry point: wires together all modules and starts the NSApplication run loop.
"""

import sys
import signal
import AppKit
import objc
from Foundation import NSObject

from kitto.settings import Settings
from kitto.storage import Storage
from kitto.clipboard_monitor import ClipboardMonitor
from kitto.hotkey_manager import HotkeyManager
from kitto.popup_window import PopupWindow
from kitto.menu_bar import MenuBarController
from kitto.hotkey_config_sheet import HotkeyConfigSheet


class KittoAppDelegate(NSObject):
    """NSApplicationDelegate – owns all the components."""

    def init(self):
        self = objc.super(KittoAppDelegate, self).init()
        if self is None:
            return None
        self._settings = None
        self._storage = None
        self._monitor = None
        self._hotkey = None
        self._popup = None
        self._menu_bar = None
        return self

    # ── NSApplicationDelegate ───────────────────────────────────

    def applicationDidFinishLaunching_(self, notif):
        # Hide dock icon – we are a menu-bar-only app
        AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)

        self._settings = Settings()
        self._storage = Storage(
            self._settings.db_path, self._settings.max_items
        )
        self._monitor = ClipboardMonitor(self._storage)
        self._monitor.start()

        self._popup = PopupWindow(self._storage, self._settings)

        self._hotkey = HotkeyManager(
            self._settings.hotkey_modifiers,
            self._settings.hotkey_key,
            self._on_hotkey,
        )
        try:
            self._hotkey.start()
        except RuntimeError as exc:
            alert = AppKit.NSAlert.alloc().init()
            alert.setMessageText_("Accessibility Permission Required")
            alert.setInformativeText_(str(exc))
            alert.addButtonWithTitle_("OK")
            alert.runModal()

        self._menu_bar = MenuBarController.alloc().init()
        self._menu_bar.setup(self)

    def applicationWillTerminate_(self, notif):
        if self._monitor:
            self._monitor.stop()
        if self._hotkey:
            self._hotkey.stop()
        if self._storage:
            self._storage.close()

    # ── callbacks used by MenuBarController and hotkey ──────────

    def _on_hotkey(self):
        # Dispatch to main thread since the event tap callback
        # may fire on a background thread.
        self.performSelectorOnMainThread_withObject_waitUntilDone_(
            objc.selector(self._toggle_on_main, signature=b"v@:@"),
            None,
            False,
        )

    def _toggle_on_main(self, _=None):
        self.toggle_popup()

    def toggle_popup(self):
        if self._popup:
            self._popup.toggle()

    def show_hotkey_config(self):
        sheet = HotkeyConfigSheet.alloc().init()
        sheet.show(
            self._settings.hotkey_modifiers,
            self._settings.hotkey_key,
            self._on_hotkey_changed,
        )
        self._config_sheet = sheet  # prevent GC

    def _on_hotkey_changed(self, mods: list, key: str):
        self._settings.set("hotkey_modifiers", mods)
        self._settings.set("hotkey_key", key)
        if self._hotkey:
            self._hotkey.update_hotkey(mods, key)

    def clear_history(self):
        if self._storage:
            self._storage.clear_all()


def main():
    # Allow Ctrl-C in terminal to quit gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = AppKit.NSApplication.sharedApplication()
    delegate = KittoAppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()
