"""macOS menu-bar (status bar) icon and menu for Kitto."""

import AppKit
import objc
from Foundation import NSObject


class MenuBarController(NSObject):
    """Creates and manages the NSStatusItem with a dropdown menu."""

    def init(self):
        self = objc.super(MenuBarController, self).init()
        if self is None:
            return None
        self._app_ref = None
        return self

    def setup(self, app_ref):
        """Call after NSApplication is running."""
        self._app_ref = app_ref

        status_bar = AppKit.NSStatusBar.systemStatusBar()
        self._status_item = status_bar.statusItemWithLength_(
            AppKit.NSVariableStatusItemLength
        )
        button = self._status_item.button()
        button.setTitle_("✂")  # scissors icon as text fallback
        button.setToolTip_("Kitto – Clipboard Manager")

        self._build_menu()

    # ── menu construction ───────────────────────────────────────

    def _build_menu(self):
        menu = AppKit.NSMenu.alloc().init()

        item_show = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Show Clipboard History", "showHistory:", ""
        )
        item_show.setTarget_(self)
        menu.addItem_(item_show)

        menu.addItem_(AppKit.NSMenuItem.separatorItem())

        item_hotkey = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Configure Hotkey…", "configureHotkey:", ""
        )
        item_hotkey.setTarget_(self)
        menu.addItem_(item_hotkey)

        item_clear = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Clear History", "clearHistory:", ""
        )
        item_clear.setTarget_(self)
        menu.addItem_(item_clear)

        menu.addItem_(AppKit.NSMenuItem.separatorItem())

        item_about = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "About Kitto", "showAbout:", ""
        )
        item_about.setTarget_(self)
        menu.addItem_(item_about)

        item_quit = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit Kitto", "quitApp:", "q"
        )
        item_quit.setTarget_(self)
        menu.addItem_(item_quit)

        self._status_item.setMenu_(menu)

    # ── actions ─────────────────────────────────────────────────

    @objc.IBAction
    def showHistory_(self, sender):
        if self._app_ref:
            self._app_ref.toggle_popup()

    @objc.IBAction
    def configureHotkey_(self, sender):
        if self._app_ref:
            self._app_ref.show_hotkey_config()

    @objc.IBAction
    def clearHistory_(self, sender):
        alert = AppKit.NSAlert.alloc().init()
        alert.setMessageText_("Clear clipboard history?")
        alert.setInformativeText_(
            "This will delete all non-pinned items. This cannot be undone."
        )
        alert.addButtonWithTitle_("Clear")
        alert.addButtonWithTitle_("Cancel")
        alert.setAlertStyle_(AppKit.NSAlertStyleWarning)
        if alert.runModal() == AppKit.NSAlertFirstButtonReturn:
            if self._app_ref:
                self._app_ref.clear_history()

    @objc.IBAction
    def showAbout_(self, sender):
        alert = AppKit.NSAlert.alloc().init()
        alert.setMessageText_("Kitto v1.0.0")
        alert.setInformativeText_(
            "A lightweight clipboard manager for macOS.\n\n"
            "Keeps your last 500 copied items.\n"
            "No internet connection – your data stays local.\n\n"
            "Default hotkey: ⌘⇧V"
        )
        alert.addButtonWithTitle_("OK")
        alert.runModal()

    @objc.IBAction
    def quitApp_(self, sender):
        AppKit.NSApp.terminate_(None)
