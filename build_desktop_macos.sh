#!/usr/bin/env bash
set -e

echo "Building MediaCrush Native macOS App..."
cd desktop
flutter pub get
flutter build macos --release

mkdir -p ../dist
cp -r build/macos/Build/Products/Release/MediaCrush.app ../dist/
echo "Native macOS .app bundle assembled in: dist/MediaCrush.app"
