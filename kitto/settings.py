"""Persistent settings for Kitto stored in ~/Library/Application Support/Kitto/."""

import json
import os

_DEFAULTS = {
    "hotkey_modifiers": ["command", "shift"],
    "hotkey_key": "v",
    "max_items": 500,
    "window_width": 420,
    "window_height": 500,
    "theme": "system",
}

_APP_SUPPORT = os.path.join(
    os.path.expanduser("~"), "Library", "Application Support", "Kitto"
)
_SETTINGS_FILE = os.path.join(_APP_SUPPORT, "settings.json")


class Settings:
    def __init__(self):
        os.makedirs(_APP_SUPPORT, exist_ok=True)
        self._data = dict(_DEFAULTS)
        self._load()

    # ── public API ──────────────────────────────────────────────

    def get(self, key: str):
        return self._data.get(key, _DEFAULTS.get(key))

    def set(self, key: str, value):
        self._data[key] = value
        self._save()

    def all(self) -> dict:
        return dict(self._data)

    @property
    def db_path(self) -> str:
        return os.path.join(_APP_SUPPORT, "clipboard.db")

    @property
    def max_items(self) -> int:
        return self._data.get("max_items", 500)

    @property
    def hotkey_modifiers(self) -> list:
        return self._data.get("hotkey_modifiers", _DEFAULTS["hotkey_modifiers"])

    @property
    def hotkey_key(self) -> str:
        return self._data.get("hotkey_key", _DEFAULTS["hotkey_key"])

    @property
    def window_width(self) -> int:
        return self._data.get("window_width", _DEFAULTS["window_width"])

    @property
    def window_height(self) -> int:
        return self._data.get("window_height", _DEFAULTS["window_height"])

    # ── persistence ─────────────────────────────────────────────

    def _load(self):
        if os.path.exists(_SETTINGS_FILE):
            try:
                with open(_SETTINGS_FILE, "r") as f:
                    self._data.update(json.load(f))
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self):
        try:
            with open(_SETTINGS_FILE, "w") as f:
                json.dump(self._data, f, indent=2)
        except OSError:
            pass
