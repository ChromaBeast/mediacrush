#!/usr/bin/env bash
set -e

echo "Building MediaCrush standalone Linux executable..."
python3 -m pip install --upgrade pip pyinstaller
pyinstaller \
    --onefile \
    --name mediacrush-linux \
    --hidden-import mediacrush.gui.app \
    --hidden-import mediacrush.gui.worker \
    --hidden-import mediacrush.gui.components \
    mediacrush_launcher.py

chmod +x dist/mediacrush-linux
echo "Build complete: dist/mediacrush-linux"
