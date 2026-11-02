#!/usr/bin/env bash
set -e

echo "Building MediaCrush Native Linux App..."
cd desktop
flutter pub get
flutter build linux --release

mkdir -p ../dist/MediaCrush-Linux-x64
cp -r build/linux/x64/release/bundle/* ../dist/MediaCrush-Linux-x64/
echo "Native Linux app bundle assembled in: dist/MediaCrush-Linux-x64"
