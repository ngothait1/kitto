"""py2app build script for Kitto.

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ["kitto/main.py"]
DATA_FILES = []

OPTIONS = {
    "argv_emulation": False,
    "iconfile": "resources/Kitto.icns",
    "plist": {
        "CFBundleName": "Kitto",
        "CFBundleDisplayName": "Kitto",
        "CFBundleIdentifier": "com.kitto.clipboardmanager",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "LSMinimumSystemVersion": "12.0",
        "LSUIElement": True,  # hide from Dock
        "NSAppleEventsUsageDescription": "Kitto needs to simulate paste events.",
        "NSAccessibilityUsageDescription": (
            "Kitto needs Accessibility access to register "
            "global hotkeys and simulate paste."
        ),
    },
    "packages": ["kitto"],
    "includes": [
        "AppKit",
        "Foundation",
        "Quartz",
        "objc",
        "sqlite3",
    ],
}

setup(
    name="Kitto",
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
