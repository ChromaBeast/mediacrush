#!/usr/bin/env bash
set -e

echo "Building MediaCrush Native macOS App and .dmg Installer..."
cd desktop
flutter pub get
flutter build macos --release

mkdir -p ../dist/dmg_staging
APP_BUNDLE=$(find build/macos/Build/Products/Release -maxdepth 1 -name "*.app" | head -n 1)
if [ -z "$APP_BUNDLE" ]; then
  echo "Error: No .app bundle found in build/macos/Build/Products/Release"
  exit 1
fi
echo "Found app bundle: $APP_BUNDLE, staging as MediaCrush.app..."
cp -r "$APP_BUNDLE" ../dist/dmg_staging/MediaCrush.app
ln -s /Applications ../dist/dmg_staging/Applications
hdiutil create -volname "MediaCrush" -srcfolder ../dist/dmg_staging -ov -format UDZO ../dist/MediaCrush-macOS-Universal.dmg
rm -rf ../dist/dmg_staging

echo "Native macOS installer assembled: dist/MediaCrush-macOS-Universal.dmg"
