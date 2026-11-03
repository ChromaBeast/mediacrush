#!/usr/bin/env bash
set -e

echo "Building MediaCrush Native Linux App and Packages..."
cd desktop
flutter pub get
flutter build linux --release

# 1. Portable Tarball
mkdir -p ../dist/MediaCrush-Linux-x64
cp -r build/linux/x64/release/bundle/* ../dist/MediaCrush-Linux-x64/
if [ -f ../dist/mediacrush-linux-x86_64 ]; then
  cp ../dist/mediacrush-linux-x86_64 ../dist/MediaCrush-Linux-x64/mediacrush-cli
fi
if command -v ffmpeg &> /dev/null; then
  cp "$(which ffmpeg)" ../dist/MediaCrush-Linux-x64/
  cp "$(which ffprobe)" ../dist/MediaCrush-Linux-x64/
fi
if [ -f linux/mediacrush.png ]; then
  cp linux/mediacrush.png ../dist/MediaCrush-Linux-x64/
elif [ -f ../assets/logo_256.png ]; then
  cp ../assets/logo_256.png ../dist/MediaCrush-Linux-x64/mediacrush.png
fi
tar -czf ../dist/MediaCrush-Linux-x64.tar.gz -C ../dist MediaCrush-Linux-x64

# 2. Debian .deb package
DEB_DIR="../dist/deb_staging"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/lib/mediacrush"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$DEB_DIR/DEBIAN"

cp -r build/linux/x64/release/bundle/* "$DEB_DIR/usr/lib/mediacrush/"
if [ -f ../dist/mediacrush-linux-x86_64 ]; then
  cp ../dist/mediacrush-linux-x86_64 "$DEB_DIR/usr/lib/mediacrush/mediacrush-cli"
  chmod +x "$DEB_DIR/usr/lib/mediacrush/mediacrush-cli"
fi
if command -v ffmpeg &> /dev/null; then
  cp "$(which ffmpeg)" "$DEB_DIR/usr/lib/mediacrush/"
  cp "$(which ffprobe)" "$DEB_DIR/usr/lib/mediacrush/"
  chmod +x "$DEB_DIR/usr/lib/mediacrush/ffmpeg" "$DEB_DIR/usr/lib/mediacrush/ffprobe"
fi
if [ -f "$DEB_DIR/usr/lib/mediacrush/mediacrush-app" ]; then
  ln -sf /usr/lib/mediacrush/mediacrush-app "$DEB_DIR/usr/bin/mediacrush-app"
fi
if [ -f linux/mediacrush.png ]; then
  cp linux/mediacrush.png "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/mediacrush.png"
elif [ -f ../assets/logo_256.png ]; then
  cp ../assets/logo_256.png "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/mediacrush.png"
fi

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
Version: 1.0.3
Section: video
Priority: optional
Architecture: amd64
Maintainer: ChromaBeast <sheersh@chromabeast.com>
Description: Universal Hardware-Accelerated Media Optimizer
EOF

dpkg-deb --build "$DEB_DIR" ../dist/mediacrush_1.0.3_amd64.deb || true
rm -rf "$DEB_DIR"

echo "Linux packages assembled in dist/"
