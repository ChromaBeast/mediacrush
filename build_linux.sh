#!/usr/bin/env bash
set -e

ARCH=$(uname -m)
echo "Building MediaCrush standalone Linux binary for $ARCH..."
python3 -m pip install --upgrade pip pyinstaller

pyinstaller \
    --onefile \
    --name "mediacrush-linux-$ARCH" \
    --hidden-import mediacrush.gui.app \
    --hidden-import mediacrush.gui.worker \
    --hidden-import mediacrush.gui.components \
    mediacrush_launcher.py

chmod +x "dist/mediacrush-linux-$ARCH"
echo "Build complete: dist/mediacrush-linux-$ARCH"
