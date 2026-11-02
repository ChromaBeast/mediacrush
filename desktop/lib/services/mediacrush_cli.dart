import 'dart:async';
import 'dart:io';
import 'package:path/path.dart' as p;
import '../models/hardware_engine.dart';
import '../models/media_item.dart';

/// Bridges the desktop UI with the MediaCrush CLI / Python engine.
class MediaCrushCli {
  static const List<String> videoExtensions = [
    '.mkv', '.mp4', '.avi', '.mov', '.ts', '.m2ts', '.webm', '.flv', '.wmv'
  ];

  Process? _activeProcess;

  /// Detects the system's available hardware encoder.
  Future<HardwareEngine> detectHardware() async {
    try {
      final res = await _runCommand(['detect']);
      if (res.exitCode == 0) {
        final out = res.stdout.toString().toLowerCase();
        if (out.contains('hevc_nvenc') || out.contains('nvidia')) {
          return HardwareEngine.fromCliName('hevc_nvenc');
        } else if (out.contains('hevc_videotoolbox') || out.contains('apple')) {
          return HardwareEngine.fromCliName('hevc_videotoolbox');
        } else if (out.contains('hevc_amf') || out.contains('amd')) {
          return HardwareEngine.fromCliName('hevc_amf');
        } else if (out.contains('hevc_qsv') || out.contains('intel')) {
          return HardwareEngine.fromCliName('hevc_qsv');
        } else if (out.contains('hevc_vaapi')) {
          return HardwareEngine.fromCliName('hevc_vaapi');
        }
      }
    } catch (_) {}
    return HardwareEngine.fallback();
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
        // Conservative projection: 55% reduction for H.264/raw
        final estimated = (size * 0.45).round();
        items.add(MediaItem(
          path: entity.path,
          fileName: p.basename(entity.path),
          codec: 'H.264',
          resolution: '1080p',
          originalBytes: size,
          estimatedBytes: estimated,
        ));
      } catch (_) {}
    }
    return items;
  }

  /// Runs the compression pipeline for a specific file or folder.
  Future<ProcessResult> _runCommand(List<String> args) async {
    if (await File('mediacrush.exe').exists() || await File('mediacrush').exists()) {
      return Process.run('mediacrush', args);
    }
    final scriptPath = p.join(Directory.current.parent.path, 'mediacrush_launcher.py');
    if (await File(scriptPath).exists()) {
      return Process.run('python', [scriptPath, ...args]);
    }
    return Process.run('python', ['-m', 'mediacrush.cli', ...args]);
  }

  void cancelActiveJob() {
    _activeProcess?.kill(ProcessSignal.sigterm);
    _activeProcess = null;
  }
}
