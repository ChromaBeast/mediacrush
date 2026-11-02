# MediaCrush 🚀

**MediaCrush** is a universal, open-source, hardware-accelerated media optimizer and compressor for movie, TV show, and anime libraries.

It safely shrinks bloated video files (such as raw WEB-DLs taking 1.8 GB per episode) by **40% to 75%** with **zero perceptible visual loss**, automatically leveraging whatever GPU or CPU hardware acceleration is available on the machine.

---

## ⚡ Supported Hardware Accelerators

| Vendor / Architecture | Target Platform | Hardware Encoder |
| :--- | :--- | :--- |
| **Apple Silicon (M1–M4)** | macOS (MacBook Pro/Air, Mac Studio/mini) | `hevc_videotoolbox`, `av1_videotoolbox` |
| **Intel Mac (Iris/Radeon)** | macOS (Intel MacBook Pro, iMac) | `hevc_videotoolbox`, `h264_videotoolbox` |
| **NVIDIA GPU** | GeForce GTX/RTX, Ada Lovelace (Windows & Linux) | `hevc_nvenc`, `av1_nvenc` |
| **AMD GPU / APU** | Radeon RX, RDNA 2/3 (Windows & Linux) | `hevc_amf`, `hevc_vaapi` |
| **Intel GPU / iGPU** | Arc, Iris Xe, Core Ultra (Windows & Linux) | `hevc_qsv`, `hevc_vaapi` |
| **Snapdragon X Elite / X Plus** | Qualcomm Adreno (Windows on ARM64) | `hevc_mf`, `av1_mf` |
| **Multi-Core CPU** | AMD Ryzen, Intel Core, Apple Silicon (Universal) | `libx265`, `libsvtav1` |

---

## 🛡️ Safety & Quality Guarantee

- **Bit-for-Bit Stream Preservation:** All audio streams (`-c:a copy`) and all subtitle tracks (`-c:s copy`) are kept identical to source without desync.
- **Staging Verification:** Outputs to a `.mediacrush.temp.mkv` staging file and checks duration and stream integrity before in-place atomic finalization.
- **Smart Skip Logic:** Automatically skips files already encoded in HEVC/AV1 with optimal bitrates.
- **Deep Recursive Traversal:** Processes full movie/series folder trees including all nested subfolders.

---

## 💻 CLI Usage

```bash
# Detect functional hardware encoders on this PC
mediacrush detect

# Scan a folder and all subfolders without touching files
mediacrush scan "E:\Movies"

# Compress folder & subfolders with hardware acceleration
mediacrush compress "E:\Movies\Black Clover" --preset anime

# Side-by-side mode (saves as *.crushed.mkv rather than replacing original)
mediacrush compress "E:\Movies\Black Clover" --side-by-side

# Launch the desktop GUI
mediacrush gui
```

---

## 🖥️ Desktop GUI

Launch with:
```bash
mediacrush gui
```
- Modern dark mode dashboard.
- Drag-and-drop / folder picker with live scan stats.
- Visual progress bar, speed indicator, and real-time space reclaimed counter.
