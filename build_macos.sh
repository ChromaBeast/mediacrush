#!/usr/bin/env bash
set -e

echo "Building MediaCrush standalone macOS executable and .dmg..."
python3 -m pip install --upgrade pip pyinstaller

# 1. Standalone CLI binary
pyinstaller \
    --onefile \
    --name mediacrush-macos \
    --hidden-import mediacrush.gui.app \
    --hidden-import mediacrush.gui.worker \
    --hidden-import mediacrush.gui.components \
    mediacrush_launcher.py

# 2. Windowed .app bundle for GUI
pyinstaller \
    --windowed \
    --name "MediaCrush" \
    --hidden-import mediacrush.gui.app \
    --hidden-import mediacrush.gui.worker \
    --hidden-import mediacrush.gui.components \
    mediacrush_launcher.py

# 3. Assemble .dmg with drag-to-Applications shortcut
mkdir -p dist/dmg_staging
cp -r dist/MediaCrush.app dist/dmg_staging/
ln -s /Applications dist/dmg_staging/Applications
hdiutil create -volname "MediaCrush" -srcfolder dist/dmg_staging -ov -format UDZO dist/MediaCrush.dmg
rm -rf dist/dmg_staging

echo "Build complete: dist/mediacrush-macos and dist/MediaCrush.dmg"
