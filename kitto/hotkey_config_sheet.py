"""Modal sheet for configuring the global hotkey."""

import AppKit
import objc
from Foundation import NSObject, NSMakeRect


class HotkeyConfigSheet(NSObject):
    """Displays a small dialog to let the user pick modifiers + key."""

    def init(self):
        self = objc.super(HotkeyConfigSheet, self).init()
        if self is None:
            return None
        self._callback = None
        return self

    def show(self, current_mods: list, current_key: str, callback):
        """Show the config dialog. callback(mods, key) called on save."""
        self._callback = callback

        w = 360
        h = 200
        self._win = AppKit.NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(200, 300, w, h),
            AppKit.NSWindowStyleMaskTitled | AppKit.NSWindowStyleMaskClosable,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self._win.setTitle_("Configure Hotkey")
        self._win.setLevel_(AppKit.NSFloatingWindowLevel + 1)
        cv = self._win.contentView()

        y = h - 40
        label = AppKit.NSTextField.labelWithString_("Modifiers:")
        label.setFrame_(NSMakeRect(16, y, 80, 22))
        cv.addSubview_(label)

        # Modifier checkboxes
        self._cmd_cb = AppKit.NSButton.checkboxWithTitle_target_action_("⌘ Command", None, None)
        self._cmd_cb.setFrame_(NSMakeRect(100, y, 130, 22))
        self._cmd_cb.setState_(1 if "command" in current_mods else 0)
        cv.addSubview_(self._cmd_cb)

        self._shift_cb = AppKit.NSButton.checkboxWithTitle_target_action_("⇧ Shift", None, None)
        self._shift_cb.setFrame_(NSMakeRect(230, y, 110, 22))
        self._shift_cb.setState_(1 if "shift" in current_mods else 0)
        cv.addSubview_(self._shift_cb)

        y -= 30
        self._ctrl_cb = AppKit.NSButton.checkboxWithTitle_target_action_("⌃ Control", None, None)
        self._ctrl_cb.setFrame_(NSMakeRect(100, y, 130, 22))
        self._ctrl_cb.setState_(1 if "control" in current_mods else 0)
        cv.addSubview_(self._ctrl_cb)

        self._opt_cb = AppKit.NSButton.checkboxWithTitle_target_action_("⌥ Option", None, None)
        self._opt_cb.setFrame_(NSMakeRect(230, y, 110, 22))
        self._opt_cb.setState_(1 if "option" in current_mods else 0)
        cv.addSubview_(self._opt_cb)

        # Key dropdown
        y -= 40
        label2 = AppKit.NSTextField.labelWithString_("Key:")
        label2.setFrame_(NSMakeRect(16, y, 80, 22))
        cv.addSubview_(label2)

        self._key_popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(
            NSMakeRect(100, y, 120, 26), False
        )
        keys = list("abcdefghijklmnopqrstuvwxyz0123456789") + ["`", "space"]
        for k in keys:
            self._key_popup.addItemWithTitle_(k)
        idx = keys.index(current_key) if current_key in keys else 0
        self._key_popup.selectItemAtIndex_(idx)
        cv.addSubview_(self._key_popup)

        # Buttons
        y -= 50
        save_btn = AppKit.NSButton.alloc().initWithFrame_(NSMakeRect(w - 170, y, 80, 32))
        save_btn.setTitle_("Save")
        save_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        save_btn.setTarget_(self)
        save_btn.setAction_(objc.selector(self.onSave_, signature=b"v@:@"))
        save_btn.setKeyEquivalent_("\r")
        cv.addSubview_(save_btn)

        cancel_btn = AppKit.NSButton.alloc().initWithFrame_(NSMakeRect(w - 84, y, 80, 32))
        cancel_btn.setTitle_("Cancel")
        cancel_btn.setBezelStyle_(AppKit.NSBezelStyleRounded)
        cancel_btn.setTarget_(self)
        cancel_btn.setAction_(objc.selector(self.onCancel_, signature=b"v@:@"))
        cancel_btn.setKeyEquivalent_("\x1b")  # Escape
        cv.addSubview_(cancel_btn)

        self._win.makeKeyAndOrderFront_(None)
        AppKit.NSApp.activateIgnoringOtherApps_(True)

    def onSave_(self, sender):
        mods = []
        if self._cmd_cb.state():
            mods.append("command")
        if self._shift_cb.state():
            mods.append("shift")
        if self._ctrl_cb.state():
            mods.append("control")
        if self._opt_cb.state():
            mods.append("option")
        key = self._key_popup.titleOfSelectedItem()
        self._win.orderOut_(None)
        if self._callback:
            self._callback(mods, key)

    def onCancel_(self, sender):
        self._win.orderOut_(None)
