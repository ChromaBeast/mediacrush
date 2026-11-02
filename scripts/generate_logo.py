"""Generates transparent, multi-resolution application icons and SVG for MediaCrush."""

import math
from pathlib import Path
from PIL import Image, ImageDraw

def render_svg(output_path: Path):
    svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="none">
  <defs>
    <linearGradient id="cyanGrad" x1="80" y1="80" x2="432" y2="432" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#38BDF8"/>
      <stop offset="60%" stop-color="#0EA5E9"/>
      <stop offset="100%" stop-color="#0284C7"/>
    </linearGradient>
    <linearGradient id="coreGrad" x1="160" y1="160" x2="352" y2="352" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#1E222B"/>
      <stop offset="100%" stop-color="#0F1116"/>
    </linearGradient>
  </defs>

  <!-- Left Compression Jaw -->
  <path d="M 120 110 L 230 220 L 230 292 L 120 402 L 72 364 L 162 256 L 72 148 Z" fill="url(#cyanGrad)"/>

  <!-- Right Compression Jaw -->
  <path d="M 392 110 L 282 220 L 282 292 L 392 402 L 440 364 L 350 256 L 440 148 Z" fill="url(#cyanGrad)"/>

  <!-- Center Titanium Crystal Core -->
  <polygon points="256,168 328,256 256,344 184,256" fill="url(#coreGrad)" stroke="#38BDF8" stroke-width="8" stroke-linejoin="round"/>

  <!-- Precision High-Density Play Core -->
  <polygon points="242,222 284,256 242,290" fill="#FFFFFF"/>
</svg>'''
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg_code, encoding="utf-8")


def render_raster_icons(base_dir: Path):
    size = 2048
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    scale = size / 512.0

    def pt(x, y):
        return (x * scale, y * scale)

    # Color palette
    cyan_bright = (56, 189, 248, 255)
    cyan_deep = (2, 132, 199, 255)
    titanium = (26, 30, 38, 255)
    cyan_border = (56, 189, 248, 230)
    white = (255, 255, 255, 255)

    # 1. Left Compression Jaw
    left_jaw = [pt(120, 110), pt(230, 220), pt(230, 292), pt(120, 402), pt(72, 364), pt(162, 256), pt(72, 148)]
    draw.polygon(left_jaw, fill=cyan_bright)

    # 2. Right Compression Jaw
    right_jaw = [pt(392, 110), pt(282, 220), pt(282, 292), pt(392, 402), pt(440, 364), pt(350, 256), pt(440, 148)]
    draw.polygon(right_jaw, fill=cyan_deep)

    # 3. Center Diamond Core
    center_diamond = [pt(256, 168), pt(328, 256), pt(256, 344), pt(184, 256)]
    draw.polygon(center_diamond, fill=titanium)
    draw.line(center_diamond + [center_diamond[0]], fill=cyan_border, width=int(8 * scale))

    # 4. Focal Play Arrow
    core_arrow = [pt(242, 222), pt(284, 256), pt(242, 290)]
    draw.polygon(core_arrow, fill=white)

    # Save multi-resolution PNGs
    resolutions = [1024, 512, 256, 128, 64, 32, 16]
    images_by_size = {}
    for r in resolutions:
        resized = img.resize((r, r), Image.Resampling.LANCZOS)
        out_file = base_dir / f"logo_{r}.png"
        resized.save(out_file, "PNG")
        images_by_size[r] = resized

    # Master logo.png
    images_by_size[1024].save(base_dir / "logo.png", "PNG")

    # Windows Multi-Icon ICO
    ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    ico_imgs = [images_by_size[s[0]] if s[0] in images_by_size else img.resize(s, Image.Resampling.LANCZOS) for s in ico_sizes]
    ico_imgs[0].save(base_dir / "app_icon.ico", format="ICO", sizes=ico_sizes)


def main():
    root = Path(__file__).resolve().parent.parent
    assets_dir = root / "assets"
    assets_dir.mkdir(exist_ok=True)

    render_svg(assets_dir / "logo.svg")
    render_raster_icons(assets_dir)
    print("Logo suite generated successfully in assets/")


if __name__ == "__main__":
    main()
