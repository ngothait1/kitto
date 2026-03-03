"""SQLite storage with LRU eviction for clipboard items.

Supports text (any language/Unicode), images, RTF, HTML, and file references.
"""

import sqlite3
import time

_SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    content     BLOB    NOT NULL,
    content_type TEXT   NOT NULL DEFAULT 'text',
    preview     TEXT    NOT NULL DEFAULT '',
    byte_size   INTEGER NOT NULL DEFAULT 0,
    pinned      INTEGER NOT NULL DEFAULT 0,
    created_at  REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_created ON items(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_preview ON items(preview);
"""


class Storage:
    def __init__(self, db_path: str, max_items: int = 500):
        self._max = max_items
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # ── write ───────────────────────────────────────────────────

    def add(self, content: bytes, content_type: str, preview: str) -> int:
        """Insert an item and enforce the LRU cap. Returns the new row id."""
        cur = self._conn.execute(
            "INSERT INTO items (content, content_type, preview, byte_size, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (content, content_type, preview, len(content), time.time()),
        )
        self._conn.commit()
        self._enforce_limit()
        return cur.lastrowid

    def delete(self, item_id: int):
        self._conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        self._conn.commit()

    def toggle_pin(self, item_id: int):
        self._conn.execute(
            "UPDATE items SET pinned = 1 - pinned WHERE id = ?", (item_id,)
        )
        self._conn.commit()

    def clear_all(self):
        """Delete every non-pinned item."""
        self._conn.execute("DELETE FROM items WHERE pinned = 0")
        self._conn.commit()

    # ── read ────────────────────────────────────────────────────

    def recent(self, limit: int = 500, offset: int = 0) -> list:
        """Return items newest-first as list of dicts (without heavy content blob)."""
        rows = self._conn.execute(
            "SELECT id, content_type, preview, byte_size, pinned, created_at "
            "FROM items ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [
            {
                "id": r[0],
                "content_type": r[1],
                "preview": r[2],
                "byte_size": r[3],
                "pinned": bool(r[4]),
                "created_at": r[5],
            }
            for r in rows
        ]

    def search(self, query: str, limit: int = 100) -> list:
        """Case-insensitive 'contains' search on the preview text."""
        rows = self._conn.execute(
            "SELECT id, content_type, preview, byte_size, pinned, created_at "
            "FROM items WHERE preview LIKE ? "
            "ORDER BY created_at DESC LIMIT ?",
            (f"%{query}%", limit),
        ).fetchall()
        return [
            {
                "id": r[0],
                "content_type": r[1],
                "preview": r[2],
                "byte_size": r[3],
                "pinned": bool(r[4]),
                "created_at": r[5],
            }
            for r in rows
        ]

    def get_content(self, item_id: int) -> tuple | None:
        """Return (content_bytes, content_type) for a given id."""
        row = self._conn.execute(
            "SELECT content, content_type FROM items WHERE id = ?", (item_id,)
        ).fetchone()
        return (row[0], row[1]) if row else None

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]

    def is_duplicate(self, content: bytes, content_type: str) -> bool:
        """Check if the most recent item has identical content (avoid double-saves)."""
        row = self._conn.execute(
            "SELECT content, content_type FROM items ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return False
        return row[0] == content and row[1] == content_type

    # ── internal ────────────────────────────────────────────────

    def _enforce_limit(self):
        """Delete oldest non-pinned items when over the cap."""
        total = self.count()
        if total <= self._max:
            return
        overflow = total - self._max
        self._conn.execute(
            "DELETE FROM items WHERE id IN ("
            "  SELECT id FROM items WHERE pinned = 0 "
            "  ORDER BY created_at ASC LIMIT ?"
            ")",
            (overflow,),
        )
        self._conn.commit()

    def close(self):
        self._conn.close()
