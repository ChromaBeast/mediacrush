import 'dart:async';
import 'dart:io';
import 'package:path/path.dart' as p;
import '../models/hardware_engine.dart';
import '../models/media_item.dart';

/// Bridges the desktop UI with FFmpeg and the MediaCrush CLI engine.
class MediaCrushCli {
  static const List<String> videoExtensions = [
    '.mkv', '.mp4', '.avi', '.mov', '.ts', '.m2ts', '.webm', '.flv', '.wmv'
  ];

  Process? _activeProcess;

  /// Detects available hardware encoders via direct FFmpeg probing or CLI backend.
  Future<HardwareEngine> detectHardware() async {
    // 1. Probe direct FFmpeg first (safest, fastest, no child GUI spawning)
    final direct = await _detectFfmpegEncoder();
    if (direct != null) return direct;

    // 2. Safe check against distinct CLI backend
    try {
      final res = await _runCommand(['detect']);
      if (res != null && res.exitCode == 0) {
        final out = res.stdout.toString().toLowerCase();
        for (final name in ['hevc_nvenc', 'hevc_videotoolbox', 'hevc_amf', 'hevc_qsv', 'hevc_vaapi']) {
          if (out.contains(name)) return HardwareEngine.fromCliName(name);
        }
      }
    } catch (_) {}

    return HardwareEngine.fallback();
  }

  /// Probes hardware encoders directly using ffmpeg 1-frame dummy check.
  Future<HardwareEngine?> _detectFfmpegEncoder() async {
    final candidates = [
      if (Platform.isMacOS) 'hevc_videotoolbox',
      if (Platform.isWindows || Platform.isLinux) 'hevc_nvenc',
      if (Platform.isWindows) 'hevc_amf',
      if (Platform.isWindows || Platform.isLinux) 'hevc_qsv',
      if (Platform.isLinux) 'hevc_vaapi',
    ];

    for (final enc in candidates) {
      try {
        final res = await Process.run(
          'ffmpeg',
          ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=256x256:d=0.04', '-frames:v', '1', '-c:v', enc, '-f', 'null', '-'],
        ).timeout(const Duration(milliseconds: 1500));
        if (res.exitCode == 0) {
          return HardwareEngine.fromCliName(enc);
        }
      } catch (_) {
        // ffmpeg not found or candidate unsupported
      }
    }
    return null;
  }

  /// Scans a folder tree directly for candidate media files.
  Future<List<MediaItem>> scanDirectory(String dirPath) async {
    final dir = Directory(dirPath);
    if (!await dir.exists()) return [];

    final items = <MediaItem>[];
    await for (final entity in dir.list(recursive: true, followLinks: false)) {
      if (entity is! File) continue;
      final ext = p.extension(entity.path).toLowerCase();
      if (!videoExtensions.contains(ext)) continue;

      try {
        final stat = await entity.stat();
        final size = stat.size;
        items.add(MediaItem(
          path: entity.path,
          fileName: p.basename(entity.path),
          codec: 'H.264',
          resolution: '1080p',
          originalBytes: size,
          estimatedBytes: (size * 0.45).round(),
        ));
      } catch (_) {}
    }
    return items;
  }

  /// Runs the backend CLI safely without risk of invoking the GUI executable itself.
  Future<ProcessResult?> _runCommand(List<String> args) async {
    final exeDir = p.dirname(Platform.resolvedExecutable);
    final currentExeName = p.basename(Platform.resolvedExecutable).toLowerCase();
    final cliName = Platform.isWindows ? 'mediacrush-cli.exe' : 'mediacrush-cli';

    // 1. Dedicated bundled CLI executable
    final bundledCli = p.join(exeDir, cliName);
    if (await File(bundledCli).exists() && cliName != currentExeName) {
      return Process.run(bundledCli, args);
    }

    // 2. CLI in working directory if distinct from GUI
    final cwdCli = p.join(Directory.current.path, cliName);
    if (await File(cwdCli).exists() && cliName != currentExeName) {
      return Process.run(cwdCli, args);
    }

    // 3. Local Python development launcher
    final scriptPath = p.join(Directory.current.parent.path, 'mediacrush_launcher.py');
    if (await File(scriptPath).exists()) {
      return Process.run('python', [scriptPath, ...args]);
    }

    return null;
  }

  void cancelActiveJob() {
    _activeProcess?.kill(ProcessSignal.sigterm);
    _activeProcess = null;
  }
}
