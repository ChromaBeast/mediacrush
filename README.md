# MediaCrush

**Universal, Hardware-Accelerated Media Optimizer & Compression Engine**  
*Shrink movie, TV show, and anime libraries by **40% to 75%** with **zero perceptible visual loss**.*

[![CI](https://github.com/ChromaBeast/mediacrush/actions/workflows/ci.yml/badge.svg)](https://github.com/ChromaBeast/mediacrush/actions/workflows/ci.yml)
[![Release](https://github.com/ChromaBeast/mediacrush/actions/workflows/release.yml/badge.svg)](https://github.com/ChromaBeast/mediacrush/actions/workflows/release.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platforms: Windows | macOS | Linux](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-green.svg)](#cross-platform-hardware-matrix)

---

## Why MediaCrush?

Modern media releases (WEB-DLs, scene rips, Remuxes) frequently consume **1.5 GB to 4.5 GB per single 24-minute episode** and **15 GB to 40 GB per film**, often using legacy or inefficient encoding parameters.

MediaCrush scans your entire storage tree and recompresses bloat into modern **HEVC (H.265) / AV1** using your machine's dedicated hardware silicon blocks—delivering **120 to 300+ fps encoding speeds** while preserving 100% of the original audio, subtitles, and visual fidelity.

---

## Cross-Platform Hardware Matrix

MediaCrush automatically detects and activates whatever hardware encoding silicon is present on your device:

| Vendor / Platform | Supported Hardware | Native Hardware Encoder | Typical Speed |
| :--- | :--- | :--- | :--- |
| **Apple Silicon (M1–M6)** | MacBook Pro/Air, Mac Studio, Mac mini | `hevc_videotoolbox`, `av1_videotoolbox` | 150–250+ fps |
| **Intel Mac** | MacBook Pro, iMac (Iris Plus / AMD Radeon Pro) | `hevc_videotoolbox`, `h264_videotoolbox` | 80–160 fps |
| **NVIDIA GPU** | GeForce GTX/RTX, Ada Lovelace, Blackwell | `hevc_nvenc`, `av1_nvenc` (CUDA) | 150–320+ fps |
| **AMD GPU / APU** | Radeon RX 6000/7000/8000, Radeon 700M/800M | `hevc_amf` (Win), `hevc_vaapi` (Linux) | 120–220 fps |
| **Intel GPU / iGPU** | Arc, Iris Xe, Core Ultra (Meteor / Lunar Lake) | `hevc_qsv` (Win), `hevc_vaapi` (Linux) | 120–220 fps |
| **Snapdragon X** | Qualcomm Adreno (Windows on ARM64) | `hevc_mf`, `av1_mf` (D3D11 Media Foundation) | 100–180 fps |
| **Multi-Core CPU** | AMD Ryzen, Intel Core, Apple Silicon | `libx265`, `libsvtav1` (Universal Fallback) | 10–25 fps |

---

## Features at a Glance

* **Zero-Copy Hardware Pipeline:** Pre-pends hardware decoding (`-hwaccel auto`) and GPU encoding for minimal CPU consumption and heat.
* **Lossless Stream Preservation:** All audio tracks (`-c:a copy`), subtitle streams (`-c:s copy`), and container metadata are copied bit-for-bit without desync.
* **Safe Staging & Atomic Swaps:** Encodes to an isolated temporary file (`*.mediacrush.temp.mkv`), rigorously verifies duration and audio track integrity with `ffprobe`, and only commits upon success.
* **Objective VMAF & SSIM Verification:** Run `--quality-check` to measure retention mathematically via FFmpeg's built-in `libvmaf` engine (typically 93–97/100).
* **HDR10 & Dolby Vision Pass-through:** Preserves BT.2020 color primaries, SMPTE 2084 transfer characteristics, and dynamic side-data without color banding or crushing.
* **Smart Content Classifier:** Automatically samples keyframes to differentiate 2D animation/anime from live-action film, applying tuned spatial quantization.
* **Duplicate Media Cleanup:** `mediacrush find-dupes` groups redundant copies (e.g. 4K vs 1080p duplicates) and calculates reclaimable disk space.
* **Continuous Watch Mode:** `mediacrush watch` continuously monitors download folders and compresses incoming videos in the background.
* **Pause & Resume System:** Batch jobs can be paused anytime and resumed across restarts via persistent state (`~/.mediacrush/queue.json`).
* **HTML & JSON Reporting:** Output detailed per-file compression metrics, reduction percentages, and execution times (`--report report.html`).
* **Per-Folder Overrides:** Drop a `.mediacrush.json` into any subfolder to lock specific preset or skip rules for that folder.
* **Modern Desktop GUI:** Built-in dark mode dashboard with live progress and real-time space reclaimed counters.

---

## Installation & Downloads

### Option 1: Standalone Binaries (No Python Required)
Download the native package for your operating system and architecture from the **[GitHub Releases](https://github.com/ChromaBeast/mediacrush/releases)** page:

* **Windows:**
  * `mediacrush-windows-x64.exe` (Standard 64-bit Intel & AMD)
  * `mediacrush-windows-arm64.exe` (Qualcomm Snapdragon X Elite / Windows on ARM)
  * `mediacrush-windows-x86.exe` (Legacy 32-bit PCs)
* **macOS:**
  * `MediaCrush.dmg` (Drag-to-Applications installer for Apple Silicon & Intel)
  * `mediacrush-macos` (Standalone terminal CLI binary)
* **Linux:**
  * `mediacrush-linux-x86_64` (Standard 64-bit Intel & AMD)
  * `mediacrush-linux-arm64` (ARM64 / Raspberry Pi / ARM servers)

### Option 2: Via Pip / Pipx
```bash
# Recommended for CLI users:
pipx install mediacrush

# Or standard pip:
pip install mediacrush
```

*Prerequisite:* Ensure [FFmpeg](https://ffmpeg.org/download.html) is installed and accessible in your system `PATH`.

---

## CLI Usage

### 1. Hardware Detection
Inspect functional hardware encoders discovered on your machine:
```bash
mediacrush detect
```

### 2. Scan Library Without Modifying Files
Simulate space savings and discover bloat across all nested subfolders:
```bash
mediacrush scan "E:\Movies"
```

### 3. Compress Folder Tree
Compress an entire library or single season:
```bash
# Auto-detects content type (anime vs live action) and applies hardware encoding
mediacrush compress "E:\Anime\Frieren"

# Explicit preset selection (anime | film | saver)
mediacrush compress "E:\Movies" --preset film

# Verify visual quality with VMAF & SSIM scoring
mediacrush compress "E:\Movies" --quality-check

# Generate an HTML compression summary report
mediacrush compress "E:\Movies" --report report.html

# Non-destructive test (saves as *.crushed.mkv rather than replacing original)
mediacrush compress "E:\Movies" --side-by-side

# Backup original as *.bak
mediacrush compress "E:\Movies" --keep-backup
```

### 4. Continuous Folder Watcher
Monitor your finished downloads folder in the background:
```bash
mediacrush watch "D:\Downloads\Complete" --preset auto
```

### 5. Resume Interrupted Batches
Resume any paused or interrupted compression jobs:
```bash
mediacrush resume
```

### 6. Find Duplicate Media
Detect redundant copies across your libraries:
```bash
mediacrush find-dupes "E:\Movies"
```

---

## Desktop GUI

Launch the desktop interface with:
```bash
mediacrush gui
```

* **Dark Theme:** Sleek, distraction-free modern UI.
* **Scan & Estimation:** Live candidate counters, current size, and projected savings.
* **Real-time Monitoring:** Real-time speed indicator (fps / multiplier) and progress tracking.

---

## Per-Folder Configuration (.mediacrush.json)

You can place a `.mediacrush.json` file inside any folder to override default settings:

```json
{
  "preset": "anime",
  "skip_already_hevc": true,
  "in_place": true
}
```

---

## Running Tests

MediaCrush includes a test suite covering hardware detection, safety staging, preset generation, and skip logic without requiring external media files:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest tests/ -v --cov=mediacrush --cov-report=term-missing
```

---

## License

Distributed under the **MIT License**. See `LICENSE` for details.
