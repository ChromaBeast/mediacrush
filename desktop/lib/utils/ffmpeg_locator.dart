import 'dart:io';
import 'package:path/path.dart' as p;

/// Resolves bundled or system FFmpeg and FFprobe binary paths across desktop platforms.
abstract final class FfmpegLocator {
  static String? _cachedFfmpeg;
  static String? _cachedFfprobe;

  /// Returns the absolute path to the bundled or system ffmpeg binary.
  static Future<String> getFfmpegPath() async {
    if (_cachedFfmpeg != null && await _testBinary(_cachedFfmpeg!)) {
      return _cachedFfmpeg!;
    }

    final exeDir = p.dirname(Platform.resolvedExecutable);
    final isWin = Platform.isWindows;
    final binaryName = isWin ? 'ffmpeg.exe' : 'ffmpeg';

    final candidates = [
      p.join(exeDir, binaryName),
      p.join(exeDir, 'tools', binaryName),
      p.join(exeDir, 'lib', binaryName),
      if (Platform.isMacOS) p.join(exeDir, '..', 'Resources', binaryName),
      p.join(Directory.current.path, binaryName),
      binaryName, // System PATH fallback
    ];

    for (final candidate in candidates) {
      if (await _testBinary(candidate)) {
        _cachedFfmpeg = candidate;
        return candidate;
      }
    }

    return binaryName;
  }

  /// Returns the absolute path to the bundled or system ffprobe binary.
  static Future<String> getFfprobePath() async {
    if (_cachedFfprobe != null && await _testBinary(_cachedFfprobe!)) {
      return _cachedFfprobe!;
    }

    final exeDir = p.dirname(Platform.resolvedExecutable);
    final isWin = Platform.isWindows;
    final binaryName = isWin ? 'ffprobe.exe' : 'ffprobe';

    final candidates = [
      p.join(exeDir, binaryName),
      p.join(exeDir, 'tools', binaryName),
      p.join(exeDir, 'lib', binaryName),
      if (Platform.isMacOS) p.join(exeDir, '..', 'Resources', binaryName),
      p.join(Directory.current.path, binaryName),
      binaryName,
    ];

    for (final candidate in candidates) {
      if (await _testBinary(candidate)) {
        _cachedFfprobe = candidate;
        return candidate;
      }
    }

    return binaryName;
  }

  /// Verifies if a functional FFmpeg binary is available.
  static Future<bool> isFfmpegAvailable() async {
    final path = await getFfmpegPath();
    return _testBinary(path);
  }

  static Future<bool> _testBinary(String executablePath) async {
    try {
      if (executablePath.contains(p.separator) && !await File(executablePath).exists()) {
        return false;
      }
      final res = await Process.run(
        executablePath,
        ['-version'],
      ).timeout(const Duration(seconds: 2));
      return res.exitCode == 0;
    } catch (_) {
      return false;
    }
  }
}
