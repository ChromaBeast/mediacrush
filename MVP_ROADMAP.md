# MediaCrush — MVP Feature Roadmap

> **v1.0 shipped:** Core CLI + GUI with hardware-accelerated compression, recursive folder/subfolder support, smart skip logic, and safe staging pipeline.
>
> This document tracks all planned features for the official MVP release.

---

## Phase 2 — Smart Features

### 2.1 Watch Mode / Auto-Compress on New Files
Monitor a folder continuously. Whenever a new video file is added (e.g. a finished download), automatically compress it in the background.

```bash
mediacrush watch "E:\Movies" --preset anime
```

- **New file:** `mediacrush/core/watcher.py`
- **Dependency:** `watchdog`
- **Effort:** Small | **Impact:** Very High

---

### 2.2 Subtitle Extraction & External Sidecar Export
Before compression, extract all embedded subtitle tracks into sidecar `.srt` / `.ass` files, one per language. Enables stripping subtitles from the container for maximum size savings while keeping them accessible.

```bash
mediacrush extract-subs "E:\Movies\Black Clover"
# Outputs: black.clover.s02e02.eng.srt, black.clover.s02e02.jpn.srt ...
```

- **New file:** `mediacrush/core/subtitles.py`
- **Effort:** Small | **Impact:** Medium

---

### 2.3 Compression Report (HTML / JSON / CSV)
After a batch run, generate a detailed report covering every file processed: original size, new size, reduction %, time taken, encoder used, VMAF score (if checked).

```bash
mediacrush compress "E:\Movies" --report report.html
```

- **New file:** `mediacrush/core/reporter.py`
- **Template:** `mediacrush/templates/report.html`
- **Effort:** Small | **Impact:** High

---

### 2.4 Queue & Pause / Resume System
Allow users to pause an active batch job (e.g. to free GPU while gaming) and resume later from the same position — even across app restarts. State persisted to `queue.json`.

- **New file:** `mediacrush/core/queue.py`
- **State file:** `~/.mediacrush/queue.json`
- **Effort:** Medium | **Impact:** Very High for large libraries

---

### 2.5 Per-Folder Profile Config (`.mediacrush.json`)
Drop a `.mediacrush.json` into any folder to lock its compression settings. That folder will always use those settings regardless of what the CLI or GUI defaults are.

```json
{
  "preset": "anime",
  "skip_already_hevc": true,
  "in_place": true,
  "keep_backup": false
}
```

- **Changes:** `mediacrush/core/scanner.py` (reads local config per folder)
- **Effort:** Small | **Impact:** High

---

## Phase 3 — Visual Quality Upgrades

### 3.1 Auto Anime / Live-Action Detection
Automatically detect whether a video is 2D animation or live-action by sampling the first few frames using OpenCV (already installed). Applies `-tune animation` for anime automatically without requiring the user to pick a preset.

- **New file:** `mediacrush/core/content_classifier.py`
- **Dependency:** `opencv-python` (already installed)
- **Effort:** Medium | **Impact:** High — removes manual preset selection entirely

---

### 3.2 VMAF / SSIM Quality Score Verification
After encoding a short sample clip (first 30 seconds), measure visual quality retention using **VMAF** (already built into your FFmpeg as `libvmaf`) and **SSIM**. Gives objective per-file proof that quality was preserved.

```bash
mediacrush compress movie.mkv --quality-check
# Output: VMAF Score: 96.3 / 100  |  SSIM: 0.994  |  Quality: Excellent
```

- **New file:** `mediacrush/core/quality.py`
- **Dependency:** `libvmaf` (already in FFmpeg 8.0.1 build)
- **Effort:** Medium | **Impact:** Very High

---

### 3.3 HDR / Dolby Vision Metadata Pass-through
Detect HDR10 / Dolby Vision metadata in source files and safely pass it through to the output container without stripping or converting. Critical for 4K movie libraries.

- **Changes:** `mediacrush/core/probe.py` (HDR detection), `mediacrush/core/presets.py` (HDR encoder args)
- **Effort:** Medium | **Impact:** High for 4K content

---

## Phase 4 — Advanced CLI & Automation

### 4.1 Scheduled Overnight Compression
Generate a Windows Task Scheduler entry that runs compression automatically at a set time — useful for compressing large libraries overnight when the GPU is idle.

```bash
mediacrush schedule "E:\Movies" --at "02:00" --daily --preset anime
```

- **New file:** `mediacrush/core/scheduler.py`
- **Effort:** Medium | **Impact:** Very High for large library owners

---

### 4.2 Duplicate File Detector & Cleanup Report
Identify duplicate video files (same content in multiple formats, resolutions, or copies) using filename similarity, resolution, duration, and file size. Generates an interactive cleanup report.

```bash
mediacrush find-dupes "E:\Movies"
# Found: Spider-Man Brand New Day — 3 copies (12.75 GB + 6.82 GB + 3.19 GB)
# Suggested action: Keep 4K copy, delete 1080p duplicates → save 9.95 GB
```

- **New file:** `mediacrush/core/deduplicator.py`
- **Effort:** Small | **Impact:** Very High

---

### 4.3 REST API / Headless Server Mode
Run MediaCrush as a local HTTP server so other applications (e.g. Jellyfin, home automation scripts, webhooks) can trigger scans and compression jobs programmatically.

```bash
mediacrush serve --port 8765

# POST /api/scan   { "path": "E:/Movies" }
# POST /api/compress  { "path": "E:/Movies/Black Clover", "preset": "anime" }
# GET  /api/status
```

- **New folder:** `mediacrush/server/`
- **Dependency:** `fastapi`, `uvicorn` (already installed)
- **Effort:** Medium | **Impact:** High — enables integrations

---

## Phase 5 — GUI Upgrades

### 5.1 Modern GUI Overhaul (CustomTkinter or DearPyGUI)
Replace the current tkinter base with **CustomTkinter** (rounded widgets, native dark mode, polished look) or **DearPyGUI** (GPU-accelerated rendering, very fast with large file lists). Adds drag-and-drop folder loading.

- **Changes:** Refactor `mediacrush/gui/` entirely
- **Effort:** Medium | **Impact:** Very High for UX

---

### 5.2 Live GPU Monitor Panel
Show real-time GPU utilization, VRAM usage, encoder temperature, and encoding speed (fps / multiplier) as live gauges inside the GUI while compression is active.

- **New file:** `mediacrush/gui/gpu_monitor.py`
- **Dependency:** `pynvml` (NVIDIA) or `wmi` (cross-vendor)
- **Effort:** Medium | **Impact:** High

---

### 5.3 Library Browser Mode
A full visual media library manager inside the GUI: browse the folder tree, inspect per-file codec/bitrate/size, right-click individual files to compress or skip, and view a live pie chart of codec distribution across the entire library.

- **New file:** `mediacrush/gui/library_browser.py`
- **Effort:** Large | **Impact:** Very High — distinguishes MediaCrush from all other tools

---

## Phase 6 — Open Source & Distribution

### 6.1 Standalone Executable (PyInstaller / Nuitka)
Package MediaCrush as a single `.exe` (Windows) that users can download and run without installing Python or any dependencies. Optionally bundle FFmpeg.

```bash
pyinstaller --onefile --windowed mediacrush_launcher.py
```

- **Effort:** Small | **Impact:** Critical for adoption

---

### 6.2 GitHub Actions CI/CD Pipeline
Automated pipeline that:
- Runs all unit tests on every push
- Builds a Windows `.exe`, Linux binary, and macOS app bundle on release tags
- Auto-publishes to GitHub Releases and PyPI

- **New file:** `.github/workflows/release.yml`
- **Effort:** Medium | **Impact:** Critical for open source contributors

---

### 6.3 Cross-Platform Support (Linux & macOS)
Extend hardware detection for additional platforms:

| Platform | Hardware Encoder |
| :--- | :--- |
| Linux (NVIDIA) | `hevc_nvenc` via NVENC |
| Linux (AMD) | `hevc_vaapi` via VAAPI |
| Linux (Intel) | `hevc_vaapi` or `hevc_qsv` |
| macOS (Apple Silicon) | `hevc_videotoolbox` |
| Raspberry Pi / ARM Linux | V4L2 M2M encoder |

- **Changes:** `mediacrush/core/hardware.py` (platform-aware probe table)
- **Effort:** Medium | **Impact:** High — enables a much larger contributor base

---

## Priority Summary

| # | Feature | Effort | Impact | Phase |
| :-- | :--- | :--- | :--- | :--- |
| 1 | Duplicate File Detector | Small | ⭐ Very High | 4.2 |
| 2 | Watch Mode | Small | ⭐ Very High | 2.1 |
| 3 | VMAF / SSIM Quality Score | Medium | ⭐ Very High | 3.2 |
| 4 | Queue / Pause-Resume | Medium | ⭐ Very High | 2.4 |
| 5 | GUI Overhaul (CustomTkinter) | Medium | ⭐ Very High | 5.1 |
| 6 | Auto Anime Detection | Medium | High | 3.1 |
| 7 | Compression HTML Report | Small | High | 2.3 |
| 8 | HDR Pass-through | Medium | High | 3.3 |
| 9 | Per-Folder Config File | Small | High | 2.5 |
| 10 | Live GPU Monitor Panel | Medium | High | 5.2 |
| 11 | Standalone .exe | Small | ⭐ Critical | 6.1 |
| 12 | REST API Server | Medium | High | 4.3 |
| 13 | Scheduled Compression | Medium | High | 4.1 |
| 14 | Library Browser Mode | Large | ⭐ Very High | 5.3 |
| 15 | GitHub CI/CD | Medium | ⭐ Critical | 6.2 |
| 16 | Linux / macOS Support | Medium | High | 6.3 |
| 17 | Subtitle Extraction | Small | Medium | 2.2 |
