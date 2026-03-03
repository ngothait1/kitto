"""Floating popup window that shows clipboard history.

Appears at the current mouse position.  Typing immediately filters items
(no need to click a search box).  Enter/click pastes the selected item.
Escape closes the popup.  Supports text and image previews.
"""

import time
import AppKit
import Quartz
import objc
from Foundation import NSObject, NSMakeRect, NSMakeSize, NSMakePoint

# ── Constants ───────────────────────────────────────────────────────────
_ROW_HEIGHT = 36.0
_SEARCH_HEIGHT = 32.0
_PADDING = 4.0


def _mouse_location():
    return AppKit.NSEvent.mouseLocation()


# ════════════════════════════════════════════════════════════════════════
#  Custom panel that forwards Enter / Escape / arrow keys
# ════════════════════════════════════════════════════════════════════════
class KittoPanel(AppKit.NSPanel):
    """Intercepts key events for Enter, Escape, and arrow navigation."""

    popupOwner = objc.ivar()

    def keyDown_(self, event):
        keycode = event.keyCode()
        # Escape → close
        if keycode == 0x35:
            if self.popupOwner:
                self.popupOwner.hide()
            return
        # Return / Enter → paste selected
        if keycode in (0x24, 0x4C):
            if self.popupOwner:
                self.popupOwner.paste_selected()
            return
        # Down arrow → move selection down and keep focus in search
        if keycode == 0x7D:
            if self.popupOwner:
                self.popupOwner.move_selection(1)
            return
        # Up arrow → move selection up
        if keycode == 0x7E:
            if self.popupOwner:
                self.popupOwner.move_selection(-1)
            return
        # Tab → move selection down
        if keycode == 0x30:
            if self.popupOwner:
                self.popupOwner.move_selection(1)
            return
        # Everything else → let the search field handle it
        objc.super(KittoPanel, self).keyDown_(event)


# ════════════════════════════════════════════════════════════════════════
#  Tooltip window – shows full content on hover
# ════════════════════════════════════════════════════════════════════════
class TooltipWindow(AppKit.NSPanel):
    @classmethod
    def create(cls):
        w = cls.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 400, 300),
            AppKit.NSWindowStyleMaskBorderless,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        w.setLevel_(AppKit.NSFloatingWindowLevel + 2)
        w.setOpaque_(False)
        w.setBackgroundColor_(AppKit.NSColor.windowBackgroundColor())
        w.setHasShadow_(True)
        w.setAlphaValue_(0.96)

        scroll = AppKit.NSScrollView.alloc().initWithFrame_(
            NSMakeRect(0, 0, 400, 300)
        )
        scroll.setHasVerticalScroller_(True)
        scroll.setAutoresizingMask_(
            AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable
        )

        tv = AppKit.NSTextView.alloc().initWithFrame_(
            NSMakeRect(0, 0, 400, 300)
        )
        tv.setEditable_(False)
        tv.setSelectable_(True)
        tv.setFont_(AppKit.NSFont.monospacedSystemFontOfSize_weight_(12, 0))
        tv.setTextContainerInset_(NSMakeSize(8, 8))
        scroll.setDocumentView_(tv)

        w.setContentView_(scroll)
        w._textView = tv
        w._scrollView = scroll
        return w

    def showText_near_(self, text, rect):
        self._textView.setString_(text)
        x = rect.origin.x + rect.size.width + 8
        y = rect.origin.y
        screen = AppKit.NSScreen.mainScreen().frame()
        if x + 400 > screen.size.width:
            x = rect.origin.x - 408
        self.setFrameOrigin_(NSMakePoint(x, y))
        self.orderFront_(None)

    def showImage_near_(self, image, rect):
        self._textView.setString_("")
        attachment = AppKit.NSTextAttachment.alloc().init()
        cell = AppKit.NSTextAttachmentCell.alloc().initImageCell_(image)
        attachment.setAttachmentCell_(cell)
        attr_str = AppKit.NSAttributedString.attributedStringWithAttachment_(attachment)
        self._textView.textStorage().setAttributedString_(attr_str)
        x = rect.origin.x + rect.size.width + 8
        y = rect.origin.y
        self.setFrameOrigin_(NSMakePoint(x, y))
        self.orderFront_(None)

    def hide(self):
        self.orderOut_(None)


# ════════════════════════════════════════════════════════════════════════
#  Table data source / delegate
# ════════════════════════════════════════════════════════════════════════
class ClipTableDelegate(NSObject):

    def init(self):
        self = objc.super(ClipTableDelegate, self).init()
        if self is None:
            return None
        self.items = []
        self.storage = None
        self.popup = None
        self.tooltip = None
        return self

    # ── NSTableViewDataSource ───────────────────────────────────

    def numberOfRowsInTableView_(self, tv):
        return len(self.items)

    def tableView_objectValueForTableColumn_row_(self, tv, col, row):
        if row >= len(self.items):
            return ""
        item = self.items[row]
        ident = col.identifier()
        if ident == "content":
            if item["content_type"] == "image":
                return f"  [Image – {item['byte_size'] // 1024} KB]"
            preview = item["preview"]
            return preview.replace("\n", " \u21b5 ")[:200]
        if ident == "time":
            delta = time.time() - item["created_at"]
            if delta < 60:
                return "just now"
            if delta < 3600:
                return f"{int(delta // 60)}m ago"
            if delta < 86400:
                return f"{int(delta // 3600)}h ago"
            return f"{int(delta // 86400)}d ago"
        return ""

    # ── NSTableViewDelegate ─────────────────────────────────────

    def tableViewSelectionDidChange_(self, notif):
        tv = notif.object()
        row = tv.selectedRow()
        if row < 0 or row >= len(self.items):
            if self.tooltip:
                self.tooltip.hide()
            return
        self._showTooltipForRow_inTable_(row, tv)

    def _showTooltipForRow_inTable_(self, row, tv):
        item = self.items[row]
        row_rect = tv.rectOfRow_(row)
        win_rect = tv.convertRect_toView_(row_rect, None)
        screen_point = tv.window().convertRectToScreen_(win_rect)

        if item["content_type"] == "image":
            data = self.storage.get_content(item["id"])
            if data:
                ns_data = AppKit.NSData.dataWithBytes_length_(data[0], len(data[0]))
                ns_image = AppKit.NSImage.alloc().initWithData_(ns_data)
                if ns_image and self.tooltip:
                    self.tooltip.showImage_near_(ns_image, screen_point)
        else:
            data = self.storage.get_content(item["id"])
            if data and self.tooltip:
                try:
                    text = data[0].decode("utf-8")
                except UnicodeDecodeError:
                    text = repr(data[0][:500])
                self.tooltip.showText_near_(text, screen_point)

    def tableView_shouldSelectRow_(self, tv, row):
        return True


# ════════════════════════════════════════════════════════════════════════
#  Search field delegate
# ════════════════════════════════════════════════════════════════════════
class SearchDelegate(NSObject):
    def init(self):
        self = objc.super(SearchDelegate, self).init()
        if self is None:
            return None
        self.popup = None
        return self

    def controlTextDidChange_(self, notif):
        field = notif.object()
        query = field.stringValue()
        if self.popup:
            self.popup.filter(query)

    def control_textView_doCommandBySelector_(self, control, tv, selector):
        """Intercept Enter/Escape/arrows inside the search field."""
        sel = str(selector)
        if sel == "insertNewline:":
            if self.popup:
                self.popup.paste_selected()
            return True
        if sel == "cancelOperation:":
            if self.popup:
                self.popup.hide()
            return True
        if sel == "moveDown:":
            if self.popup:
                self.popup.move_selection(1)
            return True
        if sel == "moveUp:":
            if self.popup:
                self.popup.move_selection(-1)
            return True
        if sel == "insertTab:":
            if self.popup:
                self.popup.move_selection(1)
            return True
        if sel == "insertBacktab:":
            if self.popup:
                self.popup.move_selection(-1)
            return True
        return False


# ════════════════════════════════════════════════════════════════════════
#  PopupWindow delegate (NSObject subclass for window delegate)
# ════════════════════════════════════════════════════════════════════════
class PopupWindowDelegate(NSObject):
    def init(self):
        self = objc.super(PopupWindowDelegate, self).init()
        if self is None:
            return None
        self.popup = None
        return self

    def windowDidResignKey_(self, notif):
        if self.popup:
            self.popup.hide()


# ════════════════════════════════════════════════════════════════════════
#  Main popup
# ════════════════════════════════════════════════════════════════════════
class PopupWindow:
    def __init__(self, storage, settings):
        self._storage = storage
        self._settings = settings
        self._visible = False
        self._query = ""
        self._build_ui()

    # ── public API ──────────────────────────────────────────────

    def toggle(self):
        if self._visible:
            self.hide()
        else:
            self.show()

    def show(self):
        self._query = ""
        self._search_field.setStringValue_("")
        self._refresh_items()
        loc = _mouse_location()
        w = self._settings.window_width
        h = self._settings.window_height
        # Keep within screen bounds
        screen = AppKit.NSScreen.mainScreen().frame()
        x = min(loc.x, screen.size.width - w)
        y = max(loc.y - h, 0)
        self._panel.setFrame_display_(NSMakeRect(x, y, w, h), True)
        self._panel.makeKeyAndOrderFront_(None)
        AppKit.NSApp.activateIgnoringOtherApps_(True)
        self._panel.makeFirstResponder_(self._search_field)
        self._visible = True

    def hide(self):
        if not self._visible:
            return
        self._tooltip.hide()
        self._panel.orderOut_(None)
        self._visible = False
        self._save_geometry()

    def filter(self, query: str):
        self._query = query
        self._refresh_items()

    def move_selection(self, delta: int):
        row = self._table.selectedRow()
        count = len(self._delegate.items)
        if count == 0:
            return
        new_row = max(0, min(row + delta, count - 1))
        idx = AppKit.NSIndexSet.indexSetWithIndex_(new_row)
        self._table.selectRowIndexes_byExtendingSelection_(idx, False)
        self._table.scrollRowToVisible_(new_row)

    def paste_selected(self):
        row = self._table.selectedRow()
        if row < 0 or row >= len(self._delegate.items):
            return
        item = self._delegate.items[row]
        data = self._storage.get_content(item["id"])
        if data is None:
            return
        content, ctype = data
        pb = AppKit.NSPasteboard.generalPasteboard()
        pb.clearContents()

        if ctype == "image":
            pb.setData_forType_(
                AppKit.NSData.dataWithBytes_length_(content, len(content)),
                AppKit.NSPasteboardTypePNG,
            )
        elif ctype == "rtf":
            pb.setData_forType_(
                AppKit.NSData.dataWithBytes_length_(content, len(content)),
                AppKit.NSPasteboardTypeRTF,
            )
            try:
                pb.setString_forType_(
                    content.decode("utf-8"), AppKit.NSPasteboardTypeString
                )
            except UnicodeDecodeError:
                pass
        elif ctype == "html":
            pb.setData_forType_(
                AppKit.NSData.dataWithBytes_length_(content, len(content)),
                AppKit.NSPasteboardTypeHTML,
            )
            try:
                pb.setString_forType_(
                    content.decode("utf-8"), AppKit.NSPasteboardTypeString
                )
            except UnicodeDecodeError:
                pass
        elif ctype == "file":
            try:
                pb.setString_forType_(
                    content.decode("utf-8"), AppKit.NSPasteboardTypeString
                )
            except UnicodeDecodeError:
                pass
        else:
            try:
                pb.setString_forType_(
                    content.decode("utf-8"), AppKit.NSPasteboardTypeString
                )
            except UnicodeDecodeError:
                pass

        self.hide()
        self._simulate_paste()

    # ── build UI ────────────────────────────────────────────────

    def _build_ui(self):
        w = self._settings.window_width
        h = self._settings.window_height

        self._panel = KittoPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, w, h),
            AppKit.NSWindowStyleMaskTitled
            | AppKit.NSWindowStyleMaskClosable
            | AppKit.NSWindowStyleMaskResizable
            | AppKit.NSWindowStyleMaskUtilityWindow
            | AppKit.NSWindowStyleMaskNonactivatingPanel,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self._panel.popupOwner = self
        self._panel.setTitle_("Kitto")
        self._panel.setLevel_(AppKit.NSFloatingWindowLevel)
        self._panel.setHidesOnDeactivate_(False)
        self._panel.setMovableByWindowBackground_(True)
        self._panel.setBecomesKeyOnlyIfNeeded_(False)
        self._panel.setMinSize_(NSMakeSize(280, 200))

        # Window delegate (proper NSObject subclass)
        self._win_delegate = PopupWindowDelegate.alloc().init()
        self._win_delegate.popup = self
        self._panel.setDelegate_(self._win_delegate)

        content = self._panel.contentView()

        # ── search field ────────────────────────────────────────
        self._search_field = AppKit.NSSearchField.alloc().initWithFrame_(
            NSMakeRect(
                _PADDING,
                h - _SEARCH_HEIGHT - _PADDING,
                w - 2 * _PADDING,
                _SEARCH_HEIGHT,
            )
        )
        self._search_field.setPlaceholderString_("Type to search\u2026")
        self._search_field.setAutoresizingMask_(
            AppKit.NSViewWidthSizable | AppKit.NSViewMinYMargin
        )
        self._search_delegate = SearchDelegate.alloc().init()
        self._search_delegate.popup = self
        self._search_field.setDelegate_(self._search_delegate)
        content.addSubview_(self._search_field)

        # ── table scroll view ───────────────────────────────────
        table_h = h - _SEARCH_HEIGHT - 3 * _PADDING
        scroll = AppKit.NSScrollView.alloc().initWithFrame_(
            NSMakeRect(_PADDING, _PADDING, w - 2 * _PADDING, table_h)
        )
        scroll.setHasVerticalScroller_(True)
        scroll.setAutohidesScrollers_(True)
        scroll.setAutoresizingMask_(
            AppKit.NSViewWidthSizable | AppKit.NSViewHeightSizable
        )

        self._table = AppKit.NSTableView.alloc().initWithFrame_(
            NSMakeRect(0, 0, w - 2 * _PADDING, table_h)
        )

        col_content = AppKit.NSTableColumn.alloc().initWithIdentifier_("content")
        col_content.setWidth_(w - 100)
        col_content.setResizingMask_(AppKit.NSTableColumnAutoresizingMask)
        col_content.headerCell().setStringValue_("Content")
        self._table.addTableColumn_(col_content)

        col_time = AppKit.NSTableColumn.alloc().initWithIdentifier_("time")
        col_time.setWidth_(70)
        col_time.setMinWidth_(60)
        col_time.headerCell().setStringValue_("When")
        self._table.addTableColumn_(col_time)

        self._delegate = ClipTableDelegate.alloc().init()
        self._delegate.storage = self._storage
        self._delegate.popup = self
        self._table.setDataSource_(self._delegate)
        self._table.setDelegate_(self._delegate)
        self._table.setRowHeight_(_ROW_HEIGHT)
        self._table.setTarget_(self)
        self._table.setDoubleAction_(
            objc.selector(self._on_double_click, signature=b"v@:")
        )
        self._table.setGridStyleMask_(
            AppKit.NSTableViewSolidHorizontalGridLineMask
        )
        self._table.setUsesAlternatingRowBackgroundColors_(True)

        scroll.setDocumentView_(self._table)
        content.addSubview_(scroll)

        # ── tooltip ─────────────────────────────────────────────
        self._tooltip = TooltipWindow.create()
        self._delegate.tooltip = self._tooltip

    # ── data ────────────────────────────────────────────────────

    def _refresh_items(self):
        if self._query:
            self._delegate.items = self._storage.search(self._query)
        else:
            self._delegate.items = self._storage.recent()
        self._table.reloadData()
        if self._delegate.items:
            idx = AppKit.NSIndexSet.indexSetWithIndex_(0)
            self._table.selectRowIndexes_byExtendingSelection_(idx, False)

    # ── actions ─────────────────────────────────────────────────

    def _on_double_click(self):
        self.paste_selected()

    def _simulate_paste(self):
        """Post Cmd+V via Quartz to paste into the previously active app."""
        src = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
        event_down = Quartz.CGEventCreateKeyboardEvent(src, 0x09, True)  # 'v'
        Quartz.CGEventSetFlags(event_down, Quartz.kCGEventFlagMaskCommand)
        event_up = Quartz.CGEventCreateKeyboardEvent(src, 0x09, False)
        Quartz.CGEventSetFlags(event_up, Quartz.kCGEventFlagMaskCommand)
        Quartz.CGEventPost(Quartz.kCGAnnotatedSessionEventTap, event_down)
        Quartz.CGEventPost(Quartz.kCGAnnotatedSessionEventTap, event_up)

    def _save_geometry(self):
        frame = self._panel.frame()
        self._settings.set("window_width", int(frame.size.width))
        self._settings.set("window_height", int(frame.size.height))

    @property
    def is_visible(self):
        return self._visible
