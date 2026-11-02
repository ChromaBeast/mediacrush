#!/usr/bin/env bash
set -e

echo "Building MediaCrush Native Linux App and Packages..."
cd desktop
flutter pub get
flutter build linux --release

# 1. Portable Tarball
mkdir -p ../dist/MediaCrush-Linux-x64
cp -r build/linux/x64/release/bundle/* ../dist/MediaCrush-Linux-x64/
cp mediacrush.png ../dist/MediaCrush-Linux-x64/
tar -czf ../dist/MediaCrush-Linux-x64.tar.gz -C ../dist MediaCrush-Linux-x64

# 2. Debian .deb package
DEB_DIR="../dist/deb_staging"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/lib/mediacrush"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$DEB_DIR/DEBIAN"

cp -r build/linux/x64/release/bundle/* "$DEB_DIR/usr/lib/mediacrush/"
ln -sf /usr/lib/mediacrush/mediacrush-app "$DEB_DIR/usr/bin/mediacrush-app"
cp mediacrush.png "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/mediacrush.png"

cat << 'EOF' > "$DEB_DIR/usr/share/applications/mediacrush.desktop"
[Desktop Entry]
Name=MediaCrush
Comment=Universal Hardware-Accelerated Media Optimizer
Exec=/usr/bin/mediacrush-app
Icon=mediacrush
Terminal=false
Type=Application
Categories=AudioVideo;Video;AudioVideoEditing;
EOF

cat << 'EOF' > "$DEB_DIR/DEBIAN/control"
Package: mediacrush
Version: 1.0.1
Section: video
Priority: optional
Architecture: amd64
Maintainer: ChromaBeast <sheersh@chromabeast.com>
Description: Universal Hardware-Accelerated Media Optimizer
EOF

dpkg-deb --build "$DEB_DIR" ../dist/mediacrush_1.0.1_amd64.deb || true
rm -rf "$DEB_DIR"

echo "Linux packages assembled in dist/"
