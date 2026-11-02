#!/usr/bin/env bash
set -e

echo "Building MediaCrush standalone macOS executable (Apple Silicon / Intel)..."
python3 -m pip install --upgrade pip pyinstaller
pyinstaller \
    --onefile \
    --name mediacrush-macos \
    --hidden-import mediacrush.gui.app \
    --hidden-import mediacrush.gui.worker \
    --hidden-import mediacrush.gui.components \
    mediacrush_launcher.py

chmod +x dist/mediacrush-macos
echo "Build complete: dist/mediacrush-macos"
