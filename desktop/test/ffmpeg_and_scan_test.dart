import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:desktop/models/hardware_engine.dart';
import 'package:desktop/services/mediacrush_cli.dart';
import 'package:desktop/services/transcode_service.dart';
import 'package:desktop/utils/ffmpeg_locator.dart';

void main() {
  group('FfmpegLocator', () {
    test('always returns a non-empty binary name/path', () async {
      expect(await FfmpegLocator.getFfmpegPath(), isNotEmpty);
      expect(await FfmpegLocator.getFfprobePath(), isNotEmpty);
    });

    test('path lookups are stable (cached)', () async {
      expect(await FfmpegLocator.getFfmpegPath(), await FfmpegLocator.getFfmpegPath());
    });

    test('availability agrees with the resolved binary', () async {
      final available = await FfmpegLocator.isFfmpegAvailable();
      final path = await FfmpegLocator.getFfmpegPath();
      final res = await Process.run(path, ['-version']).then((r) => r.exitCode == 0, onError: (_) => false);
      expect(available, res);
    });
  });

  group('MediaCrushCli.scanDirectory', () {
    late Directory tmp;
    final cli = MediaCrushCli();

    setUp(() => tmp = Directory.systemTemp.createTempSync('mc_scan_'));
    tearDown(() => tmp.deleteSync(recursive: true));

    void touch(String rel, [int bytes = 4]) {
      File(p.join(tmp.path, rel))
        ..createSync(recursive: true)
        ..writeAsBytesSync(List.filled(bytes, 1));
    }

    test('every supported extension is picked up (case-insensitive)', () async {
      for (final ext in MediaCrushCli.videoExtensions) {
        touch('v$ext');
        touch('UP${ext.toUpperCase()}');
      }
      final items = await cli.scanDirectory(tmp.path);
      expect(items, hasLength(MediaCrushCli.videoExtensions.length * 2));
    });

    test('ignores non-video files', () async {
      touch('a.txt');
      touch('b.jpg');
      touch('c.srt');
      expect(await cli.scanDirectory(tmp.path), isEmpty);
    });

    test('recurses and records size + 45% estimate', () async {
      touch('deep/er/clip.mkv', 2000);
      final items = await cli.scanDirectory(tmp.path);
      expect(items.single.originalBytes, 2000);
      expect(items.single.estimatedBytes, 900);
      expect(items.single.fileName, 'clip.mkv');
    });

    test('empty directory', () async {
      expect(await cli.scanDirectory(tmp.path), isEmpty);
    });
  });

  group('TranscodeService', () {
    test('returns false and leaves no output for a missing input', () async {
      final tmp = Directory.systemTemp.createTempSync('mc_tc_');
      addTearDown(() => tmp.deleteSync(recursive: true));
      final out = p.join(tmp.path, 'out.mp4');
      final progress = <double>[];
      final ok = await TranscodeService().transcode(
        inputPath: p.join(tmp.path, 'missing.mkv'),
        outputPath: out,
        engine: HardwareEngine.fallback(),
        preset: 'film',
        onProgress: progress.add,
      );
      expect(ok, isFalse);
      expect(File(out).existsSync(), isFalse);
    }, timeout: const Timeout(Duration(seconds: 60)));

    test('cancel is safe with no active process', () {
      TranscodeService().cancel();
    });
  });
}
