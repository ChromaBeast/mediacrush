import 'dart:async';
import 'dart:convert';
import 'dart:io';
import '../models/hardware_engine.dart';
import '../utils/ffmpeg_locator.dart';

/// Real FFmpeg hardware-accelerated transcoding engine with live progress parsing.
class TranscodeService {
  Process? _activeProcess;
  bool _isCancelled = false;

  static final RegExp _timeRegex = RegExp(r'time=(\d+):(\d+):(\d+\.\d+)');

  /// Transcodes an input media file to outputPath using the selected hardware engine.
  Future<bool> transcode({
    required String inputPath,
    required String outputPath,
    required HardwareEngine engine,
    required String preset,
    required void Function(double progress) onProgress,
  }) async {
    _isCancelled = false;
    final totalDuration = await _getDuration(inputPath);

    final args = _buildFfmpegArgs(
      inputPath: inputPath,
      outputPath: outputPath,
      engine: engine,
      preset: preset,
    );

    try {
      final ffmpegBin = await FfmpegLocator.getFfmpegPath();
      final process = await Process.start(ffmpegBin, args);
      _activeProcess = process;

      process.stderr.transform(utf8.decoder).transform(const LineSplitter()).listen((line) {
        if (_isCancelled) return;
        final match = _timeRegex.firstMatch(line);
        if (match != null && totalDuration > 0) {
          final h = int.tryParse(match.group(1)!) ?? 0;
          final m = int.tryParse(match.group(2)!) ?? 0;
          final s = double.tryParse(match.group(3)!) ?? 0.0;
          final currentSecs = (h * 3600) + (m * 60) + s;
          final progress = (currentSecs / totalDuration).clamp(0.0, 0.99);
          onProgress(progress);
        }
      });

      final exitCode = await process.exitCode;
      _activeProcess = null;

      if (_isCancelled || exitCode != 0) {
        _cleanupFailedOutput(outputPath);
        return false;
      }

      final outFile = File(outputPath);
      if (await outFile.exists() && await outFile.length() > 0) {
        onProgress(1.0);
        return true;
      }
    } catch (_) {
      _cleanupFailedOutput(outputPath);
    }

    return false;
  }

  /// Probes the duration of the media file using ffprobe.
  Future<double> _getDuration(String filePath) async {
    try {
      final ffprobeBin = await FfmpegLocator.getFfprobePath();
      final res = await Process.run(ffprobeBin, [
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        filePath,
      ]).timeout(const Duration(seconds: 4));

      if (res.exitCode == 0) {
        return double.tryParse(res.stdout.toString().trim()) ?? 0.0;
      }
    } catch (_) {}
    return 0.0;
  }

  /// Builds optimized FFmpeg arguments.
  List<String> _buildFfmpegArgs({
    required String inputPath,
    required String outputPath,
    required HardwareEngine engine,
    required String preset,
  }) {
    final enc = engine.name;
    final isNvenc = enc.contains('nvenc');
    final isApple = enc.contains('videotoolbox');
    final isAmf = enc.contains('amf');
    final isQsv = enc.contains('qsv');

    final cq = preset == 'saver' ? '24' : '20';
    final crf = preset == 'saver' ? '24' : '20';

    final args = <String>['-y', '-i', inputPath];

    if (isNvenc) {
      args.addAll(['-c:v', 'hevc_nvenc', '-preset', 'p6', '-rc', 'vbr', '-cq', cq, '-b:v', '0']);
    } else if (isApple) {
      args.addAll(['-c:v', 'hevc_videotoolbox', '-q:v', preset == 'saver' ? '55' : '70', '-tag:v', 'hvc1']);
    } else if (isAmf) {
      args.addAll(['-c:v', 'hevc_amf', '-quality', 'quality', '-rc', 'cqp', '-qp_p', cq]);
    } else if (isQsv) {
      args.addAll(['-c:v', 'hevc_qsv', '-preset', 'veryslow', '-global_quality', cq]);
    } else {
      args.addAll(['-c:v', 'libx265', '-preset', 'slow', '-crf', crf]);
      if (preset == 'anime') args.addAll(['-tune', 'animation']);
    }

    // Preserve audio & subtitles losslessly
    args.addAll(['-c:a', 'copy', '-c:s', 'copy', '-map_metadata', '0', outputPath]);
    return args;
  }

  void cancel() {
    _isCancelled = true;
    _activeProcess?.kill(ProcessSignal.sigterm);
    _activeProcess = null;
  }

  void _cleanupFailedOutput(String path) {
    try {
      final f = File(path);
      if (f.existsSync()) f.deleteSync();
    } catch (_) {}
  }
}
