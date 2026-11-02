#!/usr/bin/env bash
set -e

echo "Building MediaCrush Native macOS App and .dmg Installer..."
cd desktop
flutter pub get
flutter build macos --release

mkdir -p ../dist/dmg_staging
cp -r build/macos/Build/Products/Release/MediaCrush.app ../dist/dmg_staging/
ln -s /Applications ../dist/dmg_staging/Applications
hdiutil create -volname "MediaCrush" -srcfolder ../dist/dmg_staging -ov -format UDZO ../dist/MediaCrush-macOS-Universal.dmg
rm -rf ../dist/dmg_staging

echo "Native macOS installer assembled: dist/MediaCrush-macOS-Universal.dmg"
